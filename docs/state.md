# Checkpoint state

## Current: FT-011 photographic evidence informs planning (PARTIAL)

Implemented on `feat/ft-011-photo-planning` from verified clean
`86d8e76e463652aa7b3dc76ba248df1309141a12`. Photographs now contribute bounded,
validated model claims to saved planner context, with source/task association,
original readings/units, uncertainty, identity limits, compatibility, freshness and
human/model disagreements. Explicit Operator handoff releases an awaiting blocker
without accepting a measurement; Commander still explicitly chooses an action.
Accepted proposal citations and source-photo clarification links appear in the
respective workspaces. Refusal restrictions, budgets, revisions, accounting and
independent correction/recovery policy remain intact. No inference or restart.

159 backend tests pass with external networking forbidden (zero forbidden socket
attempts), including 11 new fake-provider integration cases; 45 frontend tests,
TypeScript and production build pass. Initial static citation test caught an
incorrect separator introduced during editing; corrected in source and rerun.
All source files remain below 500 lines. Historical preview public states and
stored image hashes match the earlier baseline; ledger byte hash is unchanged.
Core implementation: `fd5ec2e3492ffa5df5e8399dc93d95b060e4e136`. A subsequent scoped
presentation fix allows source-photo/handoff buttons to wrap within mobile panels;
45 frontend tests and type/build pass again. This is not browser verification.
Read-only preservation/check record: `.local/visual/ft011-offline/verification.json`.
Browser surfaces are absent and in-app opening fails: no desktop/mobile/keyboard
or live adaptive-planning pass is claimed, and no screenshots were captured.
Existing preview backends are untouched and have not loaded this implementation.

Next: isolated inference-disabled visual acceptance of photo assessment, explicit
handoff, accepted citations and source-photo clarification, then separately
authorize bounded live planner evaluation. [Exact commands and limitations](photo-planning.md).
Photographic numeric accuracy, integrated AI recovery, roles/authentication, CI
and hosting remain open; no submission gate is newly satisfied.

## FT-010 photographic observation analysis (PARTIAL)

First completed real-photo evaluation recorded read-only (2026-10-26): user-run
attempt 0d31fbe3-3fc2-49e2-b17f-888815ce8c41 occurs exactly once and its saved
receipt matches the ledger and private response. Tested implementation
5e41726b2d190eb4087d2cc5c0c31547bcebc0f1; model nvidia/Nemotron-3.5-Super-VL,
reasoning_effort=none, max_tokens=2048, no response_format. Completion/contract
validation passed: stop, 0 reported reasoning tokens, 1678 / 120 / 1798 usage,
2610 ms. Model returned readable pressure, 5000 psi, with no uncertainty codes.
Numeric interpretation FAILED the user-reported preliminary comparison (800–850
bar). Reviewer estimates are not calibrated ground truth; no error cause or
photographic accuracy is established. No diagnosis, task completion or correction
was authorized; the call created no workflow task. FT-010 remains PARTIAL.
Image, private diagnostic response, receipt and ledger are unchanged; no imports,
replay, inference, server operations or source/configuration edits in this audit.
Ledger known 10312 / 16823 / 27135 across 20 attempts; four retain missing usage.
Separate manual success 155 / 112 / 267; cross-record known 10467 / 16935 / 27402.
Prior 148 backend/40 frontend tests and type/build remain valid; source unchanged.
Next: collect/freeze independent labels for eight new single-scale, dual-scale and
unreadable gauge photos, then seek authorization for at most eight one-call cases
with unchanged production input/settings. Score contract, numeric agreement and
abstention separately; do not tune to MAXIMATOR or feed labels to the model.
[Evidence and bounded evaluation plan](photographic-analysis.md#first-completed-real-photo-evaluation-contract-pass-reviewer-mismatch).

Photo-workflow presentation refinement (2026-10-26), starting clean at
a388d5383d9adfe1782dcec6c59cadc73f61d053: compact connected status/navigation,
Operator asset/task/photo controls first, technical guidance and synthetic fixture
controls in accessible details. Refusal/human reporting remains outside fixture
tools. Both workspaces retain every evidence record as a contained thumbnail,
status, assigned asset, wall-clock UTC time and Inspect action. The native dialog
keeps full structured interpretations, uncropped full-image fit/enlarged views,
a keyboard-focusable pan region, sticky close control and expandable provenance.
Commander investigation/approval responsibilities and all analysis gates remain.
User references desktop and 390x844 screenshots; their files were unavailable to
the agent. Record this as user-captured/reported review, not agent inspection.
No browser surfaces or native helper are available; in-app opening failed.
Desktop/390x844 layout, actual focus return/dialog panning and file-picker journeys
remain unverified; no agent screenshots exist. 40 frontend tests, typecheck and
production build pass, including inspection content, record separation, labels
and loading/disabled states. Static rendering of the actual two-upload run passes;
this is not visual acceptance. Both runs/tables/images and ledger are unchanged.
No inference, backend edits, API writes or server operations. Source hashes,
read-only state checks and manual review steps are in ignored
`.local/visual/ft010-photo-refinement-ab8abb2e3f6e4afea92908e3cae74c54/`.
Next: refresh 5181/operator and /commander; review at 1440x900 and 390x844,
Tab/Shift+Tab, Escape/focus return, native file inputs and Enlarge/Fit scrolling.

Isolated photo review (2026-10-26), starting clean at 95ac2f8c68726e88753f76d139a873fed9ab7eaa:
new preview 5181/8781 uses ignored
`.local/visual/ft010-isolated-7661c16d0084429a9e9ac130010f12e9/data` and
FAULTTRACE_ALLOW_INFERENCE=0. Existing offline test setup pattern seeds one
explicitly TEST-CREATED / NOT AI-generated F-17 assignment; no planner or model
was invoked. Fixed-port origin rejection was reproduced and corrected with an
explicit, validated loopback-only FAULTTRACE_PREVIEW_ORIGIN setting; defaults and
local header policy remain intact. Five focused regressions cover this boundary.
API checks: compliant 960x960 MAXIMATOR copy collected once, stored bytes match;
bad image (400) and stale revision (409) rejected; analyze-photo returns 403
inference_disabled with no attempt or ledger change. Task remains awaiting so
manual review can exercise collection controls. Both routes serve HTTP 200.
Completed 5180/8780 preview, its tables/images and original photo are preserved.
141 backend tests pass with zero forbidden external sockets; 34 frontend tests,
typecheck and production build pass. Native/browser automation unavailable: no
desktop/mobile/keyboard/photo interaction or camera verification, no screenshots.
Exact manual and resume steps: `manual-review.md` in that ignored review folder;
[review scope and origin configuration](photo-evidence.md#isolated-inference-disabled-review).
Next: founder exercises selection, preview, replace/cancel, failed/throttled upload
and stored-image inspection on both isolated routes. Visual acceptance stays PARTIAL.

Local preview activation (2026-10-26), tested code 626daa9a7bdd873b224b28fc701b7636c7177b58:
restarted only the verified FaultTrace backend on 127.0.0.1:8780 with
FAULTTRACE_ALLOW_INFERENCE=0 and the same data directory
`.local/verification/ft008-ff11c43ec36b4f44901c9a46a8a1375f`. Frontends on
5180/5173 were left running. /commander and /operator on 5180 return HTTP 200;
their shared API proxy matches the updated backend and advertises photo support.
Completed incident 2a9ab9ea-0b2f-400a-946b-72dde56313b2 remains revision 9,
recovery verified with five samples over 40 simulated seconds. Prior table rows,
image inventory and ledger hash match; only an empty photo_analyses table was
added by startup migration. A consistent pre-restart SQLite backup and audit are
under ignored `.local/visual/ft010-activation-6208ef4c89a84c9090a15d0f8b9043c8/`.
34 frontend tests, typecheck, 7 photo-collection and 12 photographic-workflow tests
pass offline. No inference or run mutation was performed. Browser inventory is
empty, native pipe unavailable and in-app opening failed: desktop/mobile,
keyboard, camera and photo interactions are NOT verified; no screenshots exist.
The preserved run has no assigned task or stored image, so photo upload controls
cannot be exercised there without changing its workflow. Next: founder review at
http://127.0.0.1:5180/commander and /operator; separately scope an offline collection
test with an assigned task if interactive photo acceptance is needed. This later
documentation update does not change the activated application code.

Latest offline request audit, starting clean at a52b1642e2cc2a2a3a924efc992985fca500d644:
experimental attempt b2e90f31-9383-45e8-a88e-4df019c0796a occurs once and matches
its saved receipt: valid 1676 / 4096 / 5772 usage, finish_reason=length, no validated
interpretation. Current serialized request asks for JSON in prose only, without
response_format or reasoning controls. Nine fields/principal uncertainty outcomes
are present; no concrete causal defect established. Final content/reasoning was
discarded and is not reconstructed. Six contract and seven diagnostic tests pass;
mocked transport serialization checked. Production defaults/validator unchanged.
Ledger known 8634 / 16703 / 25337; 19 attempts, four missing usage. Separate manual
success 155 / 112 / 267 gives cross-record known 8789 / 16815 / 25604. Existing
records/images/provenance remain intact; no provider calls, imports or server work.
Next: obtain exact-alias Nebius confirmation of reasoning-off and image JSON-mode
support using the [unsent support draft](photographic-analysis.md#repeated-truncation-request-audit-and-unsent-support-question).
Only then propose one authorized standalone reasoning-off test at the unchanged
2048 cap. FT-010 remains PARTIAL; no live reading accuracy has been established.

Offline non-stop diagnostic follow-up at clean starting revision
2ca07c1fea25846275643c92fbee79921e68e5f7: attempt
50740c31-0635-4d56-af69-f4b4f7a64073 occurs once, matches the ledger receipt and
retains its image/provenance unchanged. Valid usage 1675 / 2048 / 3723, failed
non_stop_completion, no validated interpretation. Exact historical finish reason
and reasoning/output split are unavailable; no image-reading error established.
Future receipts now retain an allowlisted finish_reason before validation fails,
without changing historical receipt shape or accepting non-stop output. No
provider configuration change: NVIDIA's documented reasoning controls do not
establish support on Nebius's exact alias. Request limits, prompts and fixtures
remain intact. [Sources, evidence and bounded next diagnostic](photographic-analysis.md#non-stop-completion-investigation-offline-follow-up).
Ledger known 6958 / 12607 / 19565; 18 attempts, four missing usage. Separate
historical success 155 / 112 / 267; cross-record known 7113 / 12719 / 19832.
No provider requests, imports, workflow writes or server operations in this
follow-up. FT-010 remains PARTIAL. Next: separately authorize one standalone
diagnostic using the unchanged production builder and retained validated image,
record the new finish reason once, and stop; confirm Nebius reasoning-off support
before changing parameters.
Checks: 7 focused completion-diagnostic tests and all 136 backend regressions pass
under an external-socket guard (zero forbidden external attempts; loopback allowed
for Windows asyncio). Post-test hash checks confirm original/submitted image,
provenance, result and ledger preserved. No frontend code or UI changed.

Started clean at 5c31b58075e80f737a1e043b4483ee921a368314; new branch
feat/ft-010-photographic-analysis. No provider requests, server restarts,
existing-run writes, receipt imports/replays or fixture/photo asset changes.

photo-observation-v1 is a separate strict nine-field contract for category,
readability, model-reported measurement type, literal visible unit and numeric
reading, visible label text, external valve orientation, fixed reasons and exact
evidence reference. Readable/indeterminate type is supported; ambiguous scales,
unsupported instruments and unreadability abstain explicitly. No default reading,
DP assumption, unit conversion, asset renaming, internal-valve condition or raw
reasoning. The photo-only payload omits assignment, simulator data and answer keys.
[Full contract and evaluation plan](photographic-analysis.md).

Explicit analyze-photo reuses inference opt-in, existing single worker/transport,
2048 output-token cap, 60s socket timeout, 256 KiB response bound, one reservation
per image and sanitized receipt/ledger outbox. Additive photo_analyses metadata
holds contract and task/context revisions without altering historical analysis
schema/receipts. Stale task/context results lose their interpretation but preserve
usage. Interrupted attempts remain uncertain, consume their reservation and never
replay. No provider call spans a DB transaction. Task status is restored, not
silently completed; external photos never become simulator observations.

New interpretations are quarantined from legacy pressure comparisons and planner
interpretation payloads until explicit compatibility/evidence policy. They cannot
authorize correction, even if the model reports differential_pressure. Existing
fixture contract/validator/prompt and recovery policy are unchanged. Both routes
show actual image, structured observations, uncertainty, status, provenance and
known/unknown accounting; label text stays escaped/untrusted.

Checks: 129 backend tests including 18 new contract/workflow cases; 34 frontend
tests including four photo interpretation/control cases; TypeScript/Vite build.
Full backend socket guard reports zero forbidden external connections. Coverage
includes varied readings/units, indeterminate type, ambiguity, unreadability,
unrelated images, injection-shaped text, invalid output, usage after rejection,
HTTP/ledger failure, idempotency, stale completion and interrupted/outbox recovery.
Mocked results and generated images are not evidence of live photographic accuracy.

Existing backend is left running; new analysis is capability-gated until later
manual activation preserving its data directory and inference opt-in. Browser
inventory empty; in-app opening failed (Browser is not available: iab). No actual
desktop/mobile/keyboard, live model-contract compatibility or accuracy claimed.
FT-010 implementation/offline checks pass; runtime/evaluation acceptance remains
PARTIAL. Next: obtain original/permissioned evaluation photos, independently
review and freeze expected observations before a separately authorized bounded
photo evaluation. No ground truth has been invented or provider call authorized
by the plan. Keep existing runs/receipts intact and do not replay old analysis.

## Prior: FT-009B real-photo collection and presentation

Started clean at 4e9df6b4c8e31bbdfeef58d8879f6049ce542f47 on
feat/ft-009-workspaces; FT-008A/009A and existing runs/fixtures preserved.
Operator offers camera and ordinary files, actual local preview, replace/cancel,
measured transfer progress and clear decode/limit/network/storage states. Actual
stored photos appear in Commander/Operator and inspection. Assignment remains
separate from photographed identity; human reports and NVIDIA interpretations
are labeled separately. No tags inferred/remapped, DP inferred from an ordinary
gauge, or internal valve condition claimed from a handle image.

New reference-photo uploads on assigned F-17/V-08 tasks are collection-only,
status collected, preserving separate structured reports. They cannot reserve
analysis or satisfy simulated correction prerequisites. Existing DP fixtures,
legacy operation fingerprints, validated upload bounds, private storage, receipts,
budgets, stale revisions and vision contract remain. EXIF camera rotation is
applied before metadata stripping, fixing an offline-reproduced orientation loss.
No recovery-policy/model/prompt change or history/schema migration.

No photographic assets downloaded, extracted from the reference or committed.
[Photo guide](photo-evidence.md) covers actual source/license records and a separate
unverified analog-gauge/valve evaluation. No reuse rights/authenticity assumed.

Checks: 111 backend tests (seven new collection regressions), 30 frontend tests
(six new photo/progress/markup tests), TypeScript/Vite build, AST/source lengths
under 500 and diff review. Backend suite uses fake transport/temporary stores
with zero forbidden external network attempts. Tests cover collection-only
analysis rejection, JPEG normalization/EXIF privacy/orientation, idempotency,
stale task, restart retention, separate V-08 reports, limits, legacy fixtures,
unchanged correction gates, measured progress and sanitized failures. Existing
V-08 cannot-determine contract remains; its unreadable position label does not
introduce a new report value.

No provider request, server restart, paid infrastructure, deployment, receipt
import/replay or existing-run write. A capability flag keeps new photo inputs
disabled against the existing older backend; later activation requires a manual
restart preserving the existing data directory and inference disabled. Current
preview cannot be claimed as a completed real-photo workflow test.
Browser inventory empty; in-app opening returned Browser is not available: iab.
No actual desktop/mobile camera, keyboard, upload or visual acceptance claimed.
Implementation/offline checks pass; runtime activation/visual acceptance remains
PARTIAL. Next action: review this checkpoint, then separately schedule activation
and permissioned-photo collection QA; no inference is authorized by FT-009B.

## Prior: FT-009A distinct Commander and Operator workspaces

Started clean at 9241d66def510c202fc861a58bf0c52cc4367d82; FT-008A preserved.
Branch feat/ft-009-workspaces. Dedicated page components use /commander and
/operator; old connected query URLs canonicalize client-side. One mounted
workflow controller supplies both pages; separate tabs read the same API. No
backend, database/history, policy, inference, budget, idempotency or simulator
boundary change. No dependency installation, paid infrastructure or deployment.

Commander owns incident creation, overview/schematic, actual stored telemetry,
assessment, NVIDIA observation planning, correction approval, recovery and audit.
Operator is a mobile-first assignment screen with actual task instructions,
image upload/explicit analysis, structured reports/refusals and approved simulated
completion acknowledgment. It contains no incident creation, planner, approval
or simulation-clock controls. The shared evidence section preserves actual
provenance/scopes; no data duplication, fake links or migration. Connected
schematic/chart never substitute the sample preview's fixed numbers; absent
server telemetry is explicitly unknown.

NVIDIA task evidence can inform observation planning but does not yet satisfy
the deterministic simulated correction assessment. This integration gap is
visible in the product. Architecture docs distinguish existing local API/SQLite/
worker/private simulator from future public hosting, anomaly delivery, durable
production workflow, storage, secrets and protected logs. Server-enforced roles
and incident/evidence access are an explicit unchecked deployment gate: routes
and hidden controls are not authentication.

Checks: 24 frontend tests, TypeScript and production build; source lengths and
diff checks. Six added routing/page tests plus FT-008A regressions cover shared
references, role control boundaries, legacy URLs, image/report/refusal paths,
opt-in analysis, real/absent telemetry, recovery and loading/offline states.
Backend unchanged; prior 104 offline-test evidence remains applicable. No paid
inference or application mutation was performed. Read-only API checks confirm the existing completed incident remains revision 9,
with verified recovery; no server restart was performed. Both dedicated route
URLs, the legacy Operator URL and their transformed page modules returned HTTP
200 on the existing preview. These HTTP checks are not browser verification.

Browser inventory apps=[]/browsers=[]; in-app opening failed with Browser is
not available: iab. No actual desktop/mobile/keyboard/back-forward or browser
journey acceptance is claimed. FT-009A implementation/offline checks pass;
visual acceptance remains PARTIAL. Next action: inspect the existing completed
run at http://127.0.0.1:5180/commander and /operator, including 1440x900 and
390x844, keyboard, legacy-link canonicalization, back/forward and reload. Keep
existing histories intact; no new provider request is authorized here.

## Prior: FT-008A coherent outcome and evidence presentation

Started clean at 55c1d592402556b5a6b84f13f4556f3b4e3bb2f6 on
feat/ft-008-simulated-recovery. Presentation/tests/docs only: no backend,
recovery-policy, database/history migration, inference or server restart.
The completed local run is preserved; no simulation action was invoked.

User-reported walkthrough in both views: 180 kPa + V-08 intermediate -> explicit
approval -> simulated replacement -> five qualifying post-action samples ->
recovery verified. Read-only localhost state corroborates incident
2a9ab9ea-0b2f-400a-946b-72dde56313b2 revision 9, two simulated observations,
three populated approval references, six populated telemetry rows, five recovery
samples spanning forty simulated seconds and completed simulated maintenance.
This is user browser evidence, not agent-operated browser verification.

Finding: image/planner-task evidence is a separate empty collection, so its old
unscoped empty-state message was misleading. Journey observations now form the
primary coherent evidence record; separate workflow evidence is explicitly scoped
and expandable. No links were invented and no records migrated. Pre-change API
values and React static markup contained all references and rows, with zero
empty bullets/cells. A browser/CSS/capture cause for the pasted blanks remains
unproven; data was not rewritten to guess at one. Visible unknown fallbacks and
explicit table/reference colors make missing values distinguishable.

Role-specific next actions and the completed recovery/audit summary lead the
journey. Completed-run planning is history-only; fixture rules, technical source
metadata, optional clock controls and detailed audit history are expandable.
Simulated UTC measurement timestamps and wall-clock UTC audit times are labeled
separately; no recovery audit event or verification timestamp was invented.

Checks: 18 frontend tests, including six static React markup regressions for
both views, exact stored references/rows, zero/unknown values, evidence scope,
clock labels, history-only planning and pre-action/failed states. TypeScript and
production build pass. Backend unchanged: prior 104-test evidence remains valid.
Static markup is not browser verification. Browser inventory apps=[]/browsers=[];
in-app browser attempt returned Browser is not available: iab. Desktop/mobile,
keyboard, CSS layout and visual acceptance remain open; no screenshots claimed.
Ignored before/after markup and source-hash/blocker records live under
.local/visual/ft-008a/. Next action: refresh the existing 5180 preview and review
the preserved outcome in both views at 1440x900 and 390x844, checking keyboard,
expanded references, every telemetry cell and timestamp scope. Do not restart,
reset or repeat the completed correction. FT-008 visual acceptance remains PARTIAL.

## Prior: FT-008 simulated restriction-to-recovery journey

Started clean at 5bd6116fe12d9360e3859082c62ccc0ff2b18bf1; branch
feat/ft-008-simulated-recovery. Core implementation: b76d2ef16360ced944dfec33b63bc7652060dcf0, with a
subsequent UI-copy encoding repair and preview-evidence documentation.
Existing servers and historical
runs are untouched. No provider request, receipt import/replay, dependency
installation, deployment or merge.

A fresh opt-in synthetic run persists explicit ten-second telemetry steps,
provenance-bearing local pressure and V-08 human reports, evidence-linked
working diagnosis/alternatives, revision-bound human approval, registered
simulated filter replacement and independent sample-based recovery. It uses
additive local tables in the existing architecture. Existing incidents cannot
be converted/reset. Simulator outcome/answer controls are excluded from public
state and actual planner contexts; observed simulated telemetry/reports are
included with current references and revision. Observation-only planner policy,
opt-in, budgets, stale-result protection and ledger are preserved.

Deterministic correction gates reject stale/missing/unreadable/inaccessible/
conflicting evidence and active observation/planning tasks. Approval/execution
are idempotent and revalidate revision/policy. Decline revokes approval and
advances revision. Operator completion records simulated maintenance separately
from recovery. Verifier requires five fresh consecutive post-action samples
spanning forty simulated seconds within fixture bands with no active alarms;
ineffective corrections and later relapse fail. No model recovery declaration,
real control instructions or industrial limits are introduced. Thresholds,
clock semantics and exact startup/journey steps: [guide](recovery-journey.md).

Checks: 104 backend tests including 10 new independent journey tests; 12 frontend
tests; TypeScript/Vite production build; pip check; AST/source lengths under 500
lines. Full backend regression uses temporary stores/fake transport and a socket
guard (zero forbidden external attempts). No existing ledger/database writes;
no new inference usage. Prior ledger evidence stays 5283/10559/15842 known,
four missing-usage attempts; separate historical 155/112/267.

Browser blocker: inventory apps=[]/browsers=[]; in-app tab creation returned
Browser is not available: iab. No desktop/mobile/keyboard visual acceptance or
screenshots claimed. An isolated inference-disabled preview was launched at
http://127.0.0.1:5180/?mode=connected with a fresh private data directory;
backend 8780, frontend/proxy and JourneyPanel module HTTP checks returned 200.
No incident was created there; it is ready for founder review. Ignored browser
blocker/hash record: .local/visual/ft-008/verification.json. These HTTP checks
are not browser verification. Offline/API preparation passes; FT-008 visual acceptance
remains PARTIAL. FT-007 remains PARTIAL; CI/hosting and broad AI/recovery claims
remain open. Next action: founder review of the isolated localhost journey at
1440x900 and 390x844, including keyboard, evidence blockers, approval, progress
and verified/failed states. No paid live test is proposed by this checkpoint.

## Prior: FT-007 action-ID standalone verification finalized

Implementation c4eb08db60c7facddbfe9eeaf5084820bfafb5e3; documentation-only
finalization started clean at that SHA. Read-only existing-ledger load found
attempt 1fbccbe3-a77d-4ddc-bea5-3bd2aa194e16 exactly once, timestamp
2026-10-25T20:47:43.877892+00:00, response
chatcmpl-40a9c201-db70-4113-b74c-b764c719b71b, exact Nano text model,
3641 ms, transport invoked, validation passed, diagnostics empty, valid usage
620 input / 933 output / 1553 total; source revision matches the implementation.

The user reports validated human escalation from the saved revision-3 F-17
refusal context using the action_id contract. Prior offline preflight confirmed
F-17 unavailable and absent from the enum, with V-08 and human escalation
selectable. The ledger corroborates receipt/usage, but does not store proposal
fields. This standalone call created no workflow task and proves neither
browser behavior nor general planning reliability. FT-007 remains PARTIAL.
Earlier failures, including d4430228-f580-4175-94ca-09fc667f0707
(planner_invalid_combination, 578/956/1534), remain untouched; no discarded
fields were recovered. The application still owns action mapping and policy.

Actual ledger: 17 attempts, 13 complete known contributors, known
5283 / 10559 / 15842 tokens (input/output/total); four missing-usage attempts,
zero partial/invalid/inconsistent. Separate historical manual success
155/112/267 gives cross-record known 5438/10671/16109. No discrepancy;
unknown consumption stays unknown, with no billing estimate.

No inference, server operations, imports/replays, database/ledger writes or
source changes in this finalization. Existing 94 backend tests, 10 frontend
tests and TypeScript/Vite build evidence at c4eb08d remains applicable; no
rerun required for documentation. No new browser evidence or submission gate.
Next proposed checkpoint: FT-008, one simulation-only F-17 restriction journey
with evidence-backed working diagnosis, explicit human approval of a registered
simulated correction, and independent sustained recovery checks. Proposal only:
no implementation, new model authority or live request authorized here.

## Prior: FT-007 connected API evidence finalized; refusal-aware policy added offline

Started clean on feat/ft-007-observation-planner at
2bb97c6248450a9814cc9e503d57398e10a004ad. No inference, server restart,
receipt import/replay, actual workflow database or ledger write in this checkpoint.
The audited run remains unchanged; the new policy is prospective, not a rewrite
of earlier accepted proposals, tasks, contexts or receipts.

Read-only SQLite URI mode=ro/query_only plus existing ledger load audited incident
8654a8a2-ff58-4344-a1c5-bd9d60c05a2c in
`.local/verification/ft007-connected-8f8673e87da9431cb3f9fce92908529e`:

- Attempt 5cb5ee1d-1845-47cf-a8b9-01714c6d9b47 occurs once in SQLite and ledger;
  receipts match exactly. Context revision 1, no observations, accepted F-17 /
  READ_LOCAL_DP proposal, created task 45a54498-2c17-463a-bc27-b996381b8e85.
  Response chatcmpl-336a3652-56a1-4676-adbb-e6f0391a0ad5; 10390 ms;
  valid 328 input / 866 output / 1194 total; ledger recorded.
- Simulated cannot-access report bcd5802e-15ed-49e7-af24-14617ee637ff belongs to
  that task/asset; kind report, origin human-report, status refused. It is not
  real field evidence or an image interpretation.
- Attempt 75d1d983-4afb-4b98-ad75-8dedab22cae6 occurs once in both stores;
  receipts match exactly. Saved context revision 3 includes that same refused
  report/reference. Proposal cites it and telemetry-001, but requests F-17
  again, creating task 8db8b2c2-fbd9-42a1-8d7f-48a256e9e105.
  Response chatcmpl-aec7a419-d89d-4e19-9ada-67addc11eff1; 10110 ms;
  valid 508 / 1280 / 1788 usage; ledger recorded.

Both receipts validate passed with exact Nano model and source revision 2bb97c6
(full SHA above). Two accepted attempts, two tasks, one refused report, current
incident revision 4, two planning turns left. Current task remains awaiting;
no task was cancelled/replaced by this audit or fix. This verifies connected
provider -> validator -> task persistence and updated-evidence context/replanning
through the API. It does NOT prove useful adaptation: the repeated inaccessible
F-17 task exposed a missing application policy. No agent-operated browser test,
real equipment observation, operating recovery or diagnosis is established.

New refusal-aware policy: unresolved cannot-access blocks observation requests
for the same asset, independent of model explanation/reference choice. Full
incident history supplies bounded unavailable_assets even when older reports
fall outside the recent 16 observations. Prompt instructs an available alternative
or escalation; application rejects violations with planner_asset_unavailable.
There is no access-clearance workflow: blocks persist for the incident and are
not silently cleared by reopening, later reports or image interpretations.
Existing tasks/history remain intact; no automatic repair, rewrite or retry.
All other combination/reference/shape/revision/active-task/budget guards remain.

Accounting checked read-only: connected pair known sum 836 input / 2146 output /
2982 total. Ledger 15 attempts, 11 complete known contributors =
4085 / 8670 / 12755; four missing-usage attempts, zero partial/invalid/inconsistent.
Separate historical manual success 155/112/267; cross-record known
4240 / 8782 / 13022. These reconcile exactly to prior totals plus the connected
pair; no discrepancy, imports, missing-token inference or billing estimate.

Offline verification: seven focused refusal-policy tests and all 88 backend
tests pass with fake transport/temporary stores. Full suite socket guard recorded
zero forbidden network attempts (Windows asyncio internal loopback socket-pair
setup only allowed). Provider response schema, explanation constraints, transport,
accounting, reservations, task service and frontend are otherwise unchanged;
AST/diff checks passed. Sources remain below 500 lines (maximum 374).
The fix has not been live-verified.
FT-007 remains PARTIAL: connected API mechanism narrowly verified, browser,
useful evidence-dependent decisions, recovery, CI and hosting remain open.
Next action is review of this commit and a separately authorized future test;
do not rerun or reset the existing two-call run. No live verification now.

Prior standalone compatibility remains valid: attempt
87f5704f-d2ca-46ba-9967-7334363ac419 at cdb9f4277127feb983eb246dad3190d13ca2cdee,
3375 ms, valid 328/618/946 usage, all six fields/no extras, no workflow task.
Original uniqueItems and partial-anyOf failures remain preserved, with their
narrow causal conclusions; no provider implementation bug or discarded output
recovery is claimed.

## Prior: FT-007B safe HTTP diagnostics; FT-007 remains PARTIAL

Started clean on feat/ft-007-observation-planner at
`c571bb85773f0dda5936102587481ad122da704d`. This scoped fix preserves
numeric http_status and fixed status-derived http_error_category through
transport, sanitized receipts, the existing ledger and both UI evidence paths.
Error bodies and headers are never read or saved, so parameter names and provider
causes remain unknown. No inference, server restart, import, record rewrite,
request-contract change, budget change, deployment or merge occurred.

Read-only SQLite (mode=ro/query_only) and one shared-ledger load confirmed
isolated attempt `76a24b31-3b2e-4954-9954-dee9749ce7fa` exactly once in each,
with identical receipt, provider_http_error, missing usage, accounting recorded,
no task, and three turns remaining. Directory:
`.local/verification/ft007a-c3e18fe3026e4c87a4214bb2eda40983`.
Receipt: timestamp 2026-10-25T01:30:32.073521+00:00, 843 ms, transport invoked,
source c571bb85773f0dda5936102587481ad122da704d; returned model/response ID
unknown. Context/current revision both 1. Historical HTTP status/body cannot
be recovered and are not relabeled. No historical HTTP root cause is proven.

Actual ledger: 7 attempts, 5 complete known contributors, known
1937 input / 2712 output / 4649 total. TWO attempts now have missing usage:
the older failed probe and the new isolated HTTP failure. Partial/invalid/
inconsistent counts all zero. Separate historical manual success 155/112/267;
cross-record known 2092/2824/4916. No missing tokens or billing estimated.
Historical absent HTTP fields remain absent, avoiding rewritten receipts and
changed duplicate fingerprints. The UI reports unknown for those fields.

Schema review: named strict json_schema wrapper matches official Nebius guide;
no confirmed incompatibility found. Exact Nano support and anyOf/uniqueItems/
array-bound support remain unverified suspicions, not causes established by
this historical failure. Model/schema/prompt/token cap/retry policy unchanged.
See [workflow guide](evidence-workflow.md) for sources and exact proposed test.

Checks: 78 backend offline tests (7 new HTTP tests), 10 frontend tests,
TypeScript/Vite build and pip check. Fake HTTP opener only; malformed/oversized
bodies are not read, secret text never emitted, no task on HTTP failure,
known parsed-completion usage still survives validation rejection. Sources
and request-contract diff checks passed. The full suite also passed with
external sockets blocked (zero forbidden attempts; Windows asyncio internal
loopback socket-pair setup only allowed). All source files remain
below 500 lines. Browser inventory empty; iab unavailable. No visual pass or
screenshots; ignored `.local/visual/ft-007b/verification.json` records hashes/blocker.

Next diagnostic test, NOT RUN: after separate approval, use one fresh, empty,
UUID-named isolated simulation on a verified-free port, sharing the existing
ledger. Create one incident and issue exactly one planning request, unchanged
payload. Read status/category and usage independently; stop without retry or
schema experiment. Never reuse/reset either attempted revision-1 run, copy
historical context, or consume their remaining three turns. This tests transport
compatibility only, not live adaptive reasoning or prior-incident recovery.

## Prior: FT-007A reliability fix; FT-007 remains PARTIAL

Started clean on feat/ft-007-observation-planner at
`8ce8172ed587c3c124467329926d0ac1742f3100`. The scoped FT-007A commit
contains the tested fix and this record; identify it with git log -1.
No inference, server restart, receipt import, migration, database/ledger write,
new feature, deployment or merge occurred in this checkpoint.

Read-only inspection (SQLite URI mode=ro plus query_only; one ledger load)
confirmed attempt `13d345c9-3480-45bc-a4c6-c2260b319300` once, rejected with
`invalid_proposal`, accounting recorded, no proposal retained and no new task.
Receipt matches the ledger: timestamp 2026-10-25T00:50:18.260217+00:00,
response chatcmpl-b831667d-dc12-498c-b220-2870a78c5bd4, Nano model,
implementation 8ce8172ed587c3c124467329926d0ac1742f3100, 18703 ms,
transport invoked, 564 input / 1483 output / 2047 total, valid usage,
validation failed and metadata/accounting diagnostics empty.

Persisted context revision 1 equals current revision 1. It included the legacy
observed F-17 task, accepted user-upload image interpretation 180 kPa, simulated
184 kPa pressure / 86 m3/h flow / 72% feedback, their comparison conflict,
and four turns before reservation. One attempt leaves three turns. The old
code path establishes valid JSON and passing completion-envelope checks before
proposal rejection; it does not identify the offending field, value or exact
policy condition. Output was discarded. No reconstruction or root-cause claim
is possible. Token usage does not establish the amount of reasoning or a
cap-induced truncation. Context SHA-256:
`c1b14563a790c869c59232a6ea719979c780ffb1b469fe51f1f026f56aeee4e4`.

The fix adds fixed shape/type/revision/reference-count/unknown-reference/
duplicate-reference/asset-capability/explanation-condition codes, independently
validated and allowlisted in receipts. The strict original smoke contract is
unchanged. Requests now use strict json_schema with required fields, no extra
properties, allowed combinations, exact revision, bounded unique existing
references and currently supported explanation codes. Nebius documents this
wrapper; its official Nano cookbook advertises structured output, but uses a
different model-ID casing/regional endpoint. Exact configured ID/endpoint and
schema-keyword acceptance remain unverified. Sources and caveats are in the
[workflow guide](evidence-workflow.md). No repair/retry/fallback or cap increase.

The attempted-context button retains native disabling/idempotency, adds a
graphite disabled appearance and aria-describedby linked visible status text.
Checks: 71 backend offline tests (including five new diagnostic/payload tests),
9 frontend tests, TypeScript/Vite build and pip check. The backend suite also
passed with external sockets blocked: zero forbidden network attempts, allowing
only Windows asyncio's internal loopback socket-pair setup. Existing TestClient/Node warnings
remain. No dependencies added; source files remain below 500 lines.
Browser inventory empty; iab failed with Browser is not available: iab.
No actual desktop/mobile/keyboard visual verification or screenshots. Ignored
`.local/visual/ft-007a/verification.json` records blocker and tested file hashes.

Accounting checked once, no imports: ledger 6 attempts, 5 complete known
contributors = 1937 input / 2712 output / 4649 total. One historical attempt
has missing usage; partial/invalid/inconsistent counts are all zero. Separate
historical manual success = 155 / 112 / 267; cross-record known =
2092 / 2824 / 4916. No discrepancy, billing estimate or complete-consumption claim.

Next action: first manual inference-disabled restart and founder UI review.
A corrected call on revision 1 is BLOCKED despite three remaining turns;
restarting, deploying this fix or using a new click key cannot authorize it.
Only a genuinely needed reassessment through the existing F-17 reopen workflow,
followed by new truthful evidence/refusal, can enable a later context. Do not
reopen solely to advance revision or fabricate a report. If no genuine new
observation exists, remain blocked for live verification. The guide proposes
at most one corrected planner call after that condition and separate approval;
no replay, database reset, historical edit, budget reset or policy bypass.
Live adaptive success, mobile/broad browser coverage, recovery, CI and hosting
remain unverified. Prior verified FT-006 evidence below stays historical.

## Prior verified evidence: FT-006 connected clear-image finalization

Bounded acceptance: PASS for connected clear synthetic image submission/
interpretation and user-reported restart persistence only. Broader FT-006
coverage remains PARTIAL. This documentation-only checkpoint started clean
on `feat/ft-006-evidence-workflow` at implementation
`4b15365e20ea0b7cacf1ad2d695163bf439690ec`. No source/dependency changes,
inference, server restart, analysis replay, receipt import, or data writes.

The USER uploaded synthetic panel-a through connected Operator, observed an
actual NVIDIA interpretation of readable 180 kPa with valid usage/ledger
recorded, then restarted with FAULTTRACE_ALLOW_INFERENCE=0. The USER confirmed
identical evidence, attempt, interpretation, and usage in both Commander and
Operator. These are user observations, not agent-operated browser testing.
No screenshot was attached or inspected by the agent in this finalization.

Agent corroboration was read-only: SQLite URI mode=ro, PRAGMA query_only=ON,
and existing ledger load only. SQLite has 1 incident, 1 F-17 task (observed,
revision 4), 1 evidence record, and 1 accepted analysis with accounting recorded.
Events contain one explicit analysis request and one accepted analysis. Ledger
has exactly the prior four attempts plus the new attempt once. No additional
recorded attempt appeared during the reported restart; this does not audit
unrecorded requests outside these stores.

Evidence: `a757eca7-445b-4d0c-b2ae-c70980b3f20d`. Stored origin stays
`user-upload`, fixture_id null, 480x300. Its recorded original SHA-256 matches
committed panel-a (`865db39953a926433d00de7be42eedc07f5795940bc07d78dc5c44d90dd16da6`).
No provenance was rewritten to claim fixture-picker submission or image-proven
asset identity. Private image bytes remain outside Git and were not inspected.

Validated interpretation:
`{"readability":"readable","reading":180,"unit":"kPa","evidence_ref":"evidence-a757eca7-445b-4d0c-b2ae-c70980b3f20d"}`.
Sanitized receipt is identical in SQLite and the ledger:

```json
{
  "attempt_id": "1b6b653c-abc9-4ec2-a9be-96d24aba38cc",
  "timestamp": "2026-10-25T00:04:59.173746+00:00",
  "endpoint": "https://api.tokenfactory.nebius.com/v1",
  "requested_model": "nvidia/Nemotron-3.5-Super-VL",
  "returned_model": "nvidia/Nemotron-3.5-Super-VL",
  "response_id": "chatcmpl-f7947eb50a4d5f42d8147c26e317a604",
  "source_revision": "4b15365e20ea0b7cacf1ad2d695163bf439690ec",
  "latency_ms": 1938,
  "transport_invoked": true,
  "validation_result": "passed",
  "token_usage": {"prompt_tokens": 438, "completion_tokens": 339, "total_tokens": 777},
  "usage_status": "valid",
  "diagnostics": []
}
```

Timestamp is the stored UTC attempt/reservation time (October 24 evening in
America/New_York). Inference-disabled startup and browser continuity are
user-reported, not reenacted by the agent.

| Actual accounting coverage | Known input | Known output | Known total |
| --- | ---: | ---: | ---: |
| Ledger: 5 attempts, 4 known contributors | 1373 | 1229 | 2602 |
| Separate historical manual success | 155 | 112 | 267 |
| Cross-record known sums | 1528 | 1341 | 2869 |

Actual totals match expectations; no discrepancy. One historical failed
attempt still has missing usage: missing 1, partial 0, invalid 0, inconsistent 0;
its transport completion remains unknown. These are incomplete consumption,
not zero usage or estimated billing. The manual record stays outside the
ledger because its exact timestamp/application revision are unavailable.

Source/test inputs are unchanged; reuse the still-valid 48 Python tests,
6 frontend tests, build/type and dependency checks. No tests rerun for docs.
Documentation diff/whitespace and staged secret review precede scoped commit;
final documentation SHA and remote match are reported from Git results and
must be distinguished from the live-tested implementation above.

Still OPEN: mobile/accessibility/overflow review, agent-operated browser
verification, connected unreadable/refusal paths, adaptive planning/hidden
fault investigations, recovery verification, CI, hosting, public-host security,
and full submission eligibility. Standalone unreadable success does not prove
the connected path. Fixed simulation/SQLite/local-trust/no-authority limits
are unchanged. Exact next action: review this evidence and separately scope
the next bounded verification; do not repeat this analysis or start another
checkpoint from this documentation finalization.

## Current checkpoint: FT-006 server-backed image evidence workflow

Historical implementation handoff: PARTIAL — server-backed implementation/offline verification complete;
new connected live inference and actual two-tab/mobile browser review pending.
Started clean on `feat/ft-005-visual-preview`, expected HEAD
`9f4544eed13bd09eeb37a8a9786555ff925fa1b0`; created
`feat/ft-006-evidence-workflow`. No unrelated changes were present.

FastAPI now persists one simulated incident, a fixed F-17 observation task,
revision-checked submissions, scoped private image metadata, analysis state,
sanitized receipts/interpretations, idempotency records, and chronological
events. Task creation is fixed simulation workflow, NOT AI planning.
SQLite in ignored `.local/workflow/` is an explicit departure from proposed
PostgreSQL for portable single-instance local validation; hosted database
work, migrations, backups, and public-host hardening remain open.

Connected Commander/Operator tabs read the same API state through Vite's
loopback proxy. Bounded polling: one read at a time, 5-second timeout,
2-second interval, 900 reads per refresh cycle, pause after 3 consecutive
errors. No mutation retries. Sample preview stays explicitly separate and
single-tab only. Both modes have truthful idle states; no plausible fault
appears before start. Operator heading is compact. Simulated telemetry is
separate from actual model interpretations and known per-call usage.

PNG/JPEG uploads are bounded by bytes, dimensions, frame count, and real
decode/format checks, normalized to RGB PNG, metadata stripped, alpha flattened
onto white. Fixture-origin claims require matching committed bytes. Images
stay in `.local/workflow/images/`, served only by database-scoped UUID, never
filesystem input paths. Local users/processes are trusted; no authentication
or user isolation exists. Do not expose these loopback dev servers publicly.

Analyze image is explicit and additionally requires backend environment
FAULTTRACE_ALLOW_INFERENCE=1 and NEBIUS_API_KEY. Defaults disable inference.
The existing standalone probes/strict contract/transport remain unchanged.
One worker serializes the application analysis/accounting path. Reservations
are durable before inference; no SQLite transaction spans network activity.
Duplicate clicks/keys and stale writes cannot create a second call for an
evidence ID. A durable receipt outbox precedes the existing ledger write.
Failed persistence retains the receipt; interruptions become uncertain on
restart, reconcile accounting only, and NEVER replay inference. Available
interpretations/usage are preserved without declaring diagnosis or recovery.

Pinned backend dependency set is requirements-backend.txt (direct inputs .in),
installed in this project's isolated .venv with Python 3.12.14. FastAPI 0.162.0,
Uvicorn 0.54.0, Pillow 13.0.0, HTTPX 0.28.1; pip check passes. HTTPX's pinned
TestClient adapter emits a deprecation warning, not a failure. No frontend
dependency additions. All source files remain below 500 lines.

Checks: 48 Python tests passed (35 existing + 13 new API/reliability tests);
6 frontend state tests and production build/type check passed. Offline API
tests use fake transport, temporary DB/images/ledger, two ASGI clients, and
fresh application instances for restart checks. No real provider request
was made. A Windows byte-lock read issue was caught and corrected. An initial
all-socket test guard incorrectly blocked asyncio's internal socketpairs;
the corrected guard permits only those loopback internals, blocks outbound
network, and reports no forbidden outbound attempts. This is not a browser test.

Windows denied backend bind on 8000 even after permission retry. The unused
loopback port 8765 works. Existing FaultTrace Vite was safely identified and
restarted to load its new proxy; JSON /api/state through 5173 was then verified
with inference false and no incident. Vite denies filesystem access to private
.local storage (HTTP 403 verified) while API-scoped access remains available.
Both dev servers are left running where
the environment permits. Actual persistent local data was not populated with
canned model evidence. Full commands: [workflow guide](evidence-workflow.md).

Browser inventory is empty; iab opening still returns "Browser is not
available: iab". No actual desktop/mobile two-tab journey, keyboard/overflow
review, or screenshot inspection occurred. Ignored verification results/source
hashes are under `.local/visual/ft-006/verification.json`; no screenshots exist.
The old sample-preview screenshot blockers remain historical, not new passes.

### Supplied standalone vision evidence reconciled, not repeated

Both records are already in the local ledger exactly once at source revision
`9f4544eed13bd09eeb37a8a9786555ff925fa1b0`, endpoint
https://api.tokenfactory.nebius.com/v1, model nvidia/Nemotron-3.5-Super-VL:

| Fixture | Result | Latency | Input / output / total | Attempt |
| --- | --- | ---: | --- | --- |
| panel-a | readable, 180 kPa | 2031 ms | 428 / 403 / 831 | 6c9382df-c96a-4677-8f0d-3e0aadcf7756 |
| panel-b | unreadable, null reading/unit | 1844 ms | 428 / 341 / 769 | 94ec5368-e5e3-4baf-a36f-53b6055371d1 |

Ledger remains 4 attempts, known input 935 / output 890 / total 1825, with
one historical failure missing usage; partial/invalid/inconsistent 0. Separate
external manual success remains 155 / 112 / 267 (timestamp/revision unknown).
Cross-record known sums are 1090 / 1002 / 2092 plus unknown failed consumption.
Neither completeness nor billing is inferred. No duplicate import/generation.
These two synthetic-fixture successes establish only that standalone capability;
they do not verify the newly implemented connected runtime or arbitrary gauges.

Exact next action: separately authorize the guide's one-call connected panel-a
procedure, starting backend with inference enabled only in the founder's
Windows terminal. Open two tabs, submit image without inference, click Analyze
once, inspect actual result/accounting in both, then restart with inference
disabled and verify retained IDs/receipt without another call. Stop on failure
or ambiguity; panel-b connected verification would be a separate later call.
No cloud resources, intervention, deployment, merge, or next feature checkpoint.
Scoped commit/final SHA, remote match, and working status come from Git results.

## Current refinement: FT-005 task-first layout

Bounded founder review refinement on existing `feat/ft-005-visual-preview`.
Verified clean expected HEAD `aa5710d20132e1125e19deaebc2bcfc6ffc88b55`.
No unrelated work, branch change, dependencies, backend, inference, or deployment.
The graphite/teal direction is preserved. Founder-reported issues were excess
header height, an off-screen task, and colliding schematic labels.

Replaced the oversized Commander slogan with "INC-0042 · Reduced return flow"
and a useful incident description. Reduced framing/metric spacing without
reducing telemetry/body text sizes. The planned/active observation task is
now a dedicated top-right panel beside the process, with equipment, requested
evidence, task state, rationale, Open operator task, and retained repeat action.
Competing explanations remain beneath it. The separate lower duplicate task
strip was removed. Active incident is a status, not a disabled primary action.

RETURN LINE moved to a separate upper-left label row; bypass/return labels
are separated. Selected equipment and full details remain available via native
Equipment details disclosure. On narrow layouts the task comes first, with
contained chart/schematic scrolling. DOM order prioritizes the task action;
view navigation now focuses the destination main region. Native button/details
and SVG Enter/Space handlers were reviewed in source, not exercised in a browser.
Sample-data banner, all four response outcomes, chronology, inspector, reset,
and local-tab/no-AI limits remain in place. State reducer is unchanged.

Verification: frontend state tests and build/type checks pass. Python probes
and tests are unchanged, so the prior 35-test offline result still applies;
they were not rerun for this UI-only refinement. Local preview remains
http://127.0.0.1:5173/; HTTP readiness is checked during delivery.

Browser inventory was again empty and opening iab again failed with "Browser
is not available: iab". No desktop/mobile screenshots were captured, preserved,
or inspected. No actual 1440x900/390x844 fit, overflow, focus/keyboard traversal,
or navigation-action browser pass is claimed. The founder screenshot review
guided this change, but the screenshot file was not attached to this checkpoint.
Ignored `.local/visual/ft-005/refinement-verification.json` records source hashes
and the browser blocker separately from the earlier verification record.

Status remains PARTIAL pending founder visual review. Scoped source/docs,
secret/diff checks, commit/push, and remote SHA verification complete delivery;
Git command results identify the final revision. Exact next action: refresh
the local preview and review the task placement, label separation, keyboard
task action, and mobile overflow using docs/preview.md. Stop for visual feedback.

## Current checkpoint: FT-005 interactive website preview

Status: PARTIAL — implementation and local launch complete, actual browser
visual verification blocked. Started clean on `feat/ft-004-image-evidence`
at `a1dd87ecb4ee67e6fc396c223f8cdaecf2544568`; created
`feat/ft-005-visual-preview`. No unrelated work was present. Earlier
no-website statements below describe earlier checkpoints, not current status.

Implemented a local React/TypeScript/Vite frontend in frontend/: graphite
workspace, teal controls, amber attention states; connected Commander and
Operator views; sample metrics and SVG process selection; pressure chart;
competing explanations/evidence gaps; task rationale; synthetic fixture
selection; readable/unreadable/access-blocked/wrong-equipment responses;
chronological evidence inspection; repeat observation and reset. Mobile layout
uses a dedicated view switch and contained chart/schematic scroll areas.

The persistent banner labels "Interactive demo — sample data". All sample
results are deterministic; live AI is not connected. Single-tab in-memory
state only, cleared on refresh/reset. No cross-tab/device/cloud sync,
equipment action, diagnosis, verified recovery, backend, or provider call.
Committed synthetic PNGs are reused directly; no personal uploads or model
output are used. UI does not fabricate tokens, latency, or confidence scores.

Tooling verified: Node 22.14.0 / npm 10.9.2. Added only pinned React/ReactDOM
19.3.1, TypeScript 7.0.2, Vite 8.3.5, and React/ReactDOM types 19.3.0, with
frontend/package-lock.json. Node >=22.12 is required for Vite and the test
runner. Package metadata compatibility was checked against npm registry and
the official Vite Node requirements. No additional UI/chart/icon libraries.

Checks: npm build/type check passed; 6 Node state-transition tests passed
(incident assignment, four evidence outcomes, duplicate submission guard,
repeat observation preserving provenance, reset). All 35 existing Python
offline tests passed with zero socket connection attempts. Python source
is unchanged. Initial build caught a TypeScript action-narrowing error;
corrected before the passing final checks. An initial install invocation
resolved the wrong directory; rerun in frontend installed the pinned packages.

Local server: http://127.0.0.1:5173/ (strict port, loopback only). HTTP readiness,
served Operator module, and synthetic PNG each returned 200. Dev server is
left running if the environment retains its process; exact restart/install/
build commands are in README and [preview guide](preview.md).

Browser limitation: inventory returned no browsers, and opening iab returned
"Browser is not available: iab". Therefore no 1440x900 desktop or 390x844
mobile journey was actually exercised. Keyboard navigation/focus, rendered
contrast, overflow, modal behavior, fixture/error states, and visual polish
remain unverified in a browser. No screenshots were captured or inspected;
do not confuse build/state tests or HTTP 200 with browser testing.
Ignored `.local/visual/ft-005/verification.json` records this limitation,
check results, and source hashes tied to the tested code. Screenshot directory
exists for later manual review, but contains no screenshot evidence.

Source files stay below 500 lines. Dependencies/build output, local logs,
ledger, and visual artifacts remain ignored. Scoped diff and staged secret
review precede commit/push; delivery SHA, remote match, final status, and
available CI are established by command results. No public deployment,
merge, or inference in FT-005. Submission product/runtime gates stay open.

Exact next action: founder opens the local URL and performs the desktop and
phone manual-review sequence in docs/preview.md, then supplies visual feedback.
Do not start backend integration, live AI, vision, or deployment from this
partial preview checkpoint. Stop for founder feedback after delivery.

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
