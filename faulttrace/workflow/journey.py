"""Opt-in synthetic journey. Human approval is separate from observation planning."""
from datetime import datetime, timezone
import json
import math
import uuid

from . import simulation
from .recovery_policy import POLICY, assess, verify
from .storage import WorkflowError, identifier

ACTION = 'SIMULATE_F17_FILTER_REPLACEMENT'


class Journey:
    def __init__(self, workflow, clock=None, outcome='effective', test_output=False, demo_time=False):
        self.workflow, self.store = workflow, workflow.store
        self.test_output = test_output
        self.demo_time = demo_time
        self.clock = clock or (lambda: datetime.now(timezone.utc).timestamp())
        if outcome not in ('effective', 'ineffective', 'relapse'):
            raise ValueError('invalid_fixture_outcome')
        self.outcome = outcome  # Test-only injection; never accepted from an HTTP request.

    def run(self, db):
        row = db.execute('SELECT * FROM sim_runs').fetchone()
        if not row:
            raise WorkflowError('simulation_not_started', 409)
        return row

    def revision(self, db, revision):
        row = db.execute('SELECT revision FROM incidents').fetchone()
        if type(revision) is not int or not row or row['revision'] != revision:
            raise WorkflowError('stale_context', 409)

    def bump(self, db):
        db.execute('UPDATE incidents SET revision=revision+1')

    def start(self, key, integrated=False):
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, 'investigation_start' if integrated else 'simulation_start', {})
            if existing:
                return existing
            if db.execute('SELECT id FROM incidents').fetchone():
                raise WorkflowError('simulation_requires_fresh_run', 409)
            incident_id = str(uuid.uuid4())
            epoch = self.clock()
            stamp = datetime.fromtimestamp(epoch, timezone.utc).isoformat()
            db.execute('INSERT INTO incidents(id,singleton,created_at) VALUES(?,1,?)', (incident_id, stamp))
            db.execute('INSERT INTO sim_runs(incident_id,epoch,tick,private_outcome) VALUES(?,?,0,?)',
                       (incident_id, epoch, self.outcome))
            if integrated:
                db.execute('INSERT INTO integrated_runs(incident_id,test_output) VALUES(?,?)', (incident_id, int(self.test_output)))
            simulation.sample(db, self.run(db))
            self.store.event(db, 'task_investigation_started' if integrated else 'synthetic_journey_started')
            self.store.remember(db, key, fingerprint, incident_id)
            return incident_id

    def advance(self, revision, key):
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, 'simulation_step', revision)
            if existing:
                return existing
            run = self.run(db)
            self.revision(db, revision)
            if run['tick'] >= 360:
                raise WorkflowError('simulation_step_budget_exhausted', 409)
            db.execute('UPDATE sim_runs SET tick=tick+1')
            simulation.sample(db, self.run(db))
            self.bump(db)
            result = str(run['tick'] + 1)
            self.store.event(db, 'synthetic_telemetry_sampled')
            self.store.remember(db, key, fingerprint, result)
            return result

    def observe(self, revision, asset, status, reading, key):
        if type(asset) is not str or type(status) is not str:
            raise WorkflowError('invalid_simulated_observation')
        allowed = {'F-17': ('readable', 'unreadable', 'cannot-access', 'wrong-equipment'),
                   'V-08': ('intermediate', 'open', 'closed', 'cannot determine', 'cannot-access', 'wrong-equipment')}
        if asset not in allowed or status not in allowed[asset]:
            raise WorkflowError('invalid_simulated_observation')
        numeric = type(reading) in (int, float) and math.isfinite(reading) and 0 <= reading <= 1000
        if (asset == 'F-17' and status == 'readable' and not numeric) or (status != 'readable' and reading is not None):
            raise WorkflowError('invalid_simulated_observation')
        payload = [revision, asset, status, reading]
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, 'simulation_observe', payload)
            if existing:
                return existing
            run = self.run(db)
            self.revision(db, revision)
            from .investigation_evidence import integrated
            if integrated(db):
                raise WorkflowError('task_observation_required', 409)
            if run['executed_tick'] is not None:
                raise WorkflowError('simulation_observations_closed', 409)
            if db.execute('SELECT COUNT(*) FROM sim_observations').fetchone()[0] >= 32:
                raise WorkflowError('simulation_observation_budget_exhausted', 409)
            evidence_id = 'observation-' + str(uuid.uuid4())
            db.execute('INSERT INTO sim_observations VALUES(?,?,?,?,?,?,?,?)',
                       (evidence_id, asset, status, reading, 'kPa' if numeric else None,
                        'simulated-human-report', simulation.timestamp(run), run['tick']))
            self.bump(db)
            self.store.event(db, 'simulated_operator_observation', evidence_id)
            self.store.remember(db, key, fingerprint, evidence_id)
            return evidence_id

    def approve(self, revision, action_id, decision, key):
        if action_id != ACTION or type(action_id) is not str or decision not in ('approve', 'decline'):
            raise WorkflowError('invalid_simulated_action')
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, 'simulation_approval', [revision, action_id, decision])
            if existing:
                return existing
            run = self.run(db)
            self.revision(db, revision)
            if run['executed_tick'] is not None:
                raise WorkflowError('simulation_already_executed', 409)
            if decision == 'decline':
                db.execute('UPDATE sim_runs SET approval_id=NULL,approved_revision=NULL,approval_refs=NULL')
                self.bump(db)  # A new decision invalidates old approval/click identities.
                self.store.event(db, 'simulated_correction_declined')
                result = 'declined'
            else:
                assessment = assess(db, run, self.clock(), self.demo_time)
                if not assessment['eligible']:
                    raise WorkflowError('correction_evidence_blocked', 409)
                if self.blocking(db):
                    raise WorkflowError('active_task_conflict', 409)
                if run['approval_id'] and run['approved_revision'] == revision:
                    result = run['approval_id']
                else:
                    result = str(uuid.uuid4())
                    refs = json.dumps(assessment['evidence_refs'])
                    db.execute('INSERT INTO sim_approvals VALUES(?,?,?,?,?)',
                               (result, revision, refs, simulation.timestamp(run), action_id))
                    db.execute('UPDATE sim_runs SET approval_id=?,approved_revision=?,approval_refs=?', (result, revision, refs))
                    self.store.event(db, 'simulated_correction_approved')
            self.store.remember(db, key, fingerprint, result)
            return result

    @staticmethod
    def blocking(db):
        return (db.execute("SELECT 1 FROM tasks WHERE status IN ('awaiting','submitted','analyzing')").fetchone()
                or db.execute("SELECT 1 FROM planning WHERE status='pending'").fetchone())

    def execute(self, revision, approval_id, key):
        identifier(approval_id)
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, 'simulation_execute', [revision, approval_id])
            if existing:
                return existing
            run = self.run(db)
            self.revision(db, revision)
            if run['approval_id'] != approval_id or run['approved_revision'] != revision:
                raise WorkflowError('stale_or_missing_approval', 409)
            if not assess(db, run, self.clock(), self.demo_time)['eligible'] or self.blocking(db):
                raise WorkflowError('correction_evidence_blocked', 409)
            if run['executed_tick'] is not None:
                raise WorkflowError('simulation_already_executed', 409)
            db.execute('UPDATE sim_runs SET corrected_tick=tick,executed_tick=tick')
            self.bump(db)
            self.store.event(db, 'simulated_filter_replacement_completed')
            self.store.remember(db, key, fingerprint, approval_id)
            return approval_id

    def snapshot(self):
        with self.store.connection() as db:
            run = db.execute('SELECT * FROM sim_runs').fetchone()
            if not run:
                return None
            samples = simulation.public_samples(db)
            from .investigation_evidence import observations as records, integrated
            observations = records(db)
            assessment = assess(db, run, self.clock(), self.demo_time)
            if self.blocking(db):
                assessment['blockers'].append('active_observation_or_planning')
                assessment['eligible'] = False
            revision = db.execute('SELECT revision FROM incidents').fetchone()[0]
            from .walkthrough import paused_demo
            return {'label': 'Synthetic return-loop journey; no equipment connection',
                    'evidence_mode': 'task-evidence' if integrated(db) else 'legacy-simulation',
                    'test_output': bool(db.execute('SELECT test_output FROM integrated_runs').fetchone()[0]) if integrated(db) else False,
                    'clock': simulation.timestamp(run), 'tick': run['tick'], 'samples': samples,
                    'time_mode': 'paused-demo' if self.demo_time and paused_demo(db) else 'wall-clock-evidence',
                    'observations': observations, 'assessment': assessment, 'policy': POLICY,
                    'action_id': ACTION, 'approval_id': run['approval_id'],
                    'approved_evidence_refs': json.loads(run['approval_refs']) if run['approval_refs'] else [],
                    'approval_current': run['approval_id'] is not None and run['approved_revision'] == revision,
                    'maintenance_status': 'simulated_replacement_completed' if run['executed_tick'] is not None else 'not_completed',
                    'recovery': verify(samples, run['executed_tick'], run['tick'])}
