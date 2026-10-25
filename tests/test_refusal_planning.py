"""Refusal-aware policy outcomes; fake transport and temporary history only."""
import json

from faulttrace.ledger import load
from faulttrace.validation import ProbeError
from faulttrace.workflow.planner_contract import build_context, planner_payload, validate_plan
from test_planning import PlanningCase
from test_workflow_api import key


class RefusalPlanningTests(PlanningCase):

    def test_blocked_same_asset_rejected_with_usage_and_no_replacement_task(self):
        client = self.setup_client()
        self.plan(client)
        original = self.state(client)['task']
        self.assertEqual(self.report(client, 'cannot-access').status_code, 200)
        self.plan(client)  # Fake model ignores the access constraint: reject, never rewrite.
        state = self.state(client)
        self.assertEqual(len(state['tasks']), 1)
        self.assertEqual(state['task']['id'], original['id'])
        self.assertEqual(state['task']['status'], 'needs_evidence')
        attempt = state['planning'][-1]
        self.assertEqual(attempt['status'], 'rejected')
        self.assertEqual(attempt['error'], 'planner_asset_unavailable')
        self.assertIsNone(attempt['task_id'])
        self.assertIsNone(attempt['proposal'])
        self.assertEqual(attempt['receipt']['error'], 'planner_asset_unavailable')
        self.assertEqual(attempt['receipt']['token_usage']['total_tokens'], 18)
        self.assertEqual(len(load(self.ledger)), 2)
        self.assertEqual(self.contexts[-1]['unavailable_assets'], ['F-17'])
        self.assertEqual(len(self.calls), 2)
        self.plan(client)  # Same context reuses the rejected reservation, not another call.
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.state(client)['planning_remaining'], 2)

    def test_available_alternative_and_escalation_after_both_assets_inaccessible(self):
        client = self.setup_client()
        self.plan(client)
        self.report(client, 'cannot-access')
        self.choice = ('REQUEST_OBSERVATION', 'V-08', 'OBSERVE_POSITION')
        self.plan(client)
        self.assertEqual(self.state(client)['task']['asset_id'], 'V-08')
        self.report(client, 'cannot-access')
        self.choice = ('ESCALATE', 'HUMAN', 'HUMAN_INVESTIGATION')
        self.plan(client)
        state = self.state(client)
        self.assertEqual(state['planning'][-1]['status'], 'escalated')
        self.assertEqual(len(state['tasks']), 2)
        self.assertEqual(self.contexts[-1]['unavailable_assets'], ['F-17', 'V-08'])
        self.assertEqual(len(self.calls), 3)

    def test_v08_refusal_blocks_v08_but_allows_f17(self):
        client = self.setup_client()
        self.choice = ('REQUEST_OBSERVATION', 'V-08', 'OBSERVE_POSITION')
        self.plan(client)
        self.report(client, 'cannot-access')
        with self.app.state.workflow.store.connection() as db:
            context = build_context(db)
        with self.assertRaisesRegex(ProbeError, '^planner_asset_unavailable$'):
            validate_plan(self.envelope(self.proposal(context)), context)
        self.choice = ('REQUEST_OBSERVATION', 'F-17', 'READ_LOCAL_DP')
        self.plan(client)
        self.assertEqual(self.state(client)['planning'][-1]['status'], 'accepted')
        self.assertEqual(self.state(client)['task']['asset_id'], 'F-17')

    def test_block_survives_recent_context_limit_reopen_and_later_reports(self):
        client = self.setup_client()
        self.plan(client)
        self.report(client, 'cannot-access')
        original = self.state(client)['task']
        reopened = self.post(client, f'/api/tasks/{original["id"]}/reopen', {'revision': original['revision']})
        self.assertEqual(reopened.status_code, 200)
        self.report(client, 'unreadable')  # Does not authorize/establish restored access.
        with self.app.state.workflow.store.connection(write=True) as db:
            for _ in range(17):
                db.execute("INSERT INTO evidence VALUES(?,?,'report','human-report',NULL,NULL,NULL,NULL,'unreadable','offline','unreadable',1)",
                           (key(), original['id']))
            context = build_context(db)
        self.assertEqual(len(context['observations']), 16)
        self.assertTrue(all(o['report'] == 'unreadable' for o in context['observations']))
        self.assertEqual(context['unavailable_assets'], ['F-17'])
        with self.assertRaisesRegex(ProbeError, '^planner_asset_unavailable$'):
            validate_plan(self.envelope(self.proposal(context)), context)
        prompt = planner_payload(context)['messages'][0]['content']
        self.assertIn('cannot-access', prompt)
        self.assertIn('available alternative', prompt)
        self.assertIn('ESCALATE', prompt)
        self.assertEqual(json.loads(planner_payload(context)['messages'][1]['content'])['unavailable_assets'], ['F-17'])

    def test_legacy_visible_report_blocks_even_if_summary_is_absent_or_empty(self):
        client = self.setup_client()
        self.plan(client)
        self.report(client, 'cannot-access')
        with self.app.state.workflow.store.connection() as db:
            context = build_context(db)
        for summary in (None, []):
            if summary is None:
                context.pop('unavailable_assets', None)
            else:
                context['unavailable_assets'] = summary
            with self.assertRaisesRegex(ProbeError, '^planner_asset_unavailable$'):
                validate_plan(self.envelope(self.proposal(context)), context)

    def test_unreadable_report_alone_does_not_mean_asset_inaccessible(self):
        client = self.setup_client()
        self.plan(client)
        self.report(client, 'unreadable')
        self.plan(client)
        self.assertEqual(self.state(client)['planning'][-1]['status'], 'accepted')
        self.assertEqual(self.contexts[-1]['unavailable_assets'], [])

    def test_later_accepted_position_report_is_not_an_access_clearance(self):
        client = self.setup_client()
        self.choice = ('REQUEST_OBSERVATION', 'V-08', 'OBSERVE_POSITION')
        self.plan(client)
        self.report(client, 'cannot-access')
        self.assertEqual(self.report(client, 'open').status_code, 200)
        self.assertEqual(self.state(client)['evidence'][-1]['status'], 'accepted')
        with self.app.state.workflow.store.connection() as db:
            context = build_context(db)
        self.assertEqual(context['unavailable_assets'], ['V-08'])
        with self.assertRaisesRegex(ProbeError, '^planner_asset_unavailable$'):
            validate_plan(self.envelope(self.proposal(context)), context)
