"""Prepared metadata-only repair; no inference, retries or historical mutations."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import uuid

from faulttrace.partners.http import NoRedirect
from faulttrace.partners.tracing import metadata
from tools.diagnose_langsmith import ATTEMPTS, DiagnosticError, identity
from tools.verify_sprint_live import safe_json

ENDPOINT='https://api.smith.langchain.com'
ADDRESS='lrn:agents/faulttrace/environments/local'


def payloads(receipts,workspace):
    if not identity(workspace):
        raise DiagnosticError('invalid_repair_workspace')
    result=[]
    for receipt in receipts:
        aid=receipt['attempt_id']
        rid=str(uuid.uuid5(uuid.UUID(aid),'faulttrace-trace-repair-v1/'+workspace+'/'+ADDRESS))
        safe=metadata(ATTEMPTS[aid],receipt)
        safe['correlation_id']=rid
        safe['provenance']='reconstructed_metadata_only_repair_not_original_trace'
        start=datetime.fromisoformat(receipt['timestamp'])
        latency=receipt.get('latency_ms')
        if start.tzinfo is None or type(latency) is not int or not 0<=latency<=3600000:
            raise DiagnosticError('invalid_receipt_time_for_repair')
        start=start.astimezone(timezone.utc)
        end=start+timedelta(milliseconds=latency)
        body={'id':rid,'trace_id':rid,'dotted_order':start.strftime('%Y%m%dT%H%M%S%fZ')+rid,
            'name':'faulttrace.'+ATTEMPTS[aid],'run_type':'chain','address':ADDRESS,
            'start_time':start.isoformat(),'end_time':end.isoformat(),
            'inputs':{},'outputs':{},'extra':{'metadata':safe}}
        result.append({'attempt_id':aid,'run_id':rid,'state':'prepared','payload':body})
    return result


def atomic(path,value,key):
    text=safe_json(value,[key] if key else [])
    path=Path(path);temp=path.with_suffix('.pending')
    # An interrupted persistence operation is a blocker, never a reason to resend.
    with temp.open('x',encoding='utf-8') as stream:
        stream.write(text);stream.flush();os.fsync(stream.fileno())
    os.replace(temp,path)


def prepare(folder,receipts,workspace,source,search_path,key,project):
    if not identity(project):
        raise DiagnosticError('invalid_repair_project')
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/'plan.json'
    if path.exists():
        raise DiagnosticError('repair_plan_already_exists_review_existing_no_resend')
    plan={'version':1,'source_revision':source,'endpoint':ENDPOINT,'workspace_id':workspace,
        'destination':ADDRESS,'expected_project_id':project,
        'search_report_sha256':hashlib.sha256(search_path.read_bytes()).hexdigest(),
        'state':'prepared_not_executed','created_at':datetime.now(timezone.utc).isoformat(),
        'duplicate_risk':'Original remote IDs discarded; unknown historical runs may be duplicated.',
        'timestamp_basis':'Receipt start plus measured latency; original trace timestamps were not retained.',
        'entries':payloads(receipts,workspace),'http_events':[]}
    atomic(path,plan,key)
    return path,hashlib.sha256(path.read_bytes()).hexdigest()


def post_once(key,workspace,body):
    request=urllib.request.Request(ENDPOINT+'/runs',data=safe_json(body,[key]).encode(),
        headers={'x-api-key':key,'x-tenant-id':workspace,'Content-Type':'application/json'},method='POST')
    event={'method':'POST','route':'/runs','http_status':None,'diagnostic':'uncertain'}
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=3) as response:
            event['http_status']=response.status
            data=response.read(4097)
        event['diagnostic']=('http_acknowledged_not_read_back' if len(data)<=4096 and 200<=event['http_status']<300
                             else 'ack_unexpected_or_oversized_uncertain')
    except urllib.error.HTTPError as error:
        event.update(http_status=error.code,diagnostic='trace_http_error')
        error.close()  # No raw provider body, headers or exception strings retained.
    except Exception:
        event['diagnostic']='trace_transport_uncertain_no_retry'
    return event


def readback_path(entry,project):
    params=[('project_id',project),('start_time',entry['payload']['start_time'])]
    params += [('selects',s) for s in ('ID','NAME','PROJECT_ID','START_TIME','END_TIME','METADATA','TRACE_ID')]
    return '/api/v2/runs/'+entry['run_id']+'?'+urllib.parse.urlencode(params)


def matches(value,entry,project):
    if not isinstance(value,dict):
        return False
    body=entry['payload']
    meta=value.get('metadata')
    if meta is None and isinstance(value.get('extra'),dict):
        meta=value['extra'].get('metadata')
    if not (identity(value.get('id'))==entry['run_id'] and identity(value.get('project_id'))==project
            and value.get('name')==body['name'] and meta==body['extra']['metadata']
            and identity(value.get('trace_id'))==entry['run_id']):
        return False
    try:
        return all(datetime.fromisoformat(value[k].replace('Z','+00:00'))==datetime.fromisoformat(body[k])
                   for k in ('start_time','end_time'))
    except (KeyError,ValueError,TypeError,AttributeError):
        return False


def execute(path,reviewed_hash,receipts,key,reader,source):
    # Explicit later review only. Never called by the search/preparation path.
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=reviewed_hash:
        raise DiagnosticError('reviewed_plan_hash_mismatch')
    plan=json.loads(path.read_text(encoding='utf-8'))
    if (plan.get('state')!='prepared_not_executed' or plan.get('entries')!=payloads(receipts,plan.get('workspace_id'))
            or plan.get('source_revision')!=source or plan.get('endpoint')!=ENDPOINT
            or plan.get('destination')!=ADDRESS or not identity(plan.get('expected_project_id'))):
        raise DiagnosticError('unexpected_or_previously_started_repair_plan')
    search=path.parent.parent/'search.json'
    if hashlib.sha256(search.read_bytes()).hexdigest()!=plan.get('search_report_sha256'):
        raise DiagnosticError('reviewed_search_report_changed')
    evidence=json.loads(search.read_text(encoding='utf-8'))
    project=plan['expected_project_id']
    if (not evidence.get('repair_preparation_permitted') or evidence.get('remote_runs') or evidence.get('coverage_limits')
            or evidence.get('agent_local_project_id')!=project):
        raise DiagnosticError('search_does_not_support_repair')
    resolution=reader.request(ENDPOINT,'/api/v1/sessions/resolutions?kind=AGENT&id=faulttrace&environment=LOCAL',
                              workspace=plan['workspace_id'])
    if not isinstance(resolution,dict) or resolution.get('session_id')!=project:
        raise DiagnosticError('agent_destination_not_confirmed_no_export')
    plan['state']='started_no_automatic_retry';atomic(path,plan,key)
    for entry in plan['entries']:
        entry['state']='reserved_uncertain_until_read_back'
        atomic(path,plan,key)  # IDs/reservation persisted BEFORE the one allowed POST.
        event=post_once(key,plan['workspace_id'],entry['payload'])
        event['run_id']=entry['run_id'];plan['http_events'].append(event)
        entry['state']='http_acknowledged' if event['diagnostic']=='http_acknowledged_not_read_back' else 'uncertain_or_failed'
        atomic(path,plan,key)
        # Exactly one read-back even if the HTTP outcome was uncertain. Never resends.
        value=reader.request(ENDPOINT,readback_path(entry,project),workspace=plan['workspace_id'])
        verified=matches(value,entry,project)
        entry['remote_readable_and_fingerprint_verified']=verified
        entry['state']='read_back_verified' if verified else 'not_verified_stop'
        plan['readback_http_events']=reader.events
        if verified:
            entry['dashboard_url']=f'https://smith.langchain.com/o/{plan["workspace_id"]}/projects/p/{project}/r/{entry["run_id"]}?poll=true'
        atomic(path,plan,key)
        if not verified or event['diagnostic']!='http_acknowledged_not_read_back':
            break
    plan['state']=('read_back_verified_all' if all(e['state']=='read_back_verified' for e in plan['entries'])
                   else 'stopped_requires_review_no_resend')
    atomic(path,plan,key)
    return plan
