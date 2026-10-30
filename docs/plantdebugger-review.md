# PlantDebugger → FaultTrace: implementation review and bounded adaptation

Reviewed 30 October 2026. Reference commit: `d69507aa48aec773a5cf72761e5ff60c491eefc1`.
FaultTrace baseline: `871778aba3f5e7a755e019196e64979bdca8211c` on `feat/finish-integrated`.
Integration parent after review: `251c2b098a1fedd3fc6099e9058b50e79057b3a9`; its separate
connected-rehearsal tests/docs are preserved. Changes are isolated on `feat/real-photo-evidence-review`. This report distinguishes source review,
offline checks and missing live evidence. It does not claim the entire reference architecture was ported.

## 1. Finding and decision

The visual reference feels coherent because an investigation has a continuing owner. Field evidence
is a response to an outstanding agent request, not an unrelated record the user must manually route
through multiple subsystems. In the reference, the workflow pauses for physical input, resumes with
that result, revises its plan, dispatches the next bounded task and checks independent telemetry.

FaultTrace already has useful controls: task-linked evidence, versioned photo interpretations,
independent human reports, scoped approvals, deterministic recovery, durable receipts and spending
reservations. Its weak point is the connection between these components. A better theme alone does
not connect them. Nor does placing a synthetic display drawing inside an upload picker establish a
real photographic demonstration.

The implemented checkpoint removes a broken confirmation path and connects real-photo collection
and optional analysis. It preserves the existing NVIDIA/Nebius backend, authorization and allowance
mechanisms. It does **not** introduce automatic replanning, a new intervention catalog, site memory,
Google ADK, Gemini, Firestore or Cloud Run. Those are separate changes with separate acceptance gates.

## 2. Evidence reviewed

| Material | What was checked | Why it matters |
| --- | --- | --- |
| Reference README and architecture | Scope, process topology, roles, physical I/O loop, deployment modes | Establishes the intended behavior; distinguishes a demonstrator from plant control |
| Technical build article | Product framing, field evidence, changing decisions, simplification | The central problem is physical information/actions without an API, not dashboard styling |
| `field_ops/__init__.py`, `main.py` and manager subclasses | Which implementation is actually constructed | The final collaborative subclass overrides older QR and evidence behavior |
| `adk_orchestration.py` | Dynamic children, interrupts, resumption and terminal results | Confirms resumable orchestration exists in code |
| `planning.py`, `collaborative_planning.py` | Context, capabilities, schemas, decision guidance | Separates a dynamic choice from a fixed script; reveals strong scenario heuristics |
| `vision.py` | Live pixel analysis versus filename-driven offline fallback | Prevents mistaking an offline policy demo for computer vision |
| `collaborative_final.py`, `collaborative_manager.py` | Evidence intake, action evidence, bounded bypass logic | Explains why upload actually continues the investigation |
| `tools/verify.py`, action guard | Recovery tail, thresholds, bounds and replay prevention | Recovery is verified by code, not declared by a language model |
| `storage.py`, `adk_sessions.py`, history | Read model, evidence store, workflow history | Durable application state and durable agent invocation are different concerns |
| Deployment guide and orchestration tests | Service boundaries, credentials, model mode, pause/resume tests | Documents operational assumptions; tests are not live model benchmarks |
| FaultTrace frontend and workflow modules | Upload, analysis, human review, planning, approvals, recovery, session epochs | Traces the failure seen in the user's actual walkthrough |

Primary reference links, pinned where possible, are collected in section 12. The article was retrieved
through DEV's public article API when the normal page fetch failed. No live reference service was
probed, no reference deployment was run, and its production settings were not independently verified.

## 3. Actual reference execution path

### Runtime selection matters

Reading only the original manager gives an incomplete picture. The exported manager resolves to
`collaborative_final.FieldOpsManager`, which extends the collaborative and durable managers.
The final subclass permits direct inspection upload without manufacturing a QR verification event.
It retains the historical internal staging state but records the actual evidence binding in the audit.
Older QR-related documentation and base behavior therefore cannot be treated as the hero-path UI.

### Resumption, not a sequence of disconnected forms

`AdkDynamicFieldWorkflow` constructs a resumable ADK application. Its troubleshooting parent reruns
on resume, with stable step-specific child identities. A field image or manual action produces a
`RequestInput` interruption. The returned physical result is supplied as a function response to the
same invocation. The workflow then obtains updated planning context and decides again.

The context includes telemetry, completed tasks, current hypotheses, latest vision and verification,
remaining budget, permitted capabilities and approved site knowledge. The planner can request an
image, a bounded manual intervention, or escalation. It need not visit every node. Recovery after
one intervention is valid; an unsuccessful first action is not a requirement for a good demo.

This is a different responsibility from polling a UI. Polling merely displays saved state; it does
not make a workflow resumable, grant planner authority or supply the missing physical response.

### The topology is different

The reference models P-101, F-17, a **parallel manual bypass BV-104** and downstream flow measurement.
FaultTrace's current P-04 → F-17 → V-08 return line is a different fixture. V-08 is not BV-104, and its
72% feedback is not evidence of a bypass position. Renaming labels or copying the bypass drawing
would create a false process model unless the simulator, capability registry, evidence contracts,
action bounds and verifier changed together.

### Intervention evidence has target-dependent rules

The final manager sums completed bypass deltas and rejects movement beyond its modeled full-open
limit. A partial movement is confirmed through the operator/action flow and telemetry. Reaching
the mechanically marked full-open end state adds position-image evidence. That requirement follows
the physical target, not an arbitrary step number. It is not equivalent to accepting any photograph
as evidence that an intervention happened.

### Planning is dynamic but still scenario-guided

The structured planning instructions contain specific preferences, including non-invasive inspection
when useful, small bypass tests and RPM reductions. This is substantial scenario guidance. Calling
the reference completely unconstrained or wholly generic would overstate it. The transferable idea
is choosing among validated capabilities using new evidence, rather than copying its exact heuristic
or hiding a predetermined answer inside a model prompt.

## 4. Vision: what is real and what is a test double

| Reference component | Actual behavior | Adaptation decision |
| --- | --- | --- |
| `GeminiVisionAnalyzer` | Sends image bytes and a task question; ignores the filename; returns structured observations | Preserve the pixel-based, bounded-output principle using FaultTrace's existing NVIDIA vision model |
| `PolicyVisionAnalyzer` | Discards bytes and uses filename cues such as high-DP/open; explicitly labels itself offline policy | Do not copy this into a live vision demonstration |
| `ResilientVisionAnalyzer` | Can fall back when configured | Do not silently substitute fallback output for a failed live request |
| Prepared reference JPEGs | Present in the repository, but no reviewed camera-origin/licensing manifest establishes their photographic provenance | Do not relabel them as verified real photographs or copy them as plant evidence |
| Qualitative DP assessment | HIGH/NORMAL/UNCERTAIN and visual condition | Do not convert HIGH into a numeric kPa reading for FaultTrace's approval thresholds |
| Valve assessment | External visible position and uncertainty | Do not infer internal condition from handle orientation |

FaultTrace's new photographic contract already handles gauge/valve/other categories, measurement type,
visible units, numeric readings where supported, literal label transcription, external orientation and
bounded uncertainty reasons. Its older display-only contract has fewer fields and cannot establish
instrument type. General vision capability and end-to-end validated field interpretation are different
claims. Neither source review nor an offline double proves NVIDIA accuracy on arbitrary plant photos.

## 5. Why the current walkthrough got stuck

The failure has two independent causes. Treating it as only a dropdown mistake would be incorrect.

1. A synthetic panel was submitted through the regression-fixture path. Its analysis produced 180 kPa
   using the legacy display contract. The result and receipt were retained correctly.
2. The human form offered that image as a confirmable photographic claim. However,
   `investigation_evidence.photo_claim()` accepts the versioned photographic contract, not the legacy
   fixture contract. It therefore returned no compatible claim for this confirmation.
3. The entered observed asset was `unknown`, which independently prevented identity compatibility.
4. The backend saved the original report and unresolved flags instead of silently authorizing a
   correction. That preservation is correct. The UI failed to explain the incompatible path before
   the user spent time completing it.
5. Photograph review also has wall-clock freshness checks even while the simulated walkthrough clock
   pauses. A long manual walkthrough can introduce another blocker. Planning has a different photo
   freshness window; those windows must not be described as interchangeable.

Changing the selected identity to F-17 without evidence would not repair the contract mismatch, and
would manufacture identity. Deleting the unresolved report or resetting the incident would hide the
failure rather than fix the product. Historical records remain unchanged in this checkpoint.

## 6. Architecture comparison

| Concern | PlantDebugger reference | FaultTrace baseline | This checkpoint / remaining gap |
| --- | --- | --- | --- |
| Investigation ownership | Resumable agent invocation | Explicit planner/analysis/manual handoffs | Upload-to-analysis connected; automatic planner resumption remains absent |
| Next step | Registered image/action/escalation choice | F-17/V-08 observations or escalation | Existing planner retained; no falsely advertised new action catalog |
| Physical I/O | Image or bounded action response resumes workflow | Separate upload, analysis, handoff and human-report operations | Single explicit upload-and-analyze option plus visible current result |
| Vision | Live Gemini; separately labeled offline policy | NVIDIA photographic contract and legacy fixture contract | Legacy fixture no longer offered in hosted task entry or as confirmable photo evidence |
| Asset identity | Final collaborative flow uses image context | Human compatibility required; assignment/label is insufficient | Blank independent fields retained; no auto-confirmation |
| Correction | Several bounded interventions | One registered simulated F-17 replacement | Unchanged; a bypass intervention would require a new coherent fixture |
| Verification | At least three consecutive healthy tail samples | Five fresh post-action samples across forty simulated seconds | Existing stronger temporal rule retained, not replaced by reference thresholds |
| Knowledge | Explicit site assertions with review | No equivalent approved persistent site memory | Missing; image output must not be automatically learned |
| Durability | Field-ops store plus ADK invocation/session history | SQLite incident/task/evidence/outbox and monitor state | Existing store retained; frontend chaining is not a durable agent runner |
| Authorization | Hosted access controls and service IAM | Scoped sessions/roles, CSRF, current grants and epochs | No role bypass or provider key in browser |
| Deployment | Cloud Run, private simulator, Firestore, GCS, Vertex and logging | Existing Render service, persistent disk, Nebius/NVIDIA | No infrastructure migration or new cloud spend |
| Cost control | Bounded workflow and action budgets | Server/session inference reservations, uncertain charges retained | Existing limits remain authoritative; no resets or automatic retries |

## 7. Code changes made

### Real-photo workflow

`WorkflowController.submitPhoto()` owns a single busy interval covering upload, fresh state retrieval
and optional analysis reservation. It uses the evidence ID returned by the upload response. It does
not guess from the last element in an evidence list. Before analysis it checks incident identity,
exact expected context/task revisions, current task status, latest photo, analysis absence, advertised
contract and inference availability. The server performs its own authoritative checks afterward.

“Upload and analyze with NVIDIA” authorizes one analysis only after confirmed storage. “Collection
only” remains a separate explicit choice. An interrupted upload does not trigger analysis. A rejected
analysis allowance retains the image. Logout, access denial, competing evidence or changed context
stop the chain. Distinct idempotency keys cover upload and analysis; no automatic write retry exists.
This is browser-side coordination, not an exactly-once distributed transaction or durable resume.
Closing the tab after upload can leave a stored image awaiting explicit analysis; the current-photo
panel exposes that state on return.

`CurrentPhotograph` puts status, interpretation, inspection and the independent review link beside
photo collection. The user no longer needs to discover analysis hidden in historical evidence.
Inputs remain blank. A model result is never copied into a human assertion or used to approve an action.

### Confirmation compatibility

The human source picker offers photographic confirmation/dispute only for interpreted results with
the photographic contract. It explains legacy results instead of offering an impossible confirmation.
The backend remains the final arbiter of freshness, identity, compatibility and conflict. An unreadable
or uncertain result can still require clarification; a prominent model result is not a verified measurement.

### Real photographs and attribution

The hosted task entry no longer displays the synthetic fixture picker. Explicit local developer mode
can still exercise those regression fixtures. Existing tests and historical fixture records are retained.

Two real-photograph references are bundled: a digital pressure meter by Nick.follows and household
ball valves by NVgt156, both CC BY-SA 4.0. Source links, image credits and download controls accompany
them; `assets/reference-photos/provenance.json` records hashes, sizes, dimensions and download URLs.
They were downloaded as Wikimedia thumbnails without application retouching, fabricated tags,
compositing or generated readings. They are examples, not images of the simulated plant.

The meter photo includes multiple instruments and mBar markings. It is not a prepared successful
180 kPa F-17 sample. Its unsupported unit/mode ambiguity is an appropriate reason to abstain. The valve
photo has real pipework but no V-08 plant tag. Uploading it must not manufacture that identity.
The application does not automatically submit either reference or claim it satisfies the checklist.

## 8. What a full resumable loop still requires

A durable runner should consume a versioned physical-response event and compute the next transition
under the current incident revision. It needs persistent workflow/invocation identity, an authorized
continuation policy, idempotent step keys and a terminal state. Browser polling must remain a reader.
The runner must not acquire Commander privileges merely because an Operator uploaded a photo.

| Trigger | Required transition | Required protection |
| --- | --- | --- |
| Readable compatible photo | Preserve claim, ask for independent checks where policy requires them | No inferred identity, approval or recovery |
| Unreadable/incompatible photo | Request clarification or human investigation | New evidence required; no retry loop spending the remaining allowance |
| Independent field response | Rebuild visible planning context and reconsider permitted next step | Current revision, grants, unresolved conflicts and explicit continuation consent |
| Proposed intervention | Validate registered capability, arguments, bounds and evidence requirements | Approval binds the exact action and evidence revision |
| Operator action completion | Record physical response and collect post-action telemetry | Idempotent execution; no duplicate action on refresh/restart |
| Failed verification | Replan within remaining bounded budget or escalate | Never force a second action or falsely declare recovery |
| Verified recovery | Close operating recovery with source sample references | Keep root-cause confidence and maintenance status separate |

Before adding BV-104/RPM actions, implement the corresponding topology and simulator behavior,
capability schemas, independent action evidence, action-specific authorization and failure tests.
Do not graft reference bypass actions onto V-08. Approved site memory should be a separately reviewed
store with versioned assertions and revocation, not automatic training on uploaded labels.

## 9. Verification and its limits

- Frontend: 113 tests pass, including new transport, revision, consent, allowance, logout and legacy
  confirmation cases; TypeScript checking passes.
- Backend: 320 regression tests pass with the repository's network guard; zero external attempts.
- Combined contracts: release API and judge-demo session checks pass, with zero provider calls.
  The release contract now exercises the actual new collection pipeline against the ASGI API.
- Production and demo builds pass. Browser evidence is recorded separately in the review checkpoint.
- No hosted incident, environment variable, persistent disk, spending reservation or historical report
  was edited. No NVIDIA, Tavily or tracing request was issued by this work.
- Offline component/transport checks do not establish model accuracy. Offline browser checks do not
  establish hosted authentication, camera permissions, live inference or complete recovery acceptance.

The reference's pause/resume tests demonstrate orchestration behavior with scripted planners. They
are useful examples, not evidence that every live model handles every plant photo or chooses a safe
intervention. This review did not run its Google Cloud integration or deploy its services.

## 10. Deadline-focused integration order

1. Review the isolated diff against the current coordinator branch. Preserve unrelated work.
2. Integrate this photo checkpoint; run exact-SHA checks and the local browser harness on the combined
   revision. Do not infer acceptance from a previous deployed SHA or old screenshots.
3. Keep the current incident history and unresolved reports. Explain its actual blockers. Do not reset
   budgets or invent identity to produce a green outcome.
4. If a live real-photo trial is authorized within remaining allowance, use a genuinely acquired
   photograph and record the exact model, schema, request/result and resulting task transition.
   This trial has not been performed by this checkpoint.
5. Present the current product as a bounded assisted simulated investigation. Do not describe it as a
   completed autonomous PlantDebugger-equivalent implementation. Replanning, additional interventions
   and durable continuation remain explicit engineering scope.

## 11. Deployment implications

The reference deployment uses multiple Google services because of its chosen runtime and durability
requirements. Those service names are not prerequisites for the interaction pattern. A small SQLite
continuation journal and existing worker could support a future FaultTrace runner without migrating
clouds. That would still require concurrency, restart, authorization and budget tests.

This branch changes frontend workflow and documentation only. Existing backend endpoints, validators,
provider wrappers, simulator policy and deployment settings are preserved. Deployment must use the
reviewed integrated SHA on the existing service/disk after applicable checks. A branch passing tests
is not a deployment. No production change is claimed here.

## 12. Primary sources

Reference code links below pin the reviewed revision rather than assuming `main` stays unchanged.

- [Reference repository](https://github.com/marcosanyo/PlantDebugger/tree/d69507aa48aec773a5cf72761e5ff60c491eefc1)
- [Architecture](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/docs/architecture.md)
- [ADK orchestration design](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/docs/AGENT_ORCHESTRATION.md)
- [Dynamic workflow implementation](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/services/plant-debugger/plant_debugger/field_ops/adk_orchestration.py)
- [Final collaborative manager](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/services/plant-debugger/plant_debugger/field_ops/collaborative_final.py)
- [Collaborative planning](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/services/plant-debugger/plant_debugger/field_ops/collaborative_planning.py)
- [Vision implementations](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/services/plant-debugger/plant_debugger/field_ops/vision.py)
- [Deterministic verifier](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/services/plant-debugger/plant_debugger/tools/verify.py)
- [Deployment guide](https://github.com/marcosanyo/PlantDebugger/blob/d69507aa48aec773a5cf72761e5ff60c491eefc1/deploy/README.md)
- [Technical build article](https://dev.to/ryotakan/the-last-meter-has-no-api-building-plant-debugger-for-brownfield-operations-3eg8)
- [Digital pressure meter photograph and license](https://commons.wikimedia.org/wiki/File:C9557_01_1200_RGB_300dpi.jpg)
- [Valve photograph and license](https://commons.wikimedia.org/wiki/File:Ball_valve_in_household.jpg)

No reference source code or prepared demo imagery was copied into the application. The architectural
adaptation is independently implemented against FaultTrace's existing interfaces. Reference licensing
is Apache 2.0; the two third-party photographs retain their separate CC BY-SA 4.0 terms.
