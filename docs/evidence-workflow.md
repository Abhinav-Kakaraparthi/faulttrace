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
Browser inventory was empty; iab opening failed in FT-006, FT-007 and FT-007A. No
agent desktop/mobile screenshots were captured or inspected. Ignored
`.local/visual/ft-007b/verification.json` records the latest blocker/code hashes.
No real inference ran in FT-007, FT-007A or FT-007B coding checkpoints.

## FT-007 / FT-007A planner contract and bounded verification

Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`; endpoint:
`https://api.tokenfactory.nebius.com/v1/chat/completions`. Existing bounded
transport: 2048 output tokens, 256 KiB response, 60-second socket-operation
timeout, no retries, fallback generations or redirects. Image inference is
separate. Both operations use the same existing opt-in, worker and ledger.

FT-007A adds `response_format` with type `json_schema` and a `json_schema`
wrapper containing name, strict=true and schema. Constraints include required
fields, additionalProperties=false, typed/enumerated fields,
exact context revision, min/max evidence
references drawn from this context, and context-supported explanation codes.
Following the user diagnostic below, uniqueItems is omitted only from the
provider schema; duplicate references remain rejected by application validation.
Following structural diagnostic 81d8d4d2-0d3c-4a36-9d81-a67b3acf8211,
root anyOf was also removed. That revision used one flat six-required-field
object; allowed kind/asset/capability combinations remain enforced by application
validation. Its three-field response was rejected without filling fields;
328/1125/1453 usage was retained. Matching partial branch keys implicate
composition compatibility, not a proven provider bug. Other schema support
remains unverified until a separately authorized live checkpoint.
Application-side validation remains independent and mandatory.

Official sources checked for FT-007A:
- [Nebius structured output documentation](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
  documents json_schema, the named strict wrapper, JSON Schema compliance and
  checking a model card's JSON mode tag. Platform support is not model proof.
- [Nebius Nano cookbook](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/nemotron3-nano-30b.md)
  advertises structured output for Nano, using lowercased model ID and a
  regional endpoint. This is model-family documentation, not an authenticated
  verification of our exact ID/endpoint/schema subset. Public Playground text
  did not expose a verifiable exact-ID JSON-mode tag. No inference/model-list
  request was made. Unsupported schema requests fail without fallback/retry.

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
An unresolved cannot-access human report now blocks further observation requests
for that asset. The bounded unavailable_assets context summary is derived from
full incident history, so reports outside the recent 16 are not forgotten.
Instructions require an available alternative or escalation; application code
rejects a violation with planner_asset_unavailable, preserving available usage
and creating no task. No automatic repair/retry. There is no access-clearance
workflow: reopening, later reports or images do not silently clear the block.
This prospective rule does not cancel/relabel existing tasks or accepted attempts.
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

**FT-007A next live test is currently blocked.** Existing revision 1 already
has rejected attempt 13d345c9-3480-45bc-a4c6-c2260b319300. Three turns remain,
but a new key/restart/fixed payload cannot produce a second call on that
context. The original receipt and evidence must stay intact. No output can be
reconstructed from invalid_proposal. Do not reuse the earlier two-call plan.

Bounded proposal after review and separate authorization:

1. Manually restart inference-disabled using the command above; review the
   disabled button, visible reason and planning history in both views. The
   coding agent has not touched your servers. Inspect desktop/mobile/keyboard.
2. Determine whether a genuine new F-17 reassessment is needed. The existing
   registered `POST /api/tasks/{id}/reopen` accepts the current task revision,
   local-client header and fresh UUID Idempotency-Key. It creates an awaiting
   observation, not new evidence, and blocks planning until that task is
   answered. This is NOT a retry button. Use only to perform an actual new
   reassessment, never merely to advance context revision.
3. Submit new truthful evidence or a truthful inability/unreadability report
   through Operator. Do not falsely label the existing clear fixture unreadable,
   claim an access failure just to retry, or replay its accepted analysis. If
   fresh image interpretation is genuinely necessary, that is an additional
   separately authorized vision call, not included in this one-planner-call
   proposal. If no genuine new observation exists, STOP: corrected live
   verification remains blocked; do not reset/copy/edit history or bypass policy.
4. Once truthful new evidence is accepted/reported and both views show a new
   unattempted context with no blocking task, manually restart opt-in only
   after live authorization. Keep the existing credential in the backend
   environment; never paste it into the UI. Commands (not run in FT-007A):

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) {
    $env:NEBIUS_API_KEY = [Environment]::GetEnvironmentVariable('NEBIUS_API_KEY', 'User')
}
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) { throw 'missing_credentials; stop' }
$env:FAULTTRACE_ALLOW_INFERENCE = '1'
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log --log-level warning
```

5. Click Choose next observation ONCE. Stop regardless of result; no repair,
   retries, schema downgrade, fallback model or token increase. Check the exact
   schema/model compatibility, fixed validation diagnostic, policy/task result
   and accounting separately. Confirm this attempt occurs once, the original
   rejection/evidence remain unchanged, and budget decreases from 3 to 2 if no
   other planning turns have occurred. Manually restore inference-disabled.

Offline accounting only (no import/replay):

```powershell
& .venv\Scripts\python.exe -m faulttrace.probe --ledger-summary
```

Fixed new diagnostic codes: planner_field_shape, planner_field_type,
planner_revision_mismatch, planner_reference_count, planner_unknown_reference,
planner_duplicate_reference, planner_invalid_combination,
planner_explanation_unsupported. Existing JSON/envelope/refusal/truncation
codes remain separate; stale completion still uses stale_context. Historical
invalid_proposal remains readable and is never retrospectively relabeled.

## FT-007B: safe HTTP diagnostics and proposed isolated test

New receipts contain nullable http_status and http_error_category. Categories
describe status, not provider cause: 400 http_bad_request; 401 http_unauthorized;
402 http_payment_required; 403 http_forbidden; 404 http_not_found;
422 http_unprocessable_entity; 429 http_rate_limited; 5xx http_server_error.
Redirects use http_redirect (never followed); other valid statuses use
http_other_error; unavailable/invalid status uses http_unknown. No retry follows
any category. Historical absent fields stay absent in storage and unknown in UI,
preserving old duplicate identity. Error bodies and headers are not read at all,
including malformed/oversized bodies; no parameter name or body usage is inferred.
Parsed normal-response usage still survives completion/proposal rejection.

Schema review against the [official structured output guide](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
and [chat API reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion):
no confirmed incompatibility found. The named strict wrapper matches the guide.
At the FT-007B review, exact Nano support and anyOf/uniqueItems/array-bound support were unverified;
unsupported subset, authentication, account, route and service failures are
possible explanations, not historical findings. The discarded HTTP status/body
cannot distinguish them. Model, schema, prompt, output cap, retry policy,
context history and per-incident budget are unchanged by FT-007B.

## Standalone flat-schema compatibility evidence

Implementation cdb9f4277127feb983eb246dad3190d13ca2cdee passed standalone
verification for one saved context: ledger contains attempt
87f5704f-d2ca-46ba-9967-7334363ac419 exactly once, timestamp
2026-10-25T18:53:19.337482+00:00, response
chatcmpl-fd86af00-2a1a-4da7-9ef6-134fb58b0778, exact Nano model, 3375 ms,
valid 328/618/946 usage, validation passed with no diagnostics. The user supplied
the six-field/no-extra F-17/READ_LOCAL_DP proposal, context revision 1,
evidence_refs [telemetry-001], explanation_code evidence_gap. This standalone
call created no workflow task. The later connected API audit below verifies
task creation and updated context delivery, but not useful adaptive decisions;
FT-007 remains PARTIAL.

Failures stay intact: the uniqueItems diagnostic implicated that keyword;
the later three-field response matched partial anyOf branch keys and implicated
composition compatibility. Neither establishes a provider implementation bug
or recovers older discarded output. That historical flat schema required six
provider fields. Current action-ID selection below uses four wire fields and
retains six internal fields; independent application policy remains strict.

Accounting checked read-only: 13 ledger attempts, 9 complete known contributors,
3249 input / 6524 output / 9773 total, four missing-usage attempts and zero
partial/invalid/inconsistent. Separate manual success 155/112/267; cross-record
known 3404/6636/10040, matching expectations. No import or replay.

## Historical connected API procedure (executed by user)

The user executed this procedure against 2bb97c6248450a9814cc9e503d57398e10a004ad;
read-only audit results follow. Commands are historical: DO NOT rerun them in
this checkpoint. Their implementation guard deliberately pins the earlier
provider-compatible code, not the new refusal-aware policy. No new live test
is authorized here. This procedure used a new isolated simulation,
not a retry/reset of prior incidents. At most TWO explicit planning POSTs,
separated by a simulated operator access refusal. No image upload/analysis or
replay. Stop after a failed, uncertain, escalated or accounting-failed first
result; never create a fake response just to force the second call. A repeated
model choice is possible and must be reported honestly. The API test does not
prove the two-tab browser journey or that the new evidence caused a model choice.

**Server terminal:** existing environment/dependencies only. Use a verified-free
8877 and never-existing UUID directory; leave your 8765/5173 servers untouched.
The existing default ledger is shared. No key is printed or passed in argv.

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:/Users/surya/Projects/faulttrace'
if (git status --porcelain) { throw 'dirty_checkout; stop' }
git diff --quiet cdb9f4277127feb983eb246dad3190d13ca2cdee -- faulttrace
if ($LASTEXITCODE -ne 0) { throw 'unexpected_implementation; stop' }
if (Get-NetTCPConnection -LocalPort 8877 -State Listen -ErrorAction SilentlyContinue) { throw 'port_in_use; stop' }
$env:FAULTTRACE_VERIFICATION_DIR = Join-Path (Get-Location) ('.local/verification/ft007-connected-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $env:FAULTTRACE_VERIFICATION_DIR) { throw 'directory_exists; stop' }
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) { $env:NEBIUS_API_KEY = [Environment]::GetEnvironmentVariable('NEBIUS_API_KEY', 'User') }
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) { throw 'missing_credentials; stop' }
$env:FAULTTRACE_ALLOW_INFERENCE = '1'
Write-Output "NEW ISOLATED SIMULATION: $env:FAULTTRACE_VERIFICATION_DIR"
& ./.venv/Scripts/python.exe -c "import os, uvicorn; from faulttrace.workflow.api import create_app; uvicorn.run(create_app(directory=os.environ['FAULTTRACE_VERIFICATION_DIR']), host='127.0.0.1', port=8877, access_log=False, log_level='warning')"
```

**Client terminal:** paste ONCE. This contains exactly two planning POSTs and
only GET polling. A timeout may have committed: stop without resending.
The refusal is explicitly simulated, not a real plant observation. The API
stores origin human-report within this simulated incident; no unsupported
notes/provenance fields are added. Keep that distinction in the evidence record.

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:/Users/surya/Projects/faulttrace'
$base = 'http://127.0.0.1:8877'
function New-LocalHeaders { @{ 'X-FaultTrace-Local'='1'; 'Idempotency-Key'=[guid]::NewGuid().ToString() } }
function Get-State { Invoke-RestMethod "$base/api/state" -TimeoutSec 10 }
function Wait-Plan([string]$id) {
    for ($poll=0; $poll -lt 45; $poll++) {
        $s = Get-State
        $p = @($s.planning | Where-Object { $_.id -eq $id })
        if ($p.Count -eq 1 -and $p[0].status -ne 'pending') { return $s }
        Start-Sleep -Seconds 2
    }
    throw 'pending_or_missing_reservation; stop without retry'
}
$s = Get-State
if ($s.incident -or @($s.planning).Count -or @($s.tasks).Count -or @($s.evidence).Count) { throw 'not_a_fresh_run; stop' }
Invoke-RestMethod "$base/api/incidents" -Method Post -ContentType 'application/json' -Body '{}' -Headers (New-LocalHeaders) -TimeoutSec 10
$s = Get-State
if ($s.task -or $s.planning_remaining -ne 4) { throw 'unexpected_initial_state; stop' }
# Explicit planning call 1.
$first = Invoke-RestMethod "$base/api/planning" -Method Post -ContentType 'application/json' -Body (@{revision=$s.incident.revision} | ConvertTo-Json -Compress) -Headers (New-LocalHeaders) -TimeoutSec 10
$s = Wait-Plan $first.attempt_id
$p1 = @($s.planning | Where-Object { $_.id -eq $first.attempt_id })[0]
$p1 | Select-Object id,status,task_id,proposal,receipt,error,accounting | ConvertTo-Json -Depth 8
if ($p1.status -ne 'accepted' -or $p1.accounting -notin @('recorded','duplicate') -or -not $s.task -or $p1.task_id -ne $s.task.id) { throw 'stop_after_first_result; no second call' }
if (@($s.planning).Count -ne 1 -or $s.planning_remaining -ne 3 -or $s.task.status -ne 'awaiting') { throw 'unexpected_first_state; stop' }
$task = $s.task
$revisionBeforeReport = $s.incident.revision
Write-Output "SIMULATED OPERATOR REFUSAL for $($task.asset_id): access unavailable in this test scenario; NOT a real field observation."
$submitted = Invoke-RestMethod "$base/api/tasks/$($task.id)/reports" -Method Post -ContentType 'application/json' -Body (@{revision=$task.revision;report='cannot-access'} | ConvertTo-Json -Compress) -Headers (New-LocalHeaders) -TimeoutSec 10
$s = Get-State
$e = @($s.evidence | Where-Object { $_.id -eq $submitted.evidence_id })
if ($e.Count -ne 1 -or $e[0].origin -ne 'human-report' -or $e[0].status -ne 'refused' -or $e[0].report -ne 'cannot-access') { throw 'unexpected_report; stop' }
if ($s.incident.revision -le $revisionBeforeReport -or @($s.planning).Count -ne 1 -or $s.planning_remaining -ne 3) { throw 'unexpected_context_or_budget; stop' }
# Explicit planning call 2; updated context, never replay call 1.
$second = Invoke-RestMethod "$base/api/planning" -Method Post -ContentType 'application/json' -Body (@{revision=$s.incident.revision} | ConvertTo-Json -Compress) -Headers (New-LocalHeaders) -TimeoutSec 10
$s = Wait-Plan $second.attempt_id
$p2 = @($s.planning | Where-Object { $_.id -eq $second.attempt_id })[0]
$p2 | Select-Object id,status,task_id,proposal,receipt,error,accounting | ConvertTo-Json -Depth 8
if (@($s.planning).Count -ne 2 -or $s.planning_remaining -ne 2) { throw 'unexpected_final_budget; stop' }
Write-Output 'STOP: no third planning call, retries, or image-analysis requests.'
& ./.venv/Scripts/python.exe -m faulttrace.probe --ledger-summary
```

After the client finishes (or stops early), stop only this new server with Ctrl+C
in its own terminal. Preserve its directory and all prior runs. In that server
terminal, the directory environment variable remains available for this optional
read-only context/ledger audit, which makes no provider call:

```powershell
@'
from contextlib import closing
from pathlib import Path
import json, os, sqlite3
from faulttrace.ledger import DEFAULT_LEDGER, load
path = Path(os.environ['FAULTTRACE_VERIFICATION_DIR']) / 'workflow.sqlite3'
with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    rows = list(db.execute('SELECT id,status,context,task_id FROM planning ORDER BY rowid'))
receipts = load(DEFAULT_LEDGER)
out = []
for row in rows:
    context = json.loads(row['context'])
    out.append({'attempt_id': row['id'], 'status': row['status'], 'task_id': row['task_id'],
                'context_revision': context['context_revision'],
                'remaining_at_reservation': context['remaining_planning_calls'],
                'observations': [{k: o[k] for k in ('evidence_ref','origin','status','report')} for o in context['observations']],
                'ledger_occurrences': sum(r['attempt_id'] == row['id'] for r in receipts)})
print(json.dumps(out, indent=2))
'@ | & ./.venv/Scripts/python.exe -
```

If two calls occurred, independently check first context had no observations,
second context contained the simulated refusal/reference, remaining budget went
4 -> 3 -> 2, and each attempt appears once in the ledger. Record actual choices,
task IDs, policy result, usage completeness and persistence separately; do not
substitute expected choices or claim causation/adaptive reasoning from context
inclusion alone. No existing run is reset or resumed by this procedure.

## Connected evidence and refusal-aware limitation

Read-only audit of incident 8654a8a2-ff58-4344-a1c5-bd9d60c05a2c in
`.local/verification/ft007-connected-8f8673e87da9431cb3f9fce92908529e` found
two accepted planning attempts, each exactly once in SQLite and the ledger;
both receipts match, validate passed and report valid usage/ledger recorded.

| Attempt | Created task | Context revision | Input/output/total | Latency |
| --- | --- | ---: | --- | ---: |
| 5cb5ee1d-1845-47cf-a8b9-01714c6d9b47 | 45a54498-2c17-463a-bc27-b996381b8e85 | 1 | 328/866/1194 | 10390 ms |
| 75d1d983-4afb-4b98-ad75-8dedab22cae6 | 8db8b2c2-fbd9-42a1-8d7f-48a256e9e105 | 3 | 508/1280/1788 | 10110 ms |

Both requested F-17/READ_LOCAL_DP. The first context had no observations. The
simulated cannot-access human report bcd5802e-15ed-49e7-af24-14617ee637ff was
stored as refused for the first task and included in the second context. The
second proposal cited that reference but still repeated F-17. This verifies
provider/validator/task persistence and context update through the API, not
useful handling of refusal, a real field observation or browser verification.
Current incident revision is 4, first task needs_evidence, second awaiting,
two turns left. The fix preserves those historical records and pending task.

The new offline-tested policy described above rejects a future same-asset
request while cannot-access is unresolved, allowing V-08 or human escalation.
It is not live-verified. FT-007 remains PARTIAL. No inference, replay/import,
database reset, existing-server restart or new live test occurred here.

## Current offline correction: registered action selection

The provider no longer independently selects kind, asset_id and capability.
Its flat JSON schema requires exactly action_id, context_revision, evidence_refs
and explanation_code, with additionalProperties=false, no anyOf/uniqueItems.
The action enum and prompt catalog derive from application observation templates
and availability policy, with human escalation always retained:

- OBSERVE_F-17_READ_LOCAL_DP -> REQUEST_OBSERVATION / F-17 / READ_LOCAL_DP.
- OBSERVE_V-08_OBSERVE_POSITION -> REQUEST_OBSERVATION / V-08 / OBSERVE_POSITION.
- ESCALATE_HUMAN_INVESTIGATION -> ESCALATE / HUMAN / HUMAN_INVESTIGATION.

Inaccessible observations are omitted; selecting a registered but unavailable
ID still fails planner_asset_unavailable, and invented IDs fail
planner_unknown_action. validate_action_plan maps the exact four-field object
to the existing internal six-field proposal and applies shared strict policy.
The legacy validate_plan adapter validates internal six-field completions only;
it must not be used to validate the new provider payload. Historical procedures
above describe prior executions, not authorization to replay them.

Read-only ledger audit confirmed failed attempt
d4430228-f580-4175-94ca-09fc667f0707 once, planner_invalid_combination,
valid 578/956/1534 usage. Its discarded fields are unknown. No response was
recovered, imported or replayed. New contract compatibility and useful
refusal-aware live choices remain unverified. All 94 backend tests and 10
frontend tests pass; type/build passes. No live call or server operations.
FT-007 remains PARTIAL; see state.md for current accounting and next action.
