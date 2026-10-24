import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from faulttrace import image_probe, ledger
from faulttrace.accounting import MODEL, VISION_MODEL, new_receipt
from faulttrace.image_evidence import validate_image_evidence
from faulttrace.image_fixtures import FIXTURE_IDS, FIXTURE_ROOT, image_payload
from faulttrace.validation import ProbeError, validate_completion
from test_probe import envelope, fake

EXPECTED = json.loads((Path(__file__).parent / "data/image-expectations.json").read_text())


def response(value):
    return dict(envelope(json.dumps(value)), model=VISION_MODEL)


def png_pixels(path):
    """Independent decoder for these fixed RGB fixtures; validate no ancillary data."""
    data = path.read_bytes()
    pos, compressed, chunks = 8, b"", []
    while pos < len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + size]
        assert zlib.crc32(kind + body) & 0xffffffff == struct.unpack(">I", data[pos + 8 + size:pos + 12 + size])[0]
        chunks.append(kind)
        if kind == b"IHDR":
            assert struct.unpack(">IIBBBBB", body) == (480, 300, 8, 2, 0, 0, 0)
        if kind == b"IDAT":
            compressed += body
        pos += size + 12
    assert set(chunks) == {b"IHDR", b"IDAT", b"IEND"} and pos == len(data)
    raw, previous, rows = zlib.decompress(compressed), bytearray(1440), []
    assert len(raw) == 300 * 1441
    for y in range(300):
        filter_type = raw[y * 1441]
        assert filter_type in range(5)
        row = bytearray(raw[y * 1441 + 1:(y + 1) * 1441])
        for x in range(1440):
            left, above, corner = (row[x - 3] if x >= 3 else 0), previous[x], (previous[x - 3] if x >= 3 else 0)
            p = left + above - corner
            distances = (abs(p - left), abs(p - above), abs(p - corner))
            paeth = (left, above, corner)[distances.index(min(distances))]
            row[x] = (row[x] + (0, left, above, (left + above) // 2, paeth)[filter_type]) % 256
        rows.append(bytes(row))
        previous = row
    return rows


class ImageEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.ledger_path = Path(self.directory.name) / "usage.json"

    def test_readable_and_unreadable_contracts(self):
        for fixture in FIXTURE_IDS:
            expected = EXPECTED[fixture]
            self.assertEqual(validate_image_evidence(response(expected), expected["evidence_ref"]), expected)

    def test_invalid_readable_contracts(self):
        cases = []
        for field, values in {
            "readability": [None, False, 1, "clear", []],
            "reading": [None, True, "180", [], {}, -1, 1001, float("inf"), float("nan")],
            "unit": [None, "psi", 1, [], {}],
            "evidence_ref": [None, 1, [], "invented", "image-002"]}.items():
            for value in values:
                cases.append(dict(EXPECTED["panel-a"], **{field: value}))
        cases += [dict(EXPECTED["panel-a"], asset_id="F-17"), {}, [], None]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ProbeError):
                validate_image_evidence(response(value), "image-001")
        for reading in (0, 1000, 3.5):
            value = dict(EXPECTED["panel-a"], reading=reading)
            self.assertEqual(validate_image_evidence(response(value), "image-001")["reading"], reading)

    def test_unreadable_requires_both_null(self):
        for reading, unit in [(0, None), (None, "kPa"), (180, "kPa"), (False, None), (None, "")]:
            value = dict(EXPECTED["panel-b"], reading=reading, unit=unit)
            with self.subTest(reading=reading, unit=unit), self.assertRaises(ProbeError):
                validate_image_evidence(response(value), "image-002")

    def test_envelope_duplicate_refusal_and_truncation(self):
        values = [None, {}, {"choices": []}]
        duplicate = json.dumps(EXPECTED["panel-a"])[:-1] + ',"reading":180}'
        for content in ["", " ", "{", duplicate, 'NaN', '{"reading":1e999}']:
            values.append(dict(envelope(content), model=VISION_MODEL))
        for field, bad in [("role", "user"), ("refusal", "refused"),
                           ("tool_calls", [{}]), ("function_call", {})]:
            value = response(EXPECTED["panel-a"])
            value["choices"][0]["message"][field] = bad
            values.append(value)
        value = response(EXPECTED["panel-a"])
        value["choices"][0]["finish_reason"] = "length"
        values.append(value)
        for value in values:
            with self.subTest(value=value), self.assertRaises(ProbeError):
                validate_image_evidence(value, "image-001")

    def test_fixtures_have_no_metadata_or_transparency_and_full_occlusion(self):
        a, b = [png_pixels(FIXTURE_ROOT / (name + ".png")) for name in FIXTURE_IDS]
        for y in range(300):
            for x in range(480):
                clear, hidden = a[y][x * 3:x * 3 + 3], b[y][x * 3:x * 3 + 3]
                if 65 <= x <= 415 and 105 <= y <= 230:
                    self.assertEqual(hidden, bytes((87, 91, 96)))
                else:
                    self.assertEqual(clear, hidden)
        self.assertNotEqual(a, b)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow needed only to regenerate fixtures")
    def test_reproducible_fixture_generation(self):
        from tools.generate_image_fixtures import generate
        destination = Path(self.directory.name)
        generate(destination)
        for name in ("panel-a.png", "panel-b.png", "manifest.json"):
            self.assertEqual((destination / name).read_bytes(), (FIXTURE_ROOT / name).read_bytes())

    def test_payload_uses_one_image_no_answer_description(self):
        for fixture in FIXTURE_IDS:
            payload, ref, digest = image_payload(fixture)
            self.assertEqual(payload["model"], VISION_MODEL)
            self.assertEqual(payload["max_tokens"], 2048)
            self.assertEqual(len(payload["messages"]), 1)
            content = payload["messages"][0]["content"]
            self.assertEqual([part["type"] for part in content], ["text", "image_url"])
            self.assertNotIn("180", content[0]["text"])
            self.assertNotIn(fixture, content[0]["text"])
            self.assertIn(ref, content[0]["text"])
            encoded = content[1]["image_url"]["url"].removeprefix("data:image/png;base64,")
            self.assertEqual(base64.b64decode(encoded), (FIXTURE_ROOT / (fixture + ".png")).read_bytes())
            self.assertEqual(len(digest), 64)

    def test_usage_preserved_on_evidence_rejection_and_transport_failure(self):
        value = response(dict(EXPECTED["panel-a"], evidence_ref="invented"))
        receipt = image_probe.run_image_probe("fake_key", "a" * 40, "panel-a", fake(value))
        self.assertEqual(receipt["error"], "invalid_image_evidence")
        self.assertEqual(receipt["token_usage"]["total_tokens"], 267)
        self.assertEqual(receipt["returned_model"], VISION_MODEL)
        self.assertNotIn("image_evidence", receipt)
        def failure(*args):
            raise ProbeError("provider_network_error")
        receipt = image_probe.run_image_probe("fake_key", None, "panel-a", failure)
        self.assertEqual(receipt["error"], "provider_network_error")
        self.assertTrue(receipt["transport_invoked"])
        self.assertIsNone(receipt["token_usage"])
        self.assertEqual(receipt["usage_status"], "missing")

    def test_image_cli_accounting_failure_is_not_validation_success(self):
        value = response(EXPECTED["panel-a"])
        value["usage"]["completion_tokens"] = True
        receipt = image_probe.run_image_probe("fake_key", None, "panel-a", fake(value))
        self.assertEqual(receipt["error"], "invalid_usage")
        self.assertEqual(receipt["token_usage"]["prompt_tokens"], 155)
        self.assertIsNone(receipt["token_usage"]["completion_tokens"])
        self.assertNotIn("image_evidence", receipt)
        output = io.StringIO()
        with patch.dict(os.environ, {"NEBIUS_API_KEY": "fake_key"}), contextlib.redirect_stdout(output):
            with patch("faulttrace.ledger.os.replace", side_effect=OSError("private storage details")):
                code = image_probe.main(["--live", "--fixture", "panel-a", "--ledger", str(self.ledger_path)],
                                        fake(response(EXPECTED["panel-a"])))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["validation_result"], "passed")
        self.assertEqual(json.loads(output.getvalue())["ledger_error"], "ledger_write_failed")
        self.assertNotIn("private storage details", output.getvalue())
        wrong_model = dict(response(EXPECTED["panel-a"]), model=MODEL)
        receipt = image_probe.run_image_probe("fake_key", None, "panel-a", fake(wrong_model))
        self.assertEqual(receipt["error"], "invalid_metadata_model")
        self.assertIsNone(receipt["returned_model"])
        self.assertEqual(receipt["token_usage"]["total_tokens"], 267)

    def test_missing_key_bad_fixture_and_opt_in_do_not_send(self):
        def forbidden(*args):
            self.fail("transport called")
        missing = image_probe.run_image_probe(None, None, "panel-a", forbidden)
        self.assertEqual(missing["error"], "missing_credentials")
        self.assertFalse(missing["transport_invoked"])
        invalid = image_probe.run_image_probe("fake_key", None, "../private", forbidden)
        self.assertEqual(invalid["error"], "invalid_fixture")
        self.assertFalse(invalid["transport_invoked"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(image_probe.main(["--fixture", "panel-a"], send=forbidden), 2)
        with patch("faulttrace.image_fixtures.hashlib.sha256") as checksum:
            checksum.return_value.hexdigest.return_value = "bad_hash"
            invalid = image_probe.run_image_probe("fake_key", None, "panel-a", forbidden)
        self.assertEqual(invalid["error"], "invalid_fixture")

    def test_cli_one_call_sanitized_evidence_and_shared_ledger(self):
        for fixture in FIXTURE_IDS:
            calls = []
            def send(key, payload):
                calls.append(payload)
                return json.dumps(response(EXPECTED[fixture])).encode()
            output = io.StringIO()
            with patch.dict(os.environ, {"NEBIUS_API_KEY": "SENTINEL_PRIVATE_KEY"}), contextlib.redirect_stdout(output):
                code = image_probe.main(["--live", "--fixture", fixture, "--ledger", str(self.ledger_path)], send)
            self.assertEqual(code, 0)
            self.assertEqual(len(calls), 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result["image_evidence"], EXPECTED[fixture])
            self.assertEqual(result["ledger_result"], "recorded")
            self.assertNotIn("SENTINEL_PRIVATE_KEY", output.getvalue())
        text_failure = new_receipt("a" * 40)
        text_failure["error"] = "missing_credentials"
        ledger.record(text_failure, self.ledger_path)
        receipts = ledger.load(self.ledger_path)
        self.assertEqual([r["requested_model"] for r in receipts], [VISION_MODEL, VISION_MODEL, MODEL])
        self.assertEqual(ledger.summarize(receipts)["known_tokens"]["total_tokens"], 534)

    def test_secret_failure_never_persisted_or_printed(self):
        secret = "abcdef1234567890abcdef1234567890"
        bad = response(dict(EXPECTED["panel-a"], evidence_ref=secret))
        bad["id"] = "chatcmpl-" + secret
        def failed(*args):
            raise RuntimeError(secret)
        for send in (fake(bad), failed, lambda *args: secret.encode()):
            output = io.StringIO()
            with patch.dict(os.environ, {"NEBIUS_API_KEY": secret}), contextlib.redirect_stdout(output):
                code = image_probe.main(["--live", "--fixture", "panel-a", "--ledger", str(self.ledger_path)], send)
            self.assertEqual(code, 1)
            self.assertNotIn(secret, output.getvalue())
            self.assertNotIn(secret, self.ledger_path.read_text())

    def test_text_validator_cannot_accept_image_observation(self):
        with self.assertRaisesRegex(ProbeError, "invalid_proposal"):
            validate_completion(response(EXPECTED["panel-a"]))


if __name__ == "__main__":
    unittest.main()
