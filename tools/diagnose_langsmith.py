"""Read-only LangSmith discovery. POST is allowed ONLY for the read-only run query.

Never calls models, exports traces, reads images, or modifies workflow/ledger data.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from faulttrace.partners.http import NoRedirect
from faulttrace.partners.trace_routing import ENDPOINTS, configuration
from faulttrace.validation import parse_json
from tools.verify_sprint_live import safe_json
from tools.sprint_inventory import readonly

CASE = '.local/sprint-verification/investigations/d60ae1a28d7a47e58a73759237130cce'
ATTEMPTS = {
    '97ef7a84-880b-4e5e-9356-644552507d6b': 'planning',
    '9f6c69c8-3f9f-423b-88b5-7bd676196439': 'photo_analysis',
    '4a167f2a-cc88-48ee-8196-3d99c66ceb51': 'planning',
}
START, END = '2026-10-29T00:24:00+00:00', '2026-10-29T00:26:00+00:00'
SELECT = ['id','name','session_id','start_time','end_time','extra','trace_id','dotted_order']
SETTINGS = ('LANGSMITH_API_KEY','LANGSMITH_PROJECT','LANGSMITH_ENDPOINT',
            'LANGSMITH_WORKSPACE_ID','LANGSMITH_AGENT_ID','LANGSMITH_AGENT_ENVIRONMENT')


class DiagnosticError(Exception):
    pass


def identity(value):
    try:
        return str(uuid.UUID(value)) if isinstance(value, str) else None
    except ValueError:
        return None


def label(value):
    # Remote names are data; no markup/control characters/arbitrary strings.
    return value if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9 _./:-]{1,128}', value) else '[not displayed]'


def environment():
    for name in SETTINGS:
        value = os.environ.get(name)
        if not value and os.name == 'nt':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as registry:
                    value = winreg.QueryValueEx(registry,name)[0]
            except OSError:
                value = None
        if value:
            if not isinstance(value,str) or len(value)>4096 or any(c in value for c in '\r\n\0'):
                raise DiagnosticError('invalid_langsmith_setting')
            os.environ[name] = value
    key = os.environ.get('LANGSMITH_API_KEY')
    if not key:
        raise DiagnosticError('missing_langsmith_key_in_executing_terminal')
    endpoint = os.environ.get('LANGSMITH_ENDPOINT','https://api.smith.langchain.com').rstrip('/')
    if endpoint not in ENDPOINTS:
        raise DiagnosticError('unsupported_langsmith_endpoint_no_contact')
    return key, endpoint


class Reader:
    def __init__(self,key):
        self.key, self.events, self.requests = key, [], 0

    def request(self,endpoint,path,*,workspace=None,body=None):
        # Fail closed on any mutation endpoint, including trace create/update.
        route = path.split('?')[0]
        if endpoint not in ENDPOINTS or (body is not None and route != '/runs/query') or (
                body is None and route not in ('/api/v1/workspaces','/sessions')):
            raise DiagnosticError('non_readonly_route_rejected')
        if workspace and not identity(workspace):
            raise DiagnosticError('invalid_workspace')
        self.requests += 1
        if self.requests > 80:
            self.events.append({'diagnostic':'diagnostic_request_cap_no_contact'})
            return None
        headers = {'x-api-key':self.key,'Accept':'application/json'}
        if workspace:
            headers['x-tenant-id'] = workspace
        raw = None if body is None else json.dumps(body,allow_nan=False).encode()
        if raw is not None:
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(endpoint+path,data=raw,headers=headers,
                                         method='GET' if body is None else 'POST')
        event = {'endpoint':endpoint,'route':route,'workspace_id':workspace}
        try:
            with urllib.request.build_opener(NoRedirect()).open(request,timeout=8) as response:
                event['http_status'] = response.status
                data = response.read(262145)
            if len(data)>262144:
                event['diagnostic'] = 'response_too_large'
                return None
            try:
                value = parse_json(data.decode('utf-8'))
            except Exception:
                event['diagnostic'] = 'invalid_json_response'
                return None
            event['diagnostic'] = 'http_response_readable'
            return value
        except urllib.error.HTTPError as error:
            event.update(http_status=error.code,diagnostic={401:'authentication_failed',403:'access_denied',
                404:'resource_or_route_not_found',422:'query_rejected',429:'rate_limited'}.get(error.code,'http_error'))
            try:
                data = error.read(8193)
                event['error_body_oversized'] = len(data)>8192
                if len(data)<=8192:
                    try:
                        value = parse_json(data.decode('utf-8'))
                        code = value.get('code') if isinstance(value,dict) else None
                        recognized = ('org_scoped_key_requires_workspace','invalid_api_key','permission_denied',
                                      'workspace_not_found','rate_limit_exceeded')
                        event['error_code'] = code if code in recognized else 'unknown'
                    except Exception:
                        event['error_code'] = 'unknown'
            except Exception:
                event['error_code'] = 'unknown'
            finally:
                error.close()
            return None
        except Exception:
            event['diagnostic'] = 'transport_failure_no_retry'
            return None
        finally:
            self.events.append(event)


def candidates(rows,receipts,workspace,projects,endpoint):
    found = []
    host = endpoint.replace('api.smith.', 'smith.').replace('eu.api.smith.','eu.smith.')
    for row in rows:
        if not isinstance(row,dict) or row.get('name') not in ('faulttrace.planning','faulttrace.photo_analysis'):
            continue
        rid, pid = identity(row.get('id')), identity(row.get('session_id'))
        if not rid or pid not in projects:
            continue
        try:
            stamp = datetime.fromisoformat(row['start_time'].replace('Z','+00:00'))
            if stamp.tzinfo is None or not datetime.fromisoformat(START)<=stamp<=datetime.fromisoformat(END):
                continue
        except (ValueError,KeyError,TypeError,AttributeError):
            continue
        meta = row.get('extra',{}).get('metadata',{}) if isinstance(row.get('extra'),dict) else {}
        matches = []
        for receipt in receipts:
            aid = receipt['attempt_id']
            if (row['name']=='faulttrace.'+ATTEMPTS[aid] and isinstance(meta,dict)
                    and meta.get('operation')==ATTEMPTS[aid]
                    and meta.get('token_usage')==receipt.get('token_usage')
                    and meta.get('latency_ms')==receipt.get('latency_ms')):
                matches.append(aid)
        found.append({'run_id':rid,'project_id':pid,'project':projects[pid],
            'workspace_id':workspace,'name':row['name'],'start_time':stamp.isoformat(),
            'remote_readable':True,
            'remote_end_time_present':bool(row.get('end_time')),
            'remote_trace_id_present':bool(identity(row.get('trace_id'))),
            'receipt_fingerprint_matches':matches,'attempt_identity':'not_proven_original_run_id_discarded',
            'dashboard_url':f'{host}/o/{workspace}/projects/p/{pid}/r/{rid}?poll=true',
            'dashboard_url_basis':'SDK project/run URL construction; browser not checked'})
    return found


def discover(reader,endpoints,receipts):
    result = {'remote_runs':[], 'projects':[], 'workspaces':[], 'coverage_limits':[],
        'scope':'key-visible workspaces in API current organization; not all organizations'}
    for endpoint in endpoints:
        listing = reader.request(endpoint,'/api/v1/workspaces')
        workspaces = {identity(r.get('id')) for r in listing if isinstance(r,dict)} if isinstance(listing,list) else set()
        workspaces.discard(None)
        if isinstance(listing,list):
            result['workspaces'].extend({'endpoint':endpoint,'workspace_id':identity(r.get('id')),
                'name':label(r.get('display_name'))} for r in listing if isinstance(r,dict) and identity(r.get('id')))
        else:
            result['coverage_limits'].append('workspace_discovery_unavailable_current_key_scope_only')
        configured = identity(os.environ.get('LANGSMITH_WORKSPACE_ID'))
        if configured:
            workspaces.add(configured)
        # Even a tracing-only key may read its default project without workspace listing permission.
        scopes = sorted(workspaces)[:10] if workspaces else [None]
        if len(workspaces)>10:
            result['coverage_limits'].append('workspace_limit_10')
        for workspace in scopes:
            projects = {}
            for page in range(4):
                listing = reader.request(endpoint,'/sessions?'+urllib.parse.urlencode({'limit':50,'offset':page*50}),workspace=workspace)
                if not isinstance(listing,list):
                    result['coverage_limits'].append('project_listing_unavailable')
                    break
                for r in listing:
                    if not isinstance(r,dict):
                        continue
                    pid = identity(r.get('id'))
                    if pid:
                        projects[pid] = label(r.get('name'))
                        if workspace is None:
                            workspace = identity(r.get('tenant_id'))
                if len(listing)<50:
                    break
                if page==3:
                    result['coverage_limits'].append('project_limit_200')
            result['projects'].extend({'endpoint':endpoint,'workspace_id':workspace,'project_id':p,'name':n} for p,n in projects.items())
            if not projects or not workspace:
                continue
            body = {'session':list(projects),'start_time':START,'end_time':END,
                'filter':'or(eq(name, "faulttrace.planning"),eq(name, "faulttrace.photo_analysis"))',
                'select':SELECT,'limit':100}
            for page in range(3):
                value = reader.request(endpoint,'/runs/query',workspace=workspace,body=body)
                if not isinstance(value,dict) or not isinstance(value.get('runs'),list):
                    result['coverage_limits'].append('run_query_unavailable')
                    break
                result['remote_runs'].extend(candidates(value['runs'],receipts,workspace,projects,endpoint))
                cursor = value.get('cursors',{}).get('next') if isinstance(value.get('cursors'),dict) else None
                if not cursor:
                    break
                if not isinstance(cursor,str) or len(cursor)>4096:
                    raise DiagnosticError('invalid_pagination_cursor')
                body = dict(body,cursor=cursor)
                if page==2:
                    result['coverage_limits'].append('query_page_limit_3')
    result['http_diagnostics'] = reader.events
    return result


def local_receipts(case):
    saved = parse_json((case/'result.json').read_text(encoding='utf-8'))
    receipts = [v['receipt'] for v in saved['planning']]+[saved['photographic_contract']['receipt']]
    if {r['attempt_id'] for r in receipts} != set(ATTEMPTS) or len(receipts)!=3:
        raise DiagnosticError('unexpected_saved_attempts')
    databases = list(case.rglob('workflow.sqlite3'))
    ledgers = list(case.rglob('usage.json'))
    if len(databases)!=1 or len(ledgers)!=1:
        raise DiagnosticError('unexpected_saved_accounting_locations')
    ledger = parse_json(ledgers[0].read_text(encoding='utf-8'))['receipts']
    with readonly(databases[0]) as db:
        for receipt in receipts:
            aid = receipt['attempt_id']
            table = 'analyses' if ATTEMPTS[aid]=='photo_analysis' else 'planning'
            rows = db.execute(f'SELECT receipt FROM {table} WHERE id=?',(aid,)).fetchall()
            traces = db.execute('SELECT status FROM trace_exports WHERE attempt_id=?',(aid,)).fetchall()
            entries = [r for r in ledger if r['attempt_id']==aid]
            if (len(rows)!=1 or len(traces)!=1 or traces[0][0]!='recorded' or len(entries)!=1
                    or parse_json(rows[0][0])!=receipt or entries[0]!=receipt):
                raise DiagnosticError('saved_accounting_or_delivery_discrepancy')
    return receipts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head',required=True)
    args = parser.parse_args(argv)
    try:
        head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if head != args.expected_head or subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):
            raise DiagnosticError('reviewed_clean_checkout_required')
        case = ROOT/CASE
        receipts = local_receipts(case)
        key,endpoint = environment()
        try:
            _,_,destination = configuration()
        except ValueError as error:
            destination = {'diagnostic':str(error)}
        ledger = ROOT/'.local/nebius-usage.json'
        before = hashlib.sha256(ledger.read_bytes()).hexdigest()
        reader = Reader(key)
        result = discover(reader,list(dict.fromkeys(['https://api.smith.langchain.com',endpoint])),receipts)
        result.update(source_revision=head,mode='READ ONLY; no trace export or inference',
            configured_destination=destination,historical_destination='US / named project; historical name not retained',
            historical_reported_exports=3,historical_http_status='not retained',search_window_utc=[START,END],
            real_ledger_unchanged=hashlib.sha256(ledger.read_bytes()).hexdigest()==before,
            historical_remote_run_ids='discarded; fingerprint matches are not direct ID correlation')
        matches = {a for r in result['remote_runs'] for a in r['receipt_fingerprint_matches']}
        result['verification_result'] = ('all_three_receipt_fingerprints_located'
            if matches==set(ATTEMPTS) else 'partial_or_not_found')
        text = safe_json(result,[key])
        folder = ROOT/'.local/langsmith-diagnostics';folder.mkdir(parents=True,exist_ok=True)
        path = folder/(uuid.uuid4().hex+'.json')
        with path.open('x',encoding='utf-8') as stream:
            stream.write(text)
        print(text)
        print('Private diagnostic: '+str(path.relative_to(ROOT)))
        return 0 if matches==set(ATTEMPTS) else 1
    except DiagnosticError as error:
        print(json.dumps({'diagnostic':str(error),'no_retry':True}))
        return 2
    except Exception:
        # No arbitrary exception strings, response bodies, headers or credentials.
        print(json.dumps({'diagnostic':'local_preflight_or_readonly_diagnostic_failed','no_retry':True}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
