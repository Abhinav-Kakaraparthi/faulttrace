"""Independent expected outcomes; no real clocks, providers, or existing runs."""
from contextlib import contextmanager
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
import uuid

from fastapi.testclient import TestClient

from faulttrace.workflow.api import create_app
from faulttrace.workflow.journey import ACTION
from faulttrace.workflow.planner_contract import build_context, planner_payload, validate_action_plan
from faulttrace.workflow.recovery_policy import verify
from faulttrace.workflow.storage import Store


class JourneyTests(unittest.TestCase):
    @contextmanager
    def client(self, outcome='effective'):
        with tempfile.TemporaryDirectory() as root:
            self.root = Path(root)
            self.data = self.root / 'data'
            self.ledger = self.root / 'ledger.json'
            def forbidden(*args):
                raise AssertionError('provider_call_forbidden')
            self.app = create_app(self.data, self.ledger, send=forbidden, enabled=False,
                                  simulation_clock=lambda: 1800000000, simulation_outcome=outcome)
            with TestClient(self.app) as client:
                self.assertEqual(self.post(client, '/start', {}).status_code, 200)
                yield client

    def state(self, client):
        return client.get('/api/state').json()

    def post(self, client, path, body, key=None):
        return client.post('/api/simulation' + path, json=body,
            headers={'X-FaultTrace-Local': '1', 'Idempotency-Key': key or str(uuid.uuid4())})

    def mutate(self, client, path, **fields):
        return self.post(client, path, {'revision': self.state(client)['incident']['revision'], **fields})

    def observe(self, client, asset='F-17', status='readable', reading=180):
        return self.mutate(client, '/observe', asset_id=asset, status=status, reading=reading)

    def evidence(self, client):
        self.assertEqual(self.observe(client).status_code, 200)
        self.assertEqual(self.observe(client, 'V-08', 'intermediate', None).status_code, 200)

    def approve(self, client):
        response = self.mutate(client, '/approve', action_id=ACTION, decision='approve')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['approval_id']

    def execute(self, client):
        approval = self.approve(client)
        response = self.mutate(client, '/execute', approval_id=approval)
        self.assertEqual(response.status_code, 200, response.text)

    def test_complete_two_view_journey_duplicates_and_restart_persistence(self):
        with self.client() as client:
            self.assertFalse(self.state(client)['journey']['assessment']['eligible'])
            self.evidence(client)
            state = self.state(client)
            assessment = state['journey']['assessment']
            self.assertTrue(assessment['eligible'])
            self.assertEqual(len(assessment['evidence_refs']), 3)
            self.assertIn('deterministic', assessment['source'])
            self.assertEqual(len(assessment['alternatives']), 3)
            revision = state['incident']['revision']
            request_key = str(uuid.uuid4())
            body = {'revision': revision, 'action_id': ACTION, 'decision': 'approve'}
            first = self.post(client, '/approve', body, request_key)
            self.assertEqual(first.json(), self.post(client, '/approve', body, request_key).json())
            self.assertEqual(first.json(), self.post(client, '/approve', body).json())
            approval = first.json()['approval_id']
            body = {'revision': revision, 'approval_id': approval}
            execution_key = str(uuid.uuid4())
            self.assertEqual(self.post(client, '/execute', body, execution_key).status_code, 200)
            self.assertEqual(self.post(client, '/execute', body, execution_key).status_code, 200)
            journey = self.state(client)['journey']
            self.assertEqual(journey['maintenance_status'], 'simulated_replacement_completed')
            self.assertEqual(journey['recovery']['status'], 'observing')
            for index in range(5):
                self.assertEqual(self.mutate(client, '/advance').status_code, 200)
                self.assertEqual(self.state(client)['journey']['recovery']['status'], 'verified' if index == 4 else 'observing')
            state = self.state(client)
            operator = TestClient(self.app)
            self.assertEqual(operator.get('/api/state').json(), state)
            self.assertEqual(state['journey']['recovery']['window_seconds'], 40)
            times = [datetime.fromisoformat(s['timestamp']).timestamp() for s in state['journey']['samples']]
            self.assertEqual([b-a for a,b in zip(times,times[1:])], [10]*5)
            self.assertFalse(self.ledger.exists())
            self.assertEqual(len(state['planning']), 0)
            with Store(self.data).connection() as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM sim_approvals').fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind='simulated_filter_replacement_completed'").fetchone()[0], 1)

    def test_persistence_no_reset_or_replayed_execution(self):
        with tempfile.TemporaryDirectory() as root:
            data, ledger = Path(root)/'data', Path(root)/'ledger.json'
            def forbidden(*args):
                raise AssertionError('provider_call_forbidden')
            app = create_app(data, ledger, send=forbidden, enabled=False, simulation_clock=lambda: 1800000000)
            with TestClient(app) as client:
                self.post(client, '/start', {})
                self.evidence(client)
                self.execute(client)
                self.mutate(client, '/advance')
                before = self.state(client)
            restarted = create_app(data, ledger, send=forbidden, enabled=False, simulation_clock=lambda: 9999999999)
            with TestClient(restarted) as client:
                self.assertEqual(self.state(client), before)
                self.assertEqual(self.state(client), before)  # Polling cannot sample or repeat a correction.
                for _ in range(4):
                    self.mutate(client, '/advance')
                self.assertEqual(self.state(client)['journey']['recovery']['status'], 'verified')
            self.assertFalse(ledger.exists())

    def test_all_required_evidence_failures_block_approval(self):
        cases = [('F-17','unreadable',None), ('F-17','cannot-access',None),
                 ('F-17','wrong-equipment',None), ('F-17','readable',50),
                 ('V-08','closed',None), ('V-08','open',None),
                 ('V-08','cannot determine',None), ('V-08','cannot-access',None)]
        for asset, status, reading in cases:
            with self.subTest(status=status, asset=asset), self.client() as client:
                self.observe(client, asset, status, reading)
                if asset == 'F-17':
                    self.observe(client, 'V-08', 'intermediate', None)
                else:
                    self.observe(client)
                self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').json()['error'], 'correction_evidence_blocked')
                self.assertIsNone(self.state(client)['journey']['approval_id'])
        with self.client() as client:
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').status_code, 409)
            self.evidence(client)
            self.observe(client, reading=190)
            self.assertIn('pressure_reports_conflict', self.state(client)['journey']['assessment']['blockers'])
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').status_code, 409)

    def test_stale_reports_stale_approval_decline_and_idempotency_conflict(self):
        with self.client() as client:
            self.evidence(client)
            approval = self.approve(client)
            old_revision = self.state(client)['incident']['revision']
            self.mutate(client, '/advance')
            self.assertEqual(self.post(client, '/execute', {'revision': old_revision, 'approval_id': approval}).json()['error'], 'stale_context')
            self.assertEqual(self.mutate(client, '/execute', approval_id=approval).json()['error'], 'stale_or_missing_approval')
            approval = self.approve(client)
            self.mutate(client, '/approve', action_id=ACTION, decision='decline')
            self.assertEqual(self.mutate(client, '/execute', approval_id=approval).status_code, 409)
            replacement_approval = self.approve(client)
            self.assertNotEqual(replacement_approval, approval)
            for _ in range(12):
                self.mutate(client, '/advance')
            self.assertIn('F-17_stale', self.state(client)['journey']['assessment']['blockers'])
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').status_code, 409)
        with self.client() as client:
            key = str(uuid.uuid4())
            body = {'revision': 1, 'asset_id': 'F-17', 'status': 'readable', 'reading': 180}
            self.assertEqual(self.post(client, '/observe', body, key).status_code, 200)
            self.assertEqual(self.post(client, '/observe', dict(body, reading=181), key).json()['error'], 'idempotency_conflict')
            for value in (True, '180', -1, 1001, None):
                self.assertEqual(self.observe(client, reading=value).status_code, 400)

    def test_ineffective_correction_and_late_relapse_do_not_claim_recovery(self):
        for outcome in ('ineffective', 'relapse'):
            with self.subTest(outcome=outcome), self.client(outcome) as client:
                self.evidence(client)
                self.execute(client)
                for _ in range(5):
                    self.mutate(client, '/advance')
                self.assertEqual(self.state(client)['journey']['recovery']['status'], 'failed' if outcome == 'ineffective' else 'verified')
                self.mutate(client, '/advance')
                self.assertEqual(self.state(client)['journey']['recovery']['status'], 'failed')
                self.assertEqual(self.state(client)['journey']['maintenance_status'], 'simulated_replacement_completed')

    def test_private_truth_absent_from_state_and_actual_planner_payload(self):
        with self.client('relapse') as client:
            self.evidence(client)
            with Store(self.data).connection() as db:
                context = build_context(db)
            serialized = json.dumps({'public': self.state(client), 'payload': planner_payload(context)})
            for hidden in ('private_outcome', 'relapse', 'corrected_tick', 'answer_key', 'hidden_fault'):
                self.assertNotIn(hidden, serialized)
            self.assertEqual(len(context['observations']), 2)
            self.assertEqual(context['telemetry']['return_flow']['value'], 85)
            ref = context['telemetry']['evidence_ref']
            self.assertTrue(ref.startswith('sample-'))
            self.assertNotIn('telemetry-001', json.dumps(planner_payload(context)))
            wire = {'action_id': 'ESCALATE_HUMAN_INVESTIGATION', 'context_revision': context['context_revision'],
                    'evidence_refs': [ref], 'explanation_code': 'human_review'}
            envelope = {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(wire)}}]}
            self.assertEqual(validate_action_plan(envelope, context)['kind'], 'ESCALATE')

    def test_legacy_incident_cannot_be_repurposed(self):
        with tempfile.TemporaryDirectory() as root:
            with TestClient(create_app(Path(root)/'data', Path(root)/'usage', enabled=False)) as client:
                headers = {'X-FaultTrace-Local': '1', 'Idempotency-Key': str(uuid.uuid4())}
                client.post('/api/incidents', json={}, headers=headers)
                before = client.get('/api/state').json()
                self.assertEqual(self.post(client, '/start', {}).json()['error'], 'simulation_requires_fresh_run')
                self.assertEqual(client.get('/api/state').json(), before)

    def test_independent_verifier_freshness_gaps_alarm_and_window(self):
        samples = [dict(id=str(i), tick=i, flow=120, pressure=32, valve=72, alarm=None) for i in range(6)]
        self.assertEqual(verify(samples, 0, 5)['status'], 'verified')
        self.assertEqual(verify(samples, None, 5)['status'], 'not_started')
        self.assertEqual(verify(samples[:5], 0, 4)['status'], 'observing')
        self.assertEqual(verify(samples, 0, 18)['status'], 'failed')
        self.assertEqual(verify(samples[:3]+samples[4:], 0, 5)['status'], 'failed')
        samples[-1]['alarm'] = 'active'
        self.assertEqual(verify(samples, 0, 5)['status'], 'failed')


    def test_active_task_conflicts_and_approval_tied_to_evidence(self):
        with self.client() as client:
            self.evidence(client)
            with Store(self.data).connection(write=True) as db:
                incident = db.execute('SELECT id FROM incidents').fetchone()[0]
                db.execute("INSERT INTO tasks(id,incident_id,revision,status,created_at) VALUES(?,?,1,'awaiting','offline-test')",
                           (str(uuid.uuid4()), incident))
            self.assertIn('active_observation_or_planning', self.state(client)['journey']['assessment']['blockers'])
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').json()['error'], 'active_task_conflict')
        with self.client() as client:
            self.evidence(client)
            approval = self.approve(client)
            self.observe(client, status='cannot-access', reading=None)
            self.assertEqual(self.mutate(client, '/execute', approval_id=approval).status_code, 409)
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').status_code, 409)
            self.assertEqual(self.state(client)['journey']['maintenance_status'], 'not_completed')

    def test_rejected_shapes_provenance_and_stale_telemetry(self):
        with self.client() as client:
            self.evidence(client)
            self.assertEqual(self.mutate(client, '/approve', action_id='MOVE_VALVE', decision='approve').status_code, 400)
            extra = {'revision': self.state(client)['incident']['revision'], 'asset_id': 'F-17',
                     'status': 'readable', 'reading': 180, 'origin': 'image-verified'}
            self.assertEqual(self.post(client, '/observe', extra).status_code, 400)
            with Store(self.data).connection(write=True) as db:
                db.execute('UPDATE sim_runs SET tick=13')  # Controlled time without any new telemetry.
            blockers = self.state(client)['journey']['assessment']['blockers']
            self.assertIn('telemetry_missing_or_stale', blockers)
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').status_code, 409)
        with self.client() as client:
            self.evidence(client)
            with Store(self.data).connection(write=True) as db:
                db.execute("UPDATE sim_observations SET origin='unknown'")
            self.assertIn('F-17_provenance_invalid', self.state(client)['journey']['assessment']['blockers'])
            self.assertEqual(self.mutate(client, '/approve', action_id=ACTION, decision='approve').status_code, 409)
