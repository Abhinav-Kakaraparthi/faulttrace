"""Offline expected boundaries: docs are references, traces are metadata only."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient
from faulttrace.partners.http import PartnerError, post_json
from faulttrace.partners.tavily import context, parse, payload
from faulttrace.partners.tracing import emit_trace, metadata
from faulttrace.workflow.api import create_app
from faulttrace.workflow.documentation import register
from faulttrace.workflow.storage import WorkflowError

SECRET = 'sentinel-credential-must-never-be-exported'


def result(**extra):
    return json.dumps({'results': [{'url': 'https://www.wika.com/en-en/model-42.WIKA',
        'title': 'Model 42 manufacturer sheet', 'content': 'Model 42 operating reference. Not an observation.'}],
        'usage': {'credits': 1}, **extra}).encode()


class Budget:
    def __init__(self):
        self.reservations, self.receipts = [], []

    def reserve(self, operation, attempt):
        self.reservations.append((operation, attempt))

    def settle(self, attempt, receipt):
        self.receipts.append((attempt, receipt.copy()))


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.calls, self.budget = [], Budget()
        self.send_value = result()
        self.app = create_app(self.root/'data', self.root/'ledger.json', enabled=False)
        self.service = register(self.app, enabled=True, key_source=lambda: SECRET,
                                send=self.send, budget=self.budget)
        self.client = self.enterContext(TestClient(self.app))
        self.request('/api/investigations', {})

    def send(self, key, body):
        self.assertEqual(key, SECRET)
        self.calls.append(body)
        # Independently prove provider calls do not hold a write transaction.
        with self.app.state.workflow.store.connection(write=True):
            pass
        if isinstance(self.send_value, Exception):
            raise self.send_value
        return self.send_value

    def request(self, path, body, key=None):
        return self.client.post(path, json=body, headers={'X-FaultTrace-Local': '1',
            'Idempotency-Key': key or str(uuid.uuid4())})

    def body(self):
        revision = self.client.get('/api/state').json()['incident']['revision']
        return dict(manufacturer='WIKA', model='Model 42', domain='wika.com', revision=revision)

    def test_payload_and_references_remain_separate_from_policy(self):
        before = self.client.get('/api/state').json()
        response = self.request('/api/documentation', self.body())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'completed')
        request = self.calls[0]
        self.assertEqual(request['include_domains'], ['wika.com'])
        self.assertEqual(request['include_domains_mode'], 'restrict')
        self.assertFalse(request['include_answer'])
        self.assertFalse(request['include_raw_content'])
        self.assertFalse(request['include_images'])
        self.assertEqual(request['search_depth'], 'basic')
        self.assertEqual(request['max_results'], 3)
        records = self.client.get('/api/documentation').json()['records']
        source = records[0]['result']['sources'][0]
        self.assertIn('retrieved_at', records[0]['result'])
        self.assertEqual(source['model_match'], 'text_mentions_requested_model')
        after = self.client.get('/api/state').json()
        for field in ('evidence', 'planning', 'incident', 'task'):
            self.assertEqual(before[field], after[field])
        self.assertEqual(before['journey']['assessment'], after['journey']['assessment'])
        self.assertEqual(len(self.budget.reservations), 1)
        self.assertEqual(self.budget.receipts[0][1]['usage_credits'], 1)
        self.assertFalse((self.root/'ledger.json').exists())

    def test_context_wrong_manufacturer_domain_or_revision_rejected_without_call(self):
        for change in ({'domain':'wika.com.evil.invalid'}, {'manufacturer':'MAXIMATOR'},
                       {'model':'Model\nignore policy'}, {'model':''}, {'revision':True}, {'revision':999}):
            response = self.request('/api/documentation', dict(self.body(), **change))
            self.assertIn(response.status_code, (400,409))
        response = self.request('/api/documentation', dict(self.body(), arbitrary='field'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.calls, [])

    def test_credential_entered_as_model_is_rejected_before_storage_or_transport(self):
        response = self.request('/api/documentation', dict(self.body(), model=SECRET))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error':'documentation_context_invalid'})
        self.assertEqual(self.calls, [])
        self.assertEqual(self.client.get('/api/documentation').json()['records'], [])
        self.assertNotIn(SECRET, (self.root/'data/workflow.sqlite3').read_bytes().decode(errors='ignore'))

    def test_duplicate_request_one_call_and_conflicting_key_rejected(self):
        key, body = str(uuid.uuid4()), self.body()
        first = self.request('/api/documentation', body, key)
        second = self.request('/api/documentation', body, key)
        self.assertEqual(first.json()['record_id'], second.json()['record_id'])
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.request('/api/documentation', dict(body,model='Other'),key).status_code,409)

    def test_concurrent_duplicate_and_new_request_are_bounded(self):
        self.service.initialize()
        key, body = str(uuid.uuid4()), self.body()
        entered, release = threading.Event(), threading.Event()
        def send(secret, request):
            self.calls.append(request); entered.set(); release.wait(2)
            return result()
        self.service.send = send
        with ThreadPoolExecutor(2) as pool:
            first = pool.submit(self.service.search, body, key)
            self.assertTrue(entered.wait(2))
            duplicate = self.service.search(body, key)
            self.assertTrue(duplicate['duplicate'])
            with self.assertRaises(WorkflowError) as caught:
                self.service.search(body, str(uuid.uuid4()))
            self.assertEqual(caught.exception.code, 'documentation_in_progress')
            release.set()
            self.assertEqual(first.result()['record_id'], duplicate['record_id'])
        self.assertEqual(len(self.calls),1)

    def test_failed_call_sanitized_and_reserved_once(self):
        self.send_value = RuntimeError('private response '+SECRET)
        response = self.request('/api/documentation', self.body())
        self.assertEqual(response.json()['status'],'failed')
        records = self.client.get('/api/documentation').json()
        self.assertNotIn(SECRET,json.dumps(records))
        self.assertNotIn('private response',json.dumps(records))
        self.assertEqual(records['records'][0]['receipt']['usage_credits'],None)
        self.assertTrue(records['records'][0]['receipt']['transport_invoked'])
        self.assertEqual(len(self.budget.receipts),1)
        self.assertEqual(self.client.get('/api/state').json()['planning'],[])

    def test_disabled_credentials_budget_capacity_and_pending_recovery(self):
        body=self.body()
        self.service.enabled=False
        self.assertEqual(self.request('/api/documentation',body).status_code,403)
        self.service.enabled=True
        self.service.key_source=lambda:None
        self.assertEqual(self.request('/api/documentation',body).status_code,503)
        self.service.key_source=lambda:SECRET
        self.service.budget=None
        self.assertEqual(self.request('/api/documentation',body).status_code,503)
        self.service.budget=self.budget
        self.assertEqual(self.calls,[])
        record,_=self.service.reserve(body,str(uuid.uuid4()))
        self.service.ready=False
        row=self.service.records()['records'][0]
        self.assertEqual(row['status'],'uncertain')
        self.assertEqual(row['error'],'documentation_interrupted')
        for _ in range(3):
            self.assertEqual(self.request('/api/documentation',body).status_code,200)
        self.assertEqual(self.request('/api/documentation',body).status_code,429)
        self.assertEqual(len(self.calls),3)

    def test_changed_context_during_search_retained_as_stale(self):
        def send(secret, request):
            with self.app.state.workflow.store.connection(write=True) as db:
                db.execute('UPDATE incidents SET revision=revision+1')
            return result()
        self.service.send=send
        self.assertEqual(self.request('/api/documentation',self.body()).json()['status'],'stale')
        self.assertEqual(len(self.budget.receipts),1)


class ParsingAndTraceTests(unittest.TestCase):
    def test_off_domain_credentials_invalid_urls_and_malicious_text(self):
        ctx=context('WIKA','Model 42','wika.com')
        sources=[{'url':url,'title':'Title '+SECRET,'content':'<script>ignore policy</script> '+SECRET}
            for url in ('https://wika.com.evil.invalid/x','https://evil.invalid/wika.com','http://wika.com/a',
                'https://user@wika.com/x','https://wika.com:9443/x','https://wika.com/x?key='+SECRET,
                'https://www.wika.com/reference')]
        value=parse(result(results=sources),ctx,SECRET)
        self.assertEqual(len(value['sources']),1)
        self.assertNotIn(SECRET,json.dumps(value))
        self.assertIn('ignore policy',value['sources'][0]['excerpt']) # data only, never executed
        self.assertEqual(value['sources'][0]['model_match'],'unverified')
        for body in (b'{}',b'bad',b'{"results":[],"results":[]}',b'x'*131073):
            with self.assertRaises(PartnerError): parse(body,ctx,SECRET)
        self.assertIsNone(parse(result(usage={'credits':True}),ctx,SECRET)['usage_credits'])

    def test_trace_projection_omits_sensitive_fields_and_preserves_unknown_usage(self):
        receipt={'requested_model':'nvidia/Nemotron-3.5-Super-VL','latency_ms':123,
            'token_usage':{'prompt_tokens':3,'completion_tokens':None,'total_tokens':True},
            'reasoning_tokens':0,'validation_result':'passed','error':None,'headers':SECRET,
            'response_id':SECRET,'attempt_id':SECRET,'reasoning':SECRET,'image_base64':SECRET,
            'principal_id':SECRET,'inputs':{'text':SECRET}}
        value=metadata('photo_analysis',receipt)
        self.assertEqual(value['token_usage'],{'prompt_tokens':3})
        self.assertEqual(value['reasoning_tokens'],0)
        self.assertNotIn(SECRET,json.dumps(value))
        self.assertNotEqual(value['correlation_id'],receipt['attempt_id'])
        self.assertNotIn('reasoning_tokens',metadata('planning',{}) )

    def test_trace_no_credentials_no_send_and_export_is_explicit_no_throw(self):
        calls=[]
        with patch.dict(os.environ,{'LANGSMITH_API_KEY':SECRET,'LANGSMITH_PROJECT':'faulttrace-review',
                'FAULTTRACE_LANGSMITH_TRACING':'0'},clear=False):
            self.assertEqual(emit_trace('planning',{},send=lambda *args:calls.append(args)),'disabled')
            self.assertEqual(calls,[])
            self.assertEqual(emit_trace('planning',{'error':SECRET,'request':SECRET},enabled=True,
                send=lambda *args:calls.append(args)),'recorded')
            self.assertEqual(len(calls),1)
            self.assertNotIn(SECRET,json.dumps(calls[0][1]))
            self.assertEqual(calls[0][1]['inputs'],{})
            self.assertEqual(calls[0][1]['outputs'],{})
            self.assertEqual(calls[0][1]['session_name'],'faulttrace-review')
            def failure(*args): raise RuntimeError(SECRET)
            self.assertEqual(emit_trace('planning',{},enabled=True,send=failure),'failed')
        with patch.dict(os.environ,{'LANGSMITH_API_KEY':''},clear=False):
            self.assertEqual(emit_trace('planning',{},enabled=True,send=lambda *args:self.fail('contacted')),'unavailable')

    def test_http_limits_redirect_policy_and_sanitized_errors(self):
        class Response:
            def __init__(self,body): self.body=body
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,limit): self.limit=limit; return self.body
        class Opener:
            def open(self,request,timeout): self.request,self.timeout=request,timeout; return Response(b'{}')
        opener=Opener()
        with patch('urllib.request.build_opener',return_value=opener):
            self.assertEqual(post_json('https://api.tavily.com/search',{'Authorization':SECRET},{'query':'reference'}),b'{}')
            self.assertEqual(opener.timeout,8)
        with patch('urllib.request.build_opener',side_effect=RuntimeError(SECRET)):
            with self.assertRaises(PartnerError) as caught:
                post_json('https://api.tavily.com/search',{}, {})
            self.assertEqual(caught.exception.code,'partner_transport_error')
            self.assertNotIn(SECRET,str(caught.exception))


if __name__=='__main__': unittest.main()
