"""Image observations are evidence, never planner proposals or equipment authority."""
import math

from .validation import ProbeError, completion_content, parse_json

# Synthetic fixture constraint only; NOT an industrial operating limit.
MIN_READING, MAX_READING = 0, 1000


def validate_image_evidence(envelope, evidence_ref):
    value = parse_json(completion_content(envelope))
    fields = {"readability", "reading", "unit", "evidence_ref"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ProbeError("invalid_image_evidence")
    if not isinstance(value["evidence_ref"], str) or value["evidence_ref"] != evidence_ref:
        raise ProbeError("invalid_image_evidence")
    if value["readability"] == "unreadable":
        if value["reading"] is not None or value["unit"] is not None:
            raise ProbeError("invalid_image_evidence")
    elif value["readability"] == "readable":
        reading = value["reading"]
        if (type(reading) not in (int, float) or not MIN_READING <= reading <= MAX_READING
                or not math.isfinite(reading) or value["unit"] != "kPa"):
            raise ProbeError("invalid_image_evidence")
    else:
        raise ProbeError("invalid_image_evidence")
    return value
