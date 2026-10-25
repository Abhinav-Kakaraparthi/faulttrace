"""Independent planner diagnostics and request-wire expectations; no network."""
from copy import deepcopy
import json
import unittest

from faulttrace.accounting import MODEL, sanitized_receipt
from faulttrace.provider import run_probe
from faulttrace.validation import ProbeError
from faulttrace.workflow.planner_contract import planner_payload, validate_plan


class PlannerContractTests(unittest.TestCase):
    def setUp(self):
        self.context = {'context_revision': 7, 'observations': [], 'unresolved_conflicts': []}
        self.proposal = {'kind': 'REQUEST_OBSERVATION', 'asset_id': 'F-17', 'capability': 'READ_LOCAL_DP',
                         'context_revision': 7, 'evidence_refs': ['telemetry-001'], 'explanation_code': 'evidence_gap'}

    def envelope(self, value):
        return {'id': 'chatcmpl-abcd', 'model': MODEL,
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant',
                    'content': value if isinstance(value, str) else json.dumps(value)}}],
                'usage': {'prompt_tokens': 564, 'completion_tokens': 1483, 'total_tokens': 2047}}

    def test_valid_observations_and_escalation(self):
        for kind, asset, capability in [('REQUEST_OBSERVATION', 'F-17', 'READ_LOCAL_DP'),
                ('REQUEST_OBSERVATION', 'V-08', 'OBSERVE_POSITION'), ('ESCALATE', 'HUMAN', 'HUMAN_INVESTIGATION')]:
            value = dict(self.proposal, kind=kind, asset_id=asset, capability=capability)
            self.assertEqual(validate_plan(self.envelope(value), self.context), value)

    def test_precise_diagnostics_survive_receipt_sanitization_with_usage(self):
        changes = [
            ({'extra': 'SECRET_SENTINEL'}, 'planner_field_shape'),
            ({'context_revision': True}, 'planner_field_type'),
            ({'context_revision': 7.0}, 'planner_field_type'),
            ({'context_revision': '7'}, 'planner_field_type'),
            ({'asset_id': []}, 'planner_field_type'),
            ({'capability': None}, 'planner_field_type'),
            ({'kind': False}, 'planner_field_type'),
            ({'explanation_code': {}}, 'planner_field_type'),
            ({'evidence_refs': 'telemetry-001'}, 'planner_field_type'),
            ({'evidence_refs': [True]}, 'planner_field_type'),
            ({'context_revision': 6}, 'planner_revision_mismatch'),
            ({'evidence_refs': ['SECRET_SENTINEL']}, 'planner_unknown_reference'),
            ({'evidence_refs': ['telemetry-001', 'telemetry-001']}, 'planner_duplicate_reference'),
            ({'evidence_refs': []}, 'planner_reference_count'),
            ({'evidence_refs': ['telemetry-001'] * 9}, 'planner_reference_count'),
            ({'asset_id': 'V-08'}, 'planner_invalid_combination'),
            ({'capability': 'MOVE_VALVE'}, 'planner_invalid_combination'),
            ({'kind': 'ESCALATE'}, 'planner_invalid_combination'),
            ({'kind': 'RECOVERED'}, 'planner_invalid_combination'),
            ({'explanation_code': 'SECRET_SENTINEL'}, 'planner_explanation_unsupported'),
            ({'explanation_code': 'clarify_conflict'}, 'planner_explanation_unsupported'),
            ({'explanation_code': 'unreadable_evidence'}, 'planner_explanation_unsupported'),
        ]
        for change, expected in changes:
            with self.subTest(expected=expected, fields=list(change)):
                value = dict(self.proposal, **change)
                with self.assertRaises(ProbeError) as raised:
                    validate_plan(self.envelope(value), self.context)
                self.assertEqual(str(raised.exception), expected)
                receipt = run_probe('SECRET_SENTINEL', None,
                    lambda *_: json.dumps(self.envelope(value)).encode(), payload=planner_payload(self.context),
                    validator=lambda envelope: validate_plan(envelope, self.context))
                self.assertEqual(receipt['error'], expected)
                self.assertEqual(receipt['token_usage'], {'prompt_tokens': 564, 'completion_tokens': 1483, 'total_tokens': 2047})
                self.assertEqual(receipt['usage_status'], 'valid')
                self.assertEqual(receipt['validation_result'], 'failed')
                self.assertNotIn('SECRET_SENTINEL', json.dumps(sanitized_receipt(receipt)))

    def test_missing_fields_nonobjects_duplicate_keys_and_truncation(self):
        value = dict(self.proposal)
        del value['capability']
        for value in (value, [], None):
            with self.assertRaisesRegex(ProbeError, '^planner_field_shape$'):
                validate_plan(self.envelope(value), self.context)
        for value, code in [('{"kind":"SECRET_SENTINEL","kind":"other"}', 'duplicate_json_key'),
                            ('{"kind":', 'invalid_json')]:
            with self.assertRaises(ProbeError) as failure:
                validate_plan(self.envelope(value), self.context)
            self.assertEqual(str(failure.exception), code)

    def test_exact_payload_schema_and_context_specific_constraints(self):
        self.context.update(observations=[{'evidence_ref': 'evidence-known', 'status': 'unreadable'}],
                            unresolved_conflicts=['recorded_conflict'])
        captured = []
        def send(secret, payload):
            captured.append(json.loads(json.dumps(payload)))
            return json.dumps(self.envelope(self.proposal)).encode()
        receipt = run_probe('SECRET_SENTINEL', None, send, payload=planner_payload(self.context),
                            validator=lambda envelope: validate_plan(envelope, self.context))
        self.assertEqual(receipt['validation_result'], 'passed')
        self.assertEqual(len(captured), 1)
        payload = captured[0]
        self.assertEqual(set(payload), {'model', 'max_tokens', 'stream', 'messages', 'response_format'})
        self.assertEqual(payload['model'], 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B')
        self.assertEqual(payload['max_tokens'], 2048)
        self.assertIs(payload['stream'], False)
        self.assertEqual(json.loads(payload['messages'][1]['content']), self.context)
        response = payload['response_format']
        self.assertEqual(response['type'], 'json_schema')
        wrapper = response['json_schema']
        self.assertEqual(set(wrapper), {'name', 'strict', 'schema'})
        self.assertIs(wrapper['strict'], True)
        schema = wrapper['schema']
        self.assertIs(schema['additionalProperties'], False)
        self.assertEqual(set(schema['required']), {'kind', 'asset_id', 'capability', 'context_revision', 'evidence_refs', 'explanation_code'})
        self.assertEqual(set(schema['properties']), set(schema['required']))
        self.assertEqual(schema['properties']['context_revision'], {'type': 'integer', 'enum': [7]})
        self.assertEqual(schema['properties']['evidence_refs'], {'type': 'array', 'minItems': 1, 'maxItems': 8,
            'uniqueItems': True, 'items': {'type': 'string', 'enum': ['telemetry-001', 'evidence-known']}})
        combinations = {tuple(branch['properties'][key]['enum'][0] for key in ('kind', 'asset_id', 'capability'))
                        for branch in schema['anyOf']}
        self.assertEqual(combinations, {('REQUEST_OBSERVATION', 'F-17', 'READ_LOCAL_DP'),
            ('REQUEST_OBSERVATION', 'V-08', 'OBSERVE_POSITION'), ('ESCALATE', 'HUMAN', 'HUMAN_INVESTIGATION')})
        self.assertNotIn('SECRET_SENTINEL', json.dumps(payload))
        for code in ('clarify_conflict', 'unreadable_evidence'):
            value = dict(self.proposal, explanation_code=code, evidence_refs=['evidence-known'])
            self.assertEqual(validate_plan(self.envelope(value), self.context), value)

    def test_no_unsupported_explanation_suggestions_and_no_context_mutation(self):
        before = deepcopy(self.context)
        schema = planner_payload(self.context)['response_format']['json_schema']['schema']
        self.assertEqual(set(schema['properties']['explanation_code']['enum']), {'evidence_gap', 'human_review'})
        self.assertEqual(self.context, before)
