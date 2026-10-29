"""One wider read-only search; prepares a reviewable plan, never auto-executes it."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from faulttrace.workflow.storage import InstanceLock
from tools.diagnose_langsmith import (CASE,SELECT,Reader,DiagnosticError,environment,
    local_receipts,candidates,identity)
from tools.langsmith_trace_repair import ENDPOINT,atomic,prepare,execute
from tools.verify_sprint_live import safe_json

PRIOR='.local/langsmith-diagnostics/c8b3c5c3393e4b4cab806e290b8175c9.json'
WINDOW=('2026-10-28T00:00:00+00:00','2026-10-30T00:00:00+00:00')


def wider_search(reader,receipts,prior):
    projects={r['project_id']:r['name'] for r in prior['projects'] if r['endpoint']==ENDPOINT}
    targets=[r for r in prior['projects'] if r['endpoint']==ENDPOINT and r['name'] in ('Local','faulttrace-local')]
    local=[r['project_id'] for r in targets if r['name']=='Local']
    agent=[r['project_id'] for r in targets if r['name']=='faulttrace-local']
    scopes={r['workspace_id'] for r in targets}
    if len(scopes)!=1 or len(local)!=1 or len(agent)!=1 or not identity(next(iter(scopes))):
        raise DiagnosticError('confirmed_project_scope_mismatch')
    workspace=next(iter(scopes));local_id=local[0];agent_id=agent[0]
    if len(projects)>200:
        raise DiagnosticError('unexpected_project_inventory')
    queries=[('wider_start_time_search',{'session':list(projects),'start_time':WINDOW[0],
        'filter':f'and(gt(start_time,"{WINDOW[0]}"),lt(start_time,"{WINDOW[1]}"),or(eq(name,"faulttrace.planning"),eq(name,"faulttrace.photo_analysis")))',
        'select':SELECT,'limit':100,'order':'desc'},WINDOW),
        ('unfiltered_recent_named_Local',{'session':[local_id],'select':SELECT,'limit':100,'order':'desc'},None)]
    result={'mode':'READ ONLY; at most two run-query requests; no trace export',
        'workspace_id':workspace,'named_local_project_id':local_id,'agent_local_project_id':agent_id,'window':list(WINDOW),'queries':[],'remote_runs':[],
        'coverage_limits':[],'original_trace_timestamps':'not retained; UTC export clock was independent of receipt timestamps'}
    for name,body,window in queries:
        value=reader.request(ENDPOINT,'/runs/query',workspace=workspace,body=body)
        summary={'name':name,'request':body}
        result['queries'].append(summary)
        if not isinstance(value,dict) or not isinstance(value.get('runs'),list):
            result['coverage_limits'].append('query_failed_stop_no_retry')
            break
        rows=value['runs'];summary['returned_count']=len(rows)
        if any(not isinstance(r,dict) or not identity(r.get('id')) or not identity(r.get('session_id'))
               or not isinstance(r.get('name'),str) or not isinstance(r.get('start_time'),str) for r in rows):
            result['coverage_limits'].append(name+'_incomplete_run_rows')
        # The request is unfiltered; only faulttrace records are projected to the report.
        selected=candidates(rows,receipts,workspace,projects,ENDPOINT,window=window)
        result['remote_runs'].extend(selected)
        if sum(isinstance(r,dict) and r.get('name') in ('faulttrace.planning','faulttrace.photo_analysis') for r in rows)!=len(selected):
            result['coverage_limits'].append(name+'_faulttrace_rows_not_fully_projectable')
        if value.get('cursors',{}).get('next'):
            result['coverage_limits'].append(name+'_first_100_only')
    unique={r['run_id']:r for r in result['remote_runs']}
    result['remote_runs']=list(unique.values())
    result['http_diagnostics']=reader.events
    result['receipt_fingerprints_located']=sorted({a for r in unique.values() for a in r['receipt_fingerprint_matches']})
    result['repair_preparation_permitted']=(len(result['queries'])==2 and not unique and not result['coverage_limits']
        and len(reader.events)==2 and all(e.get('http_status')==200 and e.get('diagnostic')=='http_response_readable' for e in reader.events))
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--execute-reviewed-plan',type=Path)
    parser.add_argument('--reviewed-plan-sha256')
    args=parser.parse_args(argv)
    try:
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if head!=args.expected_head or subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):
            raise DiagnosticError('reviewed_clean_checkout_required')
        receipts=local_receipts(ROOT/CASE)
        key,_=environment()
        folder=ROOT/'.local/langsmith-followup';folder.mkdir(parents=True,exist_ok=True)
        ledger=ROOT/'.local/nebius-usage.json';before=hashlib.sha256(ledger.read_bytes()).hexdigest()
        with closing(InstanceLock(folder/'instance.lock')):
            reader=Reader(key)
            if args.execute_reviewed_plan:
                expected=(folder/'repair/plan.json').resolve()
                if args.execute_reviewed_plan.resolve()!=expected or not args.reviewed_plan_sha256:
                    raise DiagnosticError('reviewed_plan_path_and_hash_required')
                result=execute(expected,args.reviewed_plan_sha256,receipts,key,reader,head)
            else:
                path=folder/'search.json'
                if path.exists():
                    raise DiagnosticError('wider_search_already_reserved_review_saved_result_no_retry')
                atomic(path,{'state':'reserved_search_uncertain_until_saved','source_revision':head},key)
                prior=json.loads((ROOT/PRIOR).read_text(encoding='utf-8'))
                result=wider_search(reader,receipts,prior)
                result['source_revision']=head
                result['receipt_timestamps']=[{k:r.get(k) for k in ('attempt_id','timestamp','latency_ms')} for r in receipts]
                atomic(path,result,key)
                if result['repair_preparation_permitted']:
                    plan,digest=prepare(folder/'repair',receipts,result['workspace_id'],head,path,key,result['agent_local_project_id'])
                    result['prepared_plan']={'path':str(plan.relative_to(ROOT)),'sha256':digest,'state':'NOT EXECUTED; review required'}
            result['real_ledger_unchanged']=hashlib.sha256(ledger.read_bytes()).hexdigest()==before
            atomic(folder/'result.json',result,key)
            print(safe_json(result,[key]))
            print('Private artifacts: .local/langsmith-followup/')
            return 0
    except DiagnosticError as error:
        print(json.dumps({'diagnostic':str(error),'no_retry':True}));return 2
    except Exception:
        print(json.dumps({'diagnostic':'followup_failed_no_raw_details_no_retry','no_retry':True}));return 2


if __name__=='__main__':
    raise SystemExit(main())
