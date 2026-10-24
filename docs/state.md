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

## Next checkpoint (after FT-003 evidence)

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
