"""Allowlisted completion metadata, captured before strict output rejection."""
import json
from pathlib import Path
import tempfile
import unittest

from faulttrace.accounting import FINISH_REASONS, VISION_MODEL, sanitized_receipt
from faulttrace.ledger import LedgerError, load, record
from faulttrace.photo_observation import request_photo, validate_photo_observation
from faulttrace.provider import run_probe
from test_probe import envelope, fake


class CompletionDiagnosticsTests(unittest.TestCase):
    def test_recognized_reasons_retained_without_accepting_non_stop_output(self):
        for reason in FINISH_REASONS:
            with self.subTest(reason=reason):
                value = envelope()
                value['choices'][0]['finish_reason'] = reason
                value['choices'][0]['message']['reasoning'] = 'SECRET_REASONING'
                receipt = run_probe('SECRET_CREDENTIAL', None, fake(value))
                self.assertEqual(receipt['finish_reason'], reason)
                self.assertEqual(receipt['token_usage']['total_tokens'], 267)
                self.assertEqual(receipt['validation_result'], 'passed' if reason == 'stop' else 'failed')
                if reason != 'stop':
                    self.assertEqual(receipt['error'], 'non_stop_completion')
                self.assertEqual(sanitized_receipt(receipt), receipt)
                for secret in ('SECRET_CREDENTIAL', 'SECRET_REASONING'):
                    self.assertNotIn(secret, json.dumps(receipt))

    def test_unknown_missing_and_malformed_reason_or_choices_stay_unknown(self):
        cases = []
        for reason in (None, 'SECRET_CREDENTIAL', '', True, 3, {}, []):
            value = envelope()
            value['choices'][0]['finish_reason'] = reason
            cases.append(value)
        value = envelope()
        del value['choices'][0]['finish_reason']
        cases.append(value)
        for choices in (None, {}, [], [None], [{}, {}]):
            value = envelope()
            value['choices'] = choices
            cases.append(value)
        for value in cases:
            receipt = run_probe('SECRET_CREDENTIAL', None, fake(value))
            self.assertIsNone(receipt['finish_reason'])
            self.assertEqual(receipt['validation_result'], 'failed')
            self.assertEqual(receipt['token_usage']['total_tokens'], 267)
            self.assertNotIn('SECRET_CREDENTIAL', json.dumps(receipt))

    def test_photo_truncation_retains_usage_without_reading_or_reasoning(self):
        value = envelope('SECRET_PARTIAL_OUTPUT')
        value['model'] = VISION_MODEL
        value['choices'][0]['finish_reason'] = 'length'
        value['choices'][0]['message']['reasoning_content'] = 'SECRET_REASONING'
        value['usage'] = {'prompt_tokens': 1675, 'completion_tokens': 2048, 'total_tokens': 3723}
        receipt = run_probe('SECRET_CREDENTIAL', None, fake(value), model=VISION_MODEL,
                            payload=request_photo(b'fake-image', 'evidence-neutral'),
                            validator=lambda e: validate_photo_observation(e, 'evidence-neutral'))
        self.assertEqual(receipt['error'], 'non_stop_completion')
        self.assertEqual(receipt['finish_reason'], 'length')
        self.assertEqual(receipt['usage_status'], 'valid')
        self.assertEqual(receipt['token_usage'], value['usage'])
        for secret in ('SECRET_PARTIAL_OUTPUT', 'SECRET_REASONING', 'SECRET_CREDENTIAL'):
            self.assertNotIn(secret, json.dumps(receipt))

    def test_ledger_legacy_duplicate_and_new_metadata_round_trip(self):
        old = run_probe('key', None, fake(envelope()))
        del old['finish_reason']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'
            original = json.dumps({'version': 1, 'receipts': [old]})
            path.write_text(original)
            self.assertEqual(load(path), [old])
            self.assertEqual(record(old, path)[0], 'duplicate')
            self.assertEqual(path.read_text(), original)
            with self.assertRaisesRegex(LedgerError, '^ledger_conflicting_duplicate$'):
                record(dict(old, finish_reason='length'), path)
            newer = run_probe('key', None, fake(envelope()))
            record(newer, path)
            self.assertEqual(load(path), [old, newer])

    def test_persisted_metadata_rejects_arbitrary_values(self):
        receipt = run_probe('key', None, fake(envelope()))
        for reason in ('SECRET_CREDENTIAL', '', True, 2, {}, []):
            with self.assertRaises(ValueError):
                sanitized_receipt(dict(receipt, finish_reason=reason))

    def test_photo_payload_limits_and_confirmed_reasoning_control(self):
        payload = request_photo(b'fake-image', 'evidence-neutral')
        self.assertEqual(set(payload), {'model', 'max_tokens', 'stream', 'messages', 'reasoning_effort'})
        self.assertEqual(payload['reasoning_effort'], 'none')
        self.assertEqual(payload['model'], VISION_MODEL)
        self.assertEqual(payload['max_tokens'], 2048)
        self.assertFalse(payload['stream'])

    def test_transport_failure_and_missing_credentials_have_unknown_finish(self):
        def failure(*args):
            raise OSError('SECRET_CREDENTIAL')
        receipt = run_probe('SECRET_CREDENTIAL', None, failure)
        self.assertIsNone(receipt['finish_reason'])
        self.assertIsNone(receipt['token_usage'])
        self.assertEqual(receipt['error'], 'probe_failed')
        def forbidden(*args):
            self.fail('transport called without credentials')
        receipt = run_probe(None, None, forbidden)
        self.assertFalse(receipt['transport_invoked'])
        self.assertIsNone(receipt['finish_reason'])
