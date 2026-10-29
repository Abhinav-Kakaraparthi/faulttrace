"""Observed LangSmith response shape; independent offline expected projections."""
from datetime import datetime, timezone
import json
import unittest
import uuid

from tools.diagnose_langsmith import api_timestamp,candidates
from tools.langsmith_trace_repair import matches,payloads
from test_langsmith_repair import receipts,WORKSPACE,LOCAL


class LangSmithProjectionTests(unittest.TestCase):
    def row(self,receipt,**changes):
        return dict(id=str(uuid.uuid4()),session_id=LOCAL,name='faulttrace.planning',
            start_time='2026-10-29T00:24:06.134321',end_time='2026-10-29T00:24:15.025321',
            extra={'metadata':{'operation':'planning','token_usage':receipt['token_usage'],'latency_ms':1000}},**changes)

    def test_observed_timezone_free_rows_are_projected_without_changing_input(self):
        source=receipts()[0];row=self.row(source);original=json.dumps(row)
        diagnostics=[]
        result=candidates([row],[source],WORKSPACE,{LOCAL:'Local'},'https://api.smith.langchain.com',diagnostics=diagnostics)
        self.assertEqual(len(result),1);self.assertEqual(diagnostics,[])
        self.assertEqual(result[0]['start_time'],'2026-10-29T00:24:06.134321+00:00')
        self.assertEqual(result[0]['timestamp_normalization'],'timezone_free_API_value_as_UTC')
        self.assertEqual(result[0]['receipt_fingerprint_matches'],[source['attempt_id']])
        self.assertEqual(result[0]['attempt_identity'],'not_proven_original_run_id_discarded')
        self.assertEqual(json.dumps(row),original)
        self.assertIn('/r/'+row['id'],result[0]['dashboard_url'])

    def test_zulu_explicit_offsets_and_timezone_free_values_have_same_instant(self):
        expected=datetime(2026,10,29,0,24,6,134321,tzinfo=timezone.utc)
        for value in ('2026-10-29T00:24:06.134321','2026-10-29T00:24:06.134321Z',
                      '2026-10-29T00:24:06.134321+00:00','2026-10-28T20:24:06.134321-04:00'):
            self.assertEqual(api_timestamp(value),expected)

    def test_invalid_timestamp_values_remain_rejected_without_echoing_content(self):
        for value in (None,True,123,'2026-10-29','PRIVATE_TIMESTAMP_SENTINEL',
                      '2026-02-30T00:24:06','2026-10-29T00:24:06+99:00'):
            with self.subTest(value_type=type(value).__name__),self.assertRaises(ValueError):api_timestamp(value)
        row=self.row(receipts()[0]);row['start_time']='PRIVATE_TIMESTAMP_SENTINEL'
        diagnostics=[]
        self.assertEqual(candidates([row],receipts(),WORKSPACE,{LOCAL:'Local'},'https://api.smith.langchain.com',diagnostics=diagnostics),[])
        self.assertEqual(diagnostics,[{'row_index':0,'diagnostic':'invalid_start_timestamp'}])
        self.assertNotIn('PRIVATE_TIMESTAMP_SENTINEL',json.dumps(diagnostics))

    def test_window_and_project_guards_remain_strict(self):
        row=self.row(receipts()[0]);diagnostics=[];row['start_time']='2026-10-29T00:30:00'
        self.assertEqual(candidates([row],receipts(),WORKSPACE,{LOCAL:'Local'},'https://api.smith.langchain.com',diagnostics=diagnostics),[])
        self.assertEqual(diagnostics[0]['diagnostic'],'outside_query_window')
        self.assertEqual(len(candidates([row],receipts(),WORKSPACE,{LOCAL:'Local'},'https://api.smith.langchain.com',window=None)),1)
        diagnostics=[];row['session_id']=str(uuid.uuid4())
        self.assertEqual(candidates([row],receipts(),WORKSPACE,{LOCAL:'Local'},'https://api.smith.langchain.com',window=None,diagnostics=diagnostics),[])
        self.assertEqual(diagnostics[0]['diagnostic'],'project_not_in_scope')

    def test_fingerprint_mismatch_is_readable_candidate_not_attempt_identity_proof(self):
        row=self.row(receipts()[0]);row['extra']['metadata']['latency_ms']=7
        result=candidates([row],receipts(),WORKSPACE,{LOCAL:'Local'},'https://api.smith.langchain.com')
        self.assertEqual(result[0]['receipt_fingerprint_matches'],[])
        self.assertTrue(result[0]['remote_readable'])

    def test_selected_readback_accepts_observed_utc_shape_but_not_shifted_values(self):
        entry=payloads(receipts(),WORKSPACE)[0];body=entry['payload']
        value=dict(body,project_id=LOCAL,metadata=body['extra']['metadata'])
        for field in ('start_time','end_time'):value[field]=value[field].removesuffix('+00:00')
        self.assertTrue(matches(value,entry,LOCAL))
        value['end_time']='2026-10-29T01:24:07'
        self.assertFalse(matches(value,entry,LOCAL))
