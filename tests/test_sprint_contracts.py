"""OFFLINE integration of real authorization/routes with independent provider doubles."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient
from faulttrace.accounting import MODEL
from faulttrace.workflow.api import create_app
from faulttrace.workflow.demo_runtime import DemoRegistry
from faulttrace.workflow.spending import Spending


class SprintContractTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.calls=[]
        self.budget=Spending(self.root).for_session('opaque-test-visitor')
        self.registry=DemoRegistry(self.root/'data')
        self.app=create_app(self.root/'data',self.root/'usage.json',enabled=True,send=self.send,
            key_source=lambda:'TEST_ONLY_PROVIDER_KEY',profile='demo',demo_registry=self.registry,
            budget=self.budget,browser_origin='http://127.0.0.1',documentation_options={
                'enabled':True,'budget':self.budget,'key_source':lambda:'TEST_ONLY_REFERENCE_KEY',
                'send':lambda key,body:json.dumps({'results':[{'url':'https://www.wika.com/model-42',
                    'title':'Model 42','content':'OFFLINE TEST REFERENCE, not evidence.'}],'usage':{'credits':1}}).encode()})
        self.client=self.enterContext(TestClient(self.app))
        self.app.state.journey.start(str(uuid.uuid4()),True)

    def send(self, secret, payload):
        self.calls.append(payload)
        context=json.loads(payload['messages'][1]['content'])
        value={'action_id':'OBSERVE_F-17_READ_LOCAL_DP','context_revision':context['context_revision'],
            'evidence_refs':[context['telemetry']['evidence_ref']],'explanation_code':'evidence_gap'}
        return json.dumps({'id':'chatcmpl-'+str(uuid.uuid4()),'model':MODEL,
            'usage':{'prompt_tokens':12,'completion_tokens':8,'total_tokens':20},
            'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps(value)}}]}).encode()

    def headers(self, role='commander', key=None):
        return {'Authorization':'Bearer '+self.registry.tokens[role], 'Idempotency-Key':key or str(uuid.uuid4())}

    def state(self):
        return self.client.get('/api/state',headers=self.headers()).json()

    def test_documentation_commander_only_and_never_assessment_evidence(self):
        before=self.state()
        self.assertTrue(before['documentation']['enabled'])
        body={'manufacturer':'WIKA','model':'Model 42','domain':'wika.com','revision':before['incident']['revision']}
        self.assertEqual(self.client.get('/api/documentation',headers=self.headers('operator')).status_code,403)
        self.assertEqual(self.client.post('/api/documentation',json=body,headers=self.headers('operator')).status_code,403)
        op=str(uuid.uuid4())
        one=self.client.post('/api/documentation',json=body,headers=self.headers(key=op))
        two=self.client.post('/api/documentation',json=body,headers=self.headers(key=op))
        self.assertEqual(one.status_code,200)
        self.assertEqual(one.json()['record_id'],two.json()['record_id'])
        records=self.client.get('/api/documentation',headers=self.headers()).json()['records']
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['result']['usage_credits'],1)
        after=self.state()
        for name in ('incident','task','evidence','planning','journey'):
            self.assertEqual(before[name],after[name])
        self.assertEqual(self.budget.summary()['requests_reserved'],1)

    def test_trace_failure_cannot_retry_provider_or_fail_accepted_task(self):
        revision=self.state()['incident']['revision']
        with patch('faulttrace.partners.tracing.emit_trace',return_value='failed') as trace:
            response=self.client.post('/api/planning',json={'revision':revision},headers=self.headers())
            self.assertEqual(response.status_code,202)
            self.app.state.engine.wait()
        state=self.state()
        self.assertEqual(state['planning'][0]['status'],'accepted')
        self.assertEqual(len(self.calls),1)
        self.assertEqual(trace.call_args.args[0],'planning')
        serialized=json.dumps(trace.call_args.args[1])
        for forbidden in ('TEST_ONLY_PROVIDER_KEY','messages','image_url','reasoning_content'):
            self.assertNotIn(forbidden,serialized)
        with self.app.state.workflow.store.connection() as db:
            self.assertEqual(db.execute('SELECT status FROM trace_exports').fetchone()[0],'failed')

    def test_budget_persistence_failure_keeps_usage_and_creates_no_task(self):
        revision=self.state()['incident']['revision']
        with patch.object(self.budget,'settle',side_effect=OSError('PRIVATE_SENTINEL')):
            response=self.client.post('/api/planning',json={'revision':revision},headers=self.headers())
            self.assertEqual(response.status_code,202)
            self.app.state.engine.wait()
        state=self.state()
        self.assertIsNone(state['task'])
        attempt=state['planning'][0]
        self.assertEqual(attempt['receipt']['token_usage']['total_tokens'],20)
        self.assertEqual(attempt['error'],'accounting_persistence_failed')
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(state))
        self.assertEqual(self.budget.summary()['uncertain_or_pending'],1)
