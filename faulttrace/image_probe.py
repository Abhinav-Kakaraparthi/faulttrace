"""Opt-in single-image probe. No generation fallback or expected-answer lookup."""
import argparse
import json
import os
import subprocess

from .accounting import VISION_MODEL, new_receipt
from .image_evidence import validate_image_evidence
from .image_fixtures import FIXTURE_IDS, image_payload
from .ledger import DEFAULT_LEDGER, LedgerError, record
from .provider import run_probe, transport
from .validation import ProbeError


def run_image_probe(key, revision, fixture_id, send=transport):
    result = new_receipt(revision, VISION_MODEL)
    if not key or not key.strip():
        result["error"] = "missing_credentials"
        return result
    try:
        payload, evidence_ref, digest = image_payload(fixture_id)
    except ProbeError:
        result["error"] = "invalid_fixture"
        return result
    evidence = None

    def validate(envelope):
        nonlocal evidence
        evidence = validate_image_evidence(envelope, evidence_ref)

    result = run_probe(key, revision, send, model=VISION_MODEL, payload=payload, validator=validate)
    result.update(fixture_id=fixture_id, fixture_sha256=digest, evidence_ref=evidence_ref)
    if result["validation_result"] == "passed":
        result["image_evidence"] = evidence
    return result


def main(argv=None, send=transport):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--fixture", choices=FIXTURE_IDS, required=True)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    args = parser.parse_args(argv)
    if not args.live:
        print(json.dumps({"validation_result": "not_run", "error": "live_opt_in_required"}))
        return 2
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                                  capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        revision = None
    result = run_image_probe(os.environ.get("NEBIUS_API_KEY"), revision, args.fixture, send)
    try:
        status, summary = record(result, args.ledger)
        result.update(ledger_result=status, ledger_summary=summary)
    except LedgerError as error:
        result["ledger_error"] = str(error)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["validation_result"] == "passed" and "ledger_error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
