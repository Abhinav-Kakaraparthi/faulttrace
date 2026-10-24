"""Run with python -m faulttrace.probe --live; never runs implicitly."""
import argparse
import json
import os
import subprocess

from .provider import run_probe


def main(argv=None, send=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="allow one Nebius request")
    args = parser.parse_args(argv)
    if not args.live:
        print(json.dumps({"validation_result": "not_run", "error": "live_opt_in_required"}))
        return 2
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                                  capture_output=True, text=True).stdout.strip()
        if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            revision = None
    except (OSError, subprocess.SubprocessError):
        revision = None
    kwargs = {} if send is None else {"send": send}
    receipt = run_probe(os.environ.get("NEBIUS_API_KEY"), revision, **kwargs)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["validation_result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
