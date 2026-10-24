import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from faulttrace import ledger, probe, provider
from faulttrace.accounting import COUNTS, new_receipt
from test_probe import envelope, fake


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "ledger.json"

    def run_value(self, value):
        return provider.run_probe("SENTINEL_SECRET_456", "a" * 40, fake(value))

    def test_tool_calls_compatibility(self):
        for tools in [None, []]:
            value = envelope()
            value["choices"][0]["message"]["tool_calls"] = tools
            self.assertEqual(self.run_value(value)["validation_result"], "passed")
        self.assertEqual(self.run_value(envelope())["validation_result"], "passed")
        for tools in [[{}], {}, "", False, 0, "[]"]:
            value = envelope()
            value["choices"][0]["message"]["tool_calls"] = tools
            with self.subTest(tools=tools):
                self.assertEqual(self.run_value(value)["error"], "unexpected_tool_calls")
        for function in [[], {}, "", False, 0]:
            value = envelope()
            value["choices"][0]["message"]["function_call"] = function
            self.assertEqual(self.run_value(value)["error"], "unexpected_function_call")

    def test_precise_message_diagnostics_retain_accounting(self):
        for field, bad, code in [
            ("role", "user", "invalid_message_role"),
            ("refusal", "private refusal", "message_refusal"),
            ("function_call", {}, "unexpected_function_call"),
            ("tool_calls", [{}], "unexpected_tool_calls"),
            ("content", "{}", "invalid_proposal"),
        ]:
            value = envelope()
            value["choices"][0]["message"][field] = bad
            receipt = self.run_value(value)
            with self.subTest(field=field):
                self.assertEqual(receipt["error"], code)
                self.assertEqual(receipt["response_id"], "chatcmpl-1234-abcd")
                self.assertEqual(receipt["returned_model"], provider.MODEL)
                self.assertEqual(receipt["token_usage"], {
                    "prompt_tokens": 155, "completion_tokens": 112, "total_tokens": 267})
                self.assertTrue(receipt["transport_invoked"])
        value = envelope()
        value["choices"][0]["message"] = []
        self.assertEqual(self.run_value(value)["error"], "invalid_message_shape")
        value = envelope()
        value["choices"][0]["finish_reason"] = "length"
        self.assertEqual(self.run_value(value)["token_usage"]["total_tokens"], 267)
        value["choices"] = None
        self.assertEqual(self.run_value(value)["token_usage"]["total_tokens"], 267)

    def test_metadata_independent_of_each_other_and_usage(self):
        value = envelope("{}")
        value["model"] = "private text"
        receipt = self.run_value(value)
        self.assertIsNone(receipt["returned_model"])
        self.assertEqual(receipt["response_id"], "chatcmpl-1234-abcd")
        self.assertEqual(receipt["token_usage"]["total_tokens"], 267)
        self.assertIn("invalid_metadata_model", receipt["diagnostics"])
        value = envelope()
        del value["id"]
        receipt = self.run_value(value)
        self.assertEqual(receipt["error"], "invalid_metadata_id")
        self.assertEqual(receipt["returned_model"], provider.MODEL)
        self.assertIsNone(receipt["response_id"])
        self.assertEqual(receipt["token_usage"]["total_tokens"], 267)

    def test_usage_states_and_valid_partial_preservation(self):
        cases = [
            (None, None, "missing"),
            ({}, dict.fromkeys(COUNTS), "missing"),
            ({"prompt_tokens": 0}, dict.fromkeys(COUNTS, None) | {"prompt_tokens": 0}, "partial"),
            ({"prompt_tokens": 3, "completion_tokens": True, "total_tokens": 9},
             {"prompt_tokens": 3, "completion_tokens": None, "total_tokens": 9}, "invalid"),
            ({"prompt_tokens": -1, "completion_tokens": 2.5, "total_tokens": "9"},
             dict.fromkeys(COUNTS), "invalid"),
            ([], None, "invalid"),
            ({"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 8},
             {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 8}, "inconsistent"),
            (dict.fromkeys(COUNTS, 0), dict.fromkeys(COUNTS, 0), "valid"),
        ]
        for usage, expected, status in cases:
            with self.subTest(usage=usage):
                value = envelope()
                value["usage"] = usage
                receipt = self.run_value(value)
                self.assertEqual(receipt["token_usage"], expected)
                self.assertEqual(receipt["usage_status"], status)
                if status in {"invalid", "inconsistent"}:
                    self.assertEqual(receipt["error"], "inconsistent_usage" if status == "inconsistent" else "invalid_usage")
                ledger.record(receipt, self.path)
        summary = ledger.summarize(ledger.load(self.path))
        self.assertEqual(summary["known_tokens"], {"prompt_tokens": 3, "completion_tokens": 0, "total_tokens": 9})
        self.assertEqual(summary["contributing_attempts"], {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 2})
        self.assertEqual(summary["usage_unknown_or_invalid_attempts"], 7)
        self.assertEqual(summary["usage_states"], {"missing": 2, "partial": 1, "invalid": 3, "inconsistent": 1})
        self.assertFalse(summary["all_recorded_usage_complete"])

    def test_idempotence_and_conflicting_duplicates(self):
        receipt = self.run_value(envelope())
        self.assertEqual(ledger.record(receipt, self.path)[0], "recorded")
        original = self.path.read_bytes()
        self.assertEqual(ledger.record(receipt, self.path)[0], "duplicate")
        self.assertEqual(self.path.read_bytes(), original)
        changed = copy.deepcopy(receipt)
        changed["token_usage"] = dict.fromkeys(COUNTS, 0)
        with self.assertRaisesRegex(ledger.LedgerError, "^ledger_conflicting_duplicate$"):
            ledger.record(changed, self.path)
        self.assertEqual(self.path.read_bytes(), original)
        summary = ledger.summarize(ledger.load(self.path))
        self.assertEqual(summary["attempts"], 1)
        self.assertEqual(summary["known_tokens"]["total_tokens"], 267)
        self.assertTrue(summary["all_recorded_usage_complete"])

    def test_ledger_allowlist_and_inconsistent_import_cannot_be_hidden(self):
        receipt = self.run_value(envelope())
        receipt["raw_response"] = "PRIVATE_SECRET_NOT_FOR_STORAGE"
        receipt["headers"] = {"Authorization": "PRIVATE_SECRET_NOT_FOR_STORAGE"}
        ledger.record(receipt, self.path)
        self.assertNotIn("PRIVATE_SECRET_NOT_FOR_STORAGE", self.path.read_text())
        invalid = self.run_value(envelope())
        invalid["token_usage"]["total_tokens"] = 1
        invalid["usage_status"] = "invalid"
        with self.assertRaisesRegex(ledger.LedgerError, "^ledger_invalid_receipt$"):
            ledger.record(invalid, self.path)
        self.assertEqual(len(ledger.load(self.path)), 1)

    def test_legacy_import_unknown_and_original_unchanged(self):
        old = self.run_value(envelope())
        for name in ["attempt_id", "transport_invoked", "usage_status", "diagnostics"]:
            del old[name]
        old.update(validation_result="failed", error="invalid_or_refused_message", token_usage=None)
        source = self.path.with_name("old.json")
        source.write_text(json.dumps(old), encoding="utf-8")
        before = source.read_bytes()
        first = ledger.import_receipt(source, self.path)
        second = ledger.import_receipt(source, self.path)
        self.assertEqual(first["attempt_id"], second["attempt_id"])
        self.assertEqual(second["ledger_result"], "duplicate")
        self.assertEqual(source.read_bytes(), before)
        summary = second["ledger_summary"]
        self.assertEqual(summary["known_tokens"], dict.fromkeys(COUNTS, 0))
        self.assertEqual(summary["contributing_attempts"], dict.fromkeys(COUNTS, 0))
        self.assertEqual(summary["transport_unknown_attempts"], 1)
        self.assertEqual(summary["usage_unknown_or_invalid_attempts"], 1)

    def test_missing_credentials_and_attempt_ids(self):
        def forbidden(*args):
            self.fail("transport was invoked")
        first = provider.run_probe(None, "a" * 40, forbidden)
        second = provider.run_probe(None, "a" * 40, forbidden)
        self.assertFalse(first["transport_invoked"])
        self.assertEqual(first["error"], "missing_credentials")
        self.assertNotEqual(first["attempt_id"], second["attempt_id"])
        self.assertIsNone(first["token_usage"])

    def test_ledger_failure_atomicity_and_cli_failure_reporting(self):
        receipt = self.run_value(envelope())
        ledger.record(receipt, self.path)
        before = self.path.read_bytes()
        with patch("faulttrace.ledger.os.replace", side_effect=OSError("PRIVATE_SECRET")):
            with self.assertRaisesRegex(ledger.LedgerError, "^ledger_write_failed$"):
                ledger.record(self.run_value(envelope()), self.path)
            output = io.StringIO()
            with patch.dict("os.environ", {"NEBIUS_API_KEY": "FAKE_KEY_123"}), contextlib.redirect_stdout(output):
                code = probe.main(["--live", "--ledger", str(self.path)], send=fake(envelope()))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["ledger_error"], "ledger_write_failed")
        self.assertEqual(json.loads(output.getvalue())["validation_result"], "passed")
        self.assertNotIn("PRIVATE_SECRET", output.getvalue())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.path.with_name("ledger.json.lock").exists())
        self.assertEqual(list(self.path.parent.glob(".usage-*")), [])
        with self.assertRaisesRegex(ledger.LedgerError, "^ledger_write_failed$"):
            ledger.record(receipt, "")

    def test_lock_and_corrupt_ledger_not_overwritten(self):
        lock = self.path.with_name("ledger.json.lock")
        lock.touch()
        with self.assertRaisesRegex(ledger.LedgerError, "^ledger_busy$"):
            ledger.record(new_receipt(None), self.path)
        lock.unlink()
        self.path.write_bytes(b"PRIVATE_CORRUPTED_LEDGER")
        with self.assertRaisesRegex(ledger.LedgerError, "^ledger_read_failed$"):
            ledger.record(new_receipt(None), self.path)
        self.assertEqual(self.path.read_bytes(), b"PRIVATE_CORRUPTED_LEDGER")

    def test_secret_absent_from_output_and_persistent_receipt(self):
        sentinel = "abcdef1234567890abcdef1234567890"
        value = envelope("{}")
        value["id"] = "chatcmpl-" + sentinel
        output = io.StringIO()
        with patch.dict("os.environ", {"NEBIUS_API_KEY": sentinel}), contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--live", "--ledger", str(self.path)], send=fake(value)), 1)
        self.assertNotIn(sentinel, output.getvalue())
        self.assertNotIn(sentinel, self.path.read_text())
        stored = ledger.load(self.path)[0]
        self.assertIsNone(stored["response_id"])
        self.assertEqual(stored["token_usage"]["total_tokens"], 267)

    def test_network_attempt_does_not_imply_completed_inference(self):
        def failed(*args):
            raise OSError("private transport data")
        receipt = provider.run_probe("SENTINEL_SECRET_456", None, failed)
        self.assertTrue(receipt["transport_invoked"])
        self.assertEqual(receipt["validation_result"], "failed")
        self.assertIsNone(receipt["token_usage"])
        self.assertEqual(receipt["usage_status"], "missing")
        self.assertIsNone(receipt["response_id"])

    def test_cli_missing_credentials_and_offline_modes(self):
        output = io.StringIO()
        def forbidden(*args):
            self.fail("transport was invoked")
        with patch.dict("os.environ", {}, clear=True), contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--live", "--ledger", str(self.path)], send=forbidden), 1)
        value = json.loads(output.getvalue())
        self.assertEqual(value["error"], "missing_credentials")
        self.assertFalse(value["transport_invoked"])
        self.assertEqual(len(ledger.load(self.path)), 1)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--ledger-summary", "--ledger", str(self.path)], send=forbidden), 0)
        self.assertEqual(json.loads(output.getvalue())["ledger_summary"]["attempts"], 1)
        source = self.path.with_name("invalid.json")
        source.write_bytes(b"PRIVATE_NOT_JSON")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--import-receipt", str(source), "--ledger", str(self.path)], send=forbidden), 1)
        self.assertEqual(json.loads(output.getvalue()), {"ledger_error": "ledger_import_failed"})
        self.assertEqual(len(ledger.load(self.path)), 1)


if __name__ == "__main__":
    unittest.main()
