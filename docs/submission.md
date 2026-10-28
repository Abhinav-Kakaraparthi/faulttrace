# Hackathon submission checklist

Event: Nebius x NVIDIA Global AI Hackathon
Deadline: October 30, 2026, 1:00 p.m. America/New_York
Internal submission target: October 29, 2026
Recommended track: Best Apps and Agents

Official sources:
- https://nebiusglobalaihackathon.devpost.com/rules
- https://nebiusglobalaihackathon.devpost.com/details/faqs

Worker B's backend handoff `85d65c8` and tested application `e956bd4` each have
passing exact-SHA CI (195 backend / 51 frontend, zero forbidden external attempts,
dependency/type/build checks). Auth, server assignments/scoping and fail-closed
local release startup are implemented on B's unintegrated branch. Coordinator's
focused review reproduced a same-creator concurrent creation replay returning
200/403 instead of one reused result; B correction is required before integration.
No credential/API-contract change is requested; A's memory-only frontend follow-up
continues against B's relayed contract. No worker code was edited or integrated.
Backend checks do not close combined auth/browser, TLS, hosting, Windows ACL or
Linux PNG-byte portability gates. No submission checkbox changed; see state.md
for the exact finding and sequential integration prerequisites.

Worker C's four drafts at `b0de010addad04c72923d2feac59e7f7e5a42b18` were
reviewed without integration. [Exact-SHA CI passed](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40587796095)
(175 backend / 51 frontend, dependency/type/build checks; zero forbidden attempts).
Its demo script is an offline rehearsal, not recorded live integration footage.
[Final-video revision plan](final-video-revision-plan.md) prepares actual in-app
NVIDIA/Nebius capture only after B/A contract, integration, CI and manual review;
no requests or footage are authorized/executed here. Simulated equipment and any
mock footage must stay explicit. Real-photo accuracy remains unverified. Rules
and FAQ rechecked October 27; eligibility, final release CI, browser, auth, hosting,
video and submission gates remain open. B's finalized contract then A's auth
follow-up are the next implementation dependency; no checkboxes changed.

Worker A handoff `e9efbb61db4b13b78d314ee0d562fa74f2366f0b` is documentation
only; coordinator verified [successful exact-SHA CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40587272362)
(175 backend / 51 frontend tests, typecheck/build). Static checks PASS; browser
acceptance remains BLOCKED with no screenshots or exercised interactions. No
visual, authentication or release gate is newly satisfied, and no integration
has occurred. Combined-auth acceptance will use founder manual review.

Current-build visual review has fifteen isolated, inference-disabled scenario
pairs prepared with clearly labeled test output and controlled clocks. Setup,
HTTP readiness and build checks are not browser/mobile/keyboard, upload-progress
or camera acceptance. Those gates remain unchecked; no provider requests or new
live-model evidence were produced. First review: 5190/commander and /operator.

FT-012: new simulated investigations connect planner tasks, independent human
evidence, explicit correction approval and telemetry verification through shared
references. 175 backend/51 frontend offline tests and type/build pass, including
failure, dispute, stale evidence, ineffective correction and relapse. Scripted
provider doubles do not establish live reasoning or photographic accuracy.
[Implementation CI passed](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40534982605)
at `b8fc87771c4906f5477dd515ab14407604b6764f`; a fresh isolated offline-double
preview is available on 5182/8782. HTTP readiness is not browser acceptance.
Browser/mobile, server-enforced roles, live walkthrough and hosting remain open;
no product checkbox is newly satisfied. [Scope and review plan](unified-investigation.md).

CI checkpoint: push/PR backend and frontend jobs use no provider secrets and a
network-guarded Python suite. Local clean installations and hosted
[run 40399590742](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40399590742)
at `1b8249f704a900323ca71d115866704ba88fc452` pass 162 backend / 45 frontend
tests, dependency checks, typecheck and build. Backend uses the verified Windows
fixture environment; Linux PNG byte regeneration failed and remains a limitation.
The final submission revision has not been selected, so its CI checkbox stays
unchecked. Static tests do not establish browser or deployment acceptance.

FT-011 connects validated photo claims to saved observation-planner context, with
compatibility/dispute/freshness assessment, explicit Operator handoff, accepted
citations and source-photo clarification links. 159 backend/45 frontend offline
tests plus type/build pass. Provider doubles are not live adaptive evidence;
desktop/mobile/keyboard browser verification is blocked. Correction policy,
photographic-accuracy evaluation and deployment gates remain open. No checkbox
is newly satisfied. [FT-011 scope and next acceptance action](photo-planning.md).

FT-010 implements a bounded photographic-observation contract and explicit
NVIDIA analysis using existing opt-in, worker, receipts and ledger. New results
retain units/uncertainty and remain outside correction assessment; FT-011 permits
their bounded use as unverified observation-planning claims only.
148 backend and 40 frontend tests plus type/build previously passed offline.
The completed standalone call below establishes contract compatibility, not
photographic accuracy or browser acceptance. The independently labeled batch
remains a plan; no labels or ground truth have been invented.
[Contract/evaluation plan](photographic-analysis.md).
No submission checkbox is newly satisfied.

User-relayed Nebius confirmation supports photographic-only reasoning_effort=none;
148 backend/40 frontend tests and type/build pass offline. The first completed
standalone real-photo call passed its contract (stop, 0 reported reasoning tokens)
but returned 5000 psi versus preliminary reviewers' 800–850 bar. Those estimates
are not calibrated ground truth. No photographic accuracy, connected workflow or
correction-authorization gate is satisfied; existing records remain intact.

Photo-workflow refinement passes 40 frontend tests and type/build checks. Compact
records preserve every upload and full-image/interpretation inspection. User
desktop/390x844 review is attributed to the user; screenshot files and usable
browser automation were unavailable. No agent visual, keyboard or camera pass is
claimed, and no new runtime/accuracy gate is satisfied.

An isolated, inference-disabled photographic collection review is prepared with
an explicitly test-created task. API upload/storage/failure checks and offline
regressions pass; browser/mobile/keyboard/camera acceptance remains open.
[Review instructions](photo-evidence.md#isolated-inference-disabled-review).

A later standalone 4096-token experiment also truncated (finish_reason=length),
with no validated interpretation. Offline request audit found prose-only JSON,
without exact-alias evidence supporting a reasoning/structured-output override.
Production remains unchanged. [Findings and unsent support draft](photographic-analysis.md#repeated-truncation-request-audit-and-unsent-support-question).

FT-010 follow-up: one user-run standalone photo request failed strict completion
validation at 2048 completion tokens; exact historical finish reason is unknown.
Allowlisted finish reasons are retained for future diagnostics, without weakening
validation or changing requests. No live accuracy or compatibility gate is met by
this failed request or the offline follow-up. [Evidence and sources](photographic-analysis.md#non-stop-completion-investigation-offline-follow-up).

FT-009B adds collection-only original/permissioned photograph capture/upload and
stored-image presentation, with provenance and explicit identity/measurement
limits. Analog-gauge/valve AI capability remains unverified; strict vision and
recovery contracts are unchanged. 111 backend and 30 frontend tests, type/build
pass offline. No reference assets downloaded, licensed by assumption or added;
no provider requests/restarts. Browser/camera acceptance remains open and no
submission checkbox is newly satisfied. [Photo evidence scope](photo-evidence.md).

FT-009A adds dedicated Commander/Operator routes and components sharing the same
server workflow. 24 frontend tests and type/build pass. Role separation is UI
only; server authorization is an explicit required deployment gate. NVIDIA task
evidence and deterministic simulated recovery assessment remain separate. No
paid inference, hosting or browser visual acceptance is claimed. See
[architecture](architecture.md); broad submission gates remain unchecked.

FT-008A records a user-reported completed two-view simulated recovery walkthrough,
corroborated by read-only API state. Presentation now scopes evidence clearly,
shows a recovery/audit summary and separates simulated measurement from wall-clock
audit time. 18 frontend tests and type/build checks pass; source data/static
markup did not reproduce the pasted empty references/cells. Agent browser,
mobile/keyboard/visual acceptance and broad integration claims remain unverified.
No recovery policy, history, inference or submission checkbox changed.

FT-008 ships an offline-tested simulated evidence/working-diagnosis/human-approval/
correction/recovery journey. Independent measurement checks reject ineffective
correction and relapse; maintenance completion stays separate. 104 backend tests,
12 frontend tests and type/build checks pass. No paid inference, real equipment
control, browser visual pass, hosting or general AI reliability is established.
Existing broad submission gates stay unchecked pending their whole claims.
See [scope and inspection steps](recovery-journey.md).

Recheck official requirements before final submission.
Check an item only after recording evidence or a verified link.

Current offline correction: provider selects one action_id from application
observations filtered by asset availability, plus human escalation. Deterministic
mapping preserves the strict six-field internal policy; four required wire fields,
flat schema, no anyOf/uniqueItems. All 94 backend tests, 10 frontend tests and
type/build checks pass. Attempt d4430228-f580-4175-94ca-09fc667f0707 is present
once in the ledger, planner_invalid_combination, valid 578/956/1534 usage;
discarded fields remain unknown. No inference or server operations in this finalization.
Subsequent standalone action-ID verification at c4eb08d passed for one saved
refusal context: user-reported validated human escalation, no task or browser
journey. Ledger confirms attempt 1fbccbe3-a77d-4ddc-bea5-3bd2aa194e16 once,
valid 620/933/1553 usage. General planning reliability remains unverified;
FT-007 stays PARTIAL. No submission checkbox is newly satisfied.

Earlier implementation evidence: FT-007 ships offline-tested explicit text planning: bounded public evidence
context, strict observation/escalation policy, durable four-turn reservations,
stale/duplicate rejection and V-08 human reports. FT-007A adds strict schema
requests, fixed precise diagnostics and an accessible disabled-state treatment.
FT-007B adds status-derived HTTP diagnostics without retaining error bodies or
headers; historical fields remain unknown. 78 backend tests, 10 frontend tests
and type/build checks pass offline. The
first live planner request rejected with invalid_proposal (564/1483/2047 known
tokens, recorded once); its discarded output cannot establish the exact cause.
An isolated live request subsequently failed with provider_http_error and missing
usage (attempt 76a24b31-3b2e-4954-9954-dee9749ce7fa, recorded once); historical
HTTP status/cause are unrecoverable. No inference ran in FT-007B coding and no
successful connected planner or agent-operated browser review occurred; adaptive reasoning, mobile,
connected unreadable/refusal browser journeys, CI and hosting remain unverified.
No broad submission gate is checked by this checkpoint. Existing FT-006 user
browser evidence below remains attributed to that earlier implementation.

Standalone flat-schema provider compatibility is now verified for one saved
context at cdb9f4277127feb983eb246dad3190d13ca2cdee: attempt
87f5704f-d2ca-46ba-9967-7334363ac419 occurs once, validation passed with all six
fields/no extras (user-supplied proposal), 3375 ms and valid 328/618/946 usage.
This standalone call created no workflow task. A later read-only connected API
audit verified incident 8654a8a2-ff58-4344-a1c5-bd9d60c05a2c: attempts
5cb5ee1d-1845-47cf-a8b9-01714c6d9b47 and 75d1d983-4afb-4b98-ad75-8dedab22cae6
each occur once with matching SQLite/ledger receipts and created two F-17 tasks.
The simulated cannot-access report was included/cited in the second context,
but F-17 was repeated. Updated-context delivery and task creation are narrowly
verified, not useful adaptation or browser behavior. Refusal-aware validation
now blocks that asset and allows alternatives/escalation; seven focused tests
and all 88 backend tests pass offline with zero forbidden network attempts.
Historical accepted records remain unchanged. FT-007 remains PARTIAL; no broad
platform, browser or recovery checkbox is checked by this checkpoint.

Subsequent user diagnostic 17da531f-147f-4dc6-bf49-19c5580d739f implicated
uniqueItems (HTTP 400, BadRequestError; unknown usage, user reports ledger
recorded). Only that provider schema keyword was removed; application duplicate
rejection remains strict. All 79 backend tests pass. Corrected live compatibility
is pending the reserved single verification call; FT-007 remains PARTIAL and no
submission gate changes. This does not recover an earlier discarded response.

Latest user structural diagnostic 81d8d4d2-0d3c-4a36-9d81-a67b3acf8211
returned three fields matching partial anyOf properties; application rejected
planner_field_shape and retained 328/1125/1453 usage. That revision used a provider schema
flat with all six required fields and no anyOf/uniqueItems; application policy
is unchanged. Eight focused tests and 81 backend tests pass offline. This
implicates composition compatibility, not a proven provider bug; no live
verification or inference occurred in this correction. FT-007 stays PARTIAL.

FT-006 current scope: server-backed local incident/task/evidence persistence,
explicit image analysis path, and two-tab polling are implemented and tested
offline with fake transport. SQLite is temporary local architecture, not hosted
PostgreSQL. Connected clear-image submission/interpretation and user-reported
restart persistence are narrowly verified at implementation
4b15365e20ea0b7cacf1ad2d695163bf439690ec, with read-only SQLite/ledger
corroboration. Browser observations belong to the user, not agent automation.
No mobile/broad browser coverage, hosting, diagnosis, authorization, or recovery
is proven.
The two supplied standalone vision successes are recorded in state.md without
reimport/repeat calls. Full product/browser/runtime/deployment/eligibility gates
below remain open beyond the two bounded checks that follow.
See [workflow guide](evidence-workflow.md).

## FT-006 bounded verification evidence

- [x] Connected clear synthetic panel-a upload and actual NVIDIA interpretation: readable 180 kPa; user-performed browser verification, evidence a757eca7-445b-4d0c-b2ae-c70980b3f20d, attempt 1b6b653c-abc9-4ec2-a9be-96d24aba38cc. SQLite/ledger match, recorded once.
- [x] User-reported inference-disabled restart retained identical evidence, attempt, interpretation, and usage in Commander/Operator; no additional recorded analysis/ledger attempt.
- [ ] Connected unreadable/refusal paths verified in the browser.
- [ ] Mobile/accessibility/overflow review completed.

Latest read-only known ledger: 4085 input / 8670 output / 12755 total across 15
attempts (11 complete contributors). Connected pair: 836/2146/2982.
Separate historical manual record: 155 / 112 / 267.
Cross-record known: 4240 / 8782 / 13022 plus FOUR failed
requests with unknown consumption. No billing or complete-consumption claim.
Known sums match the latest expectations; records remain unchanged.
Full checklist gates remain unchecked unless their whole claim is verified.

FT-003 standalone synthetic text-probe acceptance is satisfied by corrected
live evidence at implementation c75a50be54ffb53fc728f6be0f14521e7b775bd1.
State.md records the sanitized executable result and separate external
manual evidence. Known cross-record usage is 234 input / 258 output / 492
total tokens, plus one failed request with unknown usage. The local ledger
covers only 79 / 146 / 225 known tokens plus that failed request; it excludes
the manual record, whose timestamp/revision are unavailable. No complete
consumption or cost claim follows. This does not verify application runtime
integration or the full platform claims below; those checkboxes remain open.
No website exists, so browser verification is not applicable to FT-003.

FT-004A prepares synthetic image fixtures and an offline evidence contract.
No authenticated model discovery or real image call has run; NVIDIA
`nvidia/Nemotron-3.5-Super-VL` is only a public-catalog candidate. Vision and
application runtime claims remain unverified. Fixtures were visually inspected,
but this is neither browser verification nor arbitrary analog-gauge accuracy.
See [image-probe guide](vision-probe.md). No submission checkboxes change.

FT-005 adds a local React/Vite interactive demo with sample Commander/Operator
views in one browser tab. It has no backend/provider connection or cross-session
sync. Browser access was unavailable to the agent, so desktop/mobile visual
and accessibility verification is pending; no screenshots were taken.
The checklist items below remain open. Local preview is not deployed hosting,
a completed live application, or independent recovery verification.

## Partner roadmap gates (planned only)

[Scope, dependencies and acceptance criteria](architecture.md#partner-integration-roadmap).
No new partner integration or credit entitlement is claimed. Current orchestration
is custom Python/SQLite; LangChain/LangGraph are not dependencies, and migration
is not required. Existing NVIDIA/Nebius runtime remains in place.

- [ ] **Nebius — conditional:** verify credited balance and restrictions before approving an evaluation/hosted-demo budget; no balance or redemption assumed.
- [ ] **LangSmith — optional/planned after CI:** deterministic reviewed-reference evaluation of contract validity, numeric accuracy and abstention, plus measured latency/usage; verify export controls excluding credentials, private images and raw reasoning by default.
- [ ] **Tavily — planned after the core connected journey:** confirmed equipment model, restricted official manufacturer domains, visible actual citations and rejection tests; reference context never becomes observed evidence or correction authority.
- [ ] **Toloka — conditional assessment:** confirm eligibility, reviewer suitability, cost/credit coverage and turnaround before use; approve labeling quality and data-permission/privacy controls.
- [ ] **Tandem — deferred/not selected:** establish concrete project benefit and a bounded acceptance test before reconsideration.

## Entry and eligibility

- [ ] Registration and eligibility confirmed.
- [ ] Team members and authorized representative confirmed.
- [ ] Track selected and fit explained.
- [ ] Ownership and third-party asset/dependency permissions checked.
- [ ] Project history assessed; significant updates explained if applicable.

## Required platform and product

- [ ] Actual NVIDIA open-model runtime inference through Nebius verified.
- [ ] Exact model identifiers and runtime integration documented.
- [ ] Commander/operator workflow works across browser sessions.
- [ ] Hidden faults produce evidence-dependent investigations.
- [ ] Uncertain/conflicting evidence and operator refusal handled.
- [ ] Independent verification rejects stale or transient recovery.
- [ ] Restart, duplicate submission, and stale proposal handling checked.
- [ ] Measured evaluation includes scenario count, latency, usage, and cost.
- [ ] Desktop/mobile browser review and relevant accessibility checks pass.
- [ ] Server-enforced identity, Commander/Operator roles and incident/evidence access verified, including direct API requests.
- [ ] Working demo URL verified from a fresh browser session.
- [ ] Judge testing instructions and dedicated access provided if needed.
- [ ] Free judge access maintained through December 15, 2026.
- [ ] Hosting and inference budget covers the judging period.

## Public source and reproducibility

- [x] GitHub repository verified PUBLIC (repository API, October 24, 2026).
- [x] MIT LICENSE present and automatically detected by GitHub (SPDX MIT; repository and license APIs rechecked October 24, 2026).
- [ ] Necessary source and permitted assets included.
- [ ] Clean setup and run instructions verified independently.
- [ ] Configuration examples contain no secrets.
- [ ] Dependencies and supported environment documented.
- [ ] CI passes for the submission revision.
- [ ] Tested release, deployment, and source SHA match.

## Submission materials

- [ ] English description explains audience, problem, and functionality.
- [ ] Actual NVIDIA/Nebius usage and workflow benefits explained.
- [ ] Other services and integrations disclosed accurately.
- [ ] Screenshots reflect the submitted application.
- [ ] Public YouTube video is under three minutes.
- [ ] Video shows actual application behavior and model integration.
- [ ] Video has no unlicensed music or third-party material.
- [ ] Nebius/NVIDIA feedback reflects actual experience.
- [ ] Limitations and measured claims are accurate.
- [ ] Prior-project significant-update explanation included if applicable.
- [ ] Physical AI footage requirement checked if track changes.
- [ ] City award claimed only with qualifying in-person attendance.
- [ ] Tavily bonus claimed only for useful functional runtime integration.

## Final submission

- [ ] Current official rules and FAQ checked for changes/conflicts.
- [ ] Every required form field completed and reviewed.
- [ ] Demo, repository, video, and documentation links tested.
- [ ] Entry submitted before the deadline.
- [ ] Submission confirmation retained.
- [ ] Final release and submission materials preserved.
