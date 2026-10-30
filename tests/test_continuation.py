"""Offline continuation tests. Scripted planner/vision doubles, no provider sockets."""
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from faulttrace.workflow.continuation import Continuation
from test_unified_investigation import UnifiedInvestigationTests
from test_workflow_api import key
from test_auth_release import ReleaseCase


class ContinuationTests(UnifiedInvestigationTests):
    def client(self, outcome='effective'):
        client = super().client(outcome)
        # Unit tests drive ticks deterministically. The browser test exercises
        # the real background scheduler with Commander closed.
        self.app.state.continuation.step = lambda: None
        return client

    def consent(self, client, enabled=True):
        return self.post(client, '/api/continuation', {
            'revision': self.state(client)['incident']['revision'], 'enabled': enabled})

    def tick(self):
        runner = self.app.state.continuation
        runner.step = lambda: None
        Continuation.step(runner)
        self.app.state.engine.wait()

    def test_without_consent_no_automatic_requests(self):
        client = self.client()
        for _ in range(3): self.tick()
        self.assertEqual(self.calls, [])
        self.assertFalse(self.state(client)['continuation']['enabled'])

    def test_field_response_resumes_planning_and_complete_evidence_stops_for_approval(self):
        client = self.client()
        self.assertEqual(self.consent(client).status_code, 200)
        self.tick()
        self.assertEqual(self.state(client)['task']['asset_id'], 'F-17')
        self.assertEqual(len(self.calls), 1)
        self.tick()
        self.assertEqual(len(self.calls), 1)
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'
        eid = self.human(client)
        self.tick()
        state = self.state(client)
        self.assertEqual(state['task']['asset_id'], 'V-08')
        self.assertIn('evidence-' + eid, state['planning'][-1]['proposal']['evidence_refs'])
        self.human(client)
        self.tick()
        self.assertEqual(self.state(client)['continuation']['phase'], 'awaiting_approval')
        self.assertEqual(len(self.calls), 2)
        for _ in range(3): self.tick()
        self.assertEqual(len(self.calls), 2)
        self.assertIsNone(self.state(client)['journey']['approval_id'])

    def test_compatible_photo_waits_for_independent_review_without_extra_planning(self):
        client = self.client()
        self.consent(client); self.tick()
        self.photograph(client); self.tick()
        self.assertEqual(self.state(client)['continuation']['phase'], 'awaiting_independent_review')
        self.assertEqual(len(self.calls), 2)
        self.assertFalse(self.state(client)['journey']['assessment']['eligible'])

    def test_incompatible_photo_is_forwarded_and_changes_next_model_context(self):
        client = self.client()
        self.consent(client); self.tick()
        self.photo_result.update(measurement_type='pressure', reading=3.7, visible_unit='bar')
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'
        photo = self.photograph(client)
        self.tick(); self.tick()
        self.assertEqual(self.state(client)['task']['asset_id'], 'V-08')
        self.assertTrue(any(o['evidence_ref'] == 'evidence-' + photo for o in self.contexts[-1]['observations']))
        self.assertEqual(len(self.calls), 3)
        self.assertFalse(self.state(client)['journey']['assessment']['eligible'])

    def test_pause_expiry_and_authorization_revocation_prevent_new_calls(self):
        client = self.client(); self.consent(client); self.consent(client, False); self.tick()
        self.assertEqual(self.calls, [])
        self.consent(client)
        runner = self.app.state.continuation
        runner.allowed = lambda: False
        self.tick()
        self.assertFalse(self.state(client)['continuation']['enabled'])
        self.assertEqual(self.calls, [])
        runner.allowed = lambda: True
        self.consent(client)
        with patch.object(runner, 'clock', return_value=time.time()+1801): self.tick()
        self.assertEqual(self.calls, [])

    def test_provider_failure_stops_without_retry_or_forced_task(self):
        client = self.client(); self.failed = True
        self.consent(client); self.tick(); self.tick()
        for _ in range(4): self.tick()
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(self.state(client)['continuation']['enabled'])
        self.assertIsNone(self.state(client)['task'])

    def test_failed_or_interrupted_photo_stops_even_on_a_clarification_task(self):
        client = self.client(); self.consent(client); self.tick(); photo = self.photograph(client)
        for task_status in ('awaiting', 'needs_evidence'):
            for status in ('failed', 'uncertain', 'stale'):
                with self.app.state.workflow.store.connection(write=True) as db:
                    db.execute('UPDATE analyses SET status=? WHERE evidence_id=?', (status, photo))
                    db.execute('UPDATE tasks SET status=?', (task_status,))
                self.consent(client); self.tick()
                current = self.state(client)['continuation']
                self.assertFalse(current['enabled'])
                self.assertEqual(current['error'], 'photo_result_requires_review')
                self.assertEqual(len(self.calls), 2)

    def test_crash_dispatch_journal_is_not_replayed(self):
        client = self.client(); self.consent(client)
        runner = self.app.state.continuation
        with runner.store.connection(write=True) as db:
            db.execute("INSERT INTO continuation_steps VALUES(?,'plan','offline','pending',NULL)", (key(),))
        restarted = Continuation(self.app)
        restarted.step()
        self.assertFalse(restarted.snapshot()['enabled'])
        self.assertEqual(self.calls, [])

    def test_waiting_investigation_resumes_after_reconstructing_runner(self):
        client = self.client(); self.consent(client); self.tick()
        self.app.state.continuation = Continuation(self.app)
        self.tick()
        self.assertEqual(len(self.calls), 1)
        self.choice = 'OBSERVE_V-08_OBSERVE_POSITION'
        self.human(client); self.tick()
        self.assertEqual(self.state(client)['task']['asset_id'], 'V-08')
        self.assertEqual(len(self.calls), 2)

    def test_exhausted_allowance_stops_before_transport(self):
        from faulttrace.workflow.storage import WorkflowError
        client = self.client(); self.consent(client)
        def reserve(*args): raise WorkflowError('spending_budget_exhausted', 429)
        self.app.state.engine.budget = SimpleNamespace(reserve=reserve)
        self.tick(); self.tick()
        self.assertEqual(self.calls, [])
        current = self.state(client)['continuation']
        self.assertFalse(current['enabled'])
        self.assertEqual(current['error'], 'spending_budget_exhausted')
        self.consent(client); self.tick()
        self.assertEqual(self.state(client)['continuation']['error'], 'continuation_dispatch_not_replayable')
        self.assertEqual(self.calls, [])

    def test_fresh_commander_grants_are_required_at_every_dispatch(self):
        client = self.client(); self.consent(client)
        runner = self.app.state.continuation
        with runner.store.connection(write=True) as db:
            db.execute("UPDATE investigation_continuation SET owner='chief'")
        incident = self.state(client)['incident']['id']
        runner.registry = SimpleNamespace(read=lambda: {'principals': {'chief': {
            'role': 'operator', 'incidents': [incident]}}})
        self.tick()
        self.assertFalse(self.state(client)['continuation']['enabled'])
        self.assertEqual(self.calls, [])

    def test_demo_continuation_ends_with_session_restart_end_and_expiry(self):
        from pathlib import Path
        from faulttrace.workflow.demo_sessions import DemoSessions
        clock = [1000.0]
        sessions = DemoSessions(Path(self.data).parent / 'sessions', clock=lambda: clock[0], ttl=60, limit=4)
        cookie, row = sessions.new()
        row = sessions.change(cookie, key(), 'start', '')
        run = row['run']
        self.assertTrue(sessions.continuation_active(row['hash'], run))
        row = sessions.change(cookie, key(), 'restart', run)
        self.assertFalse(sessions.continuation_active(row['hash'], run))
        self.assertTrue(sessions.continuation_active(row['hash'], row['run']))
        clock[0] = 1061
        self.assertFalse(sessions.continuation_active(row['hash'], row['run']))
        clock[0] = 1001
        sessions.end(row)
        self.assertFalse(sessions.continuation_active(row['hash'], row['run']))

    def test_monitor_starts_only_after_approved_operator_completion(self):
        client = self.client(); self.ready(client, photo=False)
        self.consent(client); self.tick()
        self.assertIsNone(self.app.state.monitor.snapshot())
        from faulttrace.workflow.journey import ACTION
        state = self.state(client)
        approval = self.post(client, '/api/simulation/approve', {'revision': state['incident']['revision'],
            'action_id': ACTION, 'decision': 'approve'}).json()['approval_id']
        self.tick()
        self.assertEqual(self.state(client)['continuation']['phase'], 'awaiting_operator_action')
        self.assertIsNone(self.app.state.monitor.snapshot())
        state = self.state(client)
        self.post(client, '/api/simulation/execute', {'revision': state['incident']['revision'], 'approval_id': approval})
        self.tick()
        self.assertEqual(self.app.state.monitor.snapshot()['status'], 'running')
        self.assertNotEqual(self.state(client)['journey']['recovery']['status'], 'verified')
        self.assertEqual(self.state(client)['continuation']['phase'], 'verifying_recovery')
        monitor = self.app.state.monitor
        due = time.time() + 10
        for index in range(6):
            monitor.clock = lambda i=index: due+i
            monitor.step()
            self.tick()
        final = self.state(client)
        self.assertEqual(final['journey']['recovery']['status'], 'verified')
        self.assertEqual(final['continuation']['phase'], 'complete')
        self.assertFalse(final['continuation']['enabled'])


class ContinuationAuthorizationTests(ReleaseCase):
    def test_operator_and_ungranted_commander_cannot_control_continuation(self):
        from faulttrace.workflow.auth_admin import grant
        incident = self.start()
        grant(self.registry, 'field', incident, assign=True)
        body = {'revision': self.state().json()['incident']['revision'], 'enabled': False}
        self.assertEqual(self.post('/api/continuation', body, 'field').status_code, 403)
        self.assertEqual(self.post('/api/continuation', body, 'viewer').status_code, 403)
        self.assertEqual(self.post('/api/continuation', body).status_code, 200)
        self.assertEqual(self.calls, [])


def load_tests(loader, tests, pattern):
    # Reuse API fixture helpers without rerunning the imported regression suite.
    return unittest.TestSuite(cls(name) for cls in (ContinuationTests, ContinuationAuthorizationTests)
                              for name in cls.__dict__ if name.startswith('test_'))
