"""Provider action IDs map to registered policy outcomes; fake transport only."""
from copy import deepcopy
import json
import unittest

from faulttrace.accounting import MODEL, sanitized_receipt
from faulttrace.provider import run_probe
from faulttrace.validation import ProbeError
from faulttrace.workflow.planner_contract import (
    TEMPLATES, permitted_actions, registered_actions, planner_payload, validate_action_plan,
)
from test_planning import PlanningCase

F17 = 'OBSERVE_F-17_READ_LOCAL_DP'
V08 = 'OBSERVE_V-08_OBSERVE_POSITION'
ESCALATE = 'ESCALATE_HUMAN_INVESTIGATION'


class ActionSelectionTests(unittest.TestCase):
    def test_catalog_supplies_scope_and_information_purpose_without_forcing_an_action(self):
        context = {'context_revision': 1, 'observations': [], 'task_history': [],
            'unresolved_conflicts': [], 'unavailable_assets': [], 'remaining_planning_calls': 4,
            'telemetry': {'evidence_ref': 'sample-existing'}}
        before = deepcopy(context)
        payload = planner_payload(context)
        instructions = payload['messages'][0]['content']
        catalog = json.loads(instructions.split('Permitted action catalog: ', 1)[1])
        self.assertEqual(set(catalog), {F17, V08, ESCALATE})
        self.assertEqual(catalog[F17]['observation_scope'], TEMPLATES[('F-17', 'READ_LOCAL_DP')])
        self.assertEqual(catalog[V08]['observation_scope'], TEMPLATES[('V-08', 'OBSERVE_POSITION')])
        self.assertIn('differential-pressure', catalog[F17]['purpose'])
        self.assertIn('unverified valve feedback', catalog[V08]['purpose'])
        self.assertIn('No Operator observation task', catalog[ESCALATE]['purpose'])
        self.assertIn('does not by itself prove that observation options are exhausted', instructions)
        self.assertIn('Escalation remains legitimate', instructions)
        self.assertIn('Do not assume unreported observations were performed', instructions)
        self.assertEqual(context, before)
        self.assertEqual(json.loads(payload['messages'][1]['content']), before)
        self.assertEqual(payload['max_tokens'], 2048)
        # All three independently expected policy outcomes remain valid initially.
        for action in (F17, V08, ESCALATE):
            wire = {'action_id': action, 'context_revision': 1,
                'evidence_refs': ['sample-existing'], 'explanation_code': 'human_review' if action == ESCALATE else 'evidence_gap'}
            result = validate_action_plan(self.envelope(wire), context)
            self.assertEqual((result['kind'], result['asset_id'], result['capability']), registered_actions()[action])
        for forbidden in ('expected_reading', 'private_outcome', 'corrected_tick', '180 kPa'):
            self.assertNotIn(forbidden, json.dumps(payload))

    def setUp(self):
        self.context = {'context_revision': 7, 'observations': [], 'unresolved_conflicts': []}
        self.wire = {'action_id': F17, 'context_revision': 7,
                     'evidence_refs': ['telemetry-001'], 'explanation_code': 'evidence_gap'}

    @staticmethod
    def envelope(value):
        return {'id': 'chatcmpl-abcd', 'model': MODEL,
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(value)}}],
                'usage': {'prompt_tokens': 7, 'completion_tokens': 11, 'total_tokens': 18}}

    def test_exact_action_mapping_without_mutation_or_extra_internal_fields(self):
        for action_id, expected in [(F17, ('REQUEST_OBSERVATION', 'F-17', 'READ_LOCAL_DP')),
                (V08, ('REQUEST_OBSERVATION', 'V-08', 'OBSERVE_POSITION')),
                (ESCALATE, ('ESCALATE', 'HUMAN', 'HUMAN_INVESTIGATION'))]:
            wire = dict(self.wire, action_id=action_id)
            before = deepcopy(wire)
            result = validate_action_plan(self.envelope(wire), self.context)
            self.assertEqual(result, {'kind': expected[0], 'asset_id': expected[1], 'capability': expected[2],
                'context_revision': 7, 'evidence_refs': ['telemetry-001'], 'explanation_code': 'evidence_gap'})
            self.assertEqual(wire, before)
            self.assertNotIn('action_id', result)

    def test_registry_uses_existing_observation_definitions_and_always_keeps_escalation(self):
        definitions = registered_actions()
        self.assertEqual({(v[1], v[2]) for v in definitions.values() if v[0] == 'REQUEST_OBSERVATION'}, set(TEMPLATES))
        self.assertEqual(definitions[ESCALATE], ('ESCALATE', 'HUMAN', 'HUMAN_INVESTIGATION'))
        for blocked, expected in [([], {F17, V08, ESCALATE}), (['F-17'], {V08, ESCALATE}),
                                 (['V-08'], {F17, ESCALATE}), (['F-17', 'V-08'], {ESCALATE})]:
            context = dict(self.context, unavailable_assets=blocked)
            self.assertEqual(set(permitted_actions(context)), expected)
            payload = planner_payload(context)
            schema = payload['response_format']['json_schema']['schema']
            self.assertEqual(set(schema['properties']['action_id']['enum']), expected)
            self.assertEqual(set(schema), {'type', 'properties', 'required', 'additionalProperties'})
            self.assertEqual(set(schema['required']), {'action_id', 'context_revision', 'evidence_refs', 'explanation_code'})
            self.assertEqual(len(schema['required']), 4)
            self.assertFalse(schema['additionalProperties'])
            self.assertNotIn('uniqueItems', json.dumps(schema))
            catalog = json.loads(payload['messages'][0]['content'].split('Permitted action catalog: ', 1)[1])
            self.assertEqual(set(catalog), expected)
            self.assertEqual(payload['max_tokens'], 2048)
            self.assertEqual(payload['model'], MODEL)

    def test_visible_refusal_excludes_action_even_without_summary_and_alternatives_pass(self):
        self.context['observations'] = [{'asset_id': 'F-17', 'kind': 'report', 'origin': 'human-report',
            'report': 'cannot-access', 'status': 'refused', 'evidence_ref': 'evidence-known'}]
        self.assertEqual(set(permitted_actions(self.context)), {V08, ESCALATE})
        with self.assertRaisesRegex(ProbeError, '^planner_asset_unavailable$'):
            validate_action_plan(self.envelope(self.wire), self.context)
        for action_id in (V08, ESCALATE):
            result = validate_action_plan(self.envelope(dict(self.wire, action_id=action_id,
                evidence_refs=['evidence-known'])), self.context)
            self.assertNotEqual(result['asset_id'], 'F-17')
        self.context['unavailable_assets'] = ['V-08']
        self.assertEqual(set(permitted_actions(self.context)), {ESCALATE})
        self.assertEqual(validate_action_plan(self.envelope(dict(self.wire, action_id=ESCALATE)), self.context)['kind'], 'ESCALATE')

    def test_invalid_wire_values_and_shared_policy_guards_retain_usage(self):
        cases = [({'action_id': 'SECRET_SENTINEL'}, 'planner_unknown_action'),
                 ({'action_id': 'READ_LOCAL_DP'}, 'planner_unknown_action'),
                 ({'action_id': True}, 'planner_field_type'), ({'action_id': []}, 'planner_field_type'),
                 ({'context_revision': 6}, 'planner_revision_mismatch'),
                 ({'context_revision': True}, 'planner_field_type'),
                 ({'evidence_refs': ['invented']}, 'planner_unknown_reference'),
                 ({'evidence_refs': ['telemetry-001'] * 2}, 'planner_duplicate_reference'),
                 ({'evidence_refs': []}, 'planner_reference_count'),
                 ({'evidence_refs': [1]}, 'planner_field_type'),
                 ({'explanation_code': 'SECRET_SENTINEL'}, 'planner_explanation_unsupported'),
                 ({'explanation_code': 'clarify_conflict'}, 'planner_explanation_unsupported'),
                 ({'kind': 'REQUEST_OBSERVATION'}, 'planner_field_shape'),
                 ({'asset_id': 'V-08', 'capability': 'MOVE_VALVE'}, 'planner_field_shape')]
        for change, code in cases:
            with self.subTest(code=code, fields=list(change)):
                wire = dict(self.wire, **change)
                calls = []
                def send(*args):
                    calls.append(True)
                    return json.dumps(self.envelope(wire)).encode()
                receipt = run_probe('SECRET_SENTINEL', None, send, payload=planner_payload(self.context),
                    validator=lambda envelope: validate_action_plan(envelope, self.context))
                self.assertEqual(receipt['error'], code)
                self.assertEqual(receipt['validation_result'], 'failed')
                self.assertEqual(receipt['token_usage']['total_tokens'], 18)
                self.assertEqual(len(calls), 1)
                self.assertNotIn('SECRET_SENTINEL', json.dumps(sanitized_receipt(receipt)))

    def test_missing_fields_and_legacy_six_field_provider_output_are_not_accepted(self):
        for name in self.wire:
            value = dict(self.wire)
            del value[name]
            with self.assertRaisesRegex(ProbeError, '^planner_field_shape$'):
                validate_action_plan(self.envelope(value), self.context)
        legacy = {'kind': 'REQUEST_OBSERVATION', 'asset_id': 'F-17', 'capability': 'READ_LOCAL_DP',
                  'context_revision': 7, 'evidence_refs': ['telemetry-001'], 'explanation_code': 'evidence_gap'}
        with self.assertRaisesRegex(ProbeError, '^planner_field_shape$'):
            validate_action_plan(self.envelope(legacy), self.context)


class ActionRuntimeTests(PlanningCase):
    def test_invented_action_rejected_without_task_repair_or_retry(self):
        client = self.setup_client()
        self.change = lambda value: dict(value, action_id='SECRET_SENTINEL')
        self.plan(client)
        state = self.state(client)
        self.assertIsNone(state['task'])
        attempt = state['planning'][0]
        self.assertEqual(attempt['error'], 'planner_unknown_action')
        self.assertIsNone(attempt['proposal'])
        self.assertEqual(attempt['receipt']['token_usage']['total_tokens'], 18)
        self.assertNotIn('SECRET_SENTINEL', json.dumps(state))
        self.plan(client)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.state(client)['planning_remaining'], 3)
