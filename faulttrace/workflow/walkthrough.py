"""Explicit demo timing, observation renewal and durable simulated monitoring."""
import time
import uuid

from .storage import WorkflowError, now


def initialize(db):
    db.executescript('''CREATE TABLE IF NOT EXISTS journey_settings(
        singleton INTEGER PRIMARY KEY CHECK(singleton=1), time_mode TEXT);
        CREATE TABLE IF NOT EXISTS recovery_monitor(
        singleton INTEGER PRIMARY KEY CHECK(singleton=1), target_tick INTEGER,
        next_due REAL, status TEXT);''')


def paused_demo(db):
    return db.execute("SELECT 1 FROM journey_settings WHERE time_mode='paused-demo'").fetchone() is not None


def renew(journey, task_id, revision, key):
    """Create a new task/report identity; never redate or overwrite evidence."""
    from .planner_contract import build_context, permitted_actions
    with journey.workflow.write_lock, journey.store.connection(write=True) as db:
        fingerprint, prior = journey.store.operation(db, key, 'renew_observation', [task_id, revision])
        if prior:
            return prior
        journey.revision(db, revision)
        if journey.run(db)['executed_tick'] is not None or journey.blocking(db):
            raise WorkflowError('active_task_conflict', 409)
        task = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        if not task:
            raise WorkflowError('task_not_found', 404)
        action = 'OBSERVE_' + task['asset_id'] + '_' + task['capability']
        if action not in permitted_actions(build_context(db)):
            raise WorkflowError('demo_action_unavailable', 409)
        if db.execute("SELECT COUNT(*) FROM events WHERE kind='observation_renewal_requested'").fetchone()[0] >= 8:
            raise WorkflowError('simulation_observation_budget_exhausted', 409)
        new = str(uuid.uuid4())
        db.execute('''INSERT INTO tasks(id,incident_id,revision,status,created_at,asset_id,
            capability,creation_source,explanation) VALUES(?,?,1,'awaiting',?,?,?,?,?)''',
            (new, task['incident_id'], now(),
             task['asset_id'], task['capability'], 'Explicit human-requested observation renewal',
             'Collect a fresh independent observation. Previous reports remain in the audit record.'))
        journey.store.event(db, 'observation_renewal_requested')
        journey.store.remember(db, key, fingerprint, new)
        return new


class RecoveryMonitor:
    def __init__(self, journey, clock=time.time):
        self.journey, self.clock = journey, clock
        self.failed = False

    def start(self, revision, key):
        j = self.journey
        with j.workflow.write_lock, j.store.connection(write=True) as db:
            fingerprint, prior = j.store.operation(db, key, 'start_recovery_monitoring', revision)
            if prior:
                return prior
            j.revision(db, revision)
            run = j.run(db)
            if run['executed_tick'] is None:
                raise WorkflowError('simulated_correction_required', 409)
            old = db.execute('SELECT * FROM recovery_monitor').fetchone()
            if old:
                result = str(old['target_tick'])
            else:
                target = run['executed_tick'] + 6
                db.execute("INSERT INTO recovery_monitor VALUES(1,?,?,'running')", (target, self.clock()+1))
                j.store.event(db, 'accelerated_simulated_monitoring_started')
                result = str(target)
            j.store.remember(db, key, fingerprint, result)
            return result

    def step(self):
        """At most one sample per scheduler tick. Tests inject the wall clock."""
        j = self.journey
        if self.failed:
            return
        with j.workflow.write_lock:
            with j.store.connection() as db:
                row = db.execute('SELECT * FROM recovery_monitor').fetchone()
                if not row or row['status'] != 'running' or row['next_due'] > self.clock():
                    return
                run = j.run(db)
                revision = db.execute('SELECT revision FROM incidents').fetchone()[0]
                target, tick, incident = row['target_tick'], run['tick'], run['incident_id']
            if tick < target:
                key = str(uuid.uuid5(uuid.NAMESPACE_URL, f'faulttrace-monitor/{incident}/{tick+1}'))
                j.advance(revision, key)
            snapshot = j.snapshot()
            finished = snapshot['tick'] >= target or snapshot['recovery']['status'] == 'failed'
            with j.store.connection(write=True) as db:
                db.execute('UPDATE recovery_monitor SET status=?,next_due=?',
                           ('completed' if finished else 'running', self.clock()+1))
                if finished:
                    j.store.event(db, 'accelerated_simulated_monitoring_finished')

    def fail(self):
        self.failed = True
        try:
            with self.journey.store.connection(write=True) as db:
                db.execute("UPDATE recovery_monitor SET status='interrupted'")
                self.journey.store.event(db, 'accelerated_simulated_monitoring_interrupted')
        except Exception:
            pass  # Memory remains fail-closed even when durable storage is unavailable.

    def snapshot(self):
        with self.journey.store.connection() as db:
            row = db.execute('SELECT status,target_tick FROM recovery_monitor').fetchone()
        return dict(row, status='interrupted') if row and self.failed else dict(row) if row else None
