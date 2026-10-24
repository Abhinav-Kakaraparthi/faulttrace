"""Bounded Nebius transport and sanitized receipt construction."""
from datetime import datetime, timezone
import json
import time
import urllib.error
import urllib.request

from .validation import ProbeError, parse_json, validate_completion

ENDPOINT = "https://api.tokenfactory.nebius.com/v1"
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
MAX_BODY = 262144
PROMPT = ('Synthetic observation-only test. Return only this JSON object: '
          '{"kind":"REQUEST_OBSERVATION","asset_id":"F-17",'
          '"capability":"READ_LOCAL_DP","evidence_refs":["telemetry-001"]}. '
          'No diagnosis, authorization, or equipment action is requested.')


def transport(key, payload):
    request = urllib.request.Request(
        ENDPOINT + "/chat/completions", data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    # Do not forward credentials through redirects. No retries.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
            body = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError:
        raise ProbeError("provider_http_error") from None
    except Exception:
        raise ProbeError("provider_network_error") from None
    if len(body) > MAX_BODY:
        raise ProbeError("response_too_large")
    return body


def run_probe(key, revision, send=transport):
    receipt = {"timestamp": datetime.now(timezone.utc).isoformat(),
               "endpoint": ENDPOINT, "requested_model": MODEL,
               "returned_model": None, "response_id": None, "latency_ms": None,
               "token_usage": None, "validation_result": "failed",
               "source_revision": revision}
    start = None
    try:
        if not key or not key.strip():
            raise ProbeError("missing_credentials")
        start = time.monotonic()
        body = send(key, {"model": MODEL, "max_tokens": 2048,
                          "messages": [{"role": "user", "content": PROMPT}]})
        if not isinstance(body, bytes) or len(body) > MAX_BODY:
            raise ProbeError("invalid_response_body")
        try:
            envelope = parse_json(body.decode("utf-8"))
        except UnicodeError:
            raise ProbeError("response_decoding_error") from None
        validate_completion(envelope)
        # Provider metadata is untrusted too: accept only narrow identifiers.
        model, response_id = envelope.get("model"), envelope.get("id")
        if model != MODEL or not isinstance(response_id, str) or not response_id.startswith("chatcmpl-"):
            raise ProbeError("invalid_metadata")
        suffix = response_id[len("chatcmpl-"):]
        if not suffix or len(suffix) > 80 or any(c not in "0123456789abcdef-" for c in suffix):
            raise ProbeError("invalid_metadata")
        receipt.update(returned_model=model, response_id=response_id)
        usage = envelope.get("usage")
        if usage is not None:
            if not isinstance(usage, dict):
                raise ProbeError("invalid_usage")
            counts = {name: usage.get(name) for name in
                      ("prompt_tokens", "completion_tokens", "total_tokens")}
            if any(v is not None and (type(v) is not int or v < 0) for v in counts.values()):
                raise ProbeError("invalid_usage")
            receipt["token_usage"] = counts
        receipt["validation_result"] = "passed"
    except ProbeError as error:
        allowed = {"missing_credentials", "provider_http_error", "provider_network_error",
                   "response_too_large", "invalid_response_body", "response_decoding_error",
                   "invalid_json", "duplicate_json_key", "invalid_envelope", "non_stop_completion",
                   "invalid_or_refused_message", "empty_or_invalid_content", "invalid_proposal",
                   "invalid_metadata", "invalid_usage"}
        receipt["error"] = str(error) if str(error) in allowed else "probe_failed"
    except Exception:
        receipt["error"] = "probe_failed"
    if start is not None:
        receipt["latency_ms"] = round((time.monotonic() - start) * 1000)
    # Last defensive boundary: even malicious metadata cannot echo the secret.
    if key and key.strip() and key in json.dumps(receipt):
        receipt.update(returned_model=None, response_id=None, error="probe_failed",
                       validation_result="failed")
    return receipt
