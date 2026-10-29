"""One live production-route reference lookup; no NVIDIA or LangSmith calls."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.sprint_inventory import Control,SprintSpending,SafeFailure
from tools.sprint_client import Client,ORIGIN,ApplicationFailure
from tools.verify_sprint_live import safe_json
from faulttrace.workflow.storage import InstanceLock,WorkflowError
from faulttrace.workflow.demo_runtime import forbidden_transport

BASE='73a29e960af3c1f3d4bacc41629b36a62574e30e'
REFERENCE={'manufacturer':'WIKA','model':'A-10','domain':'wika.com'}
VERIFIED_URLS=(
    'https://www.wika.com/en-us/a_10.WIKA',
    'https://www.wika.com/media/Data-sheets/Pressure/Pressure-sensors/ds_pe8160_en_co.pdf',
    'https://www.wika.com/media/Operating-instructions/Operating-instructions/Pressure/Pressure-sensors/oi_a_10_en_de_fr_es.pdf',
)


def preflight(head):
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.DEVNULL).decode().strip()
    if sys.version_info[:2]!=(3,12) or git('rev-parse','HEAD')!=head or len(head)!=40:
        raise SafeFailure('reviewed_python_3_12_checkout_required')
    if git('branch','--show-current')!='feat/finish-integrated' or git('status','--porcelain'):
        raise SafeFailure('reviewed_clean_feature_branch_required')
    if subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,capture_output=True).returncode or git('diff',BASE,head,'--','faulttrace'):
        raise SafeFailure('production_runtime_changed_requires_review')
    from faulttrace.ledger import load
    path=ROOT/'.local/nebius-usage.json'
    if not path.is_file():raise SafeFailure('real_ledger_missing')
    load(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def credential():
    key=os.environ.get('TAVILY_API_KEY')
    if not key and os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as registry:
                key=winreg.QueryValueEx(registry,'TAVILY_API_KEY')[0]
        except OSError:pass
    if not isinstance(key,str) or not key.strip() or len(key)>4096 or any(c in key for c in '\r\n\0'):
        raise SafeFailure('missing_or_invalid_TAVILY_API_KEY_no_contact')
    os.environ['TAVILY_API_KEY']=key
    return key


class DocumentationOnlyBudget(SprintSpending):
    def reserve(self,session,operation,aid):
        if operation!='documentation':
            raise WorkflowError('inference_disabled',403)
        return super().reserve(session,operation,aid)


def citation_checks(sources):
    known={urlsplit(u).path.casefold().rstrip('/') for u in VERIFIED_URLS}
    checks=[]
    for source in sources:
        url=urlsplit(source['url']);host=url.hostname or ''
        official=url.scheme=='https' and (host=='wika.com' or host.endswith('.wika.com')) and not url.username and not url.password and url.port in (None,443)
        # Exact pre-reviewed document path only; another official resource is not
        # silently declared applicable from a title or model substring.
        matched=host in ('wika.com','www.wika.com') and url.path.casefold().rstrip('/') in known
        checks.append({'url':source['url'],'official_domain':official,
            'model_mentioned':source.get('model_match')=='text_mentions_requested_model',
            'preverified_manufacturer_resource':bool(official and matched),
            'content_review':'preverified official A-10 resource' if official and matched else 'returned resource requires independent review'})
    return checks


def run_lookup(client):
    state=client.call('/api/state')
    answer=client.call('/api/documentation',dict(REFERENCE,revision=state['incident']['revision']))
    rows=client.call('/api/documentation')['records']
    row=next(r for r in rows if r['id']==answer['record_id'])
    sources=row['result']['sources'] if row['result'] else []
    checks=citation_checks(sources)
    after=client.call('/api/state')
    return {'mode':'LIVE Tavily / reference-equipment example / simulated isolated investigation',
        'reference_equipment':REFERENCE,'identity_scope':'Does not identify the MAXIMATOR photograph or F-17.',
        'record_id':row['id'],'status':row['status'],'receipt':row['receipt'],
        'connectivity_contract_result':'passed' if row['receipt'] and row['receipt']['transport_invoked'] is True and row['receipt']['validation_result']=='passed' else 'not_verified',
        'retrieval_outcome':'citations_retained_pending_review' if sources else 'no_retained_sources',
        'source_diagnostics':row['result'].get('source_diagnostics') if row['result'] else None,
        'sources':sources,'citation_checks':checks,
        'citation_verification':'preverified_resource_returned' if any(c['preverified_manufacturer_resource'] and c['model_mentioned'] for c in checks) else 'not_verified_requires_review',
        'preverified_basis':list(VERIFIED_URLS),'retrieved_at':row['result'].get('retrieved_at') if row['result'] else None,
        'trace_result':row['trace_result'],'nvidia_calls':0,'langsmith_exports':0,
        'investigation_evidence_count_after':len(after.get('evidence',[])),
        'scope':'Untrusted reference documents, never observed measurements or correction authority.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expected-head',required=True)
    args=parser.parse_args(argv)
    try:
        original=preflight(args.expected_head);key=credential()
        folder=ROOT/'.local/tavily-verification';folder.mkdir(parents=True,exist_ok=True)
        (ROOT/'.local/sprint-verification').mkdir(parents=True,exist_ok=True)
        with closing(InstanceLock(ROOT/'.local/sprint-verification/verification.lock')):
            control=Control(ROOT,verify=lambda:preflight(args.expected_head));before=control.snapshot()
            if before['used']['documentation']>=1 or 'documentation' in before['blocked']:
                raise SafeFailure('tavily_sprint_allowance_used_or_blocked_no_retry')
            os.environ.update(FAULTTRACE_ALLOW_INFERENCE='0',FAULTTRACE_LANGSMITH_TRACING='0',FAULTTRACE_TAVILY_ENABLED='1')
            case=folder/uuid.uuid4().hex;case.mkdir()
            from fastapi.testclient import TestClient
            from faulttrace.workflow.demo_app import create_demo_app
            app=create_demo_app(case/'application',ORIGIN,local_http=True,live=True,
                budget=DocumentationOnlyBudget(case/'application',control),
                send=forbidden_transport,key_source=lambda:None)
            result={'status':'failed_or_interrupted','no_retry':True};client=None
            try:
                with TestClient(app,base_url=ORIGIN) as http:
                    client=Client(http,case/'application')
                    result=run_lookup(client)
            finally:
                if client and result.get('status')=='failed_or_interrupted':result['retained_attempts']=client.retained()
                result.update(source_revision=args.expected_head,already_counted=before['used'],after=control.snapshot()['used'],
                    real_ledger_unchanged=hashlib.sha256((ROOT/'.local/nebius-usage.json').read_bytes()).hexdigest()==original)
                text=safe_json(result,[key])
                with (case/'result.pending').open('x',encoding='utf-8') as stream:
                    stream.write(text);stream.flush();os.fsync(stream.fileno())
                os.replace(case/'result.pending',case/'result.json')
                print(text);print('Private result: '+str((case/'result.json').relative_to(ROOT)))
            return 0 if result.get('status')=='completed' and result.get('citation_verification')=='preverified_resource_returned' and result.get('trace_result')=='disabled' and result['real_ledger_unchanged'] else 1
    except (SafeFailure,ApplicationFailure) as error:
        print(json.dumps({'diagnostic':error.code if isinstance(error,ApplicationFailure) else str(error),'no_retry':True}));return 2
    except KeyboardInterrupt:
        print(json.dumps({'diagnostic':'interrupted_reservations_retained_no_retry'}));return 2
    except Exception:
        print(json.dumps({'diagnostic':'local_preflight_or_lookup_failure_no_raw_details','no_retry':True}));return 2


if __name__=='__main__':raise SystemExit(main())
