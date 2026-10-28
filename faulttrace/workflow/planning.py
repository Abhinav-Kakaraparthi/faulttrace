"""Durable planning reservations; shared worker, transport, outbox and ledger."""
import json
import uuid

from faulttrace.accounting import MODEL, new_receipt, sanitized_receipt
from faulttrace.ledger import LedgerError, load
from faulttrace.provider import run_probe

from .planner_contract import EXPLANATIONS, build_context, planner_payload, validate_action_plan
from .storage import WorkflowError, now


class Planner:
    def __init__(self, engine):
        self.engine, self.workflow, self.store = engine, engine.workflow, engine.store
        self.recover()

    def reserve(self, revision, key):
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            fingerprint, duplicate = self.store.operation(db, key, 'plan', revision)
            if duplicate:
                return duplicate, False
            incident = db.execute('SELECT * FROM incidents').fetchone()
            if not incident:
                raise WorkflowError('incident_not_found', 404)
            existing = db.execute('SELECT id FROM planning WHERE incident_id=? AND context_revision=?',
                                  (incident['id'], revision)).fetchone()
            if existing:
                self.store.remember(db, key, fingerprint, existing['id'])
                return existing['id'], False
            if type(revision) is not int or incident['revision'] != revision:
                raise WorkflowError('stale_context', 409)
            if db.execute("SELECT id FROM planning WHERE status='pending'").fetchone():
                raise WorkflowError('planning_in_progress', 409)
            if db.execute("SELECT id FROM tasks WHERE status IN ('awaiting','submitted','analyzing')").fetchone():
                raise WorkflowError('active_task_conflict', 409)
            if db.execute('SELECT COUNT(*) FROM planning').fetchone()[0] >= 4:
                raise WorkflowError('planning_budget_exhausted', 409)
            context = build_context(db)
            attempt_id = str(uuid.uuid4())
            if self.engine.budget:
                self.engine.budget.reserve('planning', attempt_id)
            db.execute("""INSERT INTO planning(id,incident_id,context_revision,status,created_at,context,accounting)
                VALUES(?,?,?,'pending',?,?,'pending')""",
                       (attempt_id, incident['id'], revision, now(), json.dumps(context)))
            self.store.remember(db, key, fingerprint, attempt_id)
            self.store.event(db, 'planning_explicitly_requested')
            return attempt_id, True

    def choose(self, revision, key):
        if not self.engine.enabled:
            raise WorkflowError('inference_disabled', 403)
        if not (self.engine.key_source() or '').strip():
            raise WorkflowError('missing_credentials', 503)
        attempt_id, created = self.reserve(revision, key)
        if created:
            self.engine.futures.append(self.engine.executor.submit(self.perform, attempt_id))
        return attempt_id

    def perform(self, attempt_id):
        with self.store.connection() as db:
            row = dict(db.execute('SELECT * FROM planning WHERE id=?', (attempt_id,)).fetchone())
        context, proposal = json.loads(row['context']), None

        def validate(envelope):
            nonlocal proposal
            proposal = validate_action_plan(envelope, context)

        receipt = run_probe(self.engine.key_source(), self.engine.revision, self.engine.send,
                            payload=planner_payload(context), validator=validate)
        receipt.update(attempt_id=attempt_id, timestamp=row['created_at'])
        receipt = sanitized_receipt(receipt)
        if receipt['validation_result'] != 'passed':
            proposal = None
        # Durable outbox precedes external ledger; no transaction spans the call.
        with self.store.connection(write=True) as db:
            db.execute('UPDATE planning SET receipt=?,proposal=? WHERE id=?',
                       (json.dumps(receipt), json.dumps(proposal), attempt_id))
        accounting = self.engine.account(receipt)
        self.finish(attempt_id, receipt, proposal, accounting)

    def finish(self, attempt_id, receipt, proposal, accounting, interrupted=False):
        with self.workflow.write_lock, self.store.connection(write=True) as db:
            row = db.execute('SELECT * FROM planning WHERE id=?', (attempt_id,)).fetchone()
            incident = db.execute('SELECT revision FROM incidents WHERE id=?', (row['incident_id'],)).fetchone()
            status, error, task_id = 'rejected', receipt.get('error'), None
            if interrupted:
                status, error = 'uncertain', 'planning_interrupted'
            elif accounting == 'failed':
                error = 'accounting_persistence_failed'
            elif incident['revision'] != row['context_revision']:
                error = 'stale_context'
            elif db.execute("SELECT id FROM tasks WHERE status IN ('awaiting','submitted','analyzing')").fetchone():
                error = 'active_task_conflict'
            elif proposal:
                status = 'escalated' if proposal['kind'] == 'ESCALATE' else 'accepted'
                if status == 'accepted':
                    task_id = str(uuid.uuid4())
                    db.execute('''INSERT INTO tasks(id,incident_id,revision,status,created_at,asset_id,
                        capability,creation_source,explanation) VALUES(?,?,1,'awaiting',?,?,?,'validated NVIDIA proposal',?)''',
                        (task_id, row['incident_id'], now(), proposal['asset_id'], proposal['capability'],
                         EXPLANATIONS[proposal['explanation_code']]))
                    from .investigation_evidence import integrated
                    if integrated(db) and db.execute('SELECT test_output FROM integrated_runs').fetchone()[0]:
                        db.execute("UPDATE tasks SET creation_source='TEST-CREATED / offline provider double' WHERE id=?", (task_id,))
            explanation = EXPLANATIONS[proposal['explanation_code']] if proposal else None
            db.execute('UPDATE planning SET status=?,proposal=?,receipt=?,error=?,accounting=?,task_id=?,explanation=? WHERE id=?',
                       (status, json.dumps(proposal), json.dumps(receipt), error, accounting, task_id, explanation, attempt_id))
            self.store.event(db, 'planning_' + status)

    def recover(self):
        with self.store.connection() as db:
            pending = [dict(r) for r in db.execute("SELECT * FROM planning WHERE status='pending'")]
        if not pending:
            return
        try:
            prior = {r['attempt_id']: r for r in load(self.engine.ledger)}
        except LedgerError:
            prior = {}
        for row in pending:
            receipt = json.loads(row['receipt']) if row['receipt'] else prior.get(row['id'])
            if receipt is None:
                receipt = new_receipt(self.engine.revision, MODEL)
                receipt.update(attempt_id=row['id'], timestamp=row['created_at'], transport_invoked=None, error='probe_failed')
            proposal = json.loads(row['proposal']) if row['proposal'] else None
            self.finish(row['id'], receipt, proposal, self.engine.account(receipt), interrupted=True)
