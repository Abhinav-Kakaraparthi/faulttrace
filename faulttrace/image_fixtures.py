"""Load only integrity-checked, synthetic PNG fixtures; no answer-key imports."""
import base64
import hashlib
import json
from pathlib import Path

from .accounting import VISION_MODEL
from .validation import ProbeError

FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "image-evidence"
FIXTURE_IDS = ("panel-a", "panel-b")
MAX_IMAGE = 65536


def image_payload(fixture_id):
    try:
        if fixture_id not in FIXTURE_IDS:
            raise ValueError()
        manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        entry = manifest[fixture_id]
        with (FIXTURE_ROOT / (fixture_id + ".png")).open("rb") as stream:
            body = stream.read(MAX_IMAGE + 1)
        digest = hashlib.sha256(body).hexdigest()
        if (len(body) > MAX_IMAGE or not body.startswith(b"\x89PNG\r\n\x1a\n")
                or digest != entry["sha256"]
                or entry["evidence_ref"] not in ("image-001", "image-002")):
            raise ValueError()
    except Exception:
        raise ProbeError("invalid_fixture") from None
    evidence_ref = entry["evidence_ref"]
    prompt = (
        'Inspect this synthetic instrument image. Return only one JSON object with exactly '
        'readability ("readable" or "unreadable"), reading (number or null), '
        'unit ("kPa" or null), evidence_ref ("' + evidence_ref + '"). '
        'If any part of the numeric display or its unit is hidden or illegible, '
        'use unreadable and null for both reading and unit. Never infer hidden digits. '
        'For readable evidence transcribe only the displayed number and unit. '
        'The allowed numeric range is 0 through 1000 solely as a synthetic fixture '
        'constraint, not an industrial operating limit. No asset assignment, diagnosis, '
        'recovery declaration, authorization, confidence percentage, or equipment command.'
    )
    payload = {"model": VISION_MODEL, "max_tokens": 2048, "stream": False,
               "messages": [{"role": "user", "content": [
                   {"type": "text", "text": prompt},
                   {"type": "image_url", "image_url": {
                       "url": "data:image/png;base64," + base64.b64encode(body).decode("ascii")}}]}]}
    return payload, evidence_ref, digest
