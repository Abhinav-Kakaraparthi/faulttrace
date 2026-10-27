"""OFFLINE TEST OUTPUT: scripted provider doubles, not live reasoning/vision evidence."""
import json
import re
import time

from fastapi.testclient import TestClient
from faulttrace.accounting import MODEL, VISION_MODEL
from faulttrace.http_diagnostics import ProviderHTTPError
from faulttrace.ledger import load
from faulttrace.workflow.journey import ACTION
from faulttrace.workflow.planner_contract import build_context
from faulttrace.workflow.storage import Store
from test_photo_collection import jpeg
from test_photo_observation import gauge, envelope
from test_workflow_api import WorkflowCase, key, LOCAL


class UnifiedInvestigationTests(WorkflowCase):
    def setUp(self):
        super().setUp()
        self.wall = time.time() + 10
        self.choice = 'OBSERVE_F-17_READ_LOCAL_DP'
        self.photo_result = gauge(reading=180, visible_unit='kPa', measurement_type='differential_pressure', label_text=None)
        self.invented = False
        self.failed = False
        self.during_send = lambda: None
        self.contexts = []
        self.human_only = False

    def send(self, secret, payload):
        self.calls.append(payload)
        with Store(self.data).connection(write=True):
            pass
        if payload['model'] == VISION_MODEL:
            ref = re.search(r'"evidence_ref":"([^"]+)"', payload['messages'][0]['content'])[1]
            return json.dumps(envelope(dict(self.photo_result, evidence_ref=ref))).encode()
        self.assertEqual(payload['model'], MODEL)
        self.assertEqual(payload['max_tokens'], 2048)
        ctx = json.loads(payload['messages'][1]['content'])
        self.contexts.append(ctx)
        self.during_send()
        if self.failed:
            raise ProviderHTTPError(429)
        refs = [o['evidence_ref'] for o in ctx['observations']][-2:] or [ctx['telemetry']['evidence_ref']]
        if self.human_only:
            refs = refs[-1:]
        value = {'action_id': self.choice, 'context_revision': ctx['context_revision'],
                 'evidence_refs': ['invented-reference'] if self.invented else refs,
                 'explanation_code': 'human_review' if self.choice.startswith('ESCALATE') else
                    'clarify_conflict' if ctx['unresolved_conflicts'] else 'evidence_gap'}
        response = envelope(value)
        response['model'] = MODEL
        response['id'] = 'chatcmpl-acde-0001'
        return json.dumps(response).encode()

    def client(self, outcome='effective'):
        self.app = self.application(simulation_clock=lambda: self.wall, simulation_outcome=outcome)
        client = self.enterContext(TestClient(self.app))
        self.assertEqual(self.post(client, '/api/investigations', {}).status_code, 200)
        return client

    def state(self, client):
        return client.get('/api/state').json()

    def plan(self, client):
        response = self.post(client, '/api/planning', {'revision': self.state(client)['incident']['revision']})
        self.assertEqual(response.status_code, 202, response.text)
        self.app.state.engine.wait()
        return self.state(client)

    def photograph(self, client):
        task = self.state(client)['task']
        response = client.post(f"/api/tasks/{task['id']}/images", content=jpeg(), headers={**LOCAL,
            'Idempotency-Key': key(), 'X-Task-Revision': str(task['revision']),
            'X-Evidence-Purpose': 'reference-photo', 'Content-Type': 'image/jpeg'})
        self.assertEqual(response.status_code, 200)
        eid = response.json()['evidence_id']
        task = self.state(client)['task']
        self.assertEqual(self.post(client, f'/api/evidence/{eid}/analyze-photo', {'revision': task['revision']}).status_code, 202)
        self.app.state.engine.wait()
        return eid

    def human_body(self, client, photo=None, **changes):
        state = self.state(client)
        valve = state['task']['asset_id'] == 'V-08'
        return dict({'revision': state['incident']['revision'], 'task_revision': state['task']['revision'],
            'photo_id': photo, 'decision': 'confirm' if photo else 'independent',
            'observed_asset_id': state['task']['asset_id'], 'measurement_type': 'position' if valve else 'differential_pressure',
            'reading': None if valve else 180, 'unit': None if valve else 'kPa',
            'position': 'intermediate' if valve else None, 'independent': True}, **changes)

    def human(self, client, photo=None, **changes):
        task = self.state(client)['task']
        response = self.post(client, f"/api/tasks/{task['id']}/observations", self.human_body(client, photo, **changes))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['evidence_id']

    def ready(self, client, photo=True):
        self.plan(client)
        eid = self.photograph(client) if photo else None
        human = self.human(client, eid)
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'
        self.plan(client)
        valve = self.human(client)
        return eid, human, valve

    def act(self, client, operation, **body):
        return self.post(client, '/api/simulation/' + operation,
                         {'revision': self.state(client)['incident']['revision'], **body})

    def execute(self, client):
        approved = self.act(client, 'approve', action_id=ACTION, decision='approve')
        self.assertEqual(approved.status_code, 200, approved.text)
        result = self.act(client, 'execute', approval_id=approved.json()['approval_id'])
        self.assertEqual(result.status_code, 200, result.text)
        return approved.json()['approval_id']

    def test_complete_shared_journey_preserves_sources_and_independent_verification(self):
        client = self.client()
        self.human_only = True
        photo, pressure, valve = self.ready(client)
        state = self.state(client)
        self.assertEqual(state['journey']['evidence_mode'], 'task-evidence')
        self.assertTrue(state['journey']['assessment']['eligible'])
        for eid in (pressure, valve):
            self.assertIn('evidence-' + eid, state['journey']['assessment']['evidence_refs'])
        self.assertNotIn('evidence-' + photo, state['journey']['assessment']['evidence_refs'])
        human = next(e for e in state['evidence'] if e['id'] == pressure)
        self.assertEqual(human['human_observation']['photo_id'], photo)
        self.assertEqual(human['human_observation']['reading'], 180)
        self.assertEqual(state['evidence'][0]['analysis']['interpretation']['reading'], 180)
        self.assertEqual(self.contexts[1]['observations'][-1]['human_observation']['reading'], 180)
        self.assertEqual(len({o['evidence_ref'] for o in self.contexts[1]['observations']}), len(self.contexts[1]['observations']))
        self.execute(client)
        self.assertEqual(self.state(client)['journey']['recovery']['status'], 'observing')
        for i in range(5):
            self.assertEqual(self.act(client, 'advance').status_code, 200)
            self.assertEqual(self.state(client)['journey']['recovery']['status'], 'verified' if i == 4 else 'observing')
        final = self.state(client)
        self.assertEqual(TestClient(self.app).get('/api/state').json(), final)
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(len(load(self.ledger)), 3)
        self.assertEqual(len(final['tasks']), 2)
        self.assertEqual(final['planning'][-1]['proposal']['evidence_refs'], ['evidence-' + pressure])
        self.assertEqual(final['tasks'][-1]['source_photo_ids'], [photo])
        # No duplication into the legacy evidence stream.
        with Store(self.data).connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sim_observations').fetchone()[0], 0)

    def test_human_report_idempotency_stale_revision_and_approval_invalidation(self):
        client = self.client(); self.plan(client)
        task = self.state(client)['task']; body = self.human_body(client); request_key = key()
        path = f"/api/tasks/{task['id']}/observations"
        first = self.post(client, path, body, request_key)
        self.assertEqual(first.json(), self.post(client, path, body, request_key).json())
        self.assertEqual(self.post(client, path, dict(body, reading=181), request_key).json()['error'], 'idempotency_conflict')
        self.assertEqual(self.post(client, path, body).json()['error'], 'stale_context')
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'; self.plan(client); self.human(client)
        approved = self.act(client, 'approve', action_id=ACTION, decision='approve').json()['approval_id']
        self.act(client, 'advance')
        self.assertEqual(self.act(client, 'execute', approval_id=approved).json()['error'], 'stale_or_missing_approval')

    def test_dispute_and_pressure_mismatch_never_become_dp_evidence(self):
        client = self.client(); self.plan(client)
        self.photo_result = gauge(reading=43, visible_unit='psi', label_text=None)
        photo = self.photograph(client)
        eid = self.human(client, photo, decision='dispute', reading=44, unit='psi', measurement_type='pressure')
        state = self.state(client)
        human = next(e for e in state['evidence'] if e['id'] == eid)['human_observation']
        self.assertEqual(human['reading'], 44)
        self.assertEqual(state['evidence'][0]['analysis']['interpretation']['reading'], 43)
        self.assertIn('differential_pressure_required', human['flags'])
        self.assertEqual(state['evidence'][0]['photo_assessment']['status'], 'disputed')
        self.assertFalse(state['journey']['assessment']['eligible'])
        self.assertEqual(self.act(client, 'approve', action_id=ACTION, decision='approve').json()['error'], 'correction_evidence_blocked')
        self.choice = 'ESCALATE_HUMAN_INVESTIGATION'
        self.assertEqual(self.plan(client)['planning'][-1]['status'], 'escalated')
        # Isolate a dispute where every numeric/type/unit value agrees: the
        # dispute itself must block, rather than passing because bands match.
        self.data = self.data.parent / 'dispute-only'
        self.ledger = self.ledger.parent / 'dispute-only.json'
        self.choice = 'OBSERVE_F-17_READ_LOCAL_DP'
        self.photo_result = gauge(reading=180, visible_unit='kPa', measurement_type='differential_pressure', label_text=None)
        other = self.client(); self.plan(other)
        photo = self.photograph(other)
        self.human(other, photo, decision='dispute')
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'; self.plan(other); self.human(other)
        self.assertIn('human_disputes_photo', self.state(other)['journey']['assessment']['blockers'])
        self.assertEqual(self.act(other, 'approve', action_id=ACTION, decision='approve').status_code, 409)

    def test_identity_type_unit_and_numeric_disagreements_are_distinct_and_preserved(self):
        from faulttrace.workflow.investigation_evidence import review_flags
        claim = self.photo_result
        base = dict(decision='confirm', observed_asset_id='F-17', measurement_type='differential_pressure', reading=180, unit='kPa', position=None)
        for change, code in (({'observed_asset_id':'unknown'}, 'observed_identity_unresolved'),
            ({'measurement_type':'pressure'}, 'human_model_type_disagreement'),
            ({'unit':'bar'}, 'human_model_unit_disagreement'),
            ({'reading':179}, 'human_model_reading_disagreement')):
            self.assertIn(code, review_flags(dict(base, **change), 'F-17', claim))
        client = self.client(); self.plan(client)
        self.human(client, observed_asset_id='V-08')
        self.assertFalse(self.state(client)['journey']['assessment']['eligible'])

    def test_refusal_drives_available_alternative_then_escalation_without_forced_success(self):
        client = self.client(); self.plan(client)
        task = self.state(client)['task']
        self.post(client, f"/api/tasks/{task['id']}/reports", {'revision': task['revision'], 'report':'cannot-access'})
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'; self.plan(client); self.human(client)
        self.assertIn('F-17', self.contexts[1]['unavailable_assets'])
        self.assertIn('F-17_unresolved_observation', self.state(client)['journey']['assessment']['blockers'])
        self.assertFalse(self.state(client)['journey']['assessment']['eligible'])
        self.choice = 'ESCALATE_HUMAN_INVESTIGATION'
        self.assertEqual(self.plan(client)['planning'][-1]['status'], 'escalated')

    def test_existing_policy_rejects_stale_samples_and_new_wall_clock_staleness(self):
        client = self.client(); self.ready(client)
        self.wall += 121
        state = self.state(client)
        self.assertIn('human_observation_wall_clock_stale', state['journey']['assessment']['blockers'])
        self.assertIn('reviewed_photo_wall_clock_stale', state['journey']['assessment']['blockers'])
        for _ in range(13): self.act(client, 'advance')
        self.assertIn('F-17_stale', self.state(client)['journey']['assessment']['blockers'])
        self.assertEqual(self.act(client, 'approve', action_id=ACTION, decision='approve').status_code, 409)

    def test_ineffective_correction_and_relapse(self):
        for outcome in ('ineffective', 'relapse'):
            # Independent fresh database per outcome; no real-time waits.
            with self.subTest(outcome=outcome):
                original = self.data
                self.data = original.parent / outcome
                self.choice = 'OBSERVE_F-17_READ_LOCAL_DP'
                client = self.client(outcome); self.ready(client, photo=False); self.execute(client)
                for _ in range(5): self.act(client, 'advance')
                self.assertEqual(self.state(client)['journey']['recovery']['status'], 'failed' if outcome=='ineffective' else 'verified')
                self.act(client, 'advance')
                self.assertEqual(self.state(client)['journey']['recovery']['status'], 'failed')
                self.data = original

    def test_no_legacy_shortcut_invalid_body_or_invented_photo(self):
        client = self.client(); self.plan(client)
        result = self.act(client, 'observe', asset_id='F-17', status='readable', reading=180)
        self.assertEqual(result.json()['error'], 'task_observation_required')
        task = self.state(client)['task']; path = f"/api/tasks/{task['id']}/observations"
        for changes in ({'reading':True}, {'independent':False}, {'unit':'arbitrary instructions'}, {'measurement_type':'unknown'}):
            self.assertEqual(self.post(client, path, self.human_body(client, **changes)).status_code, 400)
        missing = self.post(client, path, self.human_body(client, key()))
        self.assertEqual(missing.json()['error'], 'evidence_not_found')

    def test_hidden_truth_excluded_stale_planner_and_failure_accounting(self):
        client = self.client()
        self.during_send = lambda: self.app.state.journey.advance(self.state(client)['incident']['revision'], key())
        state = self.plan(client)
        self.assertEqual(state['planning'][-1]['error'], 'stale_context')
        self.assertIsNone(state['task'])
        self.assertEqual(state['planning'][-1]['receipt']['usage_status'], 'valid')
        self.during_send = lambda: None; self.failed = True
        self.act(client, 'advance')
        state = self.plan(client)
        self.assertEqual(state['planning'][-1]['receipt']['http_status'], 429)
        self.assertEqual(state['planning'][-1]['receipt']['usage_status'], 'missing')
        with Store(self.data).connection() as db: context = build_context(db)
        for secret in ('private_outcome','corrected_tick','effective','ineffective','relapse','panel-a','MAXIMATOR'):
            self.assertNotIn(secret, json.dumps(context))

    def test_restart_retains_canonical_sources_approval_and_recovery(self):
        client = self.client(); self.ready(client); self.execute(client)
        for _ in range(5): self.act(client, 'advance')
        before = self.state(client)
        client.__exit__(None, None, None)
        with TestClient(self.application(enabled=False, simulation_clock=lambda:self.wall)) as restarted:
            after = self.state(restarted)
            for field in ('evidence','tasks','planning','journey'):
                self.assertEqual(after[field], before[field])
        self.assertEqual(len(self.calls), 3)

    def test_unreviewed_photo_cannot_be_silently_bypassed_by_an_unlinked_report(self):
        client = self.client(); self.plan(client)
        self.photograph(client); self.human(client)
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'; self.plan(client); self.human(client)
        self.assertIn('photographic_claim_requires_independent_review', self.state(client)['journey']['assessment']['blockers'])
        self.assertEqual(self.act(client, 'approve', action_id=ACTION, decision='approve').status_code, 409)

    def test_offline_harness_never_reads_real_photos_and_labels_all_test_output(self):
        from tools.offline_investigation_demo import fake_transport
        from faulttrace.workflow.api import create_app
        from faulttrace.photo_observation import request_photo, validate_photo_observation
        from faulttrace.workflow.uploads import validate_upload
        with self.assertRaisesRegex(ValueError, '^test_output_requires_provider_double$'):
            create_app(self.data, self.ledger, test_output=True)
        from pathlib import Path
        panel = Path(__file__).resolve().parents[1] / 'fixtures/image-evidence/panel-a.png'
        normalized = validate_upload(panel.read_bytes(), 'image/png', None)
        fixture_only = validate_photo_observation(json.loads(fake_transport('OFFLINE_TEST_DOUBLE',
            request_photo(normalized['bytes'], 'evidence-test'))), 'evidence-test')
        self.assertEqual((fixture_only['reading'], fixture_only['visible_unit']), (180, 'kPa'))
        self.app = self.application(send=fake_transport, simulation_clock=lambda:self.wall, test_output=True)
        client = self.enterContext(TestClient(self.app))
        self.assertEqual(self.post(client, '/api/investigations', {}).status_code, 200)
        self.plan(client)
        eid = self.photograph(client)  # Generated blank JPEG, not the known synthetic panel.
        state = self.state(client)
        self.assertTrue(state['test_output'])
        self.assertTrue(state['journey']['test_output'])
        self.assertTrue(state['evidence'][0]['test_output'])
        self.assertTrue(state['task']['creation_source'].startswith('TEST-CREATED'))
        result = state['evidence'][0]['analysis']['interpretation']
        self.assertEqual(result['category'], 'cannot-determine')
        self.assertIsNone(result['reading'])
        self.assertEqual(state['evidence'][0]['analysis']['receipt']['usage_status'], 'missing')
        self.human(client, eid, decision='dispute', measurement_type='unknown', reading=None, unit=None)
        state = self.plan(client)
        self.assertEqual(state['planning'][-1]['status'], 'escalated')

    def test_planner_interruption_consumes_turn_and_restart_does_not_replay(self):
        client = self.client()
        planner = self.app.state.engine.planner
        revision = self.state(client)['incident']['revision']
        attempt, created = planner.reserve(revision, key())
        self.assertTrue(created)
        self.assertEqual(planner.reserve(revision, key()), (attempt, False))
        client.__exit__(None, None, None)
        with TestClient(self.application(enabled=False, simulation_clock=lambda:self.wall)) as restarted:
            state = self.state(restarted)
            self.assertEqual(state['planning'][0]['status'], 'uncertain')
            self.assertEqual(state['planning_remaining'], 3)
            self.assertIsNone(state['task'])
        self.assertFalse(self.calls)
