# Checkpoint state

## FT-001: foundation

Scope: documentation, MIT license, and public GitHub repository creation.

Application, provider integration, simulator, CI, browser verification,
and deployment are not implemented.

GitHub visibility and push must be verified from command results.
Do not infer successful execution from this file.

## Delivery requirements

After UI updates: visually inspect affected desktop and mobile workflows.
After verified checkpoints: review, commit scoped changes, push, and verify.
Record actual SHA, checks, screenshots, failures, and pending work.
Never represent historical checks as validation of changed code.

## Main risk

A polished interface could conceal a scripted or disconnected workflow.
Prove runtime model capabilities before expanding the application.

## Historical FT-002 manual text smoke evidence

User-provided preceding manual test (not a run of the FT-003 executable):
endpoint https://api.tokenfactory.nebius.com/v1;
model nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B;
request chatcmpl-aa8cb057-06b7-4632-aacb-cdba63f1b76c;
latency 1029 ms; tokens 155 prompt / 112 completion / 267 total;
finish reason stop. Validated proposal:
`{"kind":"REQUEST_OBSERVATION","asset_id":"F-17","capability":"READ_LOCAL_DP","evidence_refs":["telemetry-001"]}`.

This proves connectivity and a simple output contract, not diagnosis,
vision, production readiness, or completed hackathon eligibility.

## FT-003 implementation

Python 3.12.14 verified via the bundled interpreter; Python is not on PATH.
Standard-library transport, strict validation, explicit live CLI, and fake
transport tests added. No website exists; browser testing is not applicable.
No equipment actions are authorized or executed. Main failure mode: a model
can return a plausible but invalid proposal; deterministic validation rejects it.

Initial offline run: 8 passed, 1 failed (whitespace credentials interacted
with defensive redaction). Corrected before implementation commit.
Implementation revision: `092b77d3b7755598e369d26e857cfde445665d2d`.
Final offline run: 9 tests passed (including parameterized invalid contracts,
transport limits, no retries, and sentinel-key output checks); diff whitespace
check passed. All source files are below 500 lines. Staged content was
manually reviewed before commit. An additional automated secret scan failed
to execute due to PowerShell quoting; the corrected implementation-commit
scan passed afterward. No credentials were printed or committed.

Committed CLI check: exit 1, missing_credentials; NEBIUS_API_KEY is unavailable.
No provider request was sent and no automatic retry was attempted.
Sanitized receipt: [missing credentials](evidence/ft-003-missing-credentials.json).
This is executable failure evidence, not successful live inference evidence.
Historical manual evidence above remains separate.

Delivery: implementation and later evidence are separate commits. Remote
branch SHA and available CI must be checked after push; command results,
not this record, establish successful delivery. No UI or deployment exists.

Prior license-detection issue resolved: read-only GitHub repository API
reports visibility public and license SPDX MIT on October 24, 2026.
GitHub Actions API reports zero runs; CI is not implemented.

## FT-003A: response compatibility, diagnostics, and persistent accounting

Status: offline checkpoint implemented; FT-003 remains PARTIAL. The earlier
executable live attempt failed. No corrected live request has been made.
This checkpoint sent no provider requests, installed no dependencies, and
did not advance FT-004. No commits or pushes were authorized or performed.
Base branch: `feat/ft-003-provider-probe`; unchanged base HEAD:
`468ad89b703dea4080e6c50371a35c839ff4a827`. Starting tree was clean.
Checks below apply to the uncommitted FT-003A source, not that base revision.

Completion validation now accepts absent/null/empty-array tool_calls and
rejects nonempty or malformed values. Fixed codes distinguish message shape,
role, refusal, unexpected tool calls, and unexpected function calls. All
observation-only contract checks and the no-equipment-authority boundary
remain. Accounting/metadata are extracted independently before completion
validation, so a rejected proposal no longer discards valid usage or IDs.
Invalid fields are null, partial counters survive, booleans are rejected,
and inconsistent triples receive an explicit diagnostic. Transport invocation
is recorded separately and does not establish completed inference.

Local ledger: `.local/nebius-usage.json`, verified ignored by Git. UUID attempt
IDs, validated receipt allowlist, exclusive writer lock, flushed temporary
file and atomic replacement provide idempotent recording. Conflicting
duplicates and persistence failures fail with fixed codes. Known prompt,
completion, and total counters are summed independently; contributor and
missing/partial/invalid/inconsistent attempt counts expose incomplete totals.
Inconsistent triples are preserved but excluded from sums; no billing estimate.

Imported the user-specified temporary failed receipt read-only:
`faulttrace-ft003-live-1b5344dbe17948818ac4075a9de70282.json`.
Import attempt ID: `fccd017f-1be5-5f0d-af4b-f27b6b024260`.
First import recorded; second returned duplicate without adding an attempt.
Original SHA-256 before and after:
`B15A3BA9E58AAFEF480E47494A8EFDD73B442A6507115CFC0076200F8DF51D4C`.
Lost provider response was not reconstructed. Usage and transport invocation
remain unknown for this legacy receipt. The original FT-003 missing-credential
receipt and the historical manual FT-002 success remain separate evidence;
they were not imported into this local ledger.

Local ledger summary: 1 attempt; known prompt/input 0, completion/output 0,
total 0, each with 0 contributing attempts. These empty sums do NOT mean zero
consumption. Missing usage: 1; partial: 0; invalid: 0; inconsistent: 0;
transport unknown: 1. All-recorded-usage-complete: false.

Verification: Python 3.12.14; `python -m unittest discover -s tests -v`
using the README bundled interpreter. Existing tests use temporary ledgers;
new fake-transport tests cover compatibility, fixed diagnostics, retained
accounting, invalid/partial/boolean/inconsistent usage, duplicates/conflicts,
atomic replacement failure, missing credentials, and secret non-disclosure.
Final result: all 22 tests passed, including the original 9 tests. Reviewed
the tracked diff and new accounting/ledger/test files; `git diff --check`
passed. Source files remain below 500 lines. No staged changes.

Limitations: local accounting covers only recorded receipts, not account-wide
consumption or billing. A failed persistence or process crash can lose an
attempt; a stale lock requires manual recovery after confirming no writer.
The socket timeout remains per blocking operation, not a hard process deadline.
No website exists; browser testing is not applicable. Application integration,
diagnosis, vision, and production readiness remain unverified.

## Next proposed verification (not performed in FT-003A)

After review and explicit authorization, run exactly one corrected live text
probe with the environment credential and persistent local ledger:
`python -m faulttrace.probe --live`. Inspect its sanitized receipt, metadata,
usage status and ledger summary; do not automatically retry. No FT-004 work
until the text compatibility/accounting result has been reviewed.

## Earlier FT-003 next action (superseded by FT-003A above)

Immediate next action: provision NEBIUS_API_KEY through the environment and
run exactly one `python -m faulttrace.probe --live` from this clean feature
branch; preserve its sanitized receipt in a separate evidence commit.
Do not automatically retry a failed request.

FT-004: bounded Nebius vision capability gate, using synthetic evidence,
explicit opt-in, sanitized receipts, and independent output validation.
Do not infer image support from this text test. Verify official submission
requirements before checking related gates.

## Original FT-002 scope

FT-002: Nebius provider capability gate.

Inspect available tooling and local configuration without exposing secrets.
Verify available NVIDIA model identifiers, then prove bounded real text
and image inference through Nebius. Record sanitized receipts and failures.
Use only authorized available credits; do not incur new spending.
