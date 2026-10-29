"""OFFLINE: separate durable one-call authorization preserves the spent grant."""
from contextlib import closing,redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import uuid

from faulttrace.workflow.storage import WorkflowError
from faulttrace.partners.http import PartnerError
from tools.sprint_inventory import Control,SafeFailure
from tools import verify_tavily_diagnostic as runner

KEY='SENTINEL_SEPARATE_TAVILY_AUTHORIZATION_KEY'


class SeparateTavilyAuthorizationTests(unittest.TestCase):
    def history(self,root):
        (root/'.local').mkdir()
        (root/'.local/nebius-usage.json').write_text('{"version":1,"receipts":[]}')
        control=Control(root);aid='c4e1a86b-b23b-4073-a153-c584ada8d3e2'
        control.reserve('documentation',aid);control.complete(aid,False)
        old=root/runner.ORIGINAL;(old/'data').mkdir(parents=True)
        receipt={'attempt_id':aid,'usage_credits':1}
        (old/'result.json').write_text(json.dumps({'receipt':receipt}))
        with closing(sqlite3.connect(old/'data/workflow.sqlite3')) as db,db:
            db.execute('CREATE TABLE documentation(id TEXT,receipt TEXT)')
            db.execute('INSERT INTO documentation VALUES(?,?)',(aid,json.dumps(receipt)))

    def exercise(self,failure=False):
        with tempfile.TemporaryDirectory() as temporary,patch.dict(os.environ,{'TAVILY_API_KEY':KEY},clear=True):
            root=Path(temporary);self.history(root)
            with patch.object(runner,'ROOT',root):
                before=runner.preserved();output=StringIO()
                def fake_preflight(head):return runner.preserved()
                def send(url,headers,payload,**kwargs):
                    self.assertEqual(payload,{'query':'WIKA "A-10" manufacturer manual datasheet',
                        'topic':'general','search_depth':'basic','max_results':3,'include_domains':['wika.com'],
                        'include_domains_mode':'restrict','include_answer':False,'include_raw_content':False,
                        'include_images':False,'auto_parameters':False,'include_usage':True})
                    if failure:raise PartnerError('partner_http_error')
                    return b'{"results":[],"usage":{"credits":1}}'
                with patch.object(runner,'preflight',side_effect=fake_preflight),\
                        patch('faulttrace.partners.tavily.post_json',side_effect=send) as search,\
                        patch('faulttrace.partners.tracing.post_json',side_effect=AssertionError('trace forbidden')) as trace,\
                        patch('faulttrace.provider.transport',side_effect=AssertionError('NVIDIA forbidden')) as nvidia,\
                        redirect_stdout(output):
                    self.assertEqual(runner.main(['--expected-head','a'*40]),1)
                    self.assertEqual(runner.main(['--expected-head','a'*40]),2)
                self.assertEqual(search.call_count,1);trace.assert_not_called();nvidia.assert_not_called()
                self.assertEqual(runner.preserved(),before)
                result=json.loads((root/'.local'/runner.AUTHORIZATION/'result.json').read_text())
                self.assertTrue(result['original_preservation_unchanged'])
                self.assertEqual(result['separate_reservations'],1)
                self.assertEqual(result['authorization_id'],runner.AUTHORIZATION)
                self.assertEqual(result['sources'],[])
                self.assertNotIn(KEY,output.getvalue())
                budget=runner.OneDiagnosticBudget(root/'.local'/runner.AUTHORIZATION)
                self.assertEqual(budget.used(),1)
                with self.assertRaises(WorkflowError):budget.reserve('another','documentation',str(uuid.uuid4()))
                return result

    def test_one_empty_search_records_counts_credit_and_never_refunds(self):
        result=self.exercise()
        self.assertEqual(result['source_diagnostics']['outcome'],'provider_results_empty')
        self.assertEqual(result['source_diagnostics']['returned_count'],0)
        self.assertEqual(result['receipt']['usage_credits'],1)
        self.assertEqual(result['retrieval_outcome'],'no_retained_sources')

    def test_provider_failure_is_one_attempt_with_unknown_credit_and_no_retry(self):
        result=self.exercise(failure=True)
        self.assertIsNone(result['receipt']['usage_credits'])
        self.assertEqual(result['receipt']['error'],'partner_http_error')

    def test_pending_interruption_survives_reopen_and_consumes_the_new_grant(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);budget=runner.OneDiagnosticBudget(root)
            budget.reserve('visitor','documentation',str(uuid.uuid4()))
            reopened=runner.OneDiagnosticBudget(root);reopened.recover_pending()
            self.assertEqual(reopened.used(),1)
            with self.assertRaises(WorkflowError):reopened.reserve('visitor','documentation',str(uuid.uuid4()))

    def test_non_documentation_operations_are_forbidden_before_reservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            budget=runner.OneDiagnosticBudget(Path(temporary))
            for op in ('planning','photo','fixture'):
                with self.assertRaises(WorkflowError):budget.reserve('visitor',op,str(uuid.uuid4()))
            self.assertEqual(budget.used(),0)

    def test_unavailable_key_makes_no_calls_and_creates_no_authorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);output=StringIO()
            with patch.object(runner,'ROOT',root),patch.object(runner,'preflight',return_value={}),\
                    patch.object(runner,'credential',side_effect=SafeFailure('missing_credentials_no_contact')),redirect_stdout(output):
                self.assertEqual(runner.main(['--expected-head','a'*40]),2)
            self.assertFalse((root/'.local'/runner.AUTHORIZATION).exists())
