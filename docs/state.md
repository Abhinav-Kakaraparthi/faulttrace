# Checkpoint state

## Current checkpoint: FT-004A offline image-evidence preparation

Scope: offline preparation only. Base was clean on
`feat/ft-003-provider-probe` at expected HEAD
`19f9edc2e55c0ba39b61344038115becb27b14ef`. Created
`feat/ft-004-image-evidence` from that verified revision. No unrelated work
was present. No inference, authenticated account query, UI, deployment,
merge, tooling installation, or accounting-infrastructure expansion.

Candidate: `nvidia/Nemotron-3.5-Super-VL`, documented active/image2text in
the [official public catalog](https://tokenfactory.nebius.com/api/public/models_info)
on October 24, 2026. NVIDIA vision is preferred here because it is actually
listed, not inferred from Nano. The catalog also labels a dedicated-endpoint
use case; serverless/account access is NOT established. The
[official vision example](https://docs.tokenfactory.nebius.com/api-reference/examples/vision-capabilities)
documents inline base64 images and text/image_url message parts. Request:
POST `https://api.tokenfactory.nebius.com/v1/chat/completions`; 2048 output
tokens, 60-second socket timeout, 256 KiB response limit, one selected PNG,
no redirects/retries/fallbacks. Compatibility with this candidate's returned
metadata, reasoning budget, and the account remains unverified.

The image evidence contract is separate from planner proposals. It allows
only readability, reading, unit, evidence_ref; unreadable requires both
reading/unit null. References are task-provided, not model-created asset
identity. Readable values must be finite, nonnegative, and at most 1000;
this is explicitly a synthetic fixture constraint, not an industrial limit.
No diagnosis, recovery, equipment command, confidence percentage, or
authorization. Shared completion-envelope checks remain strict. The existing
text proposal contract is unchanged. Available usage survives evidence failure.

Fixtures: invented RGB PNGs, 480x300, generated with already available Pillow
12.3.0. No new dependencies; image library is offline-generation-only.
Neutral filenames and manifest do not contain answers. Expected values stay
in offline test/generator/docs material; runtime never loads the answer key.
The image viewer was actually used to inspect both fixtures: panel-a clearly
shows the digital reading and unit, panel-b completely covers both with opaque
replacement pixels. Tests verify every covered pixel, identical outside scene,
no alpha or ancillary metadata, manifest integrity, and byte reproducibility.

- panel-a.png SHA-256: `865db39953a926433d00de7be42eedc07f5795940bc07d78dc5c44d90dd16da6`.
- panel-b.png SHA-256: `0b787644c7315751357ed5e4bee087810d37d1ed1f976a264cd15505bad4547a`.

Verification: full prior/affected offline tests passed (35 tests; Python
3.12.14), including wrong references, extra/duplicate fields, nonfinite/bool/
null/range errors, refusal/truncation, transport/accounting failures, missing
credentials, secret non-disclosure, and preservation of the text validator.
Tests use fake transport and temporary ledgers. The final network-guarded run
passed all 35 tests with zero socket connection attempts. Whitespace check
passed; all source files are below 500 lines (largest 250). Staged secret
review and remote verification are reported with delivery command results.
No fabricated model result is used as evidence.
The existing local ledger remains ignored; no image attempts were recorded.

See [image-probe guide](vision-probe.md) for exact PowerShell model/account
discovery, one-clear and one-obscured opt-in request, and offline summary.
The ledger now permits only the original text model and this exact candidate;
its persistence, summary, and accounting schema are unchanged. Fixture ID/hash,
reference, and normalized evidence appear in sanitized CLI output, not the
accounting ledger. Preserve that output during later live verification.

Offline preparation acceptance: PASS; live vision stays UNVERIFIED until
actual image calls pass both contract validation and independent fixture
expectations. Contract-valid but wrong readings still fail the capability gate.
These synthetic digital fixtures do not prove arbitrary analog-gauge accuracy.
Application integration, UI, deployment, and unverified submission gates remain
open. There is no website, so browser journey testing is not applicable.

Exact next action (not performed here): in the Windows terminal run the
documented authenticated model-list discovery. If listed and a separate live
checkpoint is authorized, run once:
`& $py -m faulttrace.image_probe --live --fixture panel-a`.
Review its receipt and independent expected reading before the separately
selected panel-b invocation. Stop on failure without retry or fallback.
The implementation/final SHA comes from the scoped commit and remote-match
command results, not a guessed self-referential SHA in this file.

## Current: FT-003 evidence finalized

FT-003 standalone text-probe acceptance: PASS. Corrected live validation
passed against implementation `c75a50be54ffb53fc728f6be0f14521e7b775bd1`.
This later documentation commit records existing evidence; it does not
represent another inference run or a new tested implementation. Earlier
PARTIAL/blocked entries below are historical and superseded by this result.
The pre-existing unstaged FT-003B blocker record is preserved below.

Corrected receipt, verified read-only against the local sanitized ledger:

```json
{
  "timestamp": "2026-10-24T17:46:10.340732+00:00",
  "attempt_id": "a2029351-6ea4-481e-936e-9d8f20221177",
  "response_id": "chatcmpl-bbb03982-9579-4717-a718-4231788cfbd8",
  "endpoint": "https://api.tokenfactory.nebius.com/v1",
  "requested_model": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
  "returned_model": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
  "source_revision": "c75a50be54ffb53fc728f6be0f14521e7b775bd1",
  "latency_ms": 1609,
  "token_usage": {"prompt_tokens": 79, "completion_tokens": 146, "total_tokens": 225},
  "usage_status": "valid",
  "transport_invoked": true,
  "validation_result": "passed",
  "diagnostics": []
}
```

Exit code 0 and ledger_result recorded are supplied verified execution
evidence; they are not fields retained in the ledger. The stored receipt
above matches that evidence. The corrected attempt occurs exactly once;
historical failed attempt `fccd017f-1be5-5f0d-af4b-f27b6b024260` also remains
exactly once with unknown usage. No receipt was reimported in this checkpoint.

### Accounting coverage

| Record | Input tokens | Output tokens | Total tokens | Coverage |
| --- | ---: | ---: | ---: | --- |
| Corrected executable request, bbb03982 response above | 79 | 146 | 225 | Local ledger |
| External manual request, aa8cb057 response below | 155 | 112 | 267 | Separate historical record |
| Known across the two distinct successful requests | 234 | 258 | 492 | Cross-record sums |
| Additional failed request | unknown | unknown | unknown | Local ledger, missing usage |

Actual offline ledger summary: 2 attempts; known input 79, output 146,
total 225, with 1 contributing attempt to each counter. Usage states:
missing 1, partial 0, invalid 0, inconsistent 0. Transport invoked 1,
transport unknown 1. All-recorded-usage-complete false. These ledger totals
exclude the manual test and are not complete consumption or billing.
The cross-record sums also exclude the failed request's unknown usage;
no missing usage or dollar cost is estimated.

Historical manual evidence is user-provided external evidence: response
`chatcmpl-aa8cb057-06b7-4632-aacb-cdba63f1b76c`, same endpoint/model,
latency 1029 ms, validation passed, finish reason stop; counts as above.
Its exact timestamp and application source revision are unavailable. It is
not attributed to an implementation commit. Reviewed import contract:
`sanitized_receipt` requires a timestamp with timezone and has no external
provenance field; legacy import also replaces usage with unknown. Therefore
it cannot honestly import this evidence without code changes. No code was
changed: this table and the original FT-002 record retain the ledger gap.

### Verification and acceptance

Repository, feature branch, expected implementation HEAD, staged/unstaged/
untracked state inspected. Only the existing docs/state.md change was pending.
Source/tests remain identical to the implementation commit; prior 22 passing
offline tests still apply and were not rerun. Offline ledger-summary exit 0;
read-only identity/accounting assertions passed for both records. Git ignore
verification passed for `.local/nebius-usage.json`. Whitespace and staged
secret checks passed before the documentation commit. No provider
request, installation, feature implementation, UI, or merge in this checkpoint.

GitHub read-only repository and license APIs on October 24, 2026 both report
automatic SPDX MIT detection; repository public, detected path LICENSE.
License unchanged. Branch Actions API reports 0 runs; CI is unverified.

The bounded smoke-test requirements (strict contract, sanitized errors,
offline validation, corrected committed live inference, and persistent
receipt/accounting) are satisfied. Accounting completeness is separately
INCOMPLETE due to the failed request and external manual coverage gap.
Application runtime integration, vision, diagnosis, UI, deployment,
production readiness, and full hackathon eligibility remain unverified.
There is no website; browser testing is not applicable.

Delivery scope: README.md, docs/founder-guide.md, docs/state.md, and
docs/submission.md only. These are later documentation changes, not part of
the live-tested implementation. The final documentation SHA and remote-match
verification are reported from Git command results; they are not inferred
from this file. Local ledgers, credentials, and temporary files stay excluded.

Exact next action: review the pushed FT-003 evidence and separately authorize
the scope of FT-004's bounded vision capability gate. Do not infer image
support from this text result. No further probe or feature checkpoint is
started by this evidence-finalization checkpoint.

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

## FT-003B: corrected live verification blocked before inference

Status: PARTIAL, October 24, 2026. Verified repository root and origin,
branch `feat/ft-003-provider-probe`, and expected starting HEAD
`468ad89b703dea4080e6c50371a35c839ff4a827`. The ten pending files matched
the reviewed FT-003A implementation, tests, and documentation; no unrelated
changes were present. The prior 22-test offline result still applies:
no subsequent source changes invalidated it, so tests were not rerun.
Staged whitespace and secret checks passed. Local ledger and temporary
files were excluded from staging.

Implementation commit: `c75a50be54ffb53fc728f6be0f14521e7b775bd1`.
Commit message: `fix(provider): preserve usage and validate empty tool calls safely`.
The committed checkout was clean before credential preflight.

Credential preflight: NEBIUS_API_KEY unavailable in both the executing
process environment and Windows user environment. No value was printed,
saved, or embedded. Per the checkpoint stop condition, the live command
was NOT RUN: no provider request, new attempt, live receipt, or inference
exit code exists. This is a preflight blocker, not a new inference failure.
No retries, additional probes, installs, pushes, merges, or FT-004 work.

Offline `python -m faulttrace.probe --ledger-summary` completed with exit 0
using Python 3.12.14. Verified the historical attempt
`fccd017f-1be5-5f0d-af4b-f27b6b024260` remains exactly once with unknown
usage. Ledger summary is unchanged: 1 recorded attempt; known input 0,
output 0, total 0, each with 0 contributing attempts. Missing usage: 1;
partial: 0; invalid: 0; inconsistent: 0; transport unknown: 1.
All-recorded-usage-complete: false. These empty sums do not establish zero
consumption. `.local/nebius-usage.json` remains ignored by Git.

Inference validation: not performed. Accounting completeness: incomplete
because historical usage remains unknown. FT-003's corrected executable
live-verification acceptance criterion is not satisfied; FT-003 remains
PARTIAL. Offline implementation checks remain verified. This standalone
probe establishes no application runtime integration, diagnosis, vision,
production readiness, or completed submission eligibility. No website exists.

Post-implementation documentation change: only this FT-003B section in
`docs/state.md`, left uncommitted. The tested source remains exactly the
implementation commit above. No remote verification was performed because
this checkpoint prohibits pushing.

Exact next action: make NEBIUS_API_KEY available through the existing process
or Windows user environment without recording its value, then authorize
one corrected live text probe from the committed implementation. Capture
the sanitized receipt, inspect the offline ledger summary, and do not retry
automatically. Do not advance FT-004 on this blocked result.

## Next proposed verification (not performed in FT-003A or FT-003B)

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
