"""Server-owned assignments and deny-by-default API authorization."""
import re

from .storage import WorkflowError, now

STARTS = {'/api/incidents', '/api/investigations', '/api/simulation/start'}
COMMANDER = {'/api/planning', '/api/continuation', '/api/simulation/approve', '/api/simulation/advance', '/api/simulation/monitor'}
OPERATOR_TASK = {'images', 'reports', 'observations', 'photo-follow-up'}


def denied():
    raise WorkflowError('access_denied', 403)


class Access:
    def __init__(self, store, registry):
        self.store, self.registry = store, registry
        store.assignment_source = lambda incident: registry.read()['operators'].get(incident)
        with store.connection(write=True) as db:
            db.execute('CREATE TABLE IF NOT EXISTS access_assignments(kind TEXT,id TEXT,principal TEXT,PRIMARY KEY(kind,id))')
            # Existing records are deliberately unassigned, including old approvals.
            for kind, table in (('task', 'tasks'), ('correction', 'sim_approvals')):
                db.execute(f'INSERT OR IGNORE INTO access_assignments SELECT ?,id,NULL FROM {table}', (kind,))
            db.execute('CREATE TABLE IF NOT EXISTS access_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT,principal TEXT,operation TEXT,status INTEGER,created_at TEXT)')
            db.executescript('''
              CREATE TRIGGER IF NOT EXISTS access_new_task AFTER INSERT ON tasks BEGIN
                INSERT INTO access_assignments VALUES('task',NEW.id,
                  faulttrace_operator(NEW.incident_id)); END;
              CREATE TRIGGER IF NOT EXISTS access_new_correction AFTER INSERT ON sim_approvals BEGIN
                INSERT INTO access_assignments VALUES('correction',NEW.id,
                  (SELECT faulttrace_operator(incident_id) FROM sim_runs)); END;
            ''')

    def audit(self, principal, method, status):
        # No raw URL, header, body, token, or upload is written to this audit trail.
        with self.store.connection(write=True) as db:
            db.execute('INSERT INTO access_audit(principal,operation,status,created_at) VALUES(?,?,?,?)',
                       (principal['principal_id'] if principal else None,
                        'read' if method in ('GET', 'HEAD') else 'mutation', status, now()))

    def incident(self, principal):
        with self.store.connection() as db:
            row = db.execute('SELECT id FROM incidents').fetchone()
        if not row or row['id'] not in principal['incidents']:
            denied()
        return row['id']

    def task(self, principal, task_id):
        with self.store.connection() as db:
            row = db.execute('SELECT t.incident_id,a.principal FROM tasks t LEFT JOIN access_assignments a '
                             "ON a.kind='task' AND a.id=t.id WHERE t.id=?", (task_id,)).fetchone()
        if not row or row['incident_id'] not in principal['incidents']:
            denied()
        if principal['role'] == 'operator' and row['principal'] != principal['principal_id']:
            denied()

    def evidence(self, principal, evidence_id):
        with self.store.connection() as db:
            row = db.execute('SELECT task_id FROM evidence WHERE id=?', (evidence_id,)).fetchone()
        if not row:
            denied()
        self.task(principal, row['task_id'])

    def correction(self, principal, approval):
        with self.store.connection() as db:
            row = db.execute("SELECT principal FROM access_assignments WHERE kind='correction' AND id=?", (approval,)).fetchone()
        if not row or row['principal'] != principal['principal_id']:
            denied()

    async def authorize(self, request, principal):
        path, method, role = request.url.path, request.method, principal['role']
        if method == 'GET' and path == '/api/identity':
            return
        if method == 'POST' and path in STARTS:
            if role != 'commander' or not principal['create']:
                denied()
            # Creation/replay resource checks use freshly authenticated grants
            # under the workflow creation lock, not this admission snapshot.
            return
        if method == 'GET' and path == '/api/state':
            with self.store.connection() as db:
                exists = db.execute('SELECT 1 FROM incidents').fetchone()
            if exists:
                self.incident(principal)
            return
        if path == '/api/documentation' and method in ('GET', 'POST') and role == 'commander':
            self.incident(principal)
            return
        match = re.fullmatch(r'/api/tasks/([^/]+)/([^/]+)', path)
        if match and method == 'POST':
            task, action = match.groups()
            if (action in OPERATOR_TASK and role == 'operator') or (action in ('reopen', 'renew-observation') and role == 'commander'):
                self.task(principal, task)
                return
            denied()
        match = re.fullmatch(r'/api/evidence/([^/]+)/(image|analyze|analyze-photo)', path)
        if match and ((method == 'GET' and match[2] == 'image') or
                      (method == 'POST' and match[2] != 'image')):
            self.evidence(principal, match[1])
            return
        if method == 'POST' and path in COMMANDER and role == 'commander':
            self.incident(principal)
            return
        if method == 'POST' and path == '/api/simulation/execute' and role == 'operator':
            self.incident(principal)
            # Assignment is checked in the route after its bounded body parser.
            return
        denied()

    def scope(self, principal, snapshot):
        if principal['role'] == 'commander':
            return snapshot
        with self.store.connection() as db:
            assigned = {r['id'] for r in db.execute("SELECT id FROM access_assignments WHERE kind='task' AND principal=?", (principal['principal_id'],))}
        snapshot['tasks'] = [t for t in snapshot['tasks'] if t['id'] in assigned]
        snapshot['task'] = snapshot['tasks'][-1] if snapshot['tasks'] else None
        snapshot['evidence'] = [e for e in snapshot['evidence'] if e['task_id'] in assigned]
        evidence_ids = {e['id'] for e in snapshot['evidence']}
        for task in snapshot['tasks']:
            task['source_photo_ids'] = [e for e in task['source_photo_ids'] if e in evidence_ids]
        snapshot['planning'], snapshot['events'] = [], []
        refs = {'evidence-' + e['id'] for e in snapshot['evidence']}
        for evidence in snapshot['evidence']:
            assessment = evidence.get('photo_assessment')
            if assessment:
                assessment['conflicting_refs'] = [r for r in assessment['conflicting_refs'] if r in refs]
        journey = snapshot.get('journey')
        if journey:
            with self.store.connection() as db:
                correction = db.execute("SELECT principal FROM access_assignments WHERE kind='correction' AND id=?", (journey['approval_id'],)).fetchone()
            if not correction or correction['principal'] != principal['principal_id']:
                journey['approval_id'], journey['approval_current'] = None, False
                journey['approved_evidence_refs'] = []
            journey['observations'] = [o for o in journey['observations'] if o['id'] in refs]
            for item in (journey, journey['assessment']):
                for field in ('evidence_refs', 'approved_evidence_refs'):
                    if field in item:
                        item[field] = [r for r in item[field] if r in refs or r.startswith('sample-')]
        return snapshot
