"""OFFLINE production documentation route; Tavily double, all model/trace sends forbidden."""
from contextlib import contextmanager,redirect_stdout
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient
from faulttrace.partners.http import PartnerError
from faulttrace.workflow.demo_app import create_demo_app
from faulttrace.workflow.demo_runtime import forbidden_transport
from faulttrace.workflow.storage import WorkflowError
from tools.sprint_inventory import Control,SafeFailure
from tools.sprint_client import Client,ORIGIN
from tools.verify_sprint_live import safe_json
from tools import verify_tavily_reference as runner

KEY='SENTINEL_TAVILY_REFERENCE_KEY_NO_DISCLOSURE'


class TavilyVerificationTests(unittest.TestCase):
    @contextmanager
    def session(self,kind='valid'):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{
                'TAVILY_API_KEY':KEY,'NEBIUS_API_KEY':'OFFLINE_NVIDIA_FORBIDDEN',
                'FAULTTRACE_ALLOW_INFERENCE':'0','FAULTTRACE_TAVILY_ENABLED':'1',
                'FAULTTRACE_LANGSMITH_TRACING':'0'},clear=True):
            root=Path(directory);control=Control(root);calls=[]
            def search(url,headers,payload,**kw):
                calls.append(payload)
                if kind=='failure':raise PartnerError('partner_http_error')
                source={'url':runner.VERIFIED_URLS[0],'title':'WIKA A-10 pressure transmitter',
                        'content':'OFFLINE DOUBLE. Reference data only. '+KEY}
                if kind=='unknown':source['url']='https://www.wika.com/other-resource'
                body={'results':[source] if kind!='empty' else []}
                if kind!='missing_usage':body['usage']={'credits':1}
                return json.dumps(body).encode()
            budget=runner.DocumentationOnlyBudget(root/'app',control)
            app=create_demo_app(root/'app',ORIGIN,local_http=True,live=True,budget=budget,
                send=forbidden_transport,key_source=lambda:None)
            with patch('faulttrace.partners.tavily.post_json',side_effect=search),\
                    patch('faulttrace.partners.tracing.post_json',side_effect=AssertionError('trace forbidden')) as trace,\
                    patch('faulttrace.provider.transport',side_effect=AssertionError('NVIDIA forbidden')) as nvidia,\
                    TestClient(app,base_url=ORIGIN) as http:
                client=Client(http,root/'app');result=runner.run_lookup(client)
                yield result,client,control,calls
                trace.assert_not_called();nvidia.assert_not_called()

    def test_production_route_payload_and_reference_only_state(self):
        with self.session() as (result,client,control,calls):
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0]['query'],'WIKA "A-10" manufacturer manual datasheet')
            self.assertEqual(calls[0]['include_domains'],['wika.com'])
            self.assertFalse(calls[0]['include_answer']);self.assertFalse(calls[0]['include_raw_content'])
            self.assertEqual(result['status'],'completed')
            self.assertEqual(result['citation_verification'],'preverified_resource_returned')
            self.assertEqual(result['trace_result'],'disabled')
            self.assertEqual(result['receipt']['usage_credits'],1)
            self.assertNotIn(KEY,safe_json(result,[KEY]))
            self.assertIn('does not identify',result['identity_scope'].lower())
            state=client.call('/api/state')
            self.assertEqual(state['evidence'],[]);self.assertIsNone(state['task'])
            self.assertEqual(state['journey']['maintenance_status'],'not_completed')
            self.assertEqual(control.snapshot()['used'],{'planning':0,'photo':0,'documentation':1})
            with self.assertRaises(WorkflowError):control.reserve('documentation',str(uuid.uuid4()))

    def test_missing_usage_stays_unknown_and_search_is_still_consumed(self):
        with self.session('missing_usage') as (result,client,control,calls):
            self.assertIsNone(result['receipt']['usage_credits'])
            self.assertEqual(len(calls),1);self.assertEqual(control.snapshot()['used']['documentation'],1)

    def test_provider_failure_retains_sanitized_receipt_without_retry(self):
        with self.session('failure') as (result,client,control,calls):
            self.assertEqual(result['status'],'failed');self.assertEqual(len(calls),1)
            self.assertEqual(result['receipt']['error'],'partner_http_error')
            self.assertTrue(result['receipt']['transport_invoked'])
            self.assertIsNone(result['receipt']['usage_credits']);self.assertEqual(result['sources'],[])
            self.assertIn('documentation',control.snapshot()['blocked'])

    def test_empty_or_unknown_citations_are_not_replaced_with_preverified_urls(self):
        for kind in ('empty','unknown'):
            with self.subTest(kind=kind),self.session(kind) as (result,client,control,calls):
                self.assertEqual(len(calls),1)
                self.assertEqual(result['citation_verification'],'not_verified_requires_review')
                if kind=='empty':self.assertEqual(result['sources'],[])
                else:self.assertEqual(result['sources'][0]['url'],'https://www.wika.com/other-resource')

    def test_budget_forbids_all_nvidia_operations_before_any_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);control=Control(root);budget=runner.DocumentationOnlyBudget(root/'app',control)
            for op in ('planning','photo','fixture'):
                with self.assertRaises(WorkflowError):budget.reserve('visitor',op,str(uuid.uuid4()))
            self.assertEqual(control.snapshot()['used'],{'planning':0,'photo':0,'documentation':0})

    def test_missing_key_fails_locally_without_disclosing_environment(self):
        with patch.dict(os.environ,{},clear=True),patch.object(runner.os,'name','posix'):
            with self.assertRaisesRegex(SafeFailure,'^missing_or_invalid_TAVILY_API_KEY_no_contact$'):
                runner.credential()

    def test_whole_cli_saves_receipt_and_citations_and_refuses_second_invocation(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'TAVILY_API_KEY':KEY},clear=True):
            root=Path(directory);(root/'.local').mkdir()
            ledger=root/'.local/nebius-usage.json';ledger.write_text('{"version":1,"receipts":[]}')
            original=ledger.read_bytes();output=StringIO()
            response={'results':[{'url':runner.VERIFIED_URLS[0],'title':'WIKA A-10','content':'OFFLINE DOUBLE'}],
                      'usage':{'credits':1}}
            with patch.object(runner,'ROOT',root),patch.object(runner,'preflight',return_value=hashlib.sha256(original).hexdigest()),\
                    patch('faulttrace.partners.tavily.post_json',return_value=json.dumps(response).encode()) as search,\
                    patch('faulttrace.partners.tracing.post_json',side_effect=AssertionError('trace forbidden')) as trace,\
                    redirect_stdout(output):
                self.assertEqual(runner.main(['--expected-head','a'*40]),0)
                self.assertEqual(runner.main(['--expected-head','a'*40]),2)
                self.assertEqual(search.call_count,1);trace.assert_not_called()
            files=list((root/'.local/tavily-verification').glob('*/result.json'))
            self.assertEqual(len(files),1)
            result=json.loads(files[0].read_text())
            self.assertEqual(result['after']['documentation'],1)
            self.assertEqual(result['source_revision'],'a'*40)
            self.assertTrue(result['real_ledger_unchanged'])
            self.assertEqual(ledger.read_bytes(),original)
            self.assertNotIn(KEY,output.getvalue())
