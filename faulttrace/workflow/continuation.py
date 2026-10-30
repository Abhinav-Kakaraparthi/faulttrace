"""Explicitly authorized, durable investigation continuation. Never approves actions."""
import time
import uuid

from .storage import WorkflowError, identifier


class Continuation:
    def __init__(self, app, registry=None, profile='local', clock=time.time):
        self.app, self.registry, self.clock = app, registry, clock
        self.workflow = app.state.workflow
        self.store = self.workflow.store
        # Demo gateway installs a live session/run check before allowing continuation.
        self.allowed = (lambda: profile != 'demo')
        with self.store.connection(write=True) as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS investigation_continuation(
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), incident_id TEXT,
                owner TEXT, enabled INTEGER, expires REAL, phase TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS continuation_steps(
                key TEXT PRIMARY KEY, kind TEXT, context TEXT, status TEXT, result TEXT);''')
            interrupted = db.execute("SELECT 1 FROM continuation_steps WHERE status='pending'").fetchone()
            if interrupted:
                db.execute("UPDATE continuation_steps SET status='uncertain' WHERE status='pending'")
                db.execute("UPDATE investigation_continuation SET enabled=0,phase='paused',error='continuation_interrupted'")

    def snapshot(self):
        with self.store.connection() as db:
            row = db.execute('SELECT enabled,expires,phase,error FROM investigation_continuation').fetchone()
        return dict(version=1, **dict(row)) if row else {
            'version': 1, 'enabled': False, 'expires': None, 'phase': 'idle', 'error': None}

    def configure(self, revision, enabled, key, principal=None):
        if type(enabled) is not bool:
            raise WorkflowError('invalid_request', 400)
        identifier(key)
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            owner = principal['principal_id'] if principal else 'local'
            fingerprint, prior = self.store.operation(db, key, 'continuation_consent', [revision, enabled, owner])
            if prior:
                return prior
            self.app.state.journey.revision(db, revision)
            from .investigation_evidence import integrated
            if not integrated(db):
                raise WorkflowError('task_investigation_required', 409)
            if enabled and not self.app.state.engine.enabled:
                raise WorkflowError('inference_disabled', 403)
            incident = db.execute('SELECT id FROM incidents').fetchone()[0]
            expires = min(self.clock() + 1800, principal.get('expires', float('inf'))) if principal else self.clock() + 1800
            db.execute('INSERT OR REPLACE INTO investigation_continuation VALUES(1,?,?,?,?,?,NULL)',
                       (incident, owner, int(enabled), expires, 'starting' if enabled else 'paused'))
            self.store.event(db, 'guided_investigation_started' if enabled else 'guided_investigation_paused')
            self.store.remember(db, key, fingerprint, incident)
            return incident

    def phase(self, phase, error=None, stop=False):
        with self.store.connection(write=True) as db:
            prior = db.execute('SELECT phase,error,enabled FROM investigation_continuation').fetchone()
            if prior and prior['phase'] == phase and prior['error'] == error and not (stop and prior['enabled']):
                return
            db.execute('UPDATE investigation_continuation SET phase=?,error=?,enabled=CASE WHEN ? THEN 0 ELSE enabled END',
                       (phase, error, int(stop)))
            self.store.event(db, 'guided_investigation_' + phase)

    def authorized(self, consent):
        if consent['expires'] <= self.clock() or not self.allowed():
            return False
        if self.registry:
            principals = self.registry.read()['principals']
            principal = principals.get(consent['owner'])
            if principal is None:
                # DemoRegistry keys by workspace role while authentication returns
                # a stable demo principal_id. Resolve that exact identity only.
                matches = [p for p in principals.values()
                           if p.get('principal_id') == consent['owner']]
                principal = matches[0] if len(matches) == 1 else None
            return bool(principal and principal['role'] == 'commander'
                        and not principal.get('revoked', False)
                        and principal.get('expires', float('inf')) > self.clock()
                        and consent['incident_id'] in principal['incidents'])
        return consent['owner'] == 'local'

    def once(self, kind, context, operation):
        """Journal before dispatch; a crash never replays an ambiguous provider request."""
        key = str(uuid.uuid5(uuid.NAMESPACE_URL, f'faulttrace-continuation/{kind}/{context}'))
        with self.store.connection(write=True) as db:
            prior = db.execute('SELECT status FROM continuation_steps WHERE key=?', (key,)).fetchone()
            if prior:
                if prior['status'] != 'reserved':
                    raise WorkflowError('continuation_dispatch_not_replayable', 409)
                return
            db.execute("INSERT INTO continuation_steps VALUES(?,?,?,'pending',NULL)", (key, kind, str(context)))
        try:
            result = operation(key)
        except Exception:
            with self.store.connection(write=True) as db:
                db.execute("UPDATE continuation_steps SET status='stopped' WHERE key=?", (key,))
            raise
        with self.store.connection(write=True) as db:
            db.execute("UPDATE continuation_steps SET status='reserved',result=? WHERE key=?", (str(result), key))

    def step(self):
        with self.workflow.write_lock:
            with self.store.connection() as db:
                row = db.execute('SELECT * FROM investigation_continuation WHERE enabled=1').fetchone()
            if not row:
                return
            try:
                if not self.authorized(dict(row)):
                    self.phase('paused', 'continuation_access_ended', True)
                    return
                self.advance()
            except WorkflowError as error:
                self.phase('paused', error.code, True)
            except Exception:
                self.phase('paused', 'continuation_interrupted', True)

    def advance(self):
        snapshot = self.store.snapshot()
        journey = self.app.state.journey.snapshot()
        revision = snapshot['incident']['revision']
        if journey['maintenance_status'] != 'not_completed':
            recovery = journey['recovery']['status']
            monitor = self.app.state.monitor.snapshot()
            if monitor and monitor['status'] == 'interrupted':
                self.phase('escalated', 'recovery_monitoring_interrupted', True)
                return
            if recovery in ('verified', 'failed'):
                self.phase('complete' if recovery == 'verified' else 'escalated',
                           None if recovery == 'verified' else 'recovery_not_verified', True)
            else:
                self.once('monitor', snapshot['incident']['id'], lambda key: self.app.state.monitor.start(revision, key))
                self.app.state.start_monitor()
                self.phase('verifying_recovery')
            return
        if journey['approval_current']:
            self.phase('awaiting_operator_action')
            return
        if journey['assessment']['eligible']:
            self.phase('awaiting_approval')
            return
        plans = snapshot['planning']
        if any(p['status'] == 'pending' for p in plans):
            self.phase('planning')
            return
        if plans and plans[-1]['status'] in ('escalated', 'rejected', 'uncertain'):
            self.phase('escalated', 'planning_' + plans[-1]['status'], True)
            return
        task = snapshot['task']
        if task:
            if task['status'] in ('submitted', 'analyzing'):
                self.phase('analyzing_evidence')
                return
            photos = [e for e in snapshot['evidence'] if e['task_id'] == task['id'] and e['kind'] == 'image']
            latest = photos[-1] if photos else None
            if latest and latest.get('analysis') and latest['analysis']['status'] in ('failed', 'uncertain', 'rejected', 'stale'):
                self.phase('escalated', 'photo_result_requires_review', True)
                return
            if task['status'] == 'awaiting' and latest:
                analysis = latest.get('analysis')
                if not analysis:
                    self.phase('awaiting_photo_analysis')
                    return
                assessment = latest.get('photo_assessment')
                if analysis['status'] == 'interpreted' and assessment:
                    if assessment['status'] == 'usable':
                        self.phase('awaiting_independent_review')
                        return
                    if assessment['status'] == 'stale':
                        self.phase('escalated', 'stale_photo_result', True)
                        return
                    from .photo_planning import forward_for_planning
                    self.once('photo-follow-up', latest['id'], lambda key: forward_for_planning(
                        self.workflow, task['id'], task['revision'], latest['id'], key))
                    self.phase('planning')
                    return
                self.phase('awaiting_independent_review')
                return
            if task['status'] == 'awaiting':
                self.phase('awaiting_field_evidence')
                return
        if snapshot['planning_remaining'] <= 0:
            self.phase('escalated', 'planning_budget_exhausted', True)
            return
        self.once('plan', f"{snapshot['incident']['id']}/{revision}",
                  lambda key: self.app.state.engine.planner.choose(revision, key))
        self.phase('planning')


def register(app, fields, request_key):
    from fastapi import Request
    from starlette.concurrency import run_in_threadpool

    @app.post('/api/continuation')
    async def configure(request: Request):
        body = await fields(request, ['revision', 'enabled'])
        result = await run_in_threadpool(app.state.continuation.configure, body['revision'], body['enabled'],
                                         request_key(request), getattr(request.state, 'principal', None))
        return {'incident_id': result}
