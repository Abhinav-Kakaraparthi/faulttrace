"""Bounded Nebius transport and sanitized receipt construction."""
import json
import time
import urllib.error
import urllib.request

from .validation import SAFE_CODES, ProbeError, parse_json, validate_completion
from .accounting import ENDPOINT, MODEL, SUPPORTED_MODELS, extract_accounting, new_receipt
from .http_diagnostics import ProviderHTTPError

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
    except urllib.error.HTTPError as error:
        failure = ProviderHTTPError(error.code)
        # Do not read even a bounded error body: status does not establish its cause.
        try:
            error.close()
        except Exception:
            pass
        raise failure from None
    except Exception:
        raise ProbeError("provider_network_error") from None
    if len(body) > MAX_BODY:
        raise ProbeError("response_too_large")
    return body


def run_probe(key, revision, send=transport, *, model=MODEL, payload=None,
              validator=validate_completion):
    receipt = new_receipt(revision, model)
    start = None
    try:
        if model not in SUPPORTED_MODELS:
            raise ProbeError("invalid_metadata_model")
        if not key or not key.strip():
            raise ProbeError("missing_credentials")
        start = time.monotonic()
        receipt["transport_invoked"] = True
        request_payload = payload if payload is not None else {
            "model": model, "max_tokens": 2048,
            "messages": [{"role": "user", "content": PROMPT}]}
        body = send(key, request_payload)
        if not isinstance(body, bytes) or len(body) > MAX_BODY:
            raise ProbeError("invalid_response_body")
        try:
            envelope = parse_json(body.decode("utf-8"))
        except UnicodeError:
            raise ProbeError("response_decoding_error") from None
        if not isinstance(envelope, dict):
            raise ProbeError("invalid_envelope")
        receipt.update(extract_accounting(envelope, model))
        validator(envelope)
        if receipt["diagnostics"]:
            raise ProbeError(receipt["diagnostics"][0])
        receipt["validation_result"] = "passed"
    except ProbeError as error:
        receipt["error"] = str(error) if str(error) in SAFE_CODES else "probe_failed"
        if isinstance(error, ProviderHTTPError):
            receipt.update(http_status=error.status, http_error_category=error.category)
    except Exception:
        receipt["error"] = "probe_failed"
    if start is not None:
        receipt["latency_ms"] = round((time.monotonic() - start) * 1000)
    # Redact even a syntactically valid identifier that contains the credential.
    for name in ("returned_model", "response_id", "source_revision"):
        if key and key.strip() and receipt[name] and key in receipt[name]:
            receipt[name] = None
            receipt.update(error="probe_failed", validation_result="failed")
    return receipt
