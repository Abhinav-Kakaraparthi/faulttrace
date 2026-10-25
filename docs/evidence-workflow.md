# Local observation planning and server-backed image evidence

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

The /api proxy to loopback 8765 is unchanged. No Vite restart is required by FT-007.
No key enters the frontend. Both servers are loopback-only; mobile testing
means a phone-sized viewport on this computer, not access from another device.

## Evidence and local trust

Start creates one persisted simulated incident without assigning a task.
Choose next observation explicitly requests a validated text proposal; see
FT-007 below. Legacy FT-006 fixed tasks retain their original provenance.
Telemetry is simulated. Submit an image/report in Operator; both
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

Limitations: no watchdog, multi-instance queue, account-wide quota, orphan-image cleanup,
backup, or hosted migration framework. FT-007 has additive local schema updates.
Image-file/SQLite power-failure atomicity is
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
Browser inventory was empty; iab opening failed in FT-006 and FT-007. No
agent desktop/mobile screenshots were captured or inspected. Ignored
`.local/visual/ft-007/verification.json` records the latest blocker/code hashes.
No real inference ran in the FT-007 coding checkpoint.

## FT-007 planner contract and later bounded verification

Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`; endpoint:
`https://api.tokenfactory.nebius.com/v1/chat/completions`. Existing bounded
transport: 2048 output tokens, 256 KiB response, 60-second socket-operation
timeout, no retries, fallback generations or redirects. Image inference is
separate. Both operations use the same existing opt-in, worker and ledger.

`POST /api/planning` accepts exactly `{ "revision": <incident revision> }`,
local-client header and UUID Idempotency-Key. Context is snapshotted before
reserving/queuing; its revision follows every task/evidence transition. Budget
is four reserved calls per single persisted incident, including failed and
interrupted turns. One attempt per context revision is intentional: repeated
clicks reuse even failed results, not another request. New evidence/context is
required; no automatic retry or reset exists. Pending uploaded images block
planning until explicitly analyzed or an operator report supersedes them.

Model JSON fields are exactly `kind`, `asset_id`, `capability`,
`context_revision`, `evidence_refs`, `explanation_code`. Allowed triples:
- REQUEST_OBSERVATION / F-17 / READ_LOCAL_DP
- REQUEST_OBSERVATION / V-08 / OBSERVE_POSITION
- ESCALATE / HUMAN / HUMAN_INVESTIGATION

References are 1..8 distinct existing references in the bounded context.
Explanation codes select short application text: evidence_gap,
unreadable_evidence, clarify_conflict, human_review. Codes referring to
unreadability or conflicts require corresponding context; no free-form model instructions or
reasoning is persisted. Strict original smoke-test validation is unchanged.
Raw uploaded notes are not supported by this API and extra fields fail.

Context contains simulated 86 m3/h flow, 184 kPa DP and 72% feedback, at most
4 recent task records and 16 recent observations, provenance, readability,
conflicts and omitted-record count. Full evidence history remains persisted.
Fixture filenames/answer keys, hidden fault labels and private images never
enter the text payload. Synthetic-fixture provenance labels are retained. Image-derived readings enter only as recorded interpretations,
not ground truth or asset identity. V-08 reports accept open / intermediate /
closed / cannot determine, plus access/equipment refusal; they remain human
reports. There is no valve movement, diagnosis, closure or recovery engine.

SQLite stores the bounded context, sanitized receipts, validated proposals,
fixed failure codes and resulting task IDs. Rejected raw output is discarded.
No transaction spans provider I/O. Available usage survives rejected/stale
proposals. Ledger persistence failure prevents task creation and retains the
receipt outbox. Restart marks unfinished planning uncertain, reconciles receipts
idempotently and never creates a task from an interrupted attempt or replays
inference. No hard overall deadline/watchdog is implemented.

**Manual restart after review, inference disabled first.** The coding agent did
not stop or restart your servers or mutate your actual workflow database. When
ready, use Ctrl+C in YOUR existing backend terminal; do not terminate arbitrary
Python processes. Then run (no installs needed for an existing environment):

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

This startup applies additive schema changes; it retains your existing
incident, fixed-task origin, private evidence and accounting. The earlier
backend is incompatible with the new frontend; a clear message asks for your
manual restart. Keep the already running frontend on 5173. If not running:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd run dev
```

Open Commander/Operator URLs above. Inspect 1440x900 and 390x844, keyboard focus,
view switching, disabled explanations, task access and history. No mock planner
is substituted when inference is disabled. Screenshots/visual approval remain
pending because the agent has no browser surface.

**Proposed later live verification: at most TWO text calls, no image calls.**
Only after separate authorization and clean committed checkout, manually stop
your disabled backend, ensure its process environment has the key (never paste
it into the UI), then run:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) {
    $env:NEBIUS_API_KEY = [Environment]::GetEnvironmentVariable('NEBIUS_API_KEY', 'User')
}
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) { throw 'missing_credentials; stop' }
$env:FAULTTRACE_ALLOW_INFERENCE = '1'
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

1. Use the retained incident/evidence (do not repeat its clear-image analysis).
   On a fresh store only, start an incident and verify no automatic task.
   Confirm at least two remaining turns and no blocking task.
2. Click Choose next observation ONCE. Inspect the real proposal, context
   revision, task template or escalation, receipt/usage and matching second-tab
   state. If rejected, failed, uncertain or escalated, stop; no retry.
3. If a task exists, submit one honest simulated observation/refusal. For F-17,
   use Report unreadable/cannot access, with no new image analysis. For V-08,
   submit a human position report or cannot determine. No equipment operation.
   Confirm the new evidence/provenance and revision in both tabs.
4. Click Choose next observation ONCE more, then stop regardless of result.
   Verify the second context includes that evidence and the remaining budget
   decreased by two overall. A repeated choice is possible and must be reported
   honestly, not replaced with an expected adaptive result. Check inference
   validation separately from accounting completeness. Save sanitized evidence.
5. Manually restart inference-disabled with the earlier command. Read offline
   accounting without importing/replaying anything:

```powershell
& .venv\Scripts\python.exe -m faulttrace.probe --ledger-summary
```

No further provider calls follow from this procedure. The application hard cap
is four planning turns, but this proposed verification is limited to two.
