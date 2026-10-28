"""Authenticated complete simulation and stale/duplicate decisions with fake transport."""
import json

from faulttrace.accounting import MODEL
from faulttrace.workflow.auth_admin import grant
from faulttrace.workflow.journey import ACTION
from test_auth_release import ReleaseCase, key


class AuthenticatedJourneyTests(ReleaseCase):
    def setUp(self):
        super().setUp()
        self.choice = 'OBSERVE_F-17_READ_LOCAL_DP'
        self.app.state.engine.enabled = True
        self.app.state.engine.key_source = lambda: 'synthetic-key'
        self.app.state.engine.send = self.send

    def send(self, secret, payload):
        self.calls.append(payload)
        context = json.loads(payload['messages'][1]['content'])
        value = {'action_id': self.choice, 'context_revision': context['context_revision'],
                 'evidence_refs': [context['observations'][-1]['evidence_ref']] if context['observations'] else [context['telemetry']['evidence_ref']],
                 'explanation_code': 'evidence_gap'}
        return json.dumps({'id': 'chatcmpl-acde-0001', 'model': MODEL,
            'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(value)}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}).encode()

    def plan(self):
        body = {'revision': self.state().json()['incident']['revision']}
        request_key = key()
        first = self.post('/api/planning', body, request_key=request_key)
        self.assertEqual(first.status_code, 202, first.text)
        self.app.state.engine.wait()
        self.assertIsNotNone(self.state().json()['task'], self.state().text)
        self.assertEqual(self.post('/api/planning', body, request_key=request_key).json(), first.json())
        return self.state('field').json()['task']

    def observe(self, task):
        valve = task['asset_id'] == 'V-08'
        body = {'revision': self.state().json()['incident']['revision'], 'task_revision': task['revision'],
                'photo_id': None, 'decision': 'independent', 'observed_asset_id': task['asset_id'],
                'measurement_type': 'position' if valve else 'differential_pressure',
                'reading': None if valve else 180, 'unit': None if valve else 'kPa',
                'position': 'intermediate' if valve else None, 'independent': True}
        request_key, path = key(), f"/api/tasks/{task['id']}/observations"
        first = self.post(path, body, 'field', request_key)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(self.post(path, body, 'field', request_key).json(), first.json())
        self.assertEqual(self.post(path, body, 'field').json(), {'error': 'stale_context'})

    def prepare(self):
        incident = self.start()
        grant(self.registry, 'field', incident, assign=True)
        grant(self.registry, 'other', incident)
        self.observe(self.plan())
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'
        self.observe(self.plan())
        self.assertTrue(self.state().json()['journey']['assessment']['eligible'])

    def approve(self):
        revision = self.state().json()['incident']['revision']
        body = {'revision': revision, 'action_id': ACTION, 'decision': 'approve'}
        request_key = key()
        first = self.post('/api/simulation/approve', body, request_key=request_key)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(self.post('/api/simulation/approve', body, request_key=request_key).json(), first.json())
        return {'revision': revision, 'approval_id': first.json()['approval_id']}

    def test_complete_role_separated_journey_and_independent_recovery(self):
        self.prepare()
        body = self.approve()
        self.assertEqual(self.post('/api/simulation/execute', body, 'other').status_code, 403)
        request_key = key()
        first = self.post('/api/simulation/execute', body, 'field', request_key)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(self.post('/api/simulation/execute', body, 'field', request_key).json(), first.json())
        self.assertEqual(self.state('field').json()['journey']['recovery']['status'], 'observing')
        for index in range(5):
            revision = self.state().json()['incident']['revision']
            self.assertEqual(self.post('/api/simulation/advance', {'revision': revision}).status_code, 200)
            expected = 'verified' if index == 4 else 'observing'
            self.assertEqual(self.state('field').json()['journey']['recovery']['status'], expected)
        self.assertEqual(self.state('other').json()['tasks'], [])
        self.assertEqual(self.state('other').json()['evidence'], [])
        self.assertEqual(self.state('other').json()['planning'], [])
        self.assertEqual(len(self.calls), 2)
        with self.app.state.workflow.store.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM planning').fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind='simulated_filter_replacement_completed'").fetchone()[0], 1)

    def test_stale_approval_remains_rejected_after_auth_passes(self):
        self.prepare()
        body = self.approve()
        self.post('/api/simulation/advance', {'revision': body['revision']})
        self.assertEqual(self.post('/api/simulation/execute', body, 'field').json(), {'error': 'stale_context'})
        revision = self.state().json()['incident']['revision']
        body['revision'] = revision
        self.assertEqual(self.post('/api/simulation/execute', body, 'field').json(), {'error': 'stale_or_missing_approval'})
