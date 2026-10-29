"""One bounded live sprint via production ASGI routes. No listening server or retries."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.sprint_inventory import BASE, CAPS, Control, SafeFailure, SprintSpending
from tools.sprint_client import ApplicationFailure, Client, ORIGIN, independent_report
from faulttrace.workflow.storage import InstanceLock

REQUIRED = ('NEBIUS_API_KEY','TAVILY_API_KEY','LANGSMITH_API_KEY','LANGSMITH_PROJECT')
CONTRACTS = ('faulttrace',)  # Production code must match the reviewed implementation.
RETAINED = '.local/verification/photo-analysis-f84d9672f11140c2b92bc1d0c930dcef'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.DEVNULL).decode().strip()


def credentials():
    for name in REQUIRED:
        value = os.environ.get(name)
        if not value and os.name == 'nt':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as registry:
                    value = winreg.QueryValueEx(registry,name)[0]
            except OSError:
                value = None
        if not isinstance(value,str) or not value.strip():
            raise SafeFailure('missing_'+name)
        if len(value)>4096 or any(c in value for c in '\r\n\0'):
            raise SafeFailure('invalid_'+name)
        os.environ[name] = value
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',os.environ['LANGSMITH_PROJECT']):
        raise SafeFailure('invalid_LANGSMITH_PROJECT')
    return [os.environ[n] for n in REQUIRED[:-1]]


def preflight(head):
    if sys.version_info[:2] != (3,12):
        raise SafeFailure('python_3_12_required')
    if not re.fullmatch(r'[0-9a-f]{40}',head or '') or git('rev-parse','HEAD') != head:
        raise SafeFailure('checkout_revision_mismatch')
    if git('branch','--show-current') != 'feat/finish-integrated' or git('status','--porcelain'):
        raise SafeFailure('checkout_branch_or_changes_require_review')
    if subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,capture_output=True).returncode:
        raise SafeFailure('unexpected_checkout_ancestry')
    if git('diff',BASE,head,'--',*CONTRACTS):
        raise SafeFailure('production_contract_changed_requires_review')
    from faulttrace.ledger import load
    ledger = ROOT/'.local/nebius-usage.json'
    if not ledger.is_file():
        raise SafeFailure('real_ledger_missing')
    try:
        load(ledger)  # Read-only validation, never imports or appends historical records.
    except Exception:
        raise SafeFailure('real_ledger_unreadable') from None
    return hashlib.sha256(ledger.read_bytes()).hexdigest()


def photo_input(path):
    from faulttrace.workflow.uploads import MAX_UPLOAD, validate_upload
    try:
        source = Path(path)
        with source.open('rb') as stream:
            data = stream.read(MAX_UPLOAD+1)
        mime = 'image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg'
        picture = validate_upload(data,mime)
        digest = hashlib.sha256(data).hexdigest()
        if source.resolve() == (ROOT/RETAINED/'submitted.png').resolve():
            prior = json.loads((ROOT/RETAINED/'provenance.json').read_text(encoding='utf-8-sig'))
            if prior['submitted']['sha256'] != digest or prior['submitted']['dimensions'] != [picture['width'],picture['height']]:
                raise ValueError()
        return picture['bytes'], {'source_sha256':digest,
            'submitted_sha256':hashlib.sha256(picture['bytes']).hexdigest(),
            'dimensions':[picture['width'],picture['height']],
            'processing':'unchanged production metadata removal; original preserved'}
    except Exception:
        raise SafeFailure('photo_missing_invalid_or_hash_mismatch_use_compliant_copy') from None


def safe_json(value,secrets):
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item,str) and any(secret in item for secret in secrets):
            raise SafeFailure('credential_in_output_rejected')
        if isinstance(item,dict):
            pending.extend(item.keys()); pending.extend(item.values())
        elif isinstance(item,(list,tuple)):
            pending.extend(item)
    text = json.dumps(value,indent=2,allow_nan=False)
    if any(secret in text for secret in secrets):
        raise SafeFailure('credential_in_output_rejected')
    return text


class Verification:
    def __init__(self, client, control, photo, ask, secrets):
        self.client,self.control,self.photo,self.ask,self.secrets = client,control,photo,ask,secrets
        self.result = {'mode':'LIVE services / simulated equipment / production ASGI routes',
            'planning':[], 'photographic_contract':{'status':'not_attempted','numeric_accuracy':'not_evaluated'},
            'tavily_retrieval':{'status':'not_attempted'}, 'langsmith_delivery':[],
            'browser_verification':'not performed','correction_or_recovery_authorized':False}

    def allowed(self,operation):
        view = self.control.snapshot()
        if 'tracing' in view['blocked']:
            os.environ['FAULTTRACE_LANGSMITH_TRACING'] = '0'
        return operation not in view['blocked'] and view['used'][operation] < CAPS[operation]

    def trace(self,operation,aid,status=None):
        status = status or self.client.trace(aid)
        self.result['langsmith_delivery'].append({'operation':operation,'attempt_id':aid,
            'status':status,'dashboard_visibility':'not_verified'})
        if status != 'recorded':
            self.control.block('tracing')
            os.environ['FAULTTRACE_LANGSMITH_TRACING'] = '0'

    def attempt(self,operation,action):
        if not self.allowed(operation):
            return {'status':'blocked','diagnostic':'prior_failure_uncertainty_or_sprint_limit'}
        try:
            return action()
        except ApplicationFailure as failure:
            self.control.block(operation)
            return {'status':'failed','diagnostic':failure.code,'http_status':failure.status}
        except SafeFailure as failure:
            self.control.block(operation)
            return {'status':'failed','diagnostic':str(failure)}
        except Exception:
            self.control.block(operation)
            return {'status':'failed','diagnostic':'operation_failed_no_retry'}

    def plan(self):
        state = self.client.call('/api/state')
        aid = self.client.call('/api/planning',{'revision':state['incident']['revision']})['attempt_id']
        row = self.client.wait('planning',aid)
        receipt = json.loads(row['receipt']) if row['receipt'] else None
        good = row['status'] in ('accepted','escalated') and receipt and receipt['validation_result']=='passed'
        self.trace('planning',aid)
        if not good or row['accounting']=='failed':
            self.control.block('planning')
        return {'status':'passed' if good else 'failed','workflow_status':row['status'],
            'proposal':json.loads(row['proposal']) if row['proposal'] else None,
            'receipt':receipt,'accounting':row['accounting']}

    def photograph(self):
        state = self.client.call('/api/state'); task = state['task']
        if not task or task['status'] not in ('awaiting','needs_evidence','observed'):
            return {'status':'blocked','diagnostic':'no_accepted_task_for_photo','numeric_accuracy':'not_evaluated'}
        eid = self.client.call('/api/tasks/'+task['id']+'/images',self.photo,'operator',{
            'Content-Type':'image/png','X-Evidence-Purpose':'reference-photo','X-Task-Revision':str(task['revision'])})['evidence_id']
        task = self.client.call('/api/state')['task']
        aid = self.client.call('/api/evidence/'+eid+'/analyze-photo',{'revision':task['revision']})['analysis_id']
        row = self.client.wait('analyses',aid)
        receipt = json.loads(row['receipt']) if row['receipt'] else None
        good = row['status']=='interpreted' and receipt and receipt['validation_result']=='passed'
        self.trace('photo_analysis',aid)
        if not good or row['accounting']=='failed':
            self.control.block('photo')
        return {'status':'passed' if good else 'failed','numeric_accuracy':'not_evaluated',
            'assigned_asset':task['asset_id'],'asset_identity':'not_established_by_assignment',
            'interpretation':json.loads(row['interpretation']) if row['interpretation'] else None,
            'receipt':receipt,'accounting':row['accounting']}

    def documentation(self,reference):
        state = self.client.call('/api/state')
        rid = self.client.call('/api/documentation',dict(reference,revision=state['incident']['revision']))['record_id']
        row = next(r for r in self.client.call('/api/documentation')['records'] if r['id']==rid)
        self.trace('documentation',rid,row['trace_result'])
        good = row['status']=='completed' and row['result'] and bool(row['result']['sources'])
        if not good:
            self.control.block('documentation')
        return {'status':'passed' if good else 'failed','record_id':rid,'receipt':row['receipt'],
            'sources':row['result']['sources'] if row['result'] else [],
            'retrieved_at':row['result'].get('retrieved_at') if row['result'] else None,
            'model_applicability':'requires_independent_review'}

    def run(self,reference):
        first = self.attempt('planning',self.plan); self.result['planning'].append(first)
        print(safe_json({'nvidia_planning':first},self.secrets))
        if first['status']=='passed':
            self.result['photographic_contract'] = self.attempt('photo',self.photograph)
            # Show the actual claim; never prefill a confirmation/report from it.
            print(safe_json({'photographic_contract':self.result['photographic_contract']},self.secrets))
            try:
                observed = independent_report(self.client,self.ask,self.secrets)
            except (SafeFailure, ApplicationFailure):
                observed = False
                self.result['operator_report'] = 'rejected_or_skipped_no_retry'
            if observed:
                self.result['planning'].append(self.attempt('planning',self.plan))
        self.result['tavily_retrieval'] = (self.attempt('documentation',lambda:self.documentation(reference))
            if reference else {'status':'blocked','diagnostic':'human_confirmed_model_required'})
        self.result['photographic_contract'].setdefault('numeric_accuracy','not_evaluated')
        return self.result


def main(argv=None,ask=input):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--photo',type=Path)
    parser.add_argument('--inventory-only',action='store_true',help='read-only, zero service calls')
    args = parser.parse_args(argv)
    secrets = []
    try:
        old_ledger_hash = preflight(args.expected_head)
        if args.inventory_only:
            from tools.sprint_inventory import audit
            records = audit(ROOT)
            print(json.dumps({'already_counted':{op:sum(v['operation']==op for v in records.values()) for op in CAPS},
                'uncertain_or_failed':sum(v['failed'] or v['uncertain'] for v in records.values()),'service_calls':0}))
            return 0
        secrets = credentials()  # Inherits this terminal first; does not infer other terminals' state.
        directory = ROOT/'.local/sprint-verification'; directory.mkdir(parents=True,exist_ok=True)
        with closing(InstanceLock(directory/'verification.lock')):
            control = Control(ROOT,verify=lambda:preflight(args.expected_head)); before = control.snapshot()
            print(safe_json({'already_counted':before['used'],'blocked_paths':before['blocked'],
                'remaining':{op:max(0,CAPS[op]-before['used'][op]) for op in CAPS}},secrets))
            if all(before['used'][op]>=CAPS[op] or op in before['blocked'] for op in CAPS):
                raise SafeFailure('sprint_limits_or_stopped_paths_require_existing_result_review')
            if ask('Confirm credited balance and no unrecorded/outside/concurrent sprint calls [yes/no]: ').strip()!='yes':
                raise SafeFailure('sprint_accounting_or_balance_not_confirmed')
            path = args.photo or ROOT/RETAINED/'submitted.png'
            photo,provenance = photo_input(path)
            from faulttrace.partners.tavily import DOMAINS, context
            domain = ask('Confirmed official domain [maximator.de / maximator.com / wika.com / emerson.com / swagelok.com; blank skips search]: ').strip()
            model = ask('Independently confirmed exact equipment model (blank skips search): ').strip() if domain else ''
            if any(secret in domain or secret in model for secret in secrets):
                raise SafeFailure('equipment_context_contains_credential')
            reference = None
            if domain and model:
                try:
                    reference = context(DOMAINS.get(domain,''),model,domain)
                except Exception:
                    raise SafeFailure('equipment_context_invalid') from None
                if ask('Was this manufacturer/model independently confirmed, rather than guessed from assignment/photo [yes/no]: ').strip()!='yes':
                    raise SafeFailure('equipment_identity_not_confirmed')
            preflight(args.expected_head)
            case = directory/'investigations'/uuid.uuid4().hex; case.mkdir(parents=True)
            (case/'submitted.png').write_bytes(photo)
            (case/'provenance.json').write_text(safe_json(provenance,secrets),encoding='utf-8')
            os.environ.update(FAULTTRACE_ALLOW_INFERENCE='1',FAULTTRACE_DEMO_LIVE='1',
                FAULTTRACE_TAVILY_ENABLED='1',FAULTTRACE_LANGSMITH_TRACING=
                '0' if 'tracing' in before['blocked'] else '1')
            from fastapi.testclient import TestClient
            from faulttrace.workflow.demo_app import create_demo_app
            budget = SprintSpending(case/'application',control)
            app = create_demo_app(case/'application',ORIGIN,local_http=True,live=True,budget=budget)
            result = {'status':'interrupted_or_failed','diagnostic':'reservations_retained_no_retry'}
            completed = False
            client = None
            try:
                with TestClient(app,base_url=ORIGIN) as http:
                    client = Client(http,case/'application')
                    verification = Verification(client,control,photo,ask,secrets)
                    result = verification.result  # Preserve partial results on interruption.
                    verification.run(reference)
                    completed = True
            finally:
                result['interrupted_or_local_failure'] = not completed
                if not completed and client:
                    result['retained_attempts'] = client.retained()
                result.update(source_revision=args.expected_head,already_counted=before['used'],after=control.snapshot()['used'])
                result['real_ledger_unchanged'] = hashlib.sha256((ROOT/'.local/nebius-usage.json').read_bytes()).hexdigest()==old_ledger_hash
                text = safe_json(result,secrets)
                temporary = case/'result.pending'
                with temporary.open('x',encoding='utf-8') as stream:
                    stream.write(text); stream.flush(); os.fsync(stream.fileno())
                os.replace(temporary,case/'result.json')
                print(text)
                print('Sanitized result: '+str((case/'result.json').relative_to(ROOT)))
            complete = (len(result.get('planning',[]))==2
                and all(p['status']=='passed' and p['accounting']!='failed' for p in result['planning'])
                and result.get('photographic_contract',{}).get('status')=='passed'
                and result.get('tavily_retrieval',{}).get('status')=='passed'
                and len(result.get('langsmith_delivery',[]))==4
                and all(t['status']=='recorded' for t in result['langsmith_delivery'])
                and result['real_ledger_unchanged'])
            return 0 if complete else 1
    except KeyboardInterrupt:
        print(json.dumps({'diagnostic':'verification_interrupted_reservations_retained','no_retry':True})); return 2
    except SafeFailure as failure:
        print(json.dumps({'diagnostic':str(failure),'no_retry':True})); return 2
    except Exception:
        print(json.dumps({'diagnostic':'local_preflight_or_verification_failed_no_raw_details','no_retry':True})); return 2


if __name__=='__main__':
    raise SystemExit(main())
