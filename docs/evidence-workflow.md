# FT-006 local server-backed image evidence

This is a single-computer validation workflow, not public hosting. SQLite
replaces proposed PostgreSQL **for this checkpoint only**: portable,
single-instance local persistence now; hosted database/migration work stays
open. No autonomous intervention, diagnosis, equipment control, or recovery.

Current evidence: the user completed connected clear panel-a analysis at
implementation 4b15365e20ea0b7cacf1ad2d695163bf439690ec, then reported identical
evidence/attempt/interpretation/usage in both tabs after restarting inference-disabled.
Read-only SQLite/ledger checks corroborate readable 180 kPa, 1938 ms,
438/339/777 tokens, recorded once. See state.md for the sanitized receipt.
This is user browser evidence, not agent-operated testing; mobile and connected
unreadable/refusal paths remain open. Do not repeat the completed analysis.

## Exact setup and startup (PowerShell)

From the clean committed project root, install into this project's environment
using verified Python 3.12.14. Do not recreate an installed venv unnecessarily:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
$bootstrap = 'C:\Users\surya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $bootstrap -m venv .venv
& .venv\Scripts\python.exe -m pip install -r requirements-backend.txt
& .venv\Scripts\python.exe -m pip check
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

Direct inputs are requirements-backend.in; requirements-backend.txt freezes
the compatible tested set. FastAPI 0.162.0, Uvicorn 0.54.0, Pillow 13.0.0,
HTTPX 0.28.1. The pinned Starlette TestClient warns that its HTTPX adapter is
deprecated; tests pass. No unrelated client migration was added. No other
project's database, credentials, services, or environment were reused.

Backend: http://127.0.0.1:8765/api/state. Windows denied port 8000; unused
8765 works. Use one worker, no reload: an OS-held lock prevents a second
instance and releases on process death. Keep the terminal open.

Frontend terminal (Node 22.12+, verified 22.14.0):

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd ci
npm.cmd run dev
```

- Commander: http://127.0.0.1:5173/?mode=connected&view=commander
- Operator in a second tab: http://127.0.0.1:5173/?mode=connected&view=operator
- Separate sample preview: http://127.0.0.1:5173/?mode=sample

Restart an existing Vite server to load the new /api proxy to loopback 8765.
No key enters the frontend. Both servers are loopback-only; mobile testing
means a phone-sized viewport on this computer, not access from another device.

## Evidence and local trust

Start creates one persisted simulated incident and fixed F-17 task: **not AI
planning**. Telemetry is simulated. Submit an image/report in Operator; both
views load the same server state. Upload alone never invokes a provider.
Analyze image is separate and disabled unless the backend opt-in is enabled.
Readings are validated model interpretations, not asset identity, diagnosis,
authorization, or recovery. Range 0..1000 is a synthetic workflow constraint,
not an industrial operating limit or proof of arbitrary analog-gauge accuracy.

PNG/JPEG limits: 2 MiB input and normalized output, 16..2048 per side,
1,048,576 pixels maximum, one frame, real MIME/format agreement. Pillow verifies
and loads pixels then reencodes RGB PNG, stripping metadata/trailing bytes and
flattening alpha onto white without exposing invisible RGB pixels. A claimed
fixture must match its committed SHA-256. User-upload/human-report provenance
stays distinct. Original filenames and filesystem paths are not accepted.

Private normalized images: `.local/workflow/images/<evidence UUID>.png`.
SQLite: `.local/workflow/workflow.sqlite3` plus WAL/SHM files. Only scoped
`/api/evidence/<UUID>/image` serves bytes after a database lookup. No private
images, headers, keys, raw provider bodies/reasoning, or personal uploads enter
Git or application logs. Access logging is disabled in the startup command.

There is **no authentication, user isolation, TLS, or public-host hardening**.
Trusted local users/processes can access this instance and known IDs; UUIDs
are lookup scopes, not authentication. Host/Origin checks, a local-client
header, no CORS, no-store responses, and loopback binding reduce accidental
exposure, not production security. Vite explicitly denies .local, .venv,
.git, environment files, and certificate/private-key paths. Do not expose these dev servers publicly or
upload sensitive field evidence. Vite source access is not private storage.

## Reliability and accounting

UUID idempotency keys bind each mutation to its content. Revision checks
reject stale writes (409); exact duplicates return prior IDs, conflicting
duplicates fail. An evidence ID has at most one analysis reservation, even
with different click keys. Reissuing marks earlier pending evidence stale.

The attempt/reservation is committed before queuing. One worker serializes
application analysis/accounting; no SQLite transaction spans the provider
request. Shared strict image/envelope validation and transport retain a 2048
output-token cap, 60-second socket-operation timeout, 256 KiB response bound,
and no redirect/retry/fallback. This is not a hard whole-process deadline.

Metadata and partial usage survive validation failure. A SQLite receipt
outbox is committed before recording through the existing idempotent ledger.
Its lock also prevents external standalone-process ledger races. Accounting
failure retains the receipt and reports failed accounting, never a retry.
On restart, pending analysis becomes uncertain. Durable interpretations and
receipts survive; existing ledger entries are reused, or a missing receipt
records unknown usage/transport completion. Reconciliation can retry recording
only, never inference. The same evidence cannot be analyzed again after
failure/interruption. Review before requesting another observation.

Limitations: no watchdog, multi-instance queue, quota, orphan-image cleanup,
backup, or database migrations. Image-file/SQLite power-failure atomicity is
not guaranteed; a missing image can coexist with metadata and is shown as
unavailable. Unknown usage is not zero, and totals are not billing.

Polling is one GET at a time, 5-second timeout, 2 seconds between reads,
900 reads maximum per refresh cycle; it pauses after 3 consecutive errors.
Refresh starts a new cycle. Mutations are never automatically retried; an
interrupted response may have committed. Both views expose pending, accepted,
unreadable, refused, failed, stale, uncertain, and per-call token/usage states.

## Offline checks

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
& .venv\Scripts\python.exe -m unittest discover -s tests -v
& .venv\Scripts\python.exe -m pip check
Set-Location frontend
npm.cmd run test
npm.cmd run build
```

API tests use fake transport and temporary data/images/ledger. Two ASGI clients
and a fresh application instance verify shared state/restart persistence,
not an actual two-tab browser journey. Standalone probes are unchanged.
Browser inventory was empty; iab opening failed. No desktop/mobile screenshots
were captured or inspected. Ignored `.local/visual/ft-006/verification.json`
records that blocker. No real inference ran in this coding checkpoint.

## Reference one-call procedure (clear panel-a completed; do not repeat automatically)

Stop the disabled backend. From a clean committed checkout, in your Windows
terminal only, copy an existing environment key without printing/pasting it:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) {
    $env:NEBIUS_API_KEY = [Environment]::GetEnvironmentVariable('NEBIUS_API_KEY', 'User')
}
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) { throw 'missing_credentials; stop' }
$env:FAULTTRACE_ALLOW_INFERENCE = '1'
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

1. Open the Commander and Operator URLs in two tabs. Start one simulated
   incident. Verify matching task ID/revision via /api/state in both tabs.
2. Submit committed panel-a in Operator. Confirm both views show the same
   evidence ID, with no analysis yet.
3. After separate live authorization, click Analyze image **once**. Review
   the actual interpretation/receipt and known usage in both tabs. Independently
   expect readable 180 kPa for this fixture; never substitute that expectation
   for the returned result. If failed/uncertain, stop without an extra call.
4. Stop the backend; set `$env:FAULTTRACE_ALLOW_INFERENCE = '0'`; run the
   same uvicorn command. Verify the same incident/task/evidence/attempt ID
   survives without another provider request. Check offline ledger:

```powershell
& .venv\Scripts\python.exe -m faulttrace.probe --ledger-summary
```

5. Save sanitized receipts and actual desktop/mobile screenshots under ignored
   `.local/visual/ft-006/`. Inspect token completeness separately. A panel-b
   connected test is a later separately scoped call; do not repeat/import the
   existing standalone vision successes as part of this procedure.
