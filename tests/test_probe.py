import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from faulttrace import probe, provider
from faulttrace.validation import ProbeError, validate_completion

PROPOSAL = {"kind": "REQUEST_OBSERVATION", "asset_id": "F-17",
            "capability": "READ_LOCAL_DP", "evidence_refs": ["telemetry-001"]}


def envelope(content=None):
    return {"id": "chatcmpl-1234-abcd", "model": provider.MODEL,
            "choices": [{"finish_reason": "stop", "message": {
                "role": "assistant", "content": json.dumps(PROPOSAL) if content is None else content}}],
            "usage": {"prompt_tokens": 155, "completion_tokens": 112, "total_tokens": 267}}


def fake(value):
    return lambda key, payload: json.dumps(value).encode()


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.ledger_args = ["--ledger", str(Path(self.temporary.name) / "usage.json")]

    def test_valid_and_request_bounds(self):
        calls = []
        def send(key, payload):
            calls.append(payload)
            return json.dumps(envelope()).encode()
        result = provider.run_probe("sentinel", "a" * 40, send)
        self.assertEqual(result["validation_result"], "passed")
        self.assertEqual(result["token_usage"]["total_tokens"], 267)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["max_tokens"], 2048)
        self.assertEqual(calls[0]["model"], "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")

    def test_invalid_proposals(self):
        variants = []
        for field, values in {
            "kind": ["ACTION", None, 1], "asset_id": ["F-18", [], None],
            "capability": ["WRITE_LOCAL_DP", True, {}],
            "evidence_refs": [[], ["other"], ["telemetry-001", "telemetry-001"],
                              "telemetry-001", [1], None]}.items():
            for value in values:
                proposal = dict(PROPOSAL, **{field: value})
                variants.append(json.dumps(proposal))
        variants += [json.dumps(dict(PROPOSAL, extra="bad")), "{}", "[]", "null",
                     "", "   ", "{", json.dumps(PROPOSAL)[:-1] + ',"kind":"REQUEST_OBSERVATION"}']
        for content in variants:
            with self.subTest(content=content), self.assertRaises(ProbeError):
                validate_completion(envelope(content))

    def test_bad_envelopes_refusal_and_truncation(self):
        variants = [None, [], {}, {"choices": []}, {"choices": [None]}]
        for reason in ["length", "content_filter", None, "tool_calls"]:
            value = envelope()
            value["choices"][0]["finish_reason"] = reason
            variants.append(value)
        for content in [None, [], 1]:
            value = envelope()
            value["choices"][0]["message"]["content"] = content
            variants.append(value)
        value = envelope()
        value["choices"][0]["message"]["refusal"] = "refused"
        variants.append(value)
        for field in ("tool_calls", "function_call"):
            value = envelope()
            value["choices"][0]["message"][field] = [{}]
            variants.append(value)
        for value in variants:
            with self.subTest(value=value):
                self.assertEqual(provider.run_probe("secret", "rev", fake(value))["validation_result"], "failed")

    def test_missing_credentials_never_calls_transport(self):
        def forbidden(*args):
            self.fail("transport called")
        for key in [None, "", " "]:
            self.assertEqual(provider.run_probe(key, "rev", forbidden)["error"], "missing_credentials")

    def test_unknown_usage(self):
        value = envelope()
        del value["usage"]
        self.assertIsNone(provider.run_probe("key", "rev", fake(value))["token_usage"])
        value["usage"] = {"prompt_tokens": 7}
        self.assertIsNone(provider.run_probe("key", "rev", fake(value))["token_usage"]["total_tokens"])

    def test_body_failures(self):
        for body in [b"\xff", b"{", b"x" * (provider.MAX_BODY + 1),
                     b'{"choices":[],"choices":[]}']:
            result = provider.run_probe("key", "rev", lambda *args: body)
            self.assertEqual(result["validation_result"], "failed")

    def test_cli_secret_never_emitted(self):
        sentinel = "SENTINEL_PRIVATE_API_KEY_987654"
        def failure(*args):
            raise RuntimeError(sentinel)
        values = [failure, lambda *args: sentinel.encode(),
                  fake(envelope(sentinel)), fake(dict(envelope(), id="chatcmpl-" + sentinel))]
        for send in values:
            output = io.StringIO()
            with patch.dict(os.environ, {"NEBIUS_API_KEY": sentinel}), contextlib.redirect_stdout(output):
                self.assertEqual(probe.main(["--live"] + self.ledger_args, send=send), 1)
            self.assertNotIn(sentinel, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["validation_result"], "failed")

    def test_opt_in(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(probe.main(self.ledger_args, send=lambda *args: self.fail("transport called")), 2)

    def test_real_transport_sanitized_failures_and_limits(self):
        for error, expected in [
            (urllib.error.HTTPError("url", 401, "private", {}, None), "provider_http_error"),
            (urllib.error.URLError("private"), "provider_network_error"),
            (TimeoutError("private"), "provider_network_error")]:
            opener = unittest.mock.Mock()
            opener.open.side_effect = error
            with patch("urllib.request.build_opener", return_value=opener):
                result = provider.run_probe("private", "rev")
            self.assertEqual(result["error"], expected)
            self.assertEqual(opener.open.call_count, 1)
            self.assertEqual(opener.open.call_args.kwargs["timeout"], 60)
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"x" * (provider.MAX_BODY + 1)
        opener.open.side_effect = None
        opener.open.return_value = response
        with patch("urllib.request.build_opener", return_value=opener):
            self.assertEqual(provider.run_probe("key", "rev")["error"], "response_too_large")
        response.__enter__.return_value.read.assert_called_once_with(provider.MAX_BODY + 1)


if __name__ == "__main__":
    unittest.main()
