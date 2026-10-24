"""Strict observation-only proposal and completion validation."""
import json


class ProbeError(Exception):
    """Only fixed, safe error codes may cross the CLI boundary."""


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
    if (not isinstance(message, dict) or message.get("role") != "assistant"
            or message.get("refusal") not in (None, "")
            or message.get("tool_calls") is not None
            or message.get("function_call") is not None):
        raise ProbeError("invalid_or_refused_message")
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
