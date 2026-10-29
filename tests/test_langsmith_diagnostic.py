"""Offline read-only discovery and exact REST agent routing; no service calls."""
from io import BytesIO, StringIO
from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import uuid

from faulttrace.partners.tracing import emit_trace
from faulttrace.partners.trace_routing import configuration
from tools.diagnose_langsmith import Reader, ATTEMPTS, DiagnosticError, candidates, discover
from tools import diagnose_langsmith as diagnostic

KEY='SENTINEL_TRACE_KEY_NEVER_DISCLOSE'
US='https://api.smith.langchain.com'
W,P,R=[str(uuid.uuid4()) for _ in range(3)]


class LangSmithDiagnosticTests(unittest.TestCase):
    def test_agent_wire_address_is_not_a_named_project(self):
        env={'LANGSMITH_API_KEY':KEY,'LANGSMITH_AGENT_ID':'faulttrace',
             'LANGSMITH_AGENT_ENVIRONMENT':'production','LANGSMITH_WORKSPACE_ID':W}
        calls=[]
        with patch.dict(os.environ,env,clear=True),patch('faulttrace.partners.tracing.post_json',
                side_effect=lambda *a,**k:calls.append((a,k))):
            self.assertEqual(emit_trace('planning',{},enabled=True),'recorded')
        args,kwargs=calls[0]
        self.assertEqual(args[0],US+'/runs')
        self.assertEqual(args[1],{'x-api-key':KEY,'x-tenant-id':W})
        self.assertEqual(args[2]['address'],'lrn:agents/faulttrace/environments/production')
        self.assertNotIn('session_name',args[2]);self.assertNotIn('session_id',args[2])
        self.assertEqual(args[2]['inputs'],{});self.assertEqual(args[2]['outputs'],{})
        self.assertNotIn(KEY,json.dumps(args[2]));self.assertEqual(kwargs,{'timeout':3,'limit':4096})

    def test_project_compatibility_and_region(self):
        with patch.dict(os.environ,{'LANGSMITH_PROJECT':'Local','LANGSMITH_ENDPOINT':'https://eu.api.smith.langchain.com'},clear=True):
            endpoint,headers,dest=configuration()
        self.assertEqual(dest,{'session_name':'Local'});self.assertEqual(headers,{})
        self.assertEqual(endpoint,'https://eu.api.smith.langchain.com')

    def test_conflicting_half_invalid_or_unsafe_destinations_never_send(self):
        for settings in ({'LANGSMITH_PROJECT':'Local','LANGSMITH_AGENT_ID':'faulttrace','LANGSMITH_AGENT_ENVIRONMENT':'production'},
                {'LANGSMITH_AGENT_ID':'faulttrace'}, {'LANGSMITH_AGENT_ENVIRONMENT':'production'},
                {'LANGSMITH_AGENT_ID':'bad/agent','LANGSMITH_AGENT_ENVIRONMENT':'production'},
                {'LANGSMITH_AGENT_ID':'faulttrace','LANGSMITH_AGENT_ENVIRONMENT':'unknown'},
                {'LANGSMITH_PROJECT':'Local','LANGSMITH_ENDPOINT':'https://untrusted.invalid'},
                {'LANGSMITH_PROJECT':'Local','LANGSMITH_WORKSPACE_ID':KEY}):
            with self.subTest(settings=tuple(settings)),patch.dict(os.environ,dict(settings,LANGSMITH_API_KEY=KEY),clear=True):
                self.assertEqual(emit_trace('planning',{},enabled=True,send=lambda *a:self.fail('sent')),'failed')

    def test_reader_cannot_create_update_export_or_redirect_credentials(self):
        reader=Reader(KEY)
        for endpoint,path,body in ((US,'/runs',{}),(US,'/runs/123',{}),(US,'/workspaces/current/secrets',None),
                                   ('https://evil.invalid','/sessions',None)):
            with self.assertRaises(DiagnosticError):
                reader.request(endpoint,path,body=body)
        self.assertEqual(reader.requests,0)

    def test_http_status_bounded_error_body_and_secret_safe_projection(self):
        for code in (400,401,403,404,422,429,500):
            for body in (b'{"code":"org_scoped_key_requires_workspace"}',b'{"detail":"'+KEY.encode()+b'"}',b'bad json',b'x'*8193):
                error=urllib.error.HTTPError(US,code,'PRIVATE_ERROR',{},BytesIO(body))
                reader=Reader(KEY)
                with patch('urllib.request.build_opener') as opener:
                    opener.return_value.open.side_effect=error
                    self.assertIsNone(reader.request(US,'/api/v1/workspaces'))
                self.assertEqual(reader.events[0]['http_status'],code)
                self.assertNotIn(KEY,json.dumps(reader.events));self.assertNotIn('PRIVATE_ERROR',json.dumps(reader.events))
                self.assertTrue(error.fp is None or error.fp.closed)

    def test_readable_http_query_is_not_a_trace_export(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):return b'{"runs":[],"cursors":{}}'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value=Response()
            r=Reader(KEY);r.request(US,'/runs/query',workspace=W,body={'select':['id']})
            req=opener.return_value.open.call_args.args[0]
            self.assertEqual(req.get_method(),'POST');self.assertTrue(req.full_url.endswith('/runs/query'))
            self.assertEqual(r.events[0]['diagnostic'],'http_response_readable')

    def test_run_discovery_has_bounded_scope_and_no_inputs_outputs(self):
        receipt={'attempt_id':next(iter(ATTEMPTS)),'token_usage':{'total_tokens':1586},'latency_ms':1100}
        row={'id':R,'name':'faulttrace.planning','session_id':P,'start_time':'2026-10-29T00:24:08Z',
             'end_time':'2026-10-29T00:24:09Z','trace_id':R,
             'extra':{'metadata':{'operation':'planning','token_usage':receipt['token_usage'],'latency_ms':1100}}}
        class FakeReader:
            events=[]
            def request(self,endpoint,path,**kw):
                if path=='/api/v1/workspaces':return [{'id':W,'display_name':'Workspace'}]
                if path.startswith('/sessions?'):return [{'id':P,'name':'Local'}]
                self_body=kw['body']
                assert 'inputs' not in self_body['select'] and 'outputs' not in self_body['select']
                assert 'ai_search' not in self_body
                return {'runs':[row],'cursors':{}}
        with patch.dict(os.environ,{},clear=True):result=discover(FakeReader(),[US],[receipt])
        self.assertEqual(len(result['remote_runs']),1)
        run=result['remote_runs'][0]
        self.assertEqual(run['receipt_fingerprint_matches'],[receipt['attempt_id']])
        self.assertEqual(run['dashboard_url'],f'https://smith.langchain.com/o/{W}/projects/p/{P}/r/{R}?poll=true')
        self.assertEqual(run['attempt_identity'],'not_proven_original_run_id_discarded')
        self.assertEqual(candidates([dict(row,name='unrelated')],[receipt],W,{P:'Local'},US),[])

    def test_unknown_http_details_remain_unknown_and_request_cap_does_not_contact(self):
        reader=Reader(KEY);reader.requests=80
        with patch('urllib.request.build_opener',side_effect=AssertionError('contacted')):
            self.assertIsNone(reader.request(US,'/sessions'))
        self.assertEqual(reader.events[-1]['diagnostic'],'diagnostic_request_cap_no_contact')

    def test_full_readonly_driver_empty_remote_results_are_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.local').mkdir()
            ledger=root/'.local/nebius-usage.json';ledger.write_bytes(b'ORIGINAL_UNMODIFIED')
            receipts=[{'attempt_id':a} for a in ATTEMPTS]
            output=StringIO()
            with patch.object(diagnostic,'ROOT',root),patch.object(diagnostic,'local_receipts',return_value=receipts),\
                    patch.object(diagnostic,'environment',return_value=(KEY,US)),\
                    patch.object(diagnostic,'discover',return_value={'remote_runs':[],'http_diagnostics':[{'http_status':403,'diagnostic':'access_denied'}]}),\
                    patch('subprocess.check_output',side_effect=['a'*40,'']),patch.dict(os.environ,{},clear=True),redirect_stdout(output):
                self.assertEqual(diagnostic.main(['--expected-head','a'*40]),1)
            self.assertEqual(ledger.read_bytes(),b'ORIGINAL_UNMODIFIED')
            report=json.loads(next((root/'.local/langsmith-diagnostics').glob('*.json')).read_text())
            self.assertEqual(report['verification_result'],'partial_or_not_found')
            self.assertEqual(report['historical_http_status'],'not retained')
            self.assertEqual(report['http_diagnostics'][0]['http_status'],403)
            self.assertNotIn(KEY,output.getvalue())

    def test_success_body_bounds_and_decoding_fail_without_retaining_content(self):
        for body,code in ((b'x'*262145,'response_too_large'),(KEY.encode(),'invalid_json_response')):
            class Response:
                status=200
                def __enter__(self):return self
                def __exit__(self,*args):pass
                def read(self,n):
                    self_size=n
                    assert self_size==262145
                    return body
            with patch('urllib.request.build_opener') as opener:
                opener.return_value.open.return_value=Response()
                reader=Reader(KEY);self.assertIsNone(reader.request(US,'/sessions'))
                self.assertEqual(reader.events[0]['diagnostic'],code)
                self.assertNotIn(KEY,json.dumps(reader.events))
