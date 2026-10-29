"""Production-route client and interactive independent observations; no server socket."""
import json
import math
import time
import uuid

from tools.sprint_inventory import SafeFailure, readonly

ORIGIN = 'http://127.0.0.1:8851'
ERRORS = {'inference_disabled','missing_credentials','stale_context','active_task_conflict',
    'planning_in_progress','planning_budget_exhausted','spending_budget_exhausted',
    'spending_concurrency_limit','photo_contract_not_applicable','analysis_in_progress',
    'stale_or_unanalyzable_evidence','invalid_human_observation','independent_report_required',
    'documentation_disabled','documentation_credentials_unavailable','documentation_context_invalid',
    'documentation_budget_unavailable','documentation_in_progress','documentation_budget_exhausted'}


class ApplicationFailure(SafeFailure):
    def __init__(self, status, value):
        self.status = status
        self.code = value if isinstance(value,str) and value in ERRORS else 'application_request_failed'


class Client:
    def __init__(self, http, directory):
        self.http, self.directory = http, directory
        self.headers = {'Origin':ORIGIN,'X-FaultTrace-Demo':'1','X-FaultTrace-Workspace':'commander'}
        session = self.call('/api/demo/session')
        self.headers.update({'X-CSRF-Token':session['csrf_token'],'X-FaultTrace-Demo-Run':''})
        session = self.call('/api/demo/start',{})
        self.headers['X-FaultTrace-Demo-Run'] = session['active_run']
        self.run = directory/'runs'/session['active_run']
        self.database = self.run/'data/workflow.sqlite3'

    def call(self, path, body=None, role='commander', extra=None):
        headers = dict(self.headers, **{'X-FaultTrace-Workspace':role})
        if body is not None:
            headers['Idempotency-Key'] = str(uuid.uuid4())
        headers.update(extra or {})
        if isinstance(body, bytes):
            response = self.http.post(path,content=body,headers=headers)
        elif body is not None:
            response = self.http.post(path,json=body,headers=headers)
        else:
            response = self.http.get(path,headers=headers)
        if response.status_code >= 400:
            try:
                error = response.json().get('error')
            except Exception:
                error = None
            raise ApplicationFailure(response.status_code,error)
        return response.json()

    def wait(self, table, aid):
        # Status polling only: never repeats a mutation/generation request.
        if table not in ('planning','analyses'):
            raise SafeFailure('invalid_verification_table')
        until = time.monotonic()+120
        while time.monotonic()<until:
            with readonly(self.database) as db:
                row = db.execute(f'SELECT * FROM {table} WHERE id=?',(aid,)).fetchone()
            if row and row['status'] != 'pending':
                return dict(row)
            time.sleep(.1)
        raise SafeFailure('attempt_still_pending_no_retry')

    def trace(self, aid):
        until = time.monotonic()+6
        while time.monotonic()<until:
            with readonly(self.database) as db:
                exists = db.execute("SELECT 1 FROM sqlite_master WHERE name='trace_exports'").fetchone()
                row = db.execute('SELECT status FROM trace_exports WHERE attempt_id=?',(aid,)).fetchone() if exists else None
            if row:
                return row[0]
            time.sleep(.1)
        return 'unknown'

    def retained(self):
        """Read available outboxes after interruption; never imports/replays them."""
        records = []
        with readonly(self.database) as db:
            for table in ('planning','analyses','documentation'):
                exists = db.execute("SELECT 1 FROM sqlite_master WHERE name=?",(table,)).fetchone()
                if not exists:
                    continue
                for row in db.execute(f'SELECT id,status,receipt FROM {table}'):
                    records.append({'table':table,'attempt_id':row['id'],'status':row['status'],
                        'receipt':json.loads(row['receipt']) if row['receipt'] else None})
        return records


def independent_report(client, ask, secrets):
    state = client.call('/api/state')
    task = state['task']
    if not task:
        return False
    print('Assigned observation: '+task['asset_id']+' / '+task['capability'])
    print('Report your own observation; do not copy the model reading. Skip or refuse if unsupported.')
    # No default or copied model value. Refusal is a real report, never invented evidence.
    choice = ask('Independent Operator response [independent / cannot-access / unreadable / wrong-equipment / skip]: ').strip()
    if choice == 'skip':
        return False
    if choice in ('cannot-access','unreadable','wrong-equipment'):
        client.call('/api/tasks/'+task['id']+'/reports',{'revision':task['revision'],'report':choice},'operator')
        return True
    if choice != 'independent':
        raise SafeFailure('invalid_operator_choice')
    observed = ask('Independently observed asset [F-17 / V-08 / unknown / other]: ').strip()
    measurement = ask('Independently observed measurement type [differential_pressure / pressure / position / unknown]: ').strip()
    reading, unit, position = None, None, None
    if measurement in ('pressure','differential_pressure'):
        value = ask('Independent numeric reading (blank answers are not accepted): ').strip()
        try:
            reading = float(value)
        except ValueError:
            raise SafeFailure('invalid_independent_reading') from None
        if not math.isfinite(reading):
            raise SafeFailure('invalid_independent_reading')
        unit = ask('Independent visible unit [Pa / kPa / MPa / bar / psi]: ').strip()
    elif measurement == 'position':
        position = ask('Human-reported position [open / intermediate / closed / cannot determine]: ').strip()
    body = {'revision':state['incident']['revision'],'task_revision':task['revision'],
        'photo_id':None,'decision':'independent','observed_asset_id':observed,'measurement_type':measurement,
        'reading':reading,'unit':unit,'position':position,'independent':True}
    if any(secret in json.dumps(body) for secret in secrets):
        raise SafeFailure('operator_input_contains_credential')
    client.call('/api/tasks/'+task['id']+'/observations',body,'operator')
    return True
