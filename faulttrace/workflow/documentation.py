"""Durable explicit reference lookup. No search result is investigation evidence."""
import json
import os
import threading
import time
import uuid

from fastapi import Request
from starlette.concurrency import run_in_threadpool

from faulttrace.partners.http import PartnerError
from faulttrace.partners.tavily import DOMAINS, context, parse, payload, tavily_transport
from faulttrace.partners.tracing import emit_trace
from .storage import WorkflowError, now


class Documentation:
    def __init__(self, app, enabled, key_source, send, budget):
        self.app, self.enabled, self.key_source, self.send, self.budget = app, enabled, key_source, send, budget
        self.lock, self.ready = threading.Lock(), False

    @property
    def workflow(self):
        return self.app.state.workflow

    def initialize(self):
        with self.lock:
            if self.ready:
                return
            with self.workflow.store.connection(write=True) as db:
                db.execute('''CREATE TABLE IF NOT EXISTS documentation (
                    id TEXT PRIMARY KEY, context_revision INTEGER, status TEXT, created_at TEXT,
                    context TEXT, result TEXT, receipt TEXT, error TEXT, trace_result TEXT)''')
                db.execute("UPDATE documentation SET status='uncertain',error='documentation_interrupted' WHERE status='pending'")
            self.ready = True

    def records(self):
        self.initialize()
        with self.workflow.store.connection() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM documentation ORDER BY created_at,id')]
        for row in rows:
            for field in ('context', 'result', 'receipt'):
                row[field] = json.loads(row[field]) if row[field] else None
        return {'records': rows, 'enabled': bool(self.enabled), 'domains': DOMAINS,
                'scope': 'Untrusted manufacturer references; not observed evidence or correction authority'}

    def reserve(self, body, key):
        self.initialize()
        try:
            value = context(body['manufacturer'], body['model'], body['domain'])
        except PartnerError as error:
            raise WorkflowError(error.code, 400) from None
        with self.workflow.write_lock, self.workflow.store.connection(write=True) as db:
            fingerprint, duplicate = self.workflow.store.operation(db, key, 'documentation', body)
            if duplicate:
                return duplicate, False
            incident = db.execute('SELECT revision FROM incidents').fetchone()
            if not incident:
                raise WorkflowError('incident_not_found', 404)
            if type(body['revision']) is not int or body['revision'] != incident['revision']:
                raise WorkflowError('stale_context', 409)
            if db.execute("SELECT 1 FROM documentation WHERE status='pending'").fetchone():
                raise WorkflowError('documentation_in_progress', 409)
            if db.execute('SELECT COUNT(*) FROM documentation').fetchone()[0] >= 4:
                raise WorkflowError('documentation_budget_exhausted', 429)
            record = str(uuid.uuid4())
            db.execute("INSERT INTO documentation(id,context_revision,status,created_at,context) VALUES(?,?,'pending',?,?)",
                       (record, body['revision'], now(), json.dumps(value)))
            self.workflow.store.remember(db, key, fingerprint, record)
            self.workflow.store.event(db, 'documentation_explicitly_requested')
            return record, True

    def search(self, body, key):
        if not self.enabled:
            raise WorkflowError('documentation_disabled', 403)
        secret = self.key_source()
        if not isinstance(secret, str) or not secret.strip():
            raise WorkflowError('documentation_credentials_unavailable', 503)
        if any(isinstance(body.get(field), str) and secret in body[field]
               for field in ('manufacturer', 'model', 'domain')):
            raise WorkflowError('documentation_context_invalid', 400)
        if self.budget is None:
            raise WorkflowError('documentation_budget_unavailable', 503)
        record, created = self.reserve(body, key)
        if not created:
            return {'record_id': record, 'duplicate': True}
        with self.workflow.store.connection() as db:
            row = dict(db.execute('SELECT * FROM documentation WHERE id=?', (record,)).fetchone())
        value, result, reserved = json.loads(row['context']), None, False
        receipt = {'attempt_id': record, 'operation': 'documentation', 'timestamp': row['created_at'],
                   'latency_ms': None, 'transport_invoked': False, 'validation_result': 'failed',
                   'usage_credits': None, 'error': None}
        start = time.monotonic()
        try:
            self.budget.reserve('documentation', record)
            reserved = True
            receipt['transport_invoked'] = True
            response = self.send(secret, payload(value))
            result = parse(response, value, secret)
            result['retrieved_at'] = now()
            receipt.update(validation_result='passed', usage_credits=result['usage_credits'])
        except PartnerError as error:
            receipt['error'] = error.code
        except WorkflowError as error:
            receipt['error'] = error.code if error.code in ('spending_budget_exhausted', 'demo_budget_exhausted', 'budget_exhausted') else 'documentation_budget_unavailable'
        except Exception:
            receipt['error'] = 'documentation_failed'
        receipt['latency_ms'] = max(0, round((time.monotonic()-start)*1000))
        # Durable outbox first. Pending/interrupted global reservations stay charged.
        with self.workflow.store.connection(write=True) as db:
            db.execute('UPDATE documentation SET result=?,receipt=? WHERE id=?',
                       (json.dumps(result), json.dumps(receipt), record))
        if reserved:
            try:
                self.budget.settle(record, receipt)
            except Exception:
                receipt['error'] = 'documentation_accounting_failed'
        trace = emit_trace('documentation', receipt)
        with self.workflow.write_lock, self.workflow.store.connection(write=True) as db:
            revision = db.execute('SELECT revision FROM incidents').fetchone()[0]
            status = 'completed' if receipt['validation_result'] == 'passed' and not receipt['error'] else 'failed'
            if revision != row['context_revision']:
                status = 'stale'
            db.execute('UPDATE documentation SET status=?,receipt=?,error=?,trace_result=? WHERE id=?',
                       (status, json.dumps(receipt), receipt['error'], trace, record))
            self.workflow.store.event(db, 'documentation_' + status)
        return {'record_id': record, 'status': status}


def register(app, *, enabled=False, key_source=None, send=tavily_transport, budget=None):
    """Caller must also authorize /api/documentation and enforce its Origin/CSRF boundary."""
    service = Documentation(app, enabled, key_source or (lambda: os.environ.get('TAVILY_API_KEY')), send, budget)
    app.state.documentation = service

    def commander(request):
        if getattr(app.state, 'access', None):
            principal = getattr(request.state, 'principal', None)
            if not principal or principal.get('role') != 'commander':
                raise WorkflowError('access_denied', 403)

    @app.get('/api/documentation')
    def records(request: Request):
        commander(request)
        return service.records()

    @app.post('/api/documentation')
    async def search(request: Request):
        from .api import fields
        commander(request)
        body = await fields(request, ['manufacturer', 'model', 'domain', 'revision'])
        return await run_in_threadpool(service.search, body, request.headers.get('idempotency-key'))

    return service
