# FaultTrace architecture: current local implementation and public target

Commander `/commander` and Operator `/operator` consume
one server-backed workflow snapshot; the pages do not own separate incident,
task, evidence, approval or recovery stores. Each tab polls the same API. Route
identity alone is not authorization: the integrated release now has server roles,
grants and assignments; the judge service has isolated HttpOnly visitor sessions.
One demo visitor may use both roles. Neither is a public deployment claim.
The current package adds explicit budgeted live-demo mode, metadata-only tracing,
restricted documentation references and simulated monitoring; live/public acceptance
remains open. [Current checks and free-hosting assessment](sprint-release.md).

## Target boundaries

```mermaid
flowchart LR
  C[Commander application] --> A[Public application API]
  O[Operator application] --> A
  S[Private simulator / telemetry source] --> D[Authenticated anomaly delivery]
  D --> A
  A --> W[Durable investigation workflow]
  W --> P[Deterministic policy and approvals]
  W --> N[NVIDIA models via Nebius Token Factory]
  W --> DB[Persistent workflow and evidence metadata]
  W --> E[Private evidence storage]
  P --> S
  S --> V[Independent recovery verifier]
  V --> W
  W --> L[Sanitized audit and accounting]
  K[Server secret store] --> W
```

The diagram is the target, not a deployment claim. An anomaly delivers public
measurements and references, not simulator fault labels or answer keys. The
model proposes bounded observations. Application policy validates references,
capabilities, context freshness and budgets. A human approves a registered
simulated correction; a separate verifier derives recovery from subsequent
measurements. Neither a model response nor an operator completion grants recovery.

| Boundary | Exists now | Future / required gate |
| --- | --- | --- |
| Application and API | React pages, FastAPI, compiled same-origin SPA/API wrapper and tested Docker package | Public HTTPS hosting, ingress/quotas and browser acceptance |
| Commander and Operator | Dedicated routes, server-enforced release identity/grants/assignments; isolated judge cookies, one visitor deliberately uses both roles | Deployed HTTPS/session/image and founder browser acceptance; demo role switching is not two-employee separation |
| Durable workflow | Single-instance SQLite records, reserved planning turns, stale revisions, idempotent operations, serialized inference worker and recovery of interrupted attempts | Production durable job execution, multi-instance coordination, migrations, backup and restore; no external workflow engine is installed |
| NVIDIA through Nebius | Text `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`; image `nvidia/Nemotron-3.5-Super-VL`; existing bounded transport and independent output validation | Broader connected adaptive evaluation and integrated evidence-based recovery reasoning remain unverified |
| Private simulator | Private fixture state; paused new-demo human-report clock, explicit accelerated sample monitoring; public measurements only | No real sensor feed, equipment-control connection or hidden truth in model context |
| Anomaly delivery | Explicit incident start; explicit steps or human-started accelerated monitoring produce simulated samples | No real sensor feed; authenticated external anomaly ingestion remains future work |
| Workflow/evidence persistence | Private SQLite, image files and sanitized ledger; actual Docker volume/restart checks pass | Render Free + external Postgres/private objects is assessed only; no storage migration. Actual hosting/backup/quotas remain open |
| Secrets | Backend-only NEBIUS_API_KEY environment; inference disabled by default; no key in browser, URLs, Git or evidence | Managed server-side secret storage and rotation; browser-facing APIs must never accept provider keys |
| Logs/accounting | Sanitized receipts plus persistent global/session allowances; optional metadata-only LangSmith export is offline-tested | Actual trace visibility, operational retention and public abuse/load acceptance remain unverified |
| Policy and verifier | Registered actions, role/revision/refusal/reference guards, human approval, independent unchanged sample verifier and explicit simulated monitoring | Broader scenario evaluation and live/browser acceptance; no real equipment control or industrial safety claim |

## Partner-integration roadmap

Current orchestration is **custom Python with SQLite**. LangChain and LangGraph
are not dependencies and no orchestration migration is required. NVIDIA inference
is retained; Tavily and LangSmith adapters are now implemented/offline-tested.
Actual new live integrations, credited balance and offer eligibility remain open.
Zero-cost external durable hosting would require a separate storage migration,
which has not begun; do not confuse that work with an orchestration replacement.

| Partner / status | Dependencies and planned scope | Acceptance before use or claiming integration |
| --- | --- | --- |
| **Nebius Token Factory — conditional budget check** | Retain NVIDIA runtime inference. Verify credited balance before budgeting evaluation or hosted-demo usage. | Privately confirm usable credited balance, expiry/restrictions and verification date; approve a bounded allocation before calls. Do not assume an offer was redeemed or that unknown usage is zero. |
| **LangSmith — implemented, offline-tested metadata tracing** | Explicit export opt-in and server-only key/project; no orchestration migration. Reviewed-reference evaluation remains planned. | Verify actual trace visibility, allowlisted usage/latency/outcomes and failure isolation. No credentials, images, raw reasoning or account identities exported. Numeric/abstention evaluation needs reviewed references. |
| **Tavily — implemented, offline-tested reference lookup** | Human-confirmed model, registered official manufacturer domain, explicit key/opt-in and global/session reservation. | Verify one useful real citation/retrieval time. References are untrusted, outside telemetry/evidence/correction policy. No bonus acceptance from offline doubles. |
| **Toloka — conditional offer assessment** | Independently labeled photo evaluation plan and permission/privacy review before sharing any data. | Confirm offer eligibility, reviewer suitability, credit coverage, actual cost and turnaround before use. Approve labeling instructions, independent review/disagreement handling and source/permission records; do not invent labels or treat preliminary estimates as calibrated truth. |
| **Tandem — deferred, not selected** | No concrete FaultTrace benefit has been established. | Reconsider only after a specific benefit and bounded acceptance test are documented, with dependency/privacy/cost review. No account, package or data transfer is selected now. |

These are planning decisions, not account creation, offer redemption, data export
or runtime changes. New spending and external-data use need applicable approval.
Track unverified gates in the [submission tracker](submission.md#partner-roadmap-gates-planned-only).

## FT-009B collection boundary

Camera/file uploads on assigned F-17/V-08 tasks use reference-photo purpose and
collected status; upload alone requests no inference. FT-010 adds a separate
explicit photo-observation contract through the existing worker/transport/ledger,
with contract/revision metadata, no replay and no historical receipt rewrite.
Task assignment does not prove photographed identity or instrument type. Actual
stored images and separate human/model records are shown in both workspaces.
Limits/private normalization persist; camera orientation is applied before
metadata removal. The API advertises the collection capability so newer UI
cannot accidentally use older analysis semantics. No migration, server restart,
provider call or recovery-policy change. See [photo evidence](photo-evidence.md)
for unverified analog/valve capabilities and actual source/license requirements.

## Evidence integration: actual scope

Both workspaces present the same real collections together, with distinct scope:

- `journey.observations`: simulated human pressure/position reports. These and
  stored simulator samples feed the deterministic fixture correction assessment.
- `evidence`: image uploads or structured reports for application-created
  observation tasks. NVIDIA image results are explicitly model interpretations,
  with their original source, validation and accounting. Human reports are not
  image-verified. FT-011 includes a bounded, validated photographic-claim projection
  in planner context, with original readings/units, compatibility, unknown identity,
  freshness and human/model disputes. Raw label text stays excluded. Explicit
  handoff enables clarification/escalation; no photographic claim satisfies the
  deterministic correction checklist. [FT-011 boundary](photo-planning.md).
- Planning receipts/proposals and human correction approval remain different
  records with different authority. No record is migrated or duplicated by UI.

**Photo model claims do not satisfy the simulated correction assessment.** New
FT-012 investigations project independently entered, compatible human task reports
into the existing deterministic assessment using the same evidence IDs as planning
and approval. Human confirmation/dispute preserves model and human sources; model
values never prefill a report. Unreviewed, conflicting or stale evidence blocks
approval. Registered simulated action and telemetry verification remain separate
authority boundaries. Historical runs retain the legacy parallel streams without
migration. This is application integration, not verified live AI recovery reasoning.
[Unified journey and offline review](unified-investigation.md).

The independent verifier consumes fresh post-correction samples and the execution
boundary, not private simulator outcomes or an LLM declaration. Maintenance
completion is separate. Thresholds and times are declared synthetic fixture
constraints in [the recovery guide](recovery-journey.md), not industrial limits.
Simulated measurement time differs from wall-clock audit time.

## Route and workspace contract

Commander owns incident creation, process/telemetry review, deterministic
assessment, optional NVIDIA observation planning, correction approval, recovery
progress and audit. Operator owns assigned observation instructions, uploads,
explicit image analysis, structured reports/refusals and approved simulated
completion acknowledgment. Operator contains no incident-start, planner,
Commander-approval or simulation-clock controls. Server APIs remain unchanged:
these presentation boundaries are not enforceable production roles yet.

`/?mode=connected&view=operator` resolves to `/operator`; Commander/default
connected URLs resolve to `/commander`. Dedicated paths override obsolete mode/
view parameters; unrelated query parameters and fragments are retained. Normal
links, reload, browser back/forward and modified-click/new-tab navigation are
supported by the client router. `/?mode=sample` retains the separately labeled
browser-only sample preview, never substituted for unavailable server data.
Unknown paths show an explicit page-not-found view.

Existing 5180 preview: `/commander` and `/operator`; no backend restart is needed
for this frontend-only checkpoint. See [startup commands](recovery-journey.md)
only if no preview is running; do not reset an existing run. Production hosting
must serve the SPA entry for both routes and proxy `/api` correctly.

## Evidence and open validation

24 frontend tests include route resolution and static React markup of both pages,
shared incident/references, role-specific controls, image/refusal/analysis paths,
recovery, missing telemetry and loading/offline states. TypeScript/Vite build
passes. No new dependency, backend policy change, provider request or deployment.
Browser inventory is empty; in-app browser opening failed. Actual 1440x900 and
390x844 layout, keyboard focus, history navigation, route reload, upload/error
journeys and recovery walkthrough remain required visual checks. Both dedicated route URLs and the legacy query URL returned HTTP 200 on the
existing preview. Static markup, build and HTTP route responses are not browser acceptance. Server role/access
checks are a separate required deployment gate, not satisfied by these tests.
