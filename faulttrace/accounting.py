"""Sanitized metadata and independently validated provider token accounting."""
from datetime import datetime, timezone
import re
import uuid

from .validation import SAFE_CODES

ENDPOINT = "https://api.tokenfactory.nebius.com/v1"
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
VISION_MODEL = "nvidia/Nemotron-3.5-Super-VL"
SUPPORTED_MODELS = {MODEL, VISION_MODEL}
COUNTS = ("prompt_tokens", "completion_tokens", "total_tokens")
USAGE_STATES = {"missing", "partial", "valid", "invalid", "inconsistent"}


def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r"chatcmpl-[0-9a-f-]{1,80}", value)


def valid_revision(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value)


def usage_fields(usage):
    if usage is None:
        return None, "missing"
    if not isinstance(usage, dict):
        return None, "invalid"
    counts = {}
    invalid = False
    for name in COUNTS:
        value = usage.get(name)
        if value is not None and (type(value) is not int or value < 0):
            invalid = True
            value = None
        counts[name] = value
    if invalid:
        return counts, "invalid"
    if all(value is not None for value in counts.values()):
        status = ("valid" if counts["prompt_tokens"] + counts["completion_tokens"]
                  == counts["total_tokens"] else "inconsistent")
        return counts, status
    return counts, "partial" if any(v is not None for v in counts.values()) else "missing"


def extract_accounting(envelope, expected_model=MODEL):
    """Return only validated fields; one bad field never erases another."""
    model, response_id = envelope.get("model"), envelope.get("id")
    usage, status = usage_fields(envelope.get("usage"))
    diagnostics = []
    if model != expected_model:
        model = None
        diagnostics.append("invalid_metadata_model")
    if not valid_id(response_id):
        response_id = None
        diagnostics.append("invalid_metadata_id")
    if status in {"invalid", "inconsistent"}:
        diagnostics.append("inconsistent_usage" if status == "inconsistent" else "invalid_usage")
    return {"returned_model": model, "response_id": response_id,
            "token_usage": usage, "usage_status": status, "diagnostics": diagnostics}


def new_receipt(revision, model=MODEL):
    return {"attempt_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": ENDPOINT, "requested_model": model, "returned_model": None,
            "response_id": None, "latency_ms": None, "transport_invoked": False,
            "token_usage": None, "usage_status": "missing", "diagnostics": [],
            "validation_result": "failed", "source_revision": revision if valid_revision(revision) else None}


def sanitized_receipt(value):
    """Validate a receipt allowlist for persistence; never copy arbitrary text."""
    if not isinstance(value, dict):
        raise ValueError()
    result = {name: value.get(name) for name in new_receipt(None)}
    attempt = result["attempt_id"]
    if not isinstance(attempt, str) or str(uuid.UUID(attempt)) != attempt:
        raise ValueError()
    timestamp = result["timestamp"]
    if not isinstance(timestamp, str) or len(timestamp) > 40:
        raise ValueError()
    if datetime.fromisoformat(timestamp).tzinfo is None:
        raise ValueError()
    if result["endpoint"] != ENDPOINT or result["requested_model"] not in SUPPORTED_MODELS:
        raise ValueError()
    if result["returned_model"] not in (None, result["requested_model"]):
        raise ValueError()
    if result["response_id"] is not None and not valid_id(result["response_id"]):
        raise ValueError()
    if result["source_revision"] is not None and not valid_revision(result["source_revision"]):
        raise ValueError()
    if result["transport_invoked"] is not None and type(result["transport_invoked"]) is not bool:
        raise ValueError()
    latency = result["latency_ms"]
    if latency is not None and (type(latency) is not int or latency < 0):
        raise ValueError()
    if result["validation_result"] not in {"passed", "failed", "not_run"}:
        raise ValueError()
    diagnostics = result["diagnostics"]
    if not isinstance(diagnostics, list) or any(not isinstance(c, str) or c not in SAFE_CODES for c in diagnostics):
        raise ValueError()
    counts, status = usage_fields(result["token_usage"])
    declared = result["usage_status"]
    preserved_invalid = declared == "invalid" and status in {"missing", "partial", "invalid"}
    if declared not in USAGE_STATES or (declared != status and not preserved_invalid):
        raise ValueError()
    # Invalid fields have already been replaced by null, but their invalid status survives.
    result["token_usage"] = counts
    error = value.get("error")
    if error is not None:
        if not isinstance(error, str) or error not in SAFE_CODES:
            raise ValueError()
        result["error"] = error
    return result
