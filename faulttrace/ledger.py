"""Local-only, idempotent token ledger. No network access or billing estimates."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

from .accounting import COUNTS, sanitized_receipt
from .validation import parse_json

DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / ".local" / "nebius-usage.json"
MAX_LEDGER = 4 * 1024 * 1024


class LedgerError(Exception):
    """Fixed diagnostic only; never propagate paths or file content."""


def read_json(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError()
    return parse_json(data.decode("utf-8"))


def load(path):
    try:
        if not Path(path).exists():
            return []
        value = read_json(path, MAX_LEDGER)
        if not isinstance(value, dict) or set(value) != {"version", "receipts"} or value["version"] != 1:
            raise ValueError()
        receipts = value["receipts"]
        if not isinstance(receipts, list):
            raise ValueError()
        seen = set()
        for receipt in receipts:
            if sanitized_receipt(receipt) != receipt or receipt["attempt_id"] in seen:
                raise ValueError()
            seen.add(receipt["attempt_id"])
        return receipts
    except Exception:
        raise LedgerError("ledger_read_failed") from None


def summarize(receipts):
    totals = dict.fromkeys(COUNTS, 0)
    contributors = dict.fromkeys(COUNTS, 0)
    states = dict.fromkeys(("missing", "partial", "invalid", "inconsistent"), 0)
    for receipt in receipts:
        status = receipt["usage_status"]
        if status != "valid":
            states[status] += 1
        # Contradictory triples are retained for audit, excluded from sums.
        if status != "inconsistent":
            for name, count in (receipt["token_usage"] or {}).items():
                if count is not None:
                    totals[name] += count
                    contributors[name] += 1
    return {"attempts": len(receipts), "known_tokens": totals,
            "contributing_attempts": contributors,
            "usage_unknown_or_invalid_attempts": sum(states.values()),
            "usage_states": states,
            "transport_invoked_attempts": sum(r["transport_invoked"] is True for r in receipts),
            "transport_unknown_attempts": sum(r["transport_invoked"] is None for r in receipts),
            "all_recorded_usage_complete": bool(receipts) and not any(states.values())}


def record(receipt, path=DEFAULT_LEDGER):
    """Serialize writers with an exclusive lock, then atomically replace the file."""
    try:
        receipt = sanitized_receipt(receipt)
    except Exception:
        raise LedgerError("ledger_invalid_receipt") from None
    try:
        path = Path(path)
        lock = path.with_name(path.name + ".lock")
    except Exception:
        raise LedgerError("ledger_write_failed") from None
    locked = False
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise LedgerError("ledger_busy") from None
        locked = True
        os.close(descriptor)
        receipts = load(path)
        for existing in receipts:
            if existing["attempt_id"] == receipt["attempt_id"]:
                if existing != receipt:
                    raise LedgerError("ledger_conflicting_duplicate")
                return "duplicate", summarize(receipts)
        receipts.append(receipt)
        encoded = json.dumps({"version": 1, "receipts": receipts}, sort_keys=True, indent=2).encode()
        if len(encoded) > MAX_LEDGER:
            raise LedgerError("ledger_capacity_exceeded")
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".usage-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        return "recorded", summarize(receipts)
    except LedgerError:
        raise
    except Exception:
        raise LedgerError("ledger_write_failed") from None
    finally:
        # Failure to clean up is also a persistence failure, never a false success.
        try:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if locked:
                lock.unlink()
        except OSError:
            raise LedgerError("ledger_cleanup_failed") from None


def import_receipt(path, ledger_path=DEFAULT_LEDGER):
    """Import a receipt, never a provider response; legacy usage remains unknown."""
    try:
        value = read_json(path, 262144)
        if not isinstance(value, dict):
            raise ValueError()
        if "attempt_id" not in value:
            # Legacy receipts lost accounting on validation failure. Do not reconstruct it.
            value = dict(value, token_usage=None, usage_status="missing", diagnostics=[],
                         transport_invoked=False if value.get("error") == "missing_credentials" else None)
            fingerprint = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
            value["attempt_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "faulttrace:legacy:" + fingerprint))
        value = sanitized_receipt(value)
    except Exception:
        raise LedgerError("ledger_import_failed") from None
    status, summary = record(value, ledger_path)
    return {"ledger_result": status, "attempt_id": value["attempt_id"], "ledger_summary": summary}
