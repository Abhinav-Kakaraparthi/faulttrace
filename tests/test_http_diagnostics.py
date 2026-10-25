"""Mocked HTTP failures only. No error body or header may cross the boundary."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from fastapi.testclient import TestClient

from faulttrace import ledger, probe, provider
from faulttrace.accounting import new_receipt, sanitized_receipt
from faulttrace.workflow.api import create_app
from test_probe import envelope
from test_workflow_api import LOCAL, key

SECRET = 'SENTINEL_PRIVATE_API_KEY_987654'


class UnreadBody(io.BytesIO):
    def read(self, *args):
        raise AssertionError('error_body_must_not_be_read')


def failed_opener(status, body=b'private body'):
    stream = UnreadBody(body)
    error = HTTPError('https://invalid.example/' + SECRET, status, SECRET,
                      {'Authorization': SECRET, 'X-Private': SECRET}, stream)
    opener = Mock()
    opener.open.side_effect = error
    return opener, stream


class HTTPDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        self.ledger_path = Path(self.directory) / 'usage.json'

    def test_status_categories_survive_receipt_ledger_and_duplicate_recording(self):
        for status, category in [(400, 'http_bad_request'), (401, 'http_unauthorized'),
                (402, 'http_payment_required'), (403, 'http_forbidden'), (404, 'http_not_found'),
                (422, 'http_unprocessable_entity'), (429, 'http_rate_limited'),
                (500, 'http_server_error'), (503, 'http_server_error'), (599, 'http_server_error'),
                (302, 'http_redirect'), (418, 'http_other_error')]:
            with self.subTest(status=status):
                opener, stream = failed_opener(status, SECRET.encode())
                with patch('urllib.request.build_opener', return_value=opener):
                    receipt = provider.run_probe(SECRET, None)
                self.assertEqual(receipt['error'], 'provider_http_error')
                self.assertEqual(receipt['http_status'], status)
                self.assertEqual(receipt['http_error_category'], category)
                self.assertIsNone(receipt['token_usage'])
                self.assertEqual(receipt['usage_status'], 'missing')
                self.assertTrue(receipt['transport_invoked'])
                self.assertEqual(receipt['validation_result'], 'failed')
                self.assertTrue(stream.closed)
                self.assertEqual(opener.open.call_count, 1)
                self.assertEqual(opener.open.call_args.kwargs['timeout'], 60)
                self.assertEqual(sanitized_receipt(receipt), receipt)
                self.assertEqual(ledger.record(receipt, self.ledger_path)[0], 'recorded')
                self.assertEqual(ledger.record(receipt, self.ledger_path)[0], 'duplicate')
                self.assertEqual(ledger.load(self.ledger_path)[-1], receipt)
        self.assertNotIn(SECRET, self.ledger_path.read_text())

    def test_empty_malformed_non_json_and_oversized_bodies_are_never_read(self):
        for body in (b'', b'{', b'\xff', b'<html>private</html>',
                     SECRET.encode() * (provider.MAX_BODY // len(SECRET) + 100),
                     json.dumps({'usage': {'prompt_tokens': 999}, 'error': SECRET}).encode()):
            opener, stream = failed_opener(400, body)
            with patch('urllib.request.build_opener', return_value=opener):
                receipt = provider.run_probe(SECRET, None)
            self.assertEqual(receipt['http_status'], 400)
            self.assertEqual(receipt['http_error_category'], 'http_bad_request')
            self.assertIsNone(receipt['token_usage'])  # Never infer accounting from an error body.
            self.assertNotIn(SECRET, json.dumps(receipt))
            self.assertTrue(stream.closed)

    def test_historical_missing_fields_remain_unknown_and_duplicate_compatible(self):
        receipt = new_receipt(None)
        receipt.update(error='provider_http_error', transport_invoked=True)
        del receipt['http_status']
        del receipt['http_error_category']
        self.assertEqual(sanitized_receipt(receipt), receipt)
        original = json.dumps({'version': 1, 'receipts': [receipt]})
        self.ledger_path.write_text(original)
        self.assertEqual(ledger.load(self.ledger_path), [receipt])
        self.assertEqual(ledger.record(receipt, self.ledger_path)[0], 'duplicate')
        self.assertEqual(self.ledger_path.read_text(), original)
        # A mixed old/new ledger does not upgrade or rewrite historical receipt fields.
        newer = new_receipt(None)
        ledger.record(newer, self.ledger_path)
        self.assertEqual(ledger.load(self.ledger_path)[0], receipt)
        changed = dict(receipt, http_status=400, http_error_category='http_bad_request')
        with self.assertRaisesRegex(ledger.LedgerError, '^ledger_conflicting_duplicate$'):
            ledger.record(changed, self.ledger_path)

    def test_http_metadata_is_strict_and_cannot_carry_arbitrary_strings(self):
        receipt = dict(new_receipt(None), error='provider_http_error')
        for fields in ({'http_status': True}, {'http_status': '400'}, {'http_status': 400.0},
                       {'http_status': 999}, {'http_error_category': SECRET},
                       {'http_status': 401, 'http_error_category': 'http_bad_request'}):
            with self.assertRaises(ValueError):
                sanitized_receipt(dict(receipt, **fields))
        self.assertEqual(sanitized_receipt(dict(receipt, http_status=401))['http_status'], 401)
        with self.assertRaises(ValueError):
            sanitized_receipt(dict(new_receipt(None), http_status=401, http_error_category='http_unauthorized'))
        for status in (None, True, 'SECRET_SENTINEL', 999):
            opener, _ = failed_opener(status)
            with patch('urllib.request.build_opener', return_value=opener):
                result = provider.run_probe(SECRET, None)
            self.assertIsNone(result['http_status'])
            self.assertEqual(result['http_error_category'], 'http_unknown')

    def test_cli_never_discloses_body_headers_credential_or_exception_message(self):
        for status in (400, 401, 402, 403, 404, 422, 429, 500):
            opener, _ = failed_opener(status, SECRET.encode())
            output, errors = io.StringIO(), io.StringIO()
            with patch('urllib.request.build_opener', return_value=opener), patch.dict(os.environ, {'NEBIUS_API_KEY': SECRET}), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = probe.main(['--live', '--ledger', str(self.ledger_path)])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue())['http_status'], status)
            self.assertNotIn(SECRET, output.getvalue() + errors.getvalue() + self.ledger_path.read_text())

    def test_parsed_completion_accounting_survives_validation_failure(self):
        value = envelope('{}')
        value['usage'] = {'prompt_tokens': 7, 'completion_tokens': 11, 'total_tokens': 18}
        result = provider.run_probe(SECRET, None, lambda *_: json.dumps(value).encode())
        self.assertEqual(result['error'], 'invalid_proposal')
        self.assertEqual(result['token_usage']['total_tokens'], 18)
        self.assertIsNone(result['http_status'])
        self.assertIsNone(result['http_error_category'])

    def test_workflow_failure_creates_no_task_and_persists_http_diagnostics_once(self):
        app = create_app(Path(self.directory) / 'data', self.ledger_path, enabled=True, key_source=lambda: SECRET)
        with TestClient(app) as client:
            headers = dict(LOCAL, **{'Idempotency-Key': key()})
            self.assertEqual(client.post('/api/incidents', json={}, headers=headers).status_code, 200)
            opener, _ = failed_opener(422, SECRET.encode())
            with patch('urllib.request.build_opener', return_value=opener):
                result = client.post('/api/planning', json={'revision': 1}, headers=dict(LOCAL, **{'Idempotency-Key': key()}))
                self.assertEqual(result.status_code, 202)
                app.state.engine.wait()
                again = client.post('/api/planning', json={'revision': 1}, headers=dict(LOCAL, **{'Idempotency-Key': key()}))
                self.assertEqual(again.json(), result.json())
            state = client.get('/api/state').json()
            self.assertIsNone(state['task'])
            self.assertEqual(state['tasks'], [])
            self.assertEqual(state['planning_remaining'], 3)
            self.assertEqual(state['planning'][0]['status'], 'rejected')
            receipt = state['planning'][0]['receipt']
            self.assertEqual(receipt['http_status'], 422)
            self.assertEqual(receipt['http_error_category'], 'http_unprocessable_entity')
            self.assertEqual(ledger.load(self.ledger_path), [receipt])
            self.assertEqual(opener.open.call_count, 1)
            self.assertNotIn(SECRET, json.dumps(state) + self.ledger_path.read_text())
