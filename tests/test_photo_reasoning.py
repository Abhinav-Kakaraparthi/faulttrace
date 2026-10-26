"""Support-confirmed photo-only control and numeric reasoning accounting; no network."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from faulttrace.accounting import VISION_MODEL, sanitized_receipt
from faulttrace.image_fixtures import image_payload
from faulttrace.ledger import LedgerError, load, record, summarize
from faulttrace.photo_observation import request_photo, validate_photo_observation
from faulttrace.provider import MAX_BODY, run_probe, transport
from faulttrace.workflow.analysis import request_image
from test_photo_observation import envelope, gauge


class PhotoReasoningTests(unittest.TestCase):
    def run_value(self, value):
        return run_probe('CREDENTIAL_SENTINEL', None, lambda *_: json.dumps(value).encode(),
                         model=VISION_MODEL, payload=request_photo(b'fixture-pixels', 'evidence-photo'),
                         validator=lambda e: validate_photo_observation(e, 'evidence-photo'))

    def test_exact_serialized_photo_delta_is_only_top_level_reasoning_effort(self):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = b'{}'
        with patch('faulttrace.provider.urllib.request.build_opener', return_value=opener):
            transport('CREDENTIAL_SENTINEL', request_photo(b'fixture-pixels', 'evidence-photo'))
        opener.open.assert_called_once()
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 60)
        opener.open.return_value.__enter__.return_value.read.assert_called_once_with(MAX_BODY + 1)
        request = opener.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload.pop('reasoning_effort'), 'none')
        # Frozen wire hash from the prior production builder at cedb85c; includes
        # the complete original prompt, model, PNG data URL and every other field.
        self.assertEqual(hashlib.sha256(json.dumps(payload).encode()).hexdigest(),
                         'e02b022a28caacc62b86148d6fe366ee88960ac0e12c4d915fc493fe4b72806d')
        self.assertNotIn('response_format', payload)
        self.assertEqual(payload['max_tokens'], 2048)

    def test_standalone_and_connected_fixture_contracts_are_unchanged(self):
        for fixture in ('panel-a', 'panel-b'):
            payload, _, _ = image_payload(fixture)
            self.assertNotIn('reasoning_effort', payload)
            self.assertEqual(payload['max_tokens'], 2048)
        self.assertNotIn('reasoning_effort', request_image(b'fixture-pixels', 'evidence-photo'))

    def test_numeric_reasoning_zero_and_positive_survive_without_raw_text(self):
        for count in (0, 7):
            value = envelope(gauge())
            value['usage']['completion_tokens_details'] = {'reasoning_tokens': count, 'reasoning': 'SECRET_RAW'}
            value['choices'][0]['message']['reasoning_content'] = 'SECRET_RAW CREDENTIAL_SENTINEL'
            receipt = self.run_value(value)
            self.assertEqual(receipt['validation_result'], 'passed')
            self.assertEqual(receipt['reasoning_tokens'], count)
            self.assertEqual(sanitized_receipt(receipt), receipt)
            self.assertNotIn('SECRET_RAW', json.dumps(receipt))
            self.assertNotIn('CREDENTIAL_SENTINEL', json.dumps(receipt))

    def test_absent_null_and_empty_details_remain_unknown(self):
        for details in (None, {}, {'reasoning_tokens': None}, {'accepted_prediction_tokens': 0}):
            value = envelope(gauge())
            value['usage']['completion_tokens_details'] = details
            receipt = self.run_value(value)
            self.assertIsNone(receipt['reasoning_tokens'])
            self.assertEqual(receipt['validation_result'], 'passed')
        self.assertIsNone(self.run_value(envelope(gauge()))['reasoning_tokens'])

    def test_malformed_reasoning_counts_are_unknown_and_have_fixed_diagnostics(self):
        for count in (True, False, -1, 0.0, 'CREDENTIAL_SENTINEL', [], {}):
            value = envelope(gauge())
            value['usage']['completion_tokens_details'] = {'reasoning_tokens': count}
            receipt = self.run_value(value)
            self.assertIsNone(receipt['reasoning_tokens'])
            self.assertEqual(receipt['error'], 'invalid_reasoning_usage')
            self.assertEqual(receipt['token_usage']['total_tokens'], 24)
            self.assertNotIn('CREDENTIAL_SENTINEL', json.dumps(receipt))
        value['usage']['completion_tokens_details'] = 'CREDENTIAL_SENTINEL'
        self.assertEqual(self.run_value(value)['error'], 'invalid_reasoning_usage')

    def test_numeric_count_retained_when_inconsistent_or_output_rejected(self):
        for finish, content in (('length', gauge()), ('stop', gauge(reading=True))):
            value = envelope(content)
            value['choices'][0]['finish_reason'] = finish
            value['usage']['completion_tokens_details'] = {'reasoning_tokens': 3}
            receipt = self.run_value(value)
            self.assertEqual(receipt['validation_result'], 'failed')
            self.assertEqual(receipt['reasoning_tokens'], 3)
            self.assertEqual(receipt['token_usage']['total_tokens'], 24)
            self.assertEqual(receipt['finish_reason'], finish)
        value = envelope(gauge())
        value['usage']['completion_tokens_details'] = {'reasoning_tokens': 14}
        receipt = self.run_value(value)
        self.assertEqual(receipt['reasoning_tokens'], 14)
        self.assertEqual(receipt['error'], 'inconsistent_reasoning_usage')
        self.assertEqual(sanitized_receipt(receipt), receipt)
        value['usage'].pop('completion_tokens')
        receipt = self.run_value(value)
        self.assertEqual(receipt['reasoning_tokens'], 14)
        self.assertEqual(receipt['usage_status'], 'partial')
        self.assertEqual(receipt['validation_result'], 'passed')

    def test_legacy_absence_idempotency_and_no_double_counting(self):
        value = envelope(gauge())
        old = self.run_value(value)
        del old['reasoning_tokens']
        value['usage']['completion_tokens_details'] = {'reasoning_tokens': 7}
        newer = self.run_value(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'usage.json'
            record(old, path)
            original = path.read_bytes()
            self.assertEqual(record(old, path)[0], 'duplicate')
            self.assertEqual(path.read_bytes(), original)
            record(newer, path)
            self.assertEqual(load(path), [old, newer])
            self.assertEqual(summarize(load(path))['known_tokens'],
                             {'prompt_tokens': 22, 'completion_tokens': 26, 'total_tokens': 48})
            with self.assertRaisesRegex(LedgerError, '^ledger_conflicting_duplicate$'):
                record(dict(newer, reasoning_tokens=0), path)
        for invalid in (True, -1, 1.0, 'SECRET_RAW'):
            with self.assertRaises(ValueError):
                sanitized_receipt(dict(newer, reasoning_tokens=invalid))
