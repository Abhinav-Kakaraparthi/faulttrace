# Provider smoke test

Current application status: FT-007 adds explicit observation planning to the
local server-backed workflow. Start incident creates no automatic task;
Choose next observation proposes F-17 local DP, V-08 position-only, or human
escalation using NVIDIA Nano. Strict application validation checks registered
asset/capability combinations, existing references and context revision.
The provider now chooses one action_id from registered, currently available
observations or human escalation; application code maps it to the existing
internal fields. Output must contain exactly action_id, context_revision,
evidence_refs and explanation_code. Inaccessible observations are omitted from
the enum/catalog and independently rejected. The four-field flat contract passed
one standalone saved-refusal-context test at c4eb08d: the user reports validated
human escalation. Attempt 1fbccbe3-a77d-4ddc-bea5-3bd2aa194e16 is recorded once,
validation passed, valid 620/933/1553 usage. No task was created or browser
behavior verified; general planning reliability remains open. No inference,
server operations or history changes occurred in this documentation finalization.
Application templates generate instructions and short explanation text.
No output grants equipment authority, diagnostic certainty or recovery.
V-08 position reports are explicitly human-reported, not image-verified.
See [workflow guide](evidence-workflow.md) for exact manual restart commands
and the audited two-call connected API record and refusal-aware policy.
FT-007A adds a documented strict JSON-schema request and precise sanitized
shape/type/revision/reference/combination/explanation diagnostics. Exact Nano
connected runtime compatibility still needs live verification; application policy
remains mandatory. No inference or server restart was performed in FT-007A.
Useful live adaptive reasoning remains unverified. A read-only audit of incident
8654a8a2-ff58-4344-a1c5-bd9d60c05a2c verified the connected API pipeline:
two accepted planning attempts, each once with SQLite/ledger receipts matching,
created two F-17 tasks. The simulated cannot-access report after the first task
was present and cited in the second context/proposal, but F-17 was requested
again. This proves updated-context delivery/task persistence, not a useful
response to refusal, real field evidence, or an agent-operated browser journey.

New policy blocks another observation request for an asset with unresolved
cannot-access. Context lists unavailable_assets from full history; instructions
require an available alternative or escalation, and deterministic validation
rejects a violation with planner_asset_unavailable. Existing tasks/history are
not rewritten, cancelled or retried. There is no access-clearance workflow;
reopening or later observations do not silently restore availability. The fix
has offline evidence only: seven focused tests and all 88 backend tests pass,
with zero forbidden network attempts under the socket guard. FT-007 remains
PARTIAL and browser review is open.

Standalone flat-schema compatibility passed at implementation
cdb9f4277127feb983eb246dad3190d13ca2cdee for the saved context. Ledger confirms
87f5704f-d2ca-46ba-9967-7334363ac419 once: 2026-10-25T18:53:19.337482+00:00,
response chatcmpl-fd86af00-2a1a-4da7-9ef6-134fb58b0778, exact Nano model,
3375 ms, valid 328/618/946 usage, validation passed. The user reports all six
fields/no extras and the F-17/READ_LOCAL_DP proposal with revision 1,
telemetry-001 reference and evidence_gap explanation. No workflow task was
created by this standalone call. The later connected API evidence is described
above; its repeated inaccessible-task limitation remains part of the record.

Earlier structural diagnostic 81d8d4d2-0d3c-4a36-9d81-a67b3acf8211 returned
only kind/asset_id/capability, matching the old partial anyOf branch properties.
Application rejection and 328/1125/1453 usage are recorded once. This implicates
composition compatibility, not a proven provider bug. Only provider root anyOf
and its unused branch construction were removed: that revision used a flat schema with six
required fields; application combination/reference/shape/revision/explanation
checks remain strict. Eight focused tests and 81 backend tests pass offline;
no inference ran in that coding step. The later standalone compatibility success
above applies only to its saved context, not the full connected journey.

The user's diagnostic reproduction 17da531f-147f-4dc6-bf49-19c5580d739f
returned HTTP 400 / BadRequestError, with redacted message
"[redacted] error [redacted] uniqueItems" and unknown usage recorded in the
ledger. The narrow correction removes only provider-facing uniqueItems;
application-side duplicate rejection remains strict. Other schema support is
still unverified. No historical body was recovered. All 79 backend tests pass;
the later flat-schema success above is separate evidence, not recovery of the
discarded HTTP body. No call ran in that coding step.

FT-007B adds numeric HTTP status and a fixed status-derived category to new
failure receipts, ledger records and the UI. Bodies/headers are never read or
retained; status is not a proven provider cause. Historical missing fields stay
unknown without rewriting records. The isolated HTTP-failed attempt
76a24b31-3b2e-4954-9954-dee9749ce7fa was verified once in SQLite/ledger, with
missing usage, no task and three turns left. No status/root cause is recoverable.
The existing schema was reviewed but not changed: no confirmed incompatibility;
exact model/schema support remains unverified. See the workflow guide for a
proposed single-call fresh isolated diagnostic case, not run in this checkpoint.

The workflow keeps the earlier sample preview separate. See the workflow guide
for exact setup/URLs and the completed FT-006 clear-image evidence. Earlier
no-backend/no-vision statements below describe their original checkpoints.
Connected clear-image submission/interpretation and user-reported restart
persistence are now narrowly verified at implementation
4b15365e20ea0b7cacf1ad2d695163bf439690ec. The user performed browser actions
and confirmed identical evidence/attempt/interpretation/usage in both tabs
after restarting inference-disabled. The agent corroborated SQLite/ledger
records read-only; it did not operate a browser, replay/import analysis, or
inspect private images. Mobile and connected unreadable/refusal paths remain open.

One simulated incident and its task/evidence history persist in local SQLite, an explicit
portable single-instance departure from planned PostgreSQL. Images are decoded,
bounded, stripped of metadata, stored privately under ignored .local, and
retrieved by scoped evidence UUID only. User uploads, verified fixture-origin
bytes, human refusals, and model interpretations remain distinguishable.
No asset identity, equipment authorization, diagnosis, or recovery follows.

Commander and Operator poll the same local API in separate tabs. Upload is
separate from Analyze image. Backend opt-in and an environment key are required
for actual inference; both are never exposed to the frontend. Coding/test
verification used fake provider transport only. Pending/accepted/unreadable/
refused/failed/stale/uncertain states and known/unknown per-call usage are shown.

Revision/idempotency checks and a durable reservation prevent duplicate calls.
One worker serializes planning, image analysis and accounting without holding a SQLite transaction
during network I/O. Interruption is uncertain, never automatically retried;
receipt reconciliation can repeat accounting only. No auth, user isolation,
public-host hardening, multi-instance queue, or recovery/maintenance engine
exists. Planning is limited to four reserved turns per incident, with duplicate
context/click reuse and stale-result rejection. Interrupted turns stay uncertain
and consume budget; known/partial usage survives rejected proposals. The bounded
context includes only public telemetry and recent observations, not fixture
answers, hidden simulator labels or raw notes. Conflicting observations remain
in the evidence history. Trust only local users/processes; do not expose these dev servers.

Latest read-only accounting found 15 ledger attempts, 11 with complete known
usage: 4085 input / 8670 output / 12755 total. The connected pair contributes
836/2146/2982. Separate historical manual success
155 / 112 / 267 gives cross-record known 4240 / 8782 / 13022. Four attempts have
unknown usage; partial/invalid/inconsistent counts are zero. Expectations match;
no records were imported or changed. Historical failures remain preserved.
Two digital fixtures cannot establish arbitrary gauge accuracy or broad
application runtime coverage.

The first live planner attempt 13d345c9-3480-45bc-a4c6-c2260b319300 rejected
with invalid_proposal, retaining valid 564 / 1483 / 2047 usage once. Its context
included accepted clear-image evidence and the simulated pressure discrepancy.
Output was discarded, so the exact defect and reasoning are unknowable.
Three turns remain, but revision 1 is already attempted. The disabled button
now looks disabled and links to its visible explanation. Do not reset history,
invent a refusal, or reopen just to change revision. A genuine reassessment
and new truthful evidence are prerequisites for the later one-call proposal;
otherwise testing remains blocked. See the guide's bounded recovery path.

The connected record is evidence a757eca7-445b-4d0c-b2ae-c70980b3f20d,
attempt 1b6b653c-abc9-4ec2-a9be-96d24aba38cc: readable 180 kPa, 1938 ms,
438 input / 339 output / 777 total tokens. SQLite/ledger receipts match exactly
and the attempt occurs once; no additional recorded attempt appeared during
restart. Origin stays user-upload, with original hash matching panel-a; no
metadata was rewritten. The interpretation proves no asset identity, diagnosis,
action authorization, or recovery. See state.md for the sanitized receipt.

Agent browser access remains unavailable; no agent-operated visual pass or
screenshot inspection is claimed. User observations are attributed explicitly.
Mobile, connected unreadable/refusal, adaptive planning, recovery, CI, and
hosting remain open. FT-007B has 78 passing offline backend tests, 10 frontend
tests and a passing type/build check. Browser surfaces remain unavailable;
these checks do not establish a visual pass or live adaptive reasoning.

Transport sends one synthetic text request to the fixed Nebius endpoint and
model. Validation independently checks the response envelope and exact
observation-only proposal. A valid proposal grants no authority and executes
no equipment action. This paragraph describes the original standalone FT-003
probe; the separately validated application planner now exists but awaits live verification.

The transport uses a 60-second socket timeout, no retries, no redirects, a
2048 output-token cap, and a 256 KiB response-body limit. A socket timeout
limits blocking socket operations; it is not a hard whole-process deadline.
Slow progress can exceed 60 seconds overall. Truncated output is rejected.

NEBIUS_API_KEY is read only from the environment. Errors use fixed codes;
provider bodies, headers, reasoning, and environment values are not logged.
Receipts contain narrowly validated metadata, never raw model content.
Missing usage remains unknown. No dollar cost is estimated.

FT-003A accepts `tool_calls` only when absent, null, or an empty JSON array.
Nonempty arrays and malformed values fail. Fixed codes distinguish
`invalid_message_shape`, `invalid_message_role`, `message_refusal`,
`unexpected_tool_calls`, and `unexpected_function_call`. Function-call,
finish-reason, content, and exact observation-only proposal checks remain
strict. Model output never grants equipment authority.

Metadata and usage are extracted before completion validation. Valid model,
response ID, and individual token counters survive a rejected proposal.
Invalid or missing fields remain null; booleans are not token counts.
`usage_status` distinguishes missing, partial, valid, invalid, and inconsistent
accounting. Three present counts must satisfy prompt + completion = total;
otherwise `inconsistent_usage` is reported. No missing count is derived.
`transport_invoked` records calling the transport, not completed inference.
For older receipts lacking this field, null means unknown.

Each invocation gets a UUID attempt ID. The CLI persists only allowlisted,
validated receipt fields to `.local/nebius-usage.json`, already gitignored.
It never persists raw responses, content, reasoning, headers, or credentials.
Offline tests always use temporary ledgers. Offline CLI commands:

```powershell
& $py -m faulttrace.probe --ledger-summary
& $py -m faulttrace.probe --import-receipt 'C:\path\to\sanitized-receipt.json'
```

`$py` is the interpreter configured in README. `--ledger PATH` overrides the
location. Importing a modern receipt retains its attempt ID; legacy imports
get a deterministic ID from a fingerprint and retain unknown usage. The
original receipt is read only. Reimporting the same receipt does not add
tokens; conflicting duplicates fail without overwriting the existing record.

`known_tokens` sums prompt/input, completion/output, and total independently.
`contributing_attempts` shows the number of known counters for each sum.
Zero contributors means unknown consumption, even if the sum displays 0.
Valid partial counters survive invalid sibling counters. Contradictory triples
are retained but excluded from sums. `usage_states` and
`usage_unknown_or_invalid_attempts` identify missing/partial/invalid/inconsistent
attempts. `all_recorded_usage_complete` refers only to this ledger's receipts;
it does not establish account-wide consumption. Historical manual tests,
other processes, lost receipts, and failed persistence can be absent.
This is provider-reported accounting for requests to the NVIDIA model, not
proof of completed inference, a provider billing statement, or a cost estimate.

An exclusive `.lock` serializes writers; a temporary file in the same directory
is flushed and fsynced before atomic replacement. Read, write, lock, capacity,
and conflicting-duplicate failures use fixed codes. A persistence failure makes
the CLI exit 1, even if proposal validation passed, while preserving the
sanitized receipt in stdout for later import. Disk-full or crash recovery may
require restoring a trusted receipt. A crash can leave a lock: confirm no
writer is running before manually removing it. The ledger is bounded to
4 MiB and is not a database or account-wide audit service. Atomic replacement
does not promise survival of every filesystem/power failure.

Offline tests use fake transport and never contact Nebius. The live command
requires explicit --live and can consume existing authorized credits.
Do not retry a failed live request automatically.

This proves connectivity and one simple output contract only. It does not
prove diagnosis, vision capability, production readiness, eligibility,
identity of equipment, or completed work. There is no website yet; browser
testing is not applicable to FT-003.

FT-003 standalone text-probe acceptance is now satisfied: the corrected
request passed at implementation `c75a50be54ffb53fc728f6be0f14521e7b775bd1`.
The earlier failed request and its lost response remain unknown; successful
validation does not repair that accounting gap. The final evidence record
is a later documentation change, not another inference run.

The local ledger contains the corrected request once (79 input, 146 output,
225 total) and one failed request with missing usage. A distinct external
manual success used 155 input, 112 output, 267 total tokens. Cross-record
known sums are 234 input, 258 output, 492 total, plus unknown failed usage.
The manual success has no exact timestamp or application source revision.
The importer requires a timestamp and cannot preserve external provenance;
legacy import would also discard its known counts. It was not imported or
attributed to code. Its separate historical accounting is documented in
state.md. Neither ledger totals nor cross-record totals establish full
consumption or billing. No further inference or FT-004 work occurs during
evidence finalization; application integration and vision remain open gates.

FT-004A adds offline image-evidence preparation, not live vision validation.
The [image-probe guide](vision-probe.md) contains official model sources and
exact later Windows-terminal commands. The candidate is NVIDIA
`nvidia/Nemotron-3.5-Super-VL`, separately listed for image input; our existing
Nano text model grants no image capability. Public listing is not account
verification. No authenticated model/account query or inference ran in FT-004A.

Image observations are separate from planner proposals: readability, nullable
reading/unit, and a task-provided image reference only. The numeric range is
a synthetic fixture constraint, never an equipment limit. No asset identity,
diagnosis, authorization, or recovery claim comes from image output. The
shared envelope checks remain strict, and the text validator still accepts
only its original observation-only proposal. A valid image contract can still
contain a wrong transcription, so fixture correctness must be checked separately.

Both invented PNGs were visually inspected: the clear digital display and
the same display fully replaced by opaque pixels. No expected answer enters
the prompt, filename, metadata, or payload description. Existing Pillow was
used only for offline generation; production probing requires no image library.
Tests check opaque occlusion and regeneration as well as the contract.
These fixtures cannot establish arbitrary analog-gauge accuracy.

The transport retains its timeout, body bound, cap, and no-retry behavior.
The same ledger accepts the two exact allowlisted text/vision model IDs;
accounting is extracted before evidence validation. No accounting infrastructure
was expanded. Raw model responses/reasoning are never persisted or printed.
No website exists; browser journeys are not applicable to this checkpoint.

FT-005 now adds a local interactive website preview. This supersedes the
earlier no-website statements for current UI status, without changing past
checkpoint evidence. Open http://127.0.0.1:5173/ while its server is running.
See [preview guide](preview.md) for exact npm install/start/build commands
and the manual desktop/mobile review sequence.

Commander and Operator share in-memory state in a single tab: incident start,
equipment inspection, task rationale, fixture selection/submission, refusal,
unreadable evidence, inspection dialog, repeat observation, and reset.
Clear sample evidence and refusal/unreadable paths lead to distinct visible
states. The clear result is a deterministic fixture transcription, not a
vision-model result. No diagnosis, recovery, or equipment authorization is
performed. All data is sample; no live AI, backend, telemetry, cloud sync,
or inference billing is connected. Refresh loses local state.

The agent could not access a browser surface: inventory empty, iab unavailable.
Build/type checks and state tests pass, but actual desktop/mobile visuals,
keyboard behavior, rendered contrast, overflow, and screenshots remain pending
founder review. No visual-verification claim follows from successful builds.

The bounded FT-005 founder refinement keeps the accepted palette, replaces
the slogan with a compact incident title, and prioritizes the observation
task beside the process. Explanations remain below the task. The task shows
equipment, requested evidence, state, rationale, and an operator action with
destination focus. Active incident is status rather than a disabled action;
schematic labels are separated and equipment details remain expandable.
Browser access is still unavailable, so before/after screenshots and actual
desktop/mobile/keyboard verification remain pending founder review. See
the updated preview guide; no backend or inference was introduced.
