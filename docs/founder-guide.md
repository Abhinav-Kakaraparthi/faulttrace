# Provider smoke test

Transport sends one synthetic text request to the fixed Nebius endpoint and
model. Validation independently checks the response envelope and exact
observation-only proposal. A valid proposal grants no authority and executes
no equipment action. There is no application runtime integration yet.

The transport uses a 60-second socket timeout, no retries, no redirects, a
2048 output-token cap, and a 256 KiB response-body limit. A socket timeout
limits blocking socket operations; it is not a hard whole-process deadline.
Slow progress can exceed 60 seconds overall. Truncated output is rejected.

NEBIUS_API_KEY is read only from the environment. Errors use fixed codes;
provider bodies, headers, reasoning, and environment values are not logged.
Receipts contain narrowly validated metadata, never raw model content.
Missing usage remains unknown. No dollar cost is estimated.

FT-003A accepts `tool_calls` only when absent, null, or an empty JSON array.
Nonempty arrays and malformed values fail. Fixed codes distinguish
`invalid_message_shape`, `invalid_message_role`, `message_refusal`,
`unexpected_tool_calls`, and `unexpected_function_call`. Function-call,
finish-reason, content, and exact observation-only proposal checks remain
strict. Model output never grants equipment authority.

Metadata and usage are extracted before completion validation. Valid model,
response ID, and individual token counters survive a rejected proposal.
Invalid or missing fields remain null; booleans are not token counts.
`usage_status` distinguishes missing, partial, valid, invalid, and inconsistent
accounting. Three present counts must satisfy prompt + completion = total;
otherwise `inconsistent_usage` is reported. No missing count is derived.
`transport_invoked` records calling the transport, not completed inference.
For older receipts lacking this field, null means unknown.

Each invocation gets a UUID attempt ID. The CLI persists only allowlisted,
validated receipt fields to `.local/nebius-usage.json`, already gitignored.
It never persists raw responses, content, reasoning, headers, or credentials.
Offline tests always use temporary ledgers. Offline CLI commands:

```powershell
& $py -m faulttrace.probe --ledger-summary
& $py -m faulttrace.probe --import-receipt 'C:\path\to\sanitized-receipt.json'
```

`$py` is the interpreter configured in README. `--ledger PATH` overrides the
location. Importing a modern receipt retains its attempt ID; legacy imports
get a deterministic ID from a fingerprint and retain unknown usage. The
original receipt is read only. Reimporting the same receipt does not add
tokens; conflicting duplicates fail without overwriting the existing record.

`known_tokens` sums prompt/input, completion/output, and total independently.
`contributing_attempts` shows the number of known counters for each sum.
Zero contributors means unknown consumption, even if the sum displays 0.
Valid partial counters survive invalid sibling counters. Contradictory triples
are retained but excluded from sums. `usage_states` and
`usage_unknown_or_invalid_attempts` identify missing/partial/invalid/inconsistent
attempts. `all_recorded_usage_complete` refers only to this ledger's receipts;
it does not establish account-wide consumption. Historical manual tests,
other processes, lost receipts, and failed persistence can be absent.
This is provider-reported accounting for requests to the NVIDIA model, not
proof of completed inference, a provider billing statement, or a cost estimate.

An exclusive `.lock` serializes writers; a temporary file in the same directory
is flushed and fsynced before atomic replacement. Read, write, lock, capacity,
and conflicting-duplicate failures use fixed codes. A persistence failure makes
the CLI exit 1, even if proposal validation passed, while preserving the
sanitized receipt in stdout for later import. Disk-full or crash recovery may
require restoring a trusted receipt. A crash can leave a lock: confirm no
writer is running before manually removing it. The ledger is bounded to
4 MiB and is not a database or account-wide audit service. Atomic replacement
does not promise survival of every filesystem/power failure.

Offline tests use fake transport and never contact Nebius. The live command
requires explicit --live and can consume existing authorized credits.
Do not retry a failed live request automatically.

This proves connectivity and one simple output contract only. It does not
prove diagnosis, vision capability, production readiness, eligibility,
identity of equipment, or completed work. There is no website yet; browser
testing is not applicable to FT-003.

FT-003 remains PARTIAL: the earlier executable live attempt failed; its lost
response cannot be reconstructed, and no corrected live request has been
made. FT-003A is offline only. The next proposed verification is one explicitly
authorized live text probe with the corrected code and persistent accounting;
no retry or FT-004 work is part of this checkpoint.
