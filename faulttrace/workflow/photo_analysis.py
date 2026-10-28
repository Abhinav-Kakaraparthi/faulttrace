"""Versioned photograph inference, reusing the existing worker and receipt outbox."""
import json
import uuid

from faulttrace.accounting import VISION_MODEL, new_receipt, sanitized_receipt
from faulttrace.ledger import LedgerError, load
from faulttrace.photo_observation import CONTRACT, request_photo, validate_photo_observation
from faulttrace.provider import run_probe
from faulttrace.validation import ProbeError
from .storage import WorkflowError, identifier, now


def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS photo_analyses (
        analysis_id TEXT PRIMARY KEY, evidence_id TEXT UNIQUE, contract TEXT,
        task_revision INTEGER, context_revision INTEGER, prior_task_status TEXT)""")


class PhotoAnalysis:
    def __init__(self, engine):
        self.engine, self.workflow, self.store = engine, engine.workflow, engine.store

    def reserve(self, evidence_id, revision, key):
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, 'analyze-photo', [evidence_id, revision])
            if existing:
                return existing, False
            evidence = db.execute('SELECT * FROM evidence WHERE id=?', (identifier(evidence_id),)).fetchone()
            if not evidence:
                raise WorkflowError('evidence_not_found', 404)
            previous = db.execute('SELECT analysis_id FROM photo_analyses WHERE evidence_id=?', (evidence_id,)).fetchone()
            if previous:
                self.store.remember(db, key, fingerprint, previous[0])
                return previous[0], False
            if (evidence['kind'] != 'image' or evidence['status'] != 'collected'
                    or evidence['origin'] != 'user-upload' or evidence['fixture_id'] is not None):
                raise WorkflowError('photo_contract_not_applicable', 409)
            task = self.store.task(db, evidence['task_id'], revision)
            latest_task = db.execute('SELECT id FROM tasks ORDER BY rowid DESC LIMIT 1').fetchone()[0]
            latest_photo = db.execute("SELECT id FROM evidence WHERE task_id=? AND kind='image' ORDER BY rowid DESC LIMIT 1", (task['id'],)).fetchone()[0]
            if latest_task != task['id'] or latest_photo != evidence_id:
                raise WorkflowError('stale_or_unanalyzable_evidence', 409)
            if task['status'] not in ('awaiting', 'needs_evidence', 'observed'):
                raise WorkflowError('analysis_in_progress', 409)
            if db.execute("SELECT 1 FROM analyses WHERE status='pending'").fetchone():
                raise WorkflowError('analysis_in_progress', 409)
            aid = str(uuid.uuid4())
            if self.engine.budget:
                self.engine.budget.reserve('photo', aid)
            db.execute("INSERT INTO analyses VALUES(?,?,'pending',?,NULL,NULL,NULL,'pending')", (aid, evidence_id, now()))
            db.execute("UPDATE tasks SET revision=revision+1,status='analyzing' WHERE id=?", (task['id'],))
            context_revision = db.execute('SELECT revision FROM incidents WHERE id=?', (task['incident_id'],)).fetchone()[0]
            db.execute('INSERT INTO photo_analyses VALUES(?,?,?,?,?,?)',
                       (aid, evidence_id, CONTRACT, revision+1, context_revision, task['status']))
            self.store.remember(db, key, fingerprint, aid)
            self.store.event(db, 'photo_analysis_explicitly_requested', evidence_id)
            return aid, True

    def analyze(self, evidence_id, revision, key):
        if not self.engine.enabled:
            raise WorkflowError('inference_disabled', 403)
        if not (self.engine.key_source() or '').strip():
            raise WorkflowError('missing_credentials', 503)
        aid, created = self.reserve(evidence_id, revision, key)
        if created:
            self.engine.futures.append(self.engine.executor.submit(self.perform, aid))
        return aid

    def perform(self, aid):
        with self.store.connection() as db:
            row = dict(db.execute('SELECT * FROM analyses WHERE id=?', (aid,)).fetchone())
        receipt = new_receipt(self.engine.revision, VISION_MODEL)
        interpretation = None
        try:
            evidence_id = identifier(row['evidence_id'])
            data = (self.store.images / (evidence_id + '.png')).read_bytes()
            key = self.engine.key_source()
            def validate(envelope):
                nonlocal interpretation
                value = validate_photo_observation(envelope, 'evidence-' + evidence_id)
                # A valid-looking transcription must not leak a credential either.
                if key and key.strip() and any(key in field for field in value.values() if isinstance(field, str)):
                    raise ProbeError('photo_invalid_text')
                interpretation = value
            receipt = run_probe(key, self.engine.revision, self.engine.send, model=VISION_MODEL,
                payload=request_photo(data, 'evidence-' + evidence_id), validator=validate)
        except Exception:
            receipt.update(error='probe_failed', validation_result='failed')
        receipt.update(attempt_id=aid, timestamp=row['created_at'])
        receipt = sanitized_receipt(receipt)
        if receipt['validation_result'] != 'passed':
            interpretation = None
        with self.store.connection(write=True) as db:
            db.execute('UPDATE analyses SET receipt=?,interpretation=? WHERE id=?',
                       (json.dumps(receipt), json.dumps(interpretation), aid))
        accounting = self.engine.account(receipt)
        self.finish(aid, receipt, interpretation, accounting)

    def finish(self, aid, receipt, interpretation, accounting, interrupted=False):
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            row = db.execute('SELECT a.status,p.* FROM analyses a JOIN photo_analyses p ON p.analysis_id=a.id WHERE a.id=?', (aid,)).fetchone()
            if row['status'] != 'pending':
                return
            task = db.execute('SELECT t.* FROM tasks t JOIN evidence e ON e.task_id=t.id WHERE e.id=?', (row['evidence_id'],)).fetchone()
            revision = db.execute('SELECT revision FROM incidents WHERE id=?', (task['incident_id'],)).fetchone()[0]
            latest_photo = db.execute("SELECT id FROM evidence WHERE task_id=? AND kind='image' ORDER BY rowid DESC LIMIT 1", (task['id'],)).fetchone()[0]
            latest_task = db.execute('SELECT id FROM tasks ORDER BY rowid DESC LIMIT 1').fetchone()[0]
            stale = (task['revision'] != row['task_revision'] or revision != row['context_revision']
                     or latest_photo != row['evidence_id'] or latest_task != task['id'])
            status, error = ('interpreted' if interpretation else 'failed'), receipt.get('error')
            if interrupted:
                status, error = 'uncertain', 'analysis_interrupted'
            elif accounting == 'failed':
                status, error = 'failed', 'accounting_persistence_failed'
            elif stale:
                status, error, interpretation = 'stale', 'stale_photo_result', None
            if stale:
                interpretation = None  # Even interrupted/accounting-failed results cannot retain stale readings.
            db.execute('UPDATE analyses SET status=?,receipt=?,interpretation=?,error=?,accounting=? WHERE id=?',
                       (status, json.dumps(receipt), json.dumps(interpretation), error, accounting, aid))
            # Preserve collection purpose and the prior human task state; no auto-completion.
            if task['revision'] == row['task_revision'] and task['status'] == 'analyzing':
                db.execute('UPDATE tasks SET revision=revision+1,status=? WHERE id=?', (row['prior_task_status'], task['id']))
            self.store.event(db, 'photo_analysis_' + status, row['evidence_id'])

    def recover(self):
        with self.store.connection() as db:
            rows = [dict(r) for r in db.execute("SELECT a.* FROM analyses a JOIN photo_analyses p ON p.analysis_id=a.id WHERE a.status='pending'")]
        if not rows:
            return
        try:
            prior = {r['attempt_id']: r for r in load(self.engine.ledger)}
        except LedgerError:
            prior = {}
        for row in rows:
            receipt = json.loads(row['receipt']) if row['receipt'] else prior.get(row['id'])
            if receipt is None:
                receipt = new_receipt(self.engine.revision, VISION_MODEL)
                receipt.update(attempt_id=row['id'], timestamp=row['created_at'], transport_invoked=None, error='probe_failed')
            interpretation = json.loads(row['interpretation']) if row['interpretation'] else None
            # Durable unknown/retained receipt, with no network replay on restart.
            with self.store.connection(write=True) as db:
                db.execute('UPDATE analyses SET receipt=? WHERE id=?', (json.dumps(receipt), row['id']))
            accounting = self.engine.account(receipt)
            self.finish(row['id'], receipt, interpretation, accounting, interrupted=True)
