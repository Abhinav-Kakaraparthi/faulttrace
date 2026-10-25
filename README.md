# FaultTrace

**Trace the cause. Verify the recovery.**

FaultTrace is a planned investigation assistant for plant operators:
combine telemetry, field observations, and adaptive AI-guided tasks to
investigate equipment anomalies.

## Status

Standalone synthetic Nebius text probe, offline image-evidence preparation,
and offline validation tests exist. Two standalone vision fixtures have passed
verified inference. A local FastAPI/SQLite workflow and React frontend now
persist tasks/evidence across tabs and backend restart in offline tests.
Connected clear-image submission and inference-disabled restart persistence
are user-verified, corroborated by read-only SQLite/ledger checks. Mobile,
connected unreadable/refusal paths, and broad browser coverage remain open.
FT-007 adds explicit NVIDIA text planning with validated F-17/V-08 observation
tasks or human escalation, four reserved turns per incident, and structured
V-08 human reports. Offline policy tests pass; live adaptive planning and
desktop/mobile browser review remain unverified. Inference is disabled by
default; CI, hosting, and recovery verification stay open.

## Planned workflow

Anomaly -> investigation -> operator task -> evidence -> revised plan ->
permitted simulated action -> independent recovery verification.

NVIDIA models through Nebius will propose investigation steps.
Application policy will authorize permitted simulated actions.
Deterministic code will verify recovery independently of the model.
Temporary recovery will remain distinct from completed repair.

Initial demonstration: a simulated plant with commander and operator
workspaces, hidden fault scenarios, evidence clarification, and refusal.

## Proposed architecture

React/TypeScript frontend; Python/FastAPI API and worker; PostgreSQL;
private evidence storage; isolated simulator; Nebius model inference.

React/TypeScript/Vite and FastAPI are implemented locally. SQLite in ignored
`.local/workflow/` explicitly replaces proposed PostgreSQL for portable,
single-instance validation; hosted database work remains open. Telemetry is
simulated. Explicit model proposals pass deterministic policy before task creation.
Provider capabilities must be verified before selecting model identifiers.

## FT-007 observation planning / server workflow

See [server workflow guide](docs/evidence-workflow.md) for trust boundaries,
restart/idempotency behavior, planner contract, and bounded later live procedure.

Backend terminal (local-only, inference disabled):

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
& 'C:\Users\surya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
& .venv\Scripts\python.exe -m pip install -r requirements-backend.txt
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

Do not recreate an installed venv unnecessarily. Frontend terminal: use the
npm commands below. Commander: http://127.0.0.1:5173/?mode=connected&view=commander;
second-tab Operator: http://127.0.0.1:5173/?mode=connected&view=operator.
Backend: http://127.0.0.1:8765/api/state. Vite proxies /api; keys stay backend-only.

Full offline checks after backend setup:

```powershell
& .venv\Scripts\python.exe -m unittest discover -s tests -v
& .venv\Scripts\python.exe -m pip check
```

## FT-005 separate sample preview

Open **http://127.0.0.1:5173/?mode=sample** while Vite runs. Commander and
Operator share deterministic sample state within one tab. Live AI is not
connected; no provider requests or equipment control exist. Refresh/reset
clears the demo. No cross-tab or cross-device synchronization is claimed.

Exact PowerShell commands (Node 22.12+, verified with 22.14.0):

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd ci
npm.cmd run dev
```

Build/type check and offline state tests in another terminal:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd run test
npm.cmd run typecheck
npm.cmd run build
```

See [preview guide](docs/preview.md) for sample-data limits and the desktop/
phone review checklist. Browser automation was unavailable; no screenshots
or completed visual/accessibility checks are claimed. Python probe commands
below remain separate and must not be run to review the website.

## Development and submission

- Public source repository; MIT license.
- Never commit credentials or private field evidence.
- [Submission checklist](docs/submission.md)
- [Checkpoint state](docs/state.md)
- [Engineering instructions](AGENTS.md)

## FT-003 provider probe

Requires Python 3.12 (verified: 3.12.14), Git, and no third-party dependencies.
From the repository root in PowerShell, select the available interpreter:

```powershell
$py = 'C:\Users\surya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py --version
& $py -m unittest discover -s tests -p test_probe.py -v
& $py -m unittest discover -s tests -p test_accounting.py -v
& $py -m unittest discover -s tests -p test_image_evidence.py -v
```

On other machines, set `$py` to your Python 3.12 executable. No installation
or package setup is needed. Offline tests never call Nebius.

To run exactly one live synthetic request, provision `NEBIUS_API_KEY` in the
process environment through your secret manager (never paste it into source
or a recorded command). Then run:

```powershell
& $py -m faulttrace.probe --live
```

Without `--live`, the command refuses inference. Missing credentials produce
a sanitized JSON error. Exit codes: 0 validated, 1 failed, 2 no live opt-in.
The JSON receipt reports source HEAD, latency and usage; missing usage is null.
Run from a clean committed checkout so HEAD identifies the tested source.
The endpoint is `https://api.tokenfactory.nebius.com/v1` and the exact model is
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

Every probe invocation gets an attempt ID and records a sanitized receipt in
the gitignored `.local/nebius-usage.json` ledger (including failures and runs
without live opt-in). Inspect or import receipts without contacting a provider:

```powershell
& $py -m faulttrace.probe --ledger-summary
& $py -m faulttrace.probe --import-receipt 'C:\path\to\sanitized-receipt.json'
```

Use `--ledger 'C:\path\to\usage.json'` to select another local file. Reimporting
the same receipt is idempotent; conflicting attempt IDs fail. Legacy receipts
get a stable import ID and unknown usage. Partial sums are not total consumption
or billing. See the founder guide for accounting and persistence limitations.
FT-003 standalone text-probe acceptance is satisfied by corrected live
evidence against `c75a50be54ffb53fc728f6be0f14521e7b775bd1`: validation passed,
1609 ms, 79 input / 146 output / 225 total tokens. The local ledger also
retains one failed attempt with unknown usage. A separate historical manual
success used 155 / 112 / 267 tokens, giving cross-record known sums of
234 / 258 / 492. These sums are incomplete consumption, not billing.
The manual record lacks an exact timestamp and source revision and remains
outside the ledger. See state.md for provenance and the sanitized live receipt.
Application integration and all other unverified product gates remain open.

See [founder guide](docs/founder-guide.md) for limits and trust boundaries,
and [checkpoint state](docs/state.md) for separate historical and executable evidence.

## FT-004A image-evidence preparation

The image probe has synthetic clear/obscured fixtures, a separate observation
contract, and fake-transport tests. Both supplied standalone fixture calls
passed on `nvidia/Nemotron-3.5-Super-VL` at implementation
`9f4544eed13bd09eeb37a8a9786555ff925fa1b0`; no calls were repeated in FT-006.
The new connected application live path remains unverified.
The existing Nano text model is not assumed to support images.

See [image-probe guide](docs/vision-probe.md) for official discovery sources,
exact PowerShell account-discovery, one-clear/one-obscured live commands,
and offline ledger summary. All live commands require a later authorized
checkpoint. Run the existing offline command above to test both probes.
