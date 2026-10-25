# FT-008: simulated restriction-to-recovery journey

FT-009A workspaces: open `/commander` to review evidence, approve correction and
advance verification; open `/operator` to submit observations and acknowledge
approved simulated completion. Both share the preserved server run. Old connected
query URLs route to these pages. Operator has no planning/creation/approval/clock
controls. Evidence scopes and the separate model/recovery integration gap are
explained in [architecture](architecture.md). Existing 5180 preview needs no
backend restart. No route separation is claimed as server role authorization.

One synthetic F-17 restriction fixture, not a plant operating procedure or live
AI demonstration. It uses the existing local FastAPI/SQLite app and both React
views. Start requires an empty run; existing incident histories cannot be
repurposed. No provider call is needed. The optional NVIDIA observation planner
retains its original opt-in, reservations, validation, accounting and four turns;
it cannot propose or authorize the separate correction action.

## FT-008A review of the preserved completed run

The user reports completing the journey in both views (180 kPa, V-08 intermediate,
approval, simulated replacement, five qualifying samples, recovery verified).
Read-only API state corroborates the stored outcome; this is not agent browser
verification. Refresh the existing http://127.0.0.1:5180/?mode=connected preview;
do not create a new run or repeat the correction to inspect FT-008A.

The outcome leads both views. Journey evidence includes the two human reports
and stored simulator samples; image/planner-task evidence is a separate scoped
record, not missing journey evidence. Approval references, telemetry rows,
fixture rules, provenance and wall-clock audit history remain expandable.
Completed-run planning is history-only. Measurement timestamps use the stepped
simulation clock; audit times are wall-clock UTC. A later optional simulation
step can change recovery status, so leave the completed run unchanged for review.

The pasted blanks were not reproduced in source data or pre-change static React
markup: all three approval references and six rows were populated. No browser
rendering claim or root cause for the paste is established. Six new static
markup regressions bring frontend tests to 18; type/build pass. Actual desktop,
mobile, keyboard and expanded-table/reference visibility still require browser
review: no browser surfaces are available, and in-app browser creation failed.

## Start a different isolated run only when needed (PowerShell)

Use the installed environments; no new dependencies. Check that 8780 and 5180
are free. If occupied, leave their processes alone. These commands start an
additional isolated run; they do not restart the existing 8765/5173 servers.

Backend terminal, from the project root:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
$env:FAULTTRACE_DATA_DIR = Join-Path (Get-Location) ('.local/verification/ft008-' + [guid]::NewGuid().ToString('N'))
& .venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8780 --workers 1 --no-access-log --log-level warning
```

Frontend terminal:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd run dev -- --config vite.recovery.config.ts --port 5180
```

Open http://127.0.0.1:5180/?mode=connected. Use the top mode switch if needed.

1. Commander: choose **Start restriction-to-recovery simulation**. The older
   **Start simulated incident** control remains the observation-only workflow.
2. Open Operator. Inspect the committed synthetic panel, explicitly report
   readable **180 kPa**, then submit a simulated human V-08 **intermediate**
   position report. Neither report is image-verified; no model was called.
3. Commander: review the evidence-linked working diagnosis, alternatives and
   fixture constraints. Tick the approval statement and approve the simulated
   correction against the displayed revision.
4. Operator: **Complete simulated filter replacement**. This applies only a
   private simulator transition and records simulated maintenance completion.
   Recovery must still show observing, never success on completion alone.
5. Advance ten simulated seconds **five times** in either view. Five consecutive
   post-correction samples span forty simulated seconds. Independent sample
   policy now reports simulated operating recovery verified.
6. Inspect provenance, sample references and audit activity in both views.
   Refreshing does not advance time or rerun the correction. Reopening the same
   data directory retains the run; a new run uses a fresh directory, never reset.

Do not advance the clock between approval and execution: a new sample changes
the context revision and requires review/approval again. This is an intentional
stale-request guard. Declining/revoking approval also changes the revision.

## Declared fixture policy and limitations

All times, freshness and windows use the explicitly stepped simulation clock,
not wall-clock freshness. Base time comes from an injectable clock; there is no
background sampling or real-time wait. The UI exposes UTC sample timestamps.
The simulator advances by ten seconds per explicit request, at most 360 steps.

Before approval and execution, deterministic policy requires a current sample,
a provenance-bearing F-17 local report and a V-08 intermediate-position report.
Freshness is at most 120 simulated seconds; local pressure must be 170-195 kPa
and agree with telemetry within 8 kPa; flow 80-95 m3/h and valve feedback
65-80%. Wrong equipment, unreadable/inaccessible/indeterminate reports, unknown
provenance, inconsistent values, missing evidence or active observation/planning
block correction. Historical conflicting/refused reports are retained and block
approval; this checkpoint adds no conflict-clearance workflow. At most 32 local
reports are accepted. A fresh report can replace stale timing evidence but does
not erase conflicting sources.

The registered **Simulate F-17 filter replacement** action is separate from
planner proposals. Approval stores its revision and evidence references;
execution rechecks both current policy and approval. Idempotency keys prevent
repeated transitions, and stale revisions fail. This local human-approval UI is
not production authentication or real equipment authorization.

The recovery verifier receives measured samples and the execution boundary,
never private simulator outcome or model declarations. It requires at least
five consecutive, fresh post-action samples spanning forty seconds: flow
115-125 m3/h, pressure 25-40 kPa, valve feedback 65-80%, no active alarm. Gaps,
stale samples and out-of-band/alarmed samples cannot establish recovery. A later
relapse changes verified to failed; failure stays visible. Maintenance completion
remains recorded independently. These numbers are synthetic fixture constraints,
not industrial operating limits, root-cause proof or completed real maintenance.

Private outcome controls (effective/ineffective/relapse) exist only behind the
simulator boundary for offline tests. Public state and actual planner payloads
are allowlisted observations/telemetry, excluding private outcomes, hidden fault
labels, fixture answer keys and correction mechanics. Tests inject failure
outcomes directly; the HTTP API offers no outcome/answer-key controls.

## Verification

104 backend offline tests (10 new journey tests), 12 frontend tests, TypeScript,
production build, pip check and source/AST/diff checks. Backend tests cover the
complete API journey/two clients, real app lifecycle restart, duplicate/stale
requests, refusal, conflicting evidence, provenance, freshness, active-task
conflicts, ineffective correction and relapse, using temporary stores and no
provider calls. A socket guard verifies zero forbidden external connections.

Browser verification is blocked: computer-use inventory returned no apps or
browsers; in-app browser creation returned `Browser is not available: iab`.
No desktop/mobile, keyboard, contrast, overflow, loading/error visual pass or
screenshots are claimed. An isolated inference-disabled preview was launched
on 8780/5180 from the tested implementation; API, proxy, page and transformed
JourneyPanel module returned HTTP 200, with no incident yet created. Ignored
`.local/visual/ft-008/verification.json` records the browser blocker and source
hashes. HTTP checks do not establish browser rendering or interaction. Inspect 1440x900 and 390x844, keyboard focus/actions,
blocked/approved/observing/failed states and cross-tab updates before calling
this visually accepted. Build and API success are not browser verification.
No deployment, hosting, production control, paid inference or historical replay.
