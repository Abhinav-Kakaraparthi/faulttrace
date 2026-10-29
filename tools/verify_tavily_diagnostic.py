"""Separate one-call authorization; does not reset the consumed sprint allowance."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from faulttrace.ledger import load
from faulttrace.partners.tavily import payload
from faulttrace.workflow.demo_runtime import forbidden_transport
from faulttrace.workflow.spending import Spending
from faulttrace.workflow.storage import InstanceLock,WorkflowError
from tools.sprint_client import Client,ORIGIN
from tools.sprint_inventory import readonly,SafeFailure
from tools.verify_sprint_live import safe_json
from tools.verify_tavily_reference import REFERENCE,credential,run_lookup

BASE='d6cc252ef124cf08b8607b1f67732e0da8bf1e3d'
AUTHORIZATION='2026-10-29-one-additional-wika-a10-diagnostic'
ORIGINAL='.local/tavily-verification/b36d4bac81084e42925b77c0887c7552'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preserved():
    case=ROOT/ORIGINAL
    saved=json.loads((case/'result.json').read_text())
    aid='c4e1a86b-b23b-4073-a153-c584ada8d3e2'
    with readonly(next(case.rglob('workflow.sqlite3'))) as db:
        rows=db.execute('SELECT receipt FROM documentation WHERE id=?',(aid,)).fetchall()
    if len(rows)!=1 or json.loads(rows[0]['receipt'])!=saved['receipt'] or saved['receipt']['usage_credits']!=1:
        raise SafeFailure('original_receipt_requires_review')
    with readonly(ROOT/'.local/sprint-verification/limits.sqlite3') as db:
        slots=[dict(r) for r in db.execute('SELECT * FROM slots ORDER BY id')]
        blocked=[dict(r) for r in db.execute('SELECT * FROM blocked ORDER BY operation')]
    if sum(r['operation']=='documentation' for r in slots)!=1:
        raise SafeFailure('original_consumed_allowance_requires_review')
    return {'original_result_sha256':digest(case/'result.json'),
        'original_receipt_sha256':hashlib.sha256(safe_json(saved['receipt'],[]).encode()).hexdigest(),
        'original_limit_state_sha256':hashlib.sha256(safe_json([slots,blocked],[]).encode()).hexdigest(),
        'real_ledger_sha256':digest(ROOT/'.local/nebius-usage.json')}


def preflight(head):
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.DEVNULL).decode().strip()
    if sys.version_info[:2]!=(3,12) or len(head)!=40 or git('rev-parse','HEAD')!=head:
        raise SafeFailure('reviewed_python_checkout_required')
    if git('branch','--show-current')!='feat/finish-integrated' or git('status','--porcelain'):
        raise SafeFailure('reviewed_clean_feature_branch_required')
    if subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,capture_output=True).returncode or git('diff',BASE,head,'--','faulttrace'):
        raise SafeFailure('production_runtime_changed_requires_review')
    load(ROOT/'.local/nebius-usage.json')
    return preserved()


class OneDiagnosticBudget(Spending):
    def __init__(self,root):super().__init__(root,requests=1,session_requests=1,concurrent=1)

    def reserve(self,session,operation,aid):
        if operation!='documentation':raise WorkflowError('inference_disabled',403)
        return super().reserve(session,operation,aid)

    def used(self):
        with self.db() as db:return db.execute('SELECT COUNT(*) FROM reservations').fetchone()[0]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expected-head',required=True)
    args=parser.parse_args(argv)
    try:
        before=preflight(args.expected_head);key=credential()
        root=ROOT/'.local'/AUTHORIZATION;root.mkdir(parents=True,exist_ok=True)
        with closing(InstanceLock(root/'authorization.lock')):
            budget=OneDiagnosticBudget(root)
            if budget.used():raise SafeFailure('separate_authorization_consumed_no_retry')
            grant=root/'authorization.json'
            if grant.exists():raise SafeFailure('authorization_already_started_review_existing_no_retry')
            request=payload(REFERENCE)
            authorization={'authorization_id':AUTHORIZATION,'maximum_searches':1,
                'scope':'Identical WIKA A-10 production request; no retry, NVIDIA or LangSmith export.',
                'source_revision':args.expected_head,'request_sha256':hashlib.sha256(safe_json(request,[]).encode()).hexdigest(),
                'original_preservation':before}
            # Durable grant marker before any application/provider call. Reopening
            # never creates another grant or refunds an uncertain attempt.
            with grant.open('x',encoding='utf-8') as stream:
                stream.write(safe_json(authorization,[key]));stream.flush();os.fsync(stream.fileno())
            os.environ.update(FAULTTRACE_ALLOW_INFERENCE='0',FAULTTRACE_LANGSMITH_TRACING='0',FAULTTRACE_TAVILY_ENABLED='1')
            from fastapi.testclient import TestClient
            from faulttrace.workflow.demo_app import create_demo_app
            app=create_demo_app(root/'application',ORIGIN,local_http=True,live=True,budget=budget,
                send=forbidden_transport,key_source=lambda:None)
            result={'status':'failed_or_interrupted','no_retry':True};client=None
            try:
                with TestClient(app,base_url=ORIGIN) as http:
                    client=Client(http,root/'application');result=run_lookup(client)
            finally:
                if client and result.get('status')=='failed_or_interrupted':result['retained_attempts']=client.retained()
                result.update(authorization_id=AUTHORIZATION,source_revision=args.expected_head,
                    separate_reservations=budget.used(),original_preservation_unchanged=preserved()==before)
                text=safe_json(result,[key])
                with (root/'result.pending').open('x',encoding='utf-8') as stream:
                    stream.write(text);stream.flush();os.fsync(stream.fileno())
                os.replace(root/'result.pending',root/'result.json')
                print(text);print('Private result: '+str((root/'result.json').relative_to(ROOT)))
            return 0 if result.get('status')=='completed' and result.get('sources') and result.get('trace_result')=='disabled' and result['original_preservation_unchanged'] else 1
    except SafeFailure as error:
        print(json.dumps({'diagnostic':str(error),'no_retry':True}));return 2
    except KeyboardInterrupt:
        print(json.dumps({'diagnostic':'interrupted_authorization_retained_no_retry'}));return 2
    except Exception:
        print(json.dumps({'diagnostic':'diagnostic_failed_no_raw_details_no_retry'}));return 2


if __name__=='__main__':raise SystemExit(main())
