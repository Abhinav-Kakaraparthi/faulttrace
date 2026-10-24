"""Run with python -m faulttrace.probe --live; never runs implicitly."""
import argparse
import json
import os
import subprocess

from .provider import run_probe
from .accounting import new_receipt
from .ledger import DEFAULT_LEDGER, LedgerError, import_receipt, load, record, summarize


def main(argv=None, send=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--live", action="store_true", help="allow one Nebius request")
    modes.add_argument("--import-receipt", metavar="PATH", help="offline receipt import")
    modes.add_argument("--ledger-summary", action="store_true", help="offline usage summary")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER), help="local ledger path")
    args = parser.parse_args(argv)
    if args.import_receipt or args.ledger_summary:
        try:
            result = (import_receipt(args.import_receipt, args.ledger) if args.import_receipt
                      else {"ledger_summary": summarize(load(args.ledger))})
            print(json.dumps(result, sort_keys=True))
            return 0
        except LedgerError as error:
            print(json.dumps({"ledger_error": str(error)}))
            return 1
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                                  capture_output=True, text=True).stdout.strip()
        if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            revision = None
    except (OSError, subprocess.SubprocessError):
        revision = None
    kwargs = {} if send is None else {"send": send}
    if args.live:
        receipt = run_probe(os.environ.get("NEBIUS_API_KEY"), revision, **kwargs)
    else:
        receipt = new_receipt(revision)
        receipt.update(validation_result="not_run", error="live_opt_in_required")
    try:
        status, summary = record(receipt, args.ledger)
        receipt.update(ledger_result=status, ledger_summary=summary)
    except LedgerError as error:
        receipt["ledger_error"] = str(error)
    print(json.dumps(receipt, sort_keys=True))
    if "ledger_error" in receipt:
        return 1
    if not args.live:
        return 2
    return 0 if receipt["validation_result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
