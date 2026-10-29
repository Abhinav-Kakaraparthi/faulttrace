"""OFFLINE verification-runner tests; all service transports are independent doubles."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager, redirect_stdout
import hashlib
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient
from PIL import Image
from faulttrace.accounting import MODEL, VISION_MODEL, new_receipt
from faulttrace.workflow.demo_app import create_demo_app
from faulttrace.workflow.storage import WorkflowError
from faulttrace.http_diagnostics import ProviderHTTPError
from faulttrace.ledger import load
from tools.sprint_client import Client, ORIGIN
from tools.sprint_inventory import audit, Control, SafeFailure, SprintSpending
from tools import verify_sprint_live as runner
from test_photo_observation import envelope, gauge

SECRETS = {'NEBIUS_API_KEY':'SENTINEL_NEBIUS_KEY_NO_DISCLOSURE',
           'TAVILY_API_KEY':'SENTINEL_TAVILY_KEY_NO_DISCLOSURE',
           'LANGSMITH_API_KEY':'SENTINEL_TRACE_KEY_NO_DISCLOSURE','LANGSMITH_PROJECT':'offline_test'}


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.root/'.local').mkdir()

    def receipt(self, **changes):
        return dict(new_receipt(None),timestamp='2026-10-29T00:00:00+00:00',transport_invoked=True,
                    validation_result='passed',**changes)

    def test_audit_deduplicates_databases_and_ledgers_without_writing_them(self):
        r=self.receipt(); folder=self.root/'.local/old'; folder.mkdir()
        ledger=folder/'usage.json'; ledger.write_text(json.dumps({'version':1,'receipts':[r]}))
        with closing(sqlite3.connect(folder/'workflow.sqlite3')) as db, db:
            db.execute('CREATE TABLE planning(id TEXT,created_at TEXT,status TEXT,receipt TEXT)')
            db.execute('INSERT INTO planning VALUES(?,?,?,?)',(r['attempt_id'],r['timestamp'],'accepted',json.dumps(r)))
        with closing(sqlite3.connect(folder/'spending.sqlite3')) as db, db:
            db.execute('CREATE TABLE reservations(id TEXT,operation TEXT,created REAL,status TEXT)')
            db.execute("INSERT INTO reservations VALUES(?,'planning',1793232000,'settled')",(r['attempt_id'],))
        before=hashlib.sha256(ledger.read_bytes()).hexdigest()
        records=audit(self.root)
        self.assertEqual(len(records),1)
        self.assertEqual(records[r['attempt_id']]['operation'],'planning')
        self.assertFalse(records[r['attempt_id']]['uncertain'])
        self.assertEqual(hashlib.sha256(ledger.read_bytes()).hexdigest(),before)

    def test_old_calls_excluded_and_pending_calls_remain_uncertain(self):
        folder=self.root/'.local/old';folder.mkdir()
        old=self.receipt();old['timestamp']='2026-10-24T00:00:00+00:00'
        (folder/'usage.json').write_text(json.dumps({'receipts':[old]}))
        with closing(sqlite3.connect(folder/'workflow.sqlite3')) as db, db:
            db.execute('CREATE TABLE planning(id TEXT,created_at TEXT,status TEXT,receipt TEXT)')
            db.execute("INSERT INTO planning VALUES(?,?,'pending',NULL)",(str(uuid.uuid4()),'2026-10-29T00:00:00+00:00'))
        control=Control(self.root)
        self.assertEqual(control.snapshot()['used']['planning'],1)
        self.assertIn('planning',control.snapshot()['blocked'])
        with self.assertRaises(WorkflowError):control.reserve('planning',str(uuid.uuid4()))

    def test_labeled_provider_doubles_and_neighbor_ledger_are_not_counted(self):
        folder=self.root/'.local/double';(folder/'data').mkdir(parents=True)
        with closing(sqlite3.connect(folder/'data/workflow.sqlite3')) as db, db:
            db.execute('CREATE TABLE integrated_runs(test_output INTEGER)');db.execute('INSERT INTO integrated_runs VALUES(1)')
        (folder/'usage.json').write_text(json.dumps({'receipts':[self.receipt()]}))
        self.assertEqual(audit(self.root),{})

    def test_malformed_inventory_fails_closed_without_reflecting_content(self):
        (self.root/'.local/result.json').write_text('PRIVATE_SENTINEL_NOT_JSON')
        with self.assertRaisesRegex(SafeFailure,'^inventory_unreadable$'):audit(self.root)

    def test_existing_failed_trace_blocks_exports_without_reclassifying_inference(self):
        folder=self.root/'.local/previous';folder.mkdir();r=self.receipt()
        with closing(sqlite3.connect(folder/'workflow.sqlite3')) as db, db:
            db.execute('CREATE TABLE planning(id TEXT,created_at TEXT,status TEXT,receipt TEXT)')
            db.execute('INSERT INTO planning VALUES(?,?,?,?)',(r['attempt_id'],r['timestamp'],'accepted',json.dumps(r)))
            db.execute('CREATE TABLE trace_exports(attempt_id TEXT,status TEXT)')
            db.execute('INSERT INTO trace_exports VALUES(?,?)',(r['attempt_id'],'failed'))
        view=Control(self.root).snapshot()
        self.assertIn('tracing',view['blocked']);self.assertNotIn('planning',view['blocked'])

    def test_shared_cap_survives_rerun_and_concurrent_image_reservations(self):
        control=Control(self.root)
        def reserve(_):
            try:control.reserve('photo',str(uuid.uuid4()));return True
            except WorkflowError:return False
        with ThreadPoolExecutor(max_workers=6) as pool:
            self.assertEqual(sum(pool.map(reserve,range(6))),1)
        restarted=Control(self.root)
        self.assertEqual(restarted.snapshot()['used']['photo'],1)
        self.assertIn('photo',restarted.snapshot()['blocked'])
        with self.assertRaises(WorkflowError):restarted.reserve('photo',str(uuid.uuid4()))

    def test_failed_planning_stops_remaining_turn_and_trace_failure_is_separate(self):
        c=Control(self.root);aid=str(uuid.uuid4());c.reserve('planning',aid);c.complete(aid,True)
        with self.assertRaises(WorkflowError):c.reserve('planning',str(uuid.uuid4()))
        c.block('tracing');c.reserve('documentation',str(uuid.uuid4()))
        self.assertEqual(c.snapshot()['used']['planning'],1)

    def test_duplicate_slot_and_conflicting_operation(self):
        c=Control(self.root);aid=str(uuid.uuid4());c.reserve('planning',aid);c.complete(aid,False)
        c.reserve('planning',aid)
        self.assertEqual(c.snapshot()['used']['planning'],1)
        with self.assertRaises(WorkflowError):c.reserve('photo',aid)

    def test_checkout_is_rechecked_at_admission_before_any_slot_is_granted(self):
        c=Control(self.root,verify=lambda:(_ for _ in ()).throw(SafeFailure('checkout_revision_mismatch')))
        with self.assertRaisesRegex(SafeFailure,'checkout_revision_mismatch'):
            c.reserve('planning',str(uuid.uuid4()))
        self.assertEqual(c.snapshot()['used']['planning'],0)

    def test_credential_presence_and_safe_failures_never_print_values(self):
        with patch.dict(os.environ,SECRETS):
            self.assertEqual(runner.credentials(),[SECRETS[n] for n in runner.REQUIRED[:-1]])
            with self.assertRaisesRegex(SafeFailure,'credential_in_output_rejected'):
                runner.safe_json({'value':SECRETS['NEBIUS_API_KEY']},runner.credentials())
            with self.assertRaisesRegex(SafeFailure,'credential_in_output_rejected'):
                runner.safe_json({'nested':['quoted-"-private']},['quoted-"-private'])
        output=StringIO()
        with patch.object(runner,'preflight',return_value='hash'), patch.object(runner,'credentials',side_effect=SafeFailure('missing_TAVILY_API_KEY')),redirect_stdout(output):
            self.assertEqual(runner.main(['--expected-head','a'*40]),2)
        self.assertIn('missing_TAVILY_API_KEY',output.getvalue())
        for secret in SECRETS.values():self.assertNotIn(secret,output.getvalue())

    def test_exact_revision_preflight_rejects_mismatch_before_service_contact(self):
        with patch.object(runner,'git',return_value='b'*40):
            with self.assertRaisesRegex(SafeFailure,'checkout_revision_mismatch'):runner.preflight('a'*40)

    def test_photo_production_validation_hashes_original_and_strips_metadata(self):
        image=Image.new('RGB',(32,24),'white'); data=BytesIO();image.save(data,format='PNG')
        path=self.root/'filename-NEVER-IN-MODEL.png';path.write_bytes(data.getvalue())
        original=path.read_bytes();submitted,provenance=runner.photo_input(path)
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(provenance['source_sha256'],hashlib.sha256(original).hexdigest())
        self.assertEqual(provenance['submitted_sha256'],hashlib.sha256(submitted).hexdigest())
        self.assertEqual(provenance['dimensions'],[32,24])


class RouteVerificationTests(unittest.TestCase):
    def test_complete_console_entrypoint_creates_only_isolated_records_and_atomic_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'.local').mkdir()
            ledger=root/'.local/nebius-usage.json';ledger.write_text('{"version":1,"receipts":[]}')
            before=ledger.read_bytes();path=root/'private-source.png'
            Image.new('RGB',(32,24),'white').save(path)
            calls=[]
            def neo(secret,payload):
                calls.append(payload)
                if payload['model']==VISION_MODEL:
                    ref=re.search(r'"evidence_ref":"([^"]+)"',payload['messages'][0]['content'])[1]
                    return json.dumps(envelope(gauge(evidence_ref=ref))).encode()
                context=json.loads(payload['messages'][1]['content'])
                choice='OBSERVE_F-17_READ_LOCAL_DP' if len(calls)==1 else 'ESCALATE_HUMAN_INVESTIGATION'
                value={'action_id':choice,'context_revision':context['context_revision'],
                    'evidence_refs':[context['telemetry']['evidence_ref']],'explanation_code':'human_review'}
                return json.dumps({'id':'chatcmpl-'+str(uuid.uuid4()),'model':MODEL,
                    'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps(value)}}],
                    'usage':{'prompt_tokens':12,'completion_tokens':8,'total_tokens':20}}).encode()
            def factory(*args,**kwargs):
                return create_demo_app(*args,**kwargs,send=neo,key_source=lambda:SECRETS['NEBIUS_API_KEY'])
            reference=json.dumps({'results':[{'url':'https://wika.com/model-42','title':'Model 42',
                'content':'OFFLINE reference double'}],'usage':{'credits':1}}).encode()
            answers=iter(('yes','wika.com','Model 42','yes','cannot-access'))
            output=StringIO()
            with patch.dict(os.environ,SECRETS),patch.object(runner,'ROOT',root),patch.object(runner,'preflight',return_value=hashlib.sha256(before).hexdigest()),patch('faulttrace.workflow.demo_app.create_demo_app',side_effect=factory),patch('faulttrace.partners.tavily.post_json',return_value=reference),patch('faulttrace.partners.tracing.post_json',return_value=b'{}'),redirect_stdout(output):
                code=runner.main(['--expected-head','a'*40,'--photo',str(path)],ask=lambda _:next(answers))
            self.assertEqual(code,0,output.getvalue())
            files=list((root/'.local/sprint-verification/investigations').glob('*/result.json'))
            self.assertEqual(len(files),1)
            result=json.loads(files[0].read_text())
            self.assertEqual(result['after'],{'planning':2,'photo':1,'documentation':1})
            self.assertTrue(result['real_ledger_unchanged']);self.assertEqual(ledger.read_bytes(),before)
            self.assertEqual(len(calls),3)
            self.assertFalse(list(files[0].parent.glob('*.pending')))
            for secret in SECRETS.values():
                if secret!='offline_test':self.assertNotIn(secret,output.getvalue())

    @contextmanager
    def session(self, failure=None):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ,dict(SECRETS,
                FAULTTRACE_TAVILY_ENABLED='1',FAULTTRACE_LANGSMITH_TRACING='1')):
            root=Path(temporary); control=Control(root)
            case=root/'.local/new-check'; case.mkdir()
            calls,trace_calls,searches=[],[],[]
            def send(secret, payload):
                calls.append(payload)
                if failure=='planning':
                    raise ProviderHTTPError(400)
                if payload['model']==VISION_MODEL:
                    ref=re.search(r'"evidence_ref":"([^"]+)"',payload['messages'][0]['content'])[1]
                    value=envelope(gauge(evidence_ref=ref))
                    if failure=='photo':
                        value['choices'][0].update(finish_reason='length')
                        value['choices'][0]['message']['reasoning_content']='MUST_NOT_LOG_REASONING'
                    return json.dumps(value).encode()
                context=json.loads(payload['messages'][1]['content'])
                n=sum(p['model']==MODEL for p in calls)
                action='OBSERVE_F-17_READ_LOCAL_DP' if n==1 else 'OBSERVE_V-08_OBSERVE_POSITION'
                value={'action_id':action,'context_revision':context['context_revision'],
                    'evidence_refs':[context['telemetry']['evidence_ref']],'explanation_code':'evidence_gap'}
                return json.dumps({'id':'chatcmpl-'+str(uuid.uuid4()),'model':MODEL,
                    'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps(value)}}],
                    'usage':{'prompt_tokens':12,'completion_tokens':8,'total_tokens':20}}).encode()
            def search(url,headers,payload,**kwargs):
                searches.append(payload)
                return json.dumps({'results':[{'url':'https://www.wika.com/model-42',
                    'title':'Model 42','content':'OFFLINE REFERENCE DOUBLE, not measured evidence'}],
                    'usage':{'credits':1}}).encode()
            def trace(url,headers,payload,**kwargs):
                trace_calls.append(payload)
                if failure=='trace':raise RuntimeError('MUST_NOT_LOG_REASONING')
                return b'{}'
            budget=SprintSpending(case,control)
            app=create_demo_app(case,ORIGIN,local_http=True,live=True,budget=budget,send=send,
                key_source=lambda:SECRETS['NEBIUS_API_KEY'])
            pixels=BytesIO();Image.new('RGB',(32,24),'white').save(pixels,format='PNG')
            with patch('faulttrace.partners.tavily.post_json',side_effect=search),patch('faulttrace.partners.tracing.post_json',side_effect=trace),TestClient(app,base_url=ORIGIN) as http:
                client=Client(http,case)
                answers=iter(('independent','F-17','differential_pressure','271.8','kPa'))
                verifier=runner.Verification(client,control,pixels.getvalue(),lambda _:next(answers),list(SECRETS.values())[:3])
                output=StringIO()
                with redirect_stdout(output):
                    result=verifier.run({'manufacturer':'WIKA','model':'Model 42','domain':'wika.com'})
                yield result,client,control,calls,searches,trace_calls,output.getvalue()

    def test_actual_integrated_routes_four_operations_and_separate_success_claims(self):
        with self.session() as (result,client,control,calls,searches,traces,output):
            self.assertEqual([r['status'] for r in result['planning']],['passed','passed'])
            self.assertEqual(result['photographic_contract']['status'],'passed')
            self.assertEqual(result['photographic_contract']['numeric_accuracy'],'not_evaluated')
            self.assertEqual(result['photographic_contract']['interpretation']['reading'],2.6)
            self.assertEqual(result['tavily_retrieval']['status'],'passed')
            self.assertEqual(len(calls),3);self.assertEqual(len(searches),1);self.assertEqual(len(traces),4)
            self.assertEqual(control.snapshot()['used'],{'planning':2,'photo':1,'documentation':1})
            self.assertEqual(len(load(client.run/'usage.json')),3)
            self.assertEqual(len(client.retained()),4)
            photo=next(p for p in calls if p['model']==VISION_MODEL)
            self.assertEqual(photo['max_tokens'],2048);self.assertEqual(photo['reasoning_effort'],'none')
            self.assertEqual(photo['messages'][1]['content'][0]['type'],'image_url')
            for forbidden in ('271.8','filename-NEVER-IN-MODEL','telemetry','expected_reading'):
                self.assertNotIn(forbidden,photo['messages'][0]['content'])
            state=client.call('/api/state')
            self.assertEqual(state['evidence'][-1]['human_observation']['reading'],271.8)
            self.assertEqual(state['journey']['maintenance_status'],'not_completed')
            for request in traces:
                self.assertEqual(request['inputs'],{});self.assertEqual(request['outputs'],{})
                self.assertNotIn('271.8',json.dumps(request))
            for secret in SECRETS.values():
                if secret!='offline_test':self.assertNotIn(secret,output)

    def test_provider_failure_stops_planning_and_photo_but_allows_reference_path(self):
        with self.session('planning') as (result,client,control,calls,searches,traces,output):
            self.assertEqual(len(calls),1);self.assertEqual(result['planning'][0]['status'],'failed')
            self.assertEqual(result['photographic_contract']['status'],'not_attempted')
            self.assertEqual(result['tavily_retrieval']['status'],'passed')
            self.assertIn('planning',control.snapshot()['blocked'])
            receipt=result['planning'][0]['receipt']
            self.assertEqual(receipt['http_status'],400);self.assertIsNone(receipt['token_usage'])
            self.assertEqual(len(load(client.run/'usage.json')),1)

    def test_truncation_retains_usage_and_never_repairs_or_retries_photo(self):
        with self.session('photo') as (result,client,control,calls,searches,traces,output):
            self.assertEqual(sum(p['model']==VISION_MODEL for p in calls),1)
            photo=result['photographic_contract']
            self.assertEqual(photo['status'],'failed');self.assertIsNone(photo['interpretation'])
            self.assertEqual(photo['receipt']['finish_reason'],'length')
            self.assertEqual(photo['receipt']['token_usage']['total_tokens'],24)
            self.assertIn('photo',control.snapshot()['blocked'])
            self.assertNotIn('MUST_NOT_LOG_REASONING',output)

    def test_trace_failure_stops_exports_without_retrying_or_failing_inference(self):
        with self.session('trace') as (result,client,control,calls,searches,traces,output):
            self.assertEqual(len(traces),1)
            self.assertEqual(len(calls),3);self.assertEqual(result['tavily_retrieval']['status'],'passed')
            self.assertEqual([t['status'] for t in result['langsmith_delivery']],['failed','disabled','disabled','disabled'])
            self.assertIn('tracing',control.snapshot()['blocked'])
            self.assertNotIn('MUST_NOT_LOG_REASONING',output)
