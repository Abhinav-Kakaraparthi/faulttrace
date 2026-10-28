"""Persistent conservative admission allowances, never a billing estimate."""
from contextlib import closing, contextmanager
import json
from pathlib import Path
import sqlite3
import time

from .storage import WorkflowError, identifier

# Full allowances stay consumed, even on rejection, missing usage or interruption.
# These are admission units, not an estimate of provider tokenization or price.
ALLOWANCE = {'planning': 65536 + 2048, 'photo': 262144 + 2048,
             'fixture': 262144 + 2048, 'documentation': 0}


class Spending:
    def __init__(self, root, *, requests=12, tokens=1200000,
                 session_requests=6, session_tokens=600000, concurrent=2):
        self.path = Path(root) / 'spending.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        limits = (requests, tokens, session_requests, session_tokens, concurrent)
        if any(type(n) is not int or n <= 0 for n in limits):
            raise ValueError('invalid_spending_limits')
        self.requests, self.tokens, self.session_requests, self.session_tokens, self.concurrent = limits
        with self.db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS reservations(
                id TEXT PRIMARY KEY, session TEXT, operation TEXT, allowance INTEGER,
                charged INTEGER, status TEXT, created REAL, accounting TEXT)''')

    @contextmanager
    def db(self):
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def recover_pending(self):
        # Called once after the owning demo instance lock, not by each child run.
        with self.db() as db:
            db.execute("UPDATE reservations SET status='uncertain' WHERE status='pending'")

    def for_session(self, session):
        return SessionSpending(self, session)

    def reserve(self, session, operation, attempt_id):
        identifier(attempt_id)
        if operation not in ALLOWANCE:
            raise WorkflowError('spending_operation_invalid', 503)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM reservations WHERE id=?', (attempt_id,)).fetchone()
            if old:
                if old['session'] != session or old['operation'] != operation:
                    raise WorkflowError('idempotency_conflict', 409)
                return
            total, charged = db.execute('SELECT COUNT(*),COALESCE(SUM(charged),0) FROM reservations').fetchone()
            own, own_charge = db.execute('SELECT COUNT(*),COALESCE(SUM(charged),0) FROM reservations WHERE session=?', (session,)).fetchone()
            allowance = ALLOWANCE[operation]
            if (total >= self.requests or charged + allowance > self.tokens
                    or own >= self.session_requests or own_charge + allowance > self.session_tokens):
                raise WorkflowError('spending_budget_exhausted', 429)
            if db.execute("SELECT COUNT(*) FROM reservations WHERE status='pending'").fetchone()[0] >= self.concurrent:
                raise WorkflowError('spending_concurrency_limit', 429)
            db.execute("INSERT INTO reservations VALUES(?,?,?,?,?,'pending',?,NULL)",
                       (attempt_id, session, operation, allowance, allowance, time.time()))

    def settle(self, session, attempt_id, receipt):
        # Accept only numeric accounting, fixed status. No raw provider/body fields.
        usage = receipt.get('token_usage') or {}
        counts = {k: v if type(v := usage.get(k)) is int and v >= 0 else None
                  for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
        status = receipt.get('usage_status')
        status = status if status in ('valid', 'partial', 'missing', 'invalid', 'inconsistent') else 'missing'
        value = json.dumps({'usage_status': status, 'token_usage': counts}, sort_keys=True)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM reservations WHERE id=? AND session=?', (attempt_id, session)).fetchone()
            if not row:
                raise WorkflowError('spending_reservation_missing', 503)
            if row['accounting'] and row['accounting'] != value:
                raise WorkflowError('spending_accounting_conflict', 503)
            known = max(counts['total_tokens'] or 0,
                        (counts['prompt_tokens'] or 0) + (counts['completion_tokens'] or 0))
            db.execute("UPDATE reservations SET status='settled',charged=?,accounting=? WHERE id=?",
                       (max(row['allowance'], known), value, attempt_id))

    def summary(self, session):
        with self.db() as db:
            rows = list(db.execute('SELECT * FROM reservations WHERE session=?', (session,)))
        return {'requests_reserved': len(rows), 'request_limit': self.session_requests,
                'token_allowance_consumed': sum(r['charged'] for r in rows),
                'token_allowance_limit': self.session_tokens,
                'uncertain_or_pending': sum(r['status'] in ('pending', 'uncertain') for r in rows),
                'label': 'Conservative admission allowances; not actual consumption or billing'}


class SessionSpending:
    def __init__(self, owner, session):
        self.owner, self.session = owner, session

    def reserve(self, operation, attempt_id):
        self.owner.reserve(self.session, operation, attempt_id)

    def settle(self, attempt_id, receipt):
        self.owner.settle(self.session, attempt_id, receipt)

    def summary(self):
        return self.owner.summary(self.session)
