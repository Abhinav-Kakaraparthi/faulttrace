"""OFFLINE doubles only: wider search and durable metadata-only trace repair."""
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from tools import langsmith_trace_repair as repair
from tools.followup_langsmith import wider_search,WINDOW
from tools.diagnose_langsmith import ATTEMPTS,DiagnosticError,Reader

KEY='SENTINEL_REPAIR_KEY_NEVER_DISCLOSE'
WORKSPACE='11111111-1111-4111-8111-111111111111'
LOCAL='22222222-2222-4222-8222-222222222222'
PROJECT='33333333-3333-4333-8333-333333333333'


def receipts():
    return [{'attempt_id':aid,'timestamp':'2026-10-29T00:24:06+00:00','latency_ms':1000,
             'token_usage':{'prompt_tokens':10+i,'completion_tokens':5,'total_tokens':15+i},
             'requested_model':'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B','validation_result':'passed'}
            for i,aid in enumerate(ATTEMPTS)]


def prior():
    return {'projects':[{'endpoint':repair.ENDPOINT,'workspace_id':WORKSPACE,'project_id':p,'name':n}
                        for p,n in ((LOCAL,'Local'),(PROJECT,'faulttrace-local'))]}


class FakeReader:
    def __init__(self,rows=None):self.calls=[];self.events=[];self.rows=rows or []
    def request(self,endpoint,path,**kw):
        self.calls.append((endpoint,path,kw))
        self.events.append({'http_status':200,'diagnostic':'http_response_readable'})
        return {'runs':self.rows,'cursors':{}}


class LangSmithRepairTests(unittest.TestCase):
    def plan(self,folder):
        source=folder/'search.json';source.write_text(json.dumps({'repair_preparation_permitted':True,'remote_runs':[],'coverage_limits':[],'agent_local_project_id':PROJECT}))
        return repair.prepare(folder/'repair',receipts(),WORKSPACE,'a'*40,source,KEY,PROJECT)

    def test_wider_search_uses_start_field_and_unfiltered_recent_Local(self):
        reader=FakeReader();result=wider_search(reader,receipts(),prior())
        self.assertEqual(len(reader.calls),2)
        first=reader.calls[0][2]['body'];second=reader.calls[1][2]['body']
        self.assertIn('gt(start_time',first['filter']);self.assertIn('lt(start_time',first['filter'])
        self.assertNotIn('end_time',first)
        self.assertEqual(second,{'session':[LOCAL],'select':first['select'],'limit':100,'order':'desc'})
        self.assertNotIn('inputs',first['select']);self.assertNotIn('outputs',first['select'])
        self.assertTrue(result['repair_preparation_permitted'])

    def test_run_outside_old_window_is_found_and_prevents_repair(self):
        receipt=receipts()[0]
        row={'id':'b841fa8f-599b-401d-a481-fabbbfbb9b02','name':'faulttrace.planning','session_id':LOCAL,
             'start_time':'2026-10-29T01:30:00Z','extra':{'metadata':{'operation':'planning',
             'token_usage':receipt['token_usage'],'latency_ms':1000}}}
        result=wider_search(FakeReader([row]),receipts(),prior())
        self.assertEqual(result['receipt_fingerprints_located'],[receipt['attempt_id']])
        self.assertIn('/r/'+row['id'],result['remote_runs'][0]['dashboard_url'])
        self.assertFalse(result['repair_preparation_permitted'])

    def test_unfiltered_recent_not_clipped_by_either_time_window(self):
        row={'id':'b841fa8f-599b-401d-a481-fabbbfbb9b02','name':'faulttrace.planning','session_id':LOCAL,
             'start_time':'2026-10-25T00:00:00Z','extra':{'metadata':{}}}
        result=wider_search(FakeReader([row]),receipts(),prior())
        self.assertEqual(len(result['remote_runs']),1)
        self.assertFalse(result['repair_preparation_permitted'])

    def test_query_failure_or_pagination_never_prepares_false_absence(self):
        for value in (None,{'runs':[],'cursors':{'next':'another_page'}}):
            reader=FakeReader()
            with patch.object(reader,'request',return_value=value):
                result=wider_search(reader,receipts(),prior())
            self.assertFalse(result['repair_preparation_permitted'])
            self.assertTrue(result['coverage_limits'])

    def test_malformed_unfiltered_rows_cannot_establish_absence(self):
        for row in ('malformed',{'id':'b841fa8f-599b-401d-a481-fabbbfbb9b02'}):
            result=wider_search(FakeReader([row]),receipts(),prior())
            self.assertFalse(result['repair_preparation_permitted'])
            self.assertTrue(any('incomplete_run_rows' in c for c in result['coverage_limits']))

    def test_plan_has_persisted_stable_ids_no_raw_content_and_explicit_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);path,digest=self.plan(folder)
            value=json.loads(path.read_text())
            self.assertEqual(digest,hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(value['entries'],repair.payloads(receipts(),WORKSPACE))
            self.assertEqual(value['state'],'prepared_not_executed')
            self.assertIn('duplicated',value['duplicate_risk'])
            for entry in value['entries']:
                body=entry['payload'];self.assertEqual(body['address'],repair.ADDRESS)
                self.assertNotIn('session_name',body)
                self.assertEqual(body['inputs'],{});self.assertEqual(body['outputs'],{})
                self.assertEqual(body['trace_id'],body['id'])
                self.assertIn('reconstructed',body['extra']['metadata']['provenance'])
            self.assertNotIn(KEY,path.read_text())
            with self.assertRaises(DiagnosticError):self.plan(folder)

    def test_reservation_precedes_each_post_and_readback_verifies_all_three(self):
        with tempfile.TemporaryDirectory() as temporary:
            path,digest=self.plan(Path(temporary));reader=FakeReader();posted=[]
            def post(key,workspace,body):
                saved=json.loads(path.read_text())
                self.assertEqual(saved['entries'][len(posted)]['state'],'reserved_uncertain_until_read_back')
                posted.append(body)
                return {'http_status':202,'diagnostic':'http_acknowledged_not_read_back'}
            def read(endpoint,route,**kw):
                if 'resolutions' in route:return {'session_id':PROJECT}
                body=posted[-1]
                self.assertIn('/api/v2/runs/'+body['id'],route)
                self.assertIn('project_id='+PROJECT,route)
                return dict(body,project_id=PROJECT,metadata=body['extra']['metadata'])
            with patch.object(reader,'request',side_effect=read),patch.object(repair,'post_once',side_effect=post):
                result=repair.execute(path,digest,receipts(),KEY,reader,'a'*40)
                self.assertEqual(result['state'],'read_back_verified_all');self.assertEqual(len(posted),3)
                self.assertEqual([r['http_status'] for r in result['http_events']],[202]*3)
                self.assertTrue(all(e['remote_readable_and_fingerprint_verified'] for e in result['entries']))
                # Even with its NEW file hash a started/completed plan cannot export again.
                with self.assertRaises(DiagnosticError):
                    repair.execute(path,hashlib.sha256(path.read_bytes()).hexdigest(),receipts(),KEY,reader,'a'*40)
                self.assertEqual(len(posted),3)

    def test_readback_failure_stops_after_one_post_and_preserves_ack(self):
        with tempfile.TemporaryDirectory() as temporary:
            path,digest=self.plan(Path(temporary));reader=FakeReader()
            with patch.object(reader,'request',side_effect=[{'session_id':PROJECT},None]),\
                    patch.object(repair,'post_once',return_value={'http_status':202,'diagnostic':'http_acknowledged_not_read_back'}) as post:
                value=repair.execute(path,digest,receipts(),KEY,reader,'a'*40)
            self.assertEqual(post.call_count,1);self.assertEqual(value['state'],'stopped_requires_review_no_resend')
            self.assertEqual(value['entries'][0]['state'],'not_verified_stop')
            self.assertEqual(value['http_events'][0]['http_status'],202)
            self.assertEqual(value['entries'][1]['state'],'prepared')

    def test_wrong_agent_resolution_or_unreviewed_plan_never_exports(self):
        with tempfile.TemporaryDirectory() as temporary:
            path,digest=self.plan(Path(temporary));reader=FakeReader()
            with patch.object(repair,'post_once',side_effect=AssertionError('contacted')):
                with self.assertRaises(DiagnosticError):repair.execute(path,'wrong',receipts(),KEY,reader,'a'*40)
                with self.assertRaises(DiagnosticError):repair.execute(path,digest,receipts(),KEY,reader,'b'*40)
                with self.assertRaises(DiagnosticError):repair.execute(path,digest,receipts(),KEY,reader,'a'*40)

    def test_readback_different_metadata_or_end_time_is_not_success(self):
        entry=repair.payloads(receipts(),WORKSPACE)[0];body=entry['payload']
        value=dict(body,project_id=PROJECT,metadata=body['extra']['metadata'])
        self.assertTrue(repair.matches(value,entry,PROJECT))
        self.assertFalse(repair.matches(dict(value,end_time=None),entry,PROJECT))
        self.assertFalse(repair.matches(dict(value,metadata={}),entry,PROJECT))
        self.assertFalse(repair.matches(dict(value,project_id=LOCAL),entry,PROJECT))

    def test_http_status_is_recorded_without_error_body_or_key(self):
        error=urllib.error.HTTPError(repair.ENDPOINT,403,KEY,{},BytesIO(KEY.encode()))
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=error
            result=repair.post_once(KEY,WORKSPACE,{'inputs':{},'outputs':{}})
        self.assertEqual(result['http_status'],403)
        self.assertEqual(result['diagnostic'],'trace_http_error')
        self.assertNotIn(KEY,json.dumps(result))

    def test_readonly_transport_accepts_selected_readback_not_mutations(self):
        reader=Reader(KEY);entry=repair.payloads(receipts(),WORKSPACE)[0]
        with patch('urllib.request.build_opener',side_effect=RuntimeError('OFFLINE')):
            self.assertIsNone(reader.request(repair.ENDPOINT,repair.readback_path(entry,PROJECT),workspace=WORKSPACE))
        self.assertEqual(reader.events[0]['diagnostic'],'transport_failure_no_retry')
        with self.assertRaises(DiagnosticError):reader.request(repair.ENDPOINT,'/runs',body={})
