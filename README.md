# FaultTrace

**Trace the cause. Verify the recovery.**

FaultTrace is a planned investigation assistant for plant operators:
combine telemetry, field observations, and adaptive AI-guided tasks to
investigate equipment anomalies.

## Status

The final integration sprint adds an explicitly enabled, globally/session-budgeted
live-demo configuration, restricted Tavily references, metadata-only LangSmith
tracing, paused simulated-observation time, observation renewal and automatic
independent recovery monitoring. Default remains offline. Current implementation
`b09a8af` passes Linux/Windows/backend/frontend/container CI. Existing real
NVIDIA planning/photo contracts, one useful Tavily reference citation and LangSmith
metadata delivery are narrowly verified; photo accuracy, the complete browser-driven
live recovery journey remain unverified. Provider allowances
are spent; do not rerun verification commands. See [current evidence](docs/state.md).
The judge demo is live at
**https://faulttrace-judge-demo.onrender.com/** on `b09a8af`. One 512 MB compute
instance plus a 1 GiB disk has a $7.25/month baseline before tax/bandwidth. HTTPS,
session/isolation, upload and same-session/state/image restart checks pass.
The user verified the unchanged synthetic spending reservation after restart;
founder browser acceptance remains pending. Explicit NVIDIA planning/photo analysis,
restricted Tavily references and metadata-only LangSmith tracing are enabled behind
the existing durable limits. Hosted verification on `4796656` passed (photo used a synthetic
panel, not a real-photo accuracy evaluation). Its agent grant is spent; global
postflight remaining: 7 requests/733,056 admission units, not actual token usage.
Open a new private window for a fresh live demo; existing offline runs stay offline.
No external-storage migration has begun. Credentials remain server-only; provider
calls must not be replayed for retakes.
Last recorded offline preview: **http://127.0.0.1:8850/**. Availability and loaded
revision have not been reverified after the laptop restart; current-code activation
is separate readiness work. Existing runs must be preserved.
[Integrated acceptance and bounded later live procedure](docs/sprint-verification.md),
[deployment proposal](docs/sprint-release.md). Existing previews/runs are preserved.

The optional judge-demo service offers **Try demo** with an expiring HttpOnly
cookie, automatic isolated simulated investigation and both
workspaces for one visitor. No account or copied token is needed. Inference is
disabled by default; offline demo templates are not NVIDIA output. Administrative bearer access
remains separate. [Startup, session/security limits and offline checks](docs/judge-demo.md).

The `feat/finish-integrated` branch combines the reviewed server authorization and
memory-only frontend authentication. Release uses privately delivered opaque
bearer tokens; Commander/Operator permissions and incident/task/image access are
checked by the server. Browser logout does not revoke a token. Combined offline
contract checks pass; founder browser acceptance, hosting/TLS and Windows ACL review
remain open. Linux fixture/container checks now pass. See [review plan](docs/combined-auth-manual-review.md).

FT-012 adds a unified, simulation-only task-evidence-to-recovery journey for new
incidents. Planner-created tasks, independent human reports, photo-claim disputes,
approval and recovery share evidence references. Model readings are never
prefilled into human reports or used directly for correction. Offline checks
pass; browser/live acceptance remains open. [Zero-provider preview and later live plan](docs/unified-investigation.md).

FT-011 carries validated photographic interpretations into observation planning
as unverified model claims. Commander sees compatibility/disputes and accepted
citations; Operator can explicitly hand off a photo for follow-up and inspect
source photos on clarification tasks. Human reports remain independent, and no
photo satisfies the simulated correction checklist. Offline checks pass; live
and browser acceptance remain open. [Behavior and preview commands](docs/photo-planning.md).

FT-010 adds explicit NVIDIA photographic-observation analysis for collected
photos: category, visible reading/unit, measurement type, label transcription,
external handle orientation and bounded uncertainty. It is separate from fixture
analysis and excluded from correction authorization. FT-011 permits bounded
planner-only claims. [Contract and real-photo evaluation plan](docs/photographic-analysis.md).
The first completed standalone photo call passed its contract but failed a
preliminary reviewer numeric comparison. Photographic accuracy remains unverified;
no diagnosis, task completion or correction was authorized.

FT-009B adds camera/file photograph collection with local preview, replace/cancel,
measured upload progress and actual stored-image display. Uploads alone remain collection-only; FT-010 adds a separate explicit observation
analysis contract, whose factual photographic accuracy remains unverified.
[Photo scope, source/license guidance and later activation](docs/photo-evidence.md).
The isolated preview at http://127.0.0.1:5180/commander and /operator now uses
the updated backend with inference disabled, preserving the completed run and its
data directory. That run has no assigned observation task or stored photograph;
photo interaction acceptance remains open. See [activation evidence](docs/state.md).

An additional inference-disabled photo-review instance is available at
http://127.0.0.1:5181/commander and /operator, with a clearly test-created task and
separate data. [Manual checks and explicit preview-origin configuration](docs/photo-evidence.md#isolated-inference-disabled-review).
The completed 5180/8780 run is unchanged; no visual or camera pass is claimed.

FT-009A provides separate server-backed **/commander** and **/operator** pages.
Open http://127.0.0.1:5180/commander and http://127.0.0.1:5180/operator in the
existing isolated preview; old connected query URLs remain compatible. See
[current and target architecture](docs/architecture.md). Route separation is
not authentication; server-enforced roles remain a deployment gate. In new FT-012
runs, independent human task evidence can support the simulated assessment;
photographic model claims alone cannot. Historical runs retain their legacy scope.

FT-008 adds a complete **simulation-only** evidence -> working diagnosis -> human
approval -> simulated filter replacement -> independent recovery journey. No paid
inference is needed; fresh isolated data preserves existing runs. See
[exact startup and inspection steps](docs/recovery-journey.md). Offline checks
pass; desktop/mobile browser acceptance is blocked by unavailable browser access.

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
desktop/mobile browser review remain unverified. Standalone flat-schema provider
compatibility passed for one saved context. A narrow connected API run verified
task creation and replanning with a simulated access refusal in the updated
context, but repeated the inaccessible task. Refusal-aware application policy
now blocks that asset (offline-tested, not live-verified). Provider selection now
uses one permitted action_id, derived from application templates plus escalation,
then maps to the strict internal proposal. Its four-field flat wire contract passed one standalone
saved-refusal-context test, producing user-reported validated human escalation.
No task or browser journey was verified by that call; general reliability is open.
FT-007 stays PARTIAL;
browser verification and useful adaptive decisions remain open. Inference is disabled by
default; hosting and broader recovery verification stay open. CI is recorded below.
FT-007A adds strict structured-output requests and precise sanitized diagnostics.
The existing rejected live attempt remains preserved; a corrected call is
blocked on its already-attempted context. See the workflow guide before testing.
FT-007B preserves safe HTTP status/categories for future failures; historical
status remains unknown. Error bodies/headers are never retained.

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
$env:FAULTTRACE_PROFILE = 'local'
$env:FAULTTRACE_DATA_DIR = Join-Path (Get-Location) ('.local/local-review-' + [guid]::NewGuid().ToString('N') + '/data')
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

Do not recreate an installed venv unnecessarily. Frontend terminal: use the
npm commands below. Commander: http://127.0.0.1:5173/?mode=connected&view=commander;
second-tab Operator: http://127.0.0.1:5173/?mode=connected&view=operator.
Backend: http://127.0.0.1:8765/api/state. Vite proxies /api; keys stay backend-only.

Full offline checks after backend setup:

```powershell
& .venv\Scripts\python.exe tools/run_offline_tests.py
& .venv\Scripts\python.exe -m pip check
```

Combined frontend/backend authentication regression (existing dependencies only;
real frontend classes against isolated ASGI, no listener or provider):

```powershell
$env:FAULTTRACE_TEST_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
Push-Location frontend
node tests/combined-contract.mjs
Pop-Location
```

For fresh authenticated startup, use [release preparation](docs/release-preparation.md)
with a new private registry and inference-disabled launcher. Frontend defaults to
release authentication; set `VITE_FAULTTRACE_PROFILE=local` explicitly only for an
intentionally unauthenticated local backend. Direct `workflow.main` now requires
both `FAULTTRACE_PROFILE` and `FAULTTRACE_DATA_DIR`; no default historical run is
selected. The local example above creates a new directory and preserves old runs.

## Continuous integration

[FaultTrace CI](.github/workflows/ci.yml) runs on every push and pull request,
using Windows Server 2025 / Python 3.12 for backend and Ubuntu 24.04 / Node 22
for frontend. It installs the existing pinned
`requirements-backend.txt` and uses `npm ci` with the frontend lockfile, then runs
the full backend suite, frontend tests, TypeScript checks and production build.
Actions are pinned to official release commit SHAs; token permissions are read-only.

The backend runner removes `NEBIUS_API_KEY`, disables inference and rejects
external Python DNS/socket operations before test discovery. Local IPC remains
available for ASGI tests. Any blocked attempt fails the run even if application
code catches the exception. This guards accidental test-process network access;
it is not a sandbox for hostile code/native extensions/subprocesses. No provider
secrets are configured. Dependency installation still needs package registries.
Run the same backend command above and the frontend commands below locally.
Static frontend tests and a successful build do not establish browser acceptance.
The initial Ubuntu run exposed different PNG compression bytes. Canonical encoding
now passes strict byte regeneration on Windows/Ubuntu; historical originals and
pixel-equivalence assertions are retained. CI also builds/restarts the container.
The following [earlier CI run](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40399590742)
at `1b8249f704a900323ca71d115866704ba88fc452`: 162 backend / 45 frontend
tests, dependency checks, typecheck and build passed. Later commits require their
own passing run; see the branch's Actions checks.

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
