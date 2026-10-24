"""Strict observation-only proposal and completion validation."""
import json


class ProbeError(Exception):
    """Only fixed, safe error codes may cross the CLI boundary."""


SAFE_CODES = frozenset({
    "missing_credentials", "provider_http_error", "provider_network_error",
    "response_too_large", "invalid_response_body", "response_decoding_error",
    "invalid_json", "duplicate_json_key", "invalid_envelope", "non_stop_completion",
    "invalid_message_shape", "invalid_message_role", "message_refusal",
    "unexpected_tool_calls", "unexpected_function_call", "empty_or_invalid_content",
    "invalid_proposal", "invalid_metadata_model", "invalid_metadata_id",
    "invalid_usage", "inconsistent_usage", "probe_failed", "live_opt_in_required",
    "invalid_or_refused_message",  # Historical sanitized receipts only.
})


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProbeError("duplicate_json_key")
        result[key] = value
    return result


def parse_json(value):
    try:
        return json.loads(value, object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, TypeError, RecursionError):
        raise ProbeError("invalid_json") from None


def validate_completion(envelope):
    if not isinstance(envelope, dict):
        raise ProbeError("invalid_envelope")
    choices = envelope.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ProbeError("invalid_envelope")
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        raise ProbeError("non_stop_completion")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise ProbeError("invalid_message_shape")
    if message.get("role") != "assistant":
        raise ProbeError("invalid_message_role")
    if message.get("refusal") not in (None, ""):
        raise ProbeError("message_refusal")
    tools = message.get("tool_calls")
    if tools is not None and not (isinstance(tools, list) and len(tools) == 0):
        raise ProbeError("unexpected_tool_calls")
    if message.get("function_call") is not None:
        raise ProbeError("unexpected_function_call")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProbeError("empty_or_invalid_content")
    proposal = parse_json(content)
    expected = {"kind": "REQUEST_OBSERVATION", "asset_id": "F-17",
                "capability": "READ_LOCAL_DP", "evidence_refs": ["telemetry-001"]}
    if (not isinstance(proposal, dict) or proposal != expected
            or set(proposal) != set(expected)):
        raise ProbeError("invalid_proposal")
    return proposal
