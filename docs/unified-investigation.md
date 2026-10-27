# FT-012: shared investigation-to-recovery journey

Offline implementation verified; live adaptive behavior and browser acceptance
remain open. No provider requests were made. Historical runs keep their original
legacy mode, reports, images and receipts. New **Start restriction-to-recovery
simulation** uses `/api/investigations`, one incident and one task-evidence stream.

## Authority and evidence

Commander explicitly requests planning. A validated registered observation creates
the Operator task. Photo analysis remains an unverified model claim. Operator
enters an independent identity, measurement type, reading/unit or position; every
answer starts blank. A confirmation or dispute references its source photo and
preserves both records. Independent field reports without photographs are also
supported. Human-reported identity is not image-verified or authenticated identity.

Each human report has one canonical `evidence-<id>` reference used by planner
context, deterministic assessment, approval and both views. Original units remain
stored; compatible human DP reports in Pa/kPa/MPa/bar/psi are normalized to kPa for
the existing fixture policy. Unsupported types/units need clarification. Model
numbers are never copied into human reports or promoted into policy measurements.
Pressure is not DP. A handle photograph cannot verify internal valve position;
V-08 needs an independent human position report. MAXIMATOR is not F-17 DP evidence.

The existing 120-second freshness, 8 kPa corroboration, restriction/recovery bands,
alarm checks, five samples / 40-second window and relapse behavior are unchanged.
New reports also require wall-clock freshness; linked photos must be fresh,
current and independently reviewed. Numeric/type/unit/identity disagreement,
dispute, unreadability, inaccessible equipment, unreviewed photos or stale evidence
block approval. Latest reports govern freshness; conflicts/refusals remain in
history and are not silently cleared by another report. There is no conflict or
access-clearance workflow in this checkpoint: clarify/escalate rather than force
success. Untasked legacy observation submission cannot bypass this new mode.

Commander approves the exact current revision; Operator acknowledges the registered
simulated replacement. Completion is maintenance status only. Only independent
post-action samples establish recovery. Existing four-turn planning budgets,
idempotency, stale-result rejection, interruption accounting and inference opt-in
remain enforced. Hidden simulator outcomes/answer keys are excluded from context.

## Offline evidence and visual limits

175 backend tests pass with external Python networking forbidden and zero forbidden
attempts, including 13 new unified cases. 51 frontend static tests, TypeScript and
production build pass. Cases cover shared references, independently entered
reports/disputes, pressure-vs-DP, identity/unit/type conflicts, stale evidence,
refusals/escalation, provider failures/accounting, duplicates, interruption,
persistence, ineffective correction and relapse. Initial test-double metadata and
microsecond timestamp-rounding defects were corrected without weakening checks.
Scripted choices demonstrate application policy, not live model reasoning/accuracy.

Browser inventory is empty and in-app opening fails. Desktop/390x844, keyboard,
file selection, dialog focus/scroll and complete visual interaction remain open;
no screenshots or camera pass are claimed. Static tests are not browser evidence.
Implementation `b8fc87771c4906f5477dd515ab14407604b6764f` passed
[hosted CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40534982605).
The isolated 5182/8782 preview is running with fresh ignored data under
`.local/visual/ft012-5297706b4e5a41a09f344ca6c62a1f31/data`.
Both route HTTP checks pass; browser access remains unavailable.

## Isolated review: zero provider requests

Visual acceptance scenarios for current application SHA `17b7ffeb` are prepared
separately on ports 5190..5204, with inference disabled while served. Start with
http://127.0.0.1:5190/commander and http://127.0.0.1:5190/operator. The complete
numbered checklist and scenario URL pairs are in ignored
`.local/visual/acceptance-ee8278bc794b4085a89d545564345c14/manual-review.md`.
Seeded results are offline test output; wall clocks are paused test fixtures,
not proof of production freshness. No browser/camera/interaction pass is claimed.

The development harness injects deterministic doubles, records **OFFLINE TEST
OUTPUT**, uses a new ignored directory and separate test-only ledger, and ignores
real provider credentials. No new dependency or runtime architecture is required.
Only the exact committed clear synthetic panel has a scripted photo result;
unknown/real photographs abstain. Usage remains unknown, not fake consumption.
This harness is separate from the production factory and must not be deployed.

Backend terminal (verify both ports are free; do not stop old servers):

```powershell
Set-Location C:\Users\surya\Projects\faulttrace
if (Get-NetTCPConnection -State Listen -LocalPort 8782,5182 -ErrorAction SilentlyContinue) { throw 'Review ports occupied; preserve the existing servers' }
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
$env:FAULTTRACE_PREVIEW_ORIGIN = 'http://127.0.0.1:5182'
$env:FAULTTRACE_DEMO_DATA_DIR = Join-Path (Get-Location) ('.local/visual/ft012-' + [guid]::NewGuid().ToString('N') + '/data')
.\.venv\Scripts\python.exe -m uvicorn tools.offline_investigation_demo:create_demo --factory --host 127.0.0.1 --port 8782 --no-access-log
```

Frontend terminal (from the project root):

```powershell
@'
export default { server: { host: '127.0.0.1', port: 5182, strictPort: true,
  fs: { strict: true, deny: ['.env', '.env.*', '*.{crt,pem}', '**/.git/**', '**/.local/**', '**/.venv/**'] },
  proxy: { '/api': { target: 'http://127.0.0.1:8782', changeOrigin: true } } } };
'@ | Set-Content -Encoding utf8 .local/visual/ft012-preview.config.mjs
Set-Location frontend
npm run dev -- --config ../.local/visual/ft012-preview.config.mjs --port 5182
```

Open http://127.0.0.1:5182/commander and http://127.0.0.1:5182/operator.
The harness enables **only its doubles**, even though production inference stays
disabled. A persistent test-output label distinguishes this from live NVIDIA.

1. Commander starts the simulation and chooses the first observation.
2. Operator uploads `fixtures/image-evidence/panel-a.png` through the ordinary
   file input, explicitly analyzes the collected photo, then independently
   transcribes/confirms its identity, type, unit and reading. These are synthetic
   rehearsal reports, not real equipment observations. Do not use the separate
   legacy fixture-analysis controls for this photographic-contract walkthrough.
3. Commander chooses the next observation; Operator submits an independent V-08
   position report. Inspect the deterministic assessment and shared references.
4. Within the 120-second freshness window, Commander explicitly approves the
   eligible revision; Operator completes the simulated assignment. Commander
   advances five samples. Recovery must progress through observation before
   verification. Competing or incompatible reports must keep approval blocked.
5. Review both routes at 1440x900 and 390x844; exercise Tab/Shift+Tab/Enter/Space,
   labels, refusal/dispute, Inspect, Escape/focus return and image scrolling.

If reports age out, preserve that run; never reset its history or bypass policy.
Use a fresh isolated review for a new complete rehearsal. Old completed previews
on 5180/8780 and photographic collection on 5181/8781 are not restarted.

## Proposed later live walkthrough (not authorized or executed here)

First verify credited Nebius balance and independently review the synthetic
reference. On a new isolated **production-factory** run, seek separate authorization
for at most two explicit planning calls and one clear synthetic photo-analysis
call, with existing per-call limits, opt-in, receipts and ledger. Human reports
are entered independently between planning calls. No retries/fallbacks or image
replay. If an unavailable alternative, abstention, rejection, dispute or budget
constraint prevents the sequence, retain evidence and stop/escalate; do not force
F-17 or a successful recovery. No general photographic accuracy is established.
