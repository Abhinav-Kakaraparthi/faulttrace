"""Read-only sprint audit and persistent verification caps; never imports receipts."""
from contextlib import closing, contextmanager
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sqlite3

from faulttrace.accounting import MODEL, VISION_MODEL
from faulttrace.workflow.spending import Spending
from faulttrace.workflow.storage import WorkflowError
from faulttrace.validation import parse_json

BASE = '68634ad0c754252ebb03e182f765e70874a51f3d'
# Conservative boundary: the committed baseline preceding the authorized sprint.
SINCE = datetime.fromisoformat('2026-10-28T15:13:27-04:00').timestamp()
CAPS = {'planning': 2, 'photo': 1, 'documentation': 1}


class SafeFailure(Exception):
    pass


@contextmanager
def readonly(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True, timeout=5)) as db:
        db.row_factory = sqlite3.Row
        yield db


def audit(root):
    """Only accounting artifacts, never response.json, images, headers or contexts."""
    found, paths, excluded = {}, [], set()
    local = Path(root)/'.local'
    for directory, dirs, files in os.walk(local, followlinks=False):
        dirs[:] = [d for d in dirs if d not in ('worktrees', 'node_modules', '.git', '__pycache__')]
        for name in files:
            p = Path(directory)/name
            if p.resolve().is_relative_to(local.resolve()):
                if name in ('spending.sqlite3', 'workflow.sqlite3', 'usage.json', 'nebius-usage.json', 'result.json', 'receipt.json', 'sanitized-receipt.json'):
                    paths.append(p)

    def add(aid, operation, stamp, failed=False, uncertain=False):
        if operation == 'fixture':
            operation = 'photo'  # Conservatively counts all image calls against one photo slot.
        if operation not in CAPS:
            raise SafeFailure('inventory_unknown_operation')
        try:
            if type(stamp) in (float, int):
                epoch = stamp
            else:
                parsed = datetime.fromisoformat(stamp)
                if parsed.tzinfo is None:
                    raise ValueError()
                epoch = parsed.timestamp()
            if not math.isfinite(epoch):
                raise ValueError()
            if epoch < SINCE:
                return
            from faulttrace.workflow.storage import identifier
            identifier(aid)
        except Exception:
            raise SafeFailure('inventory_invalid_metadata') from None
        prior = found.get(aid)
        if prior and prior['operation'] != operation:
            raise SafeFailure('inventory_conflicting_attempt')
        found[aid] = {'operation': operation, 'failed': failed or bool(prior and prior['failed']),
                      'uncertain': uncertain or bool(prior and prior['uncertain']),
                      'trace_failed':bool(prior and prior.get('trace_failed'))}

    def receipt(value, row_failed=False):
        if not isinstance(value, dict):
            return
        if 'attempt_id' not in value or 'requested_model' not in value:
            for key in ('receipt', 'receipts', 'result', 'results'):
                children = value.get(key)
                for child in children if isinstance(children, list) else [children]:
                    receipt(child)
            return
        if value.get('transport_invoked') is False:
            return
        model = value['requested_model']
        op = 'planning' if model == MODEL else 'photo' if model == VISION_MODEL else None
        add(value['attempt_id'], op, value.get('timestamp'),
            row_failed or value.get('validation_result') != 'passed', value.get('transport_invoked') is not True)

    try:
        for p in paths:
            if p.name != 'workflow.sqlite3':
                continue
            with readonly(p) as db:
                tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if 'integrated_runs' in tables and db.execute('SELECT 1 FROM integrated_runs WHERE test_output=1').fetchone():
                    excluded.add(p.parent.parent/'usage.json')
                    continue
                for table in ('planning', 'analyses'):
                    if table in tables:
                        for row in db.execute(f'SELECT id,created_at,status,receipt FROM {table}'):
                            if row['receipt']:
                                receipt(parse_json(row['receipt']), row['status'] in ('failed','rejected','uncertain','stale'))
                            elif row['status'] == 'pending':
                                add(row['id'], 'planning' if table == 'planning' else 'photo', row['created_at'], uncertain=True)
                if 'documentation' in tables:
                    for row in db.execute('SELECT id,created_at,status,receipt,trace_result FROM documentation'):
                        value = parse_json(row['receipt']) if row['receipt'] else {}
                        if value.get('transport_invoked') is not False:
                            add(row['id'], 'documentation', row['created_at'],
                                row['status'] not in ('completed','pending'), row['status'] in ('pending','uncertain'))
                            if row['id'] in found and row['trace_result'] in ('failed','unavailable','unknown'):
                                found[row['id']]['trace_failed'] = True
                if 'trace_exports' in tables:
                    for row in db.execute('SELECT attempt_id,status FROM trace_exports'):
                        if row['attempt_id'] in found and row['status'] in ('failed','unavailable','unknown'):
                            found[row['attempt_id']]['trace_failed'] = True
        for p in paths:
            if p in excluded or p.name == 'workflow.sqlite3':
                continue
            if p.name == 'spending.sqlite3':
                with readonly(p) as db:
                    for r in db.execute('SELECT id,operation,created,status FROM reservations'):
                        add(r['id'],r['operation'],r['created'],uncertain=r['status'] in ('pending','uncertain'))
            elif p.stat().st_size <= 4*1024*1024:
                receipt(parse_json(p.read_text(encoding='utf-8-sig')))
            else:
                raise SafeFailure('inventory_artifact_too_large')
    except SafeFailure:
        raise
    except Exception:
        raise SafeFailure('inventory_unreadable') from None
    return found


class Control:
    def __init__(self, root, verify=None):
        self.root = Path(root)
        self.verify = verify
        directory = self.root/'.local/sprint-verification'
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory/'limits.sqlite3'
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS slots(id TEXT PRIMARY KEY,operation TEXT,status TEXT);
                CREATE TABLE IF NOT EXISTS blocked(operation TEXT PRIMARY KEY,reason TEXT);''')

    @contextmanager
    def db(self):
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def snapshot(self):
        records = audit(self.root)
        with self.db() as db:
            blocked = {r['operation'] for r in db.execute('SELECT operation FROM blocked')}
            for row in db.execute('SELECT * FROM slots'):
                records.setdefault(row['id'], {'operation':row['operation'], 'failed':False,
                                               'uncertain':row['status']=='reserved'})
        for value in records.values():
            if value['failed'] or value['uncertain']:
                blocked.add(value['operation'])
            if value.get('trace_failed'):
                blocked.add('tracing')
        return {'used':{op:sum(v['operation']==op for v in records.values()) for op in CAPS},
                'blocked':sorted(blocked), 'attempts':records}

    def reserve(self, operation, aid):
        if self.verify:
            self.verify()  # Recheck the pinned checkout immediately before admission.
        snapshot = self.snapshot()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT operation FROM slots WHERE id=?',(aid,)).fetchone()
            if old:
                if old[0] != operation:
                    raise WorkflowError('idempotency_conflict',409)
                return
            records = dict(snapshot['attempts'])
            # Documentation persists its pending application row BEFORE asking
            # the global budget. This same ID is not an additional earlier call.
            current = records.pop(aid,None)
            if current and current['operation'] != operation:
                raise WorkflowError('idempotency_conflict',409)
            for row in db.execute('SELECT * FROM slots'):
                records.setdefault(row['id'], {'operation':row['operation']})
            blocked = {r[0] for r in db.execute('SELECT operation FROM blocked')}
            blocked |= {r['operation'] for r in records.values() if r.get('failed') or r.get('uncertain')}
            if operation not in CAPS or operation in blocked or sum(r['operation']==operation for r in records.values()) >= CAPS[operation]:
                raise WorkflowError('spending_budget_exhausted',429)
            db.execute("INSERT INTO slots VALUES(?,?,'reserved')",(aid,operation))

    def complete(self, aid, failed):
        with self.db() as db:
            row = db.execute('SELECT operation FROM slots WHERE id=?',(aid,)).fetchone()
            if row:
                db.execute("UPDATE slots SET status='completed' WHERE id=?",(aid,))
                if failed:
                    db.execute('INSERT OR IGNORE INTO blocked VALUES(?,?)',(row[0],'operation_failed_or_accounting_incomplete'))

    def block(self, operation):
        with self.db() as db:
            db.execute('INSERT OR IGNORE INTO blocked VALUES(?,?)',(operation,'operation_failed'))


class SprintSpending(Spending):
    """Stricter verification admission around the unchanged production budget."""
    def __init__(self, root, control):
        super().__init__(root, requests=4, session_requests=4, concurrent=1)
        self.control = control

    def reserve(self, session, operation, aid):
        self.control.reserve(operation, aid)  # Durable before any provider contact.
        super().reserve(session,operation,aid)

    def settle(self, session, aid, receipt):
        super().settle(session,aid,receipt)
        failed = receipt.get('validation_result') != 'passed'
        if receipt.get('operation') != 'documentation':
            failed |= receipt.get('usage_status') != 'valid'
        self.control.complete(aid, failed)
