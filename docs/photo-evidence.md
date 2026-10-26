# Photographic collection and versioned observation analysis

FT-009B established collection-only upload. FT-010 now adds a separate explicit
photographic-observation endpoint; see [contract and evaluation plan](photographic-analysis.md).
Uploads alone still request no inference. Analysis produces bounded observations,
not incident assessment, asset identity, correction approval or verified accuracy.
Both collection/analysis capability flags must be loaded by the backend before
the new controls can run. The completed-run preview is now activated with
inference disabled; the separate collection-review instance below preserves it.

## Isolated inference-disabled review

Commander: http://127.0.0.1:5181/commander. Operator:
http://127.0.0.1:5181/operator. This private test instance has an explicitly
TEST-CREATED / NOT AI-generated F-17 assignment, using the existing
`tests/test_workflow_api.py` offline setup pattern. No planner call or task-policy
change creates it. Inference is disabled; an API check returns inference_disabled
before analysis reservation. The compliant MAXIMATOR copy and one API-collected,
unanalyzed image live only in ignored storage; no photo is added to Git.

New preview ports previously failed the fixed browser-origin allowlist. Set
`FAULTTRACE_PREVIEW_ORIGIN=http://127.0.0.1:5181` only for this backend. It permits
that exact origin in addition to existing defaults; only explicit HTTP localhost
or 127.0.0.1 origins with valid ports are accepted. Invalid settings fail closed.
The local-client header check, inference opt-in and all task policy remain intact.
No wildcard, proxy-header rewrite or global origin relaxation is used.

Data, logs, source hashes and exact manual/resume steps are under
`.local/visual/ft010-isolated-7661c16d0084429a9e9ac130010f12e9/`.
Open its `manual-review.md`: select the compliant photo, replace with an explicitly
synthetic preview, cancel, simulate a blocked upload in this tab only, throttle a
successful transfer and inspect the same stored image in both workspaces. Repeat
at 1440x900 and 390x844 with keyboard navigation. Do not change the 5180/8780
completed run or enable inference. No browser surfaces/native helper are available;
these interactions, screenshots and camera capture remain unverified. API and
mocked/static tests establish only their stated checks, not visual acceptance.

Use original photographs you are entitled to supply, or photographs with clear
permission for the intended use. The user's reference is visual guidance only:
no image has been extracted, downloaded, authenticated or licensed from it.
No photographic demo asset is added to Git. Synthetic panel-a/panel-b fixtures
and their original records remain unchanged regression assets.

## Assigned observation and upload

Operator `/operator` offers camera capture where supported and a separate
ordinary file input on the assigned F-17 or V-08 observation. Both accept
PNG/JPEG only, maximum 2 MiB, 16-2048 pixels per side, at most 1,048,576 pixels.
HEIC/oversized phone images require a prepared copy; limits are not relaxed.
Before submission, the selected local image has an actual object-URL preview,
replace and cancel controls, decode/dimension errors and no inference. Local
object URLs are revoked on replacement/cancel/unmount. Filenames and local
paths are not saved as evidence metadata or logged by this flow.

Upload progress comes from browser byte-transfer events, never a timer estimate.
100% means transfer complete, not storage confirmed. The UI waits for server
validation/storage before confirming success. Network/timeout errors can leave
an uncertain outcome: refresh the shared state before another submission; there
is no automatic retry. Mutation serialization, idempotency keys and task revision
checks remain in force. Camera availability/native picker behavior varies;
ordinary file selection remains available without a capture restriction.

All new camera/file uploads use `X-Evidence-Purpose: reference-photo`. The server
stores an image record with status `collected`, origin `user-upload` and no model
interpretation. The photo does not finish the task: submit a separate structured
position/uncertainty/refusal report. F-17 retains unreadable, cannot-access and
wrong-equipment reports; V-08 retains its existing cannot-determine category for
an unreadable position, cannot-access and wrong-equipment responses. No report
value contract has been broadened.

Existing validated upload decoding and limits are reused. EXIF display orientation
is applied to pixels before all metadata is stripped and a clean PNG is privately
stored. Tests reproduced the previous lost-rotation case and check the corrected
normalized size. Stored images appear directly in both workspaces and inspection,
from the actual local evidence endpoint, with an unavailable-image fallback.
Private local storage is not public hosting or server-enforced role isolation;
existing authentication/authorization deployment gates remain open.

## Measurement and identity boundaries

The assigned asset is application task context, not a claim about photographed
identity. The current image contract does not assess identity or instrument type.
Visible tags must be recorded as seen; report wrong asset for a mismatch.
**Do not relabel BV-104 as V-08.** No OCR/tag mapping or authenticity claim is
introduced. A visible valve handle can document external appearance, not internal
valve condition, actual flow path, completed work or recovery.

An ordinary pressure gauge does not establish differential pressure. Gauge type
and units must independently support the intended measurement; kPa units alone
do not distinguish ordinary from differential pressure. No DP value is inferred
from the new collection-only photographs. Human reports and historical NVIDIA
interpretations are displayed separately with provenance. A retained model reading
is not proof of instrument type, asset identity or measurement validity.

## Existing analysis path and historical compatibility

The legacy fixture `/analyze` endpoint continues to reject collected photographs.
FT-010 uses only the new `/analyze-photo` contract for explicit observational
analysis, with separate uncertainty and orientation fields, never internal valve
condition or correction authorization. Synthetic DP-display
fixtures keep their existing explicit analysis opt-in and validated output
contract. Existing legacy pending uploads, receipts and duplicate-operation
fingerprints are preserved; the native DP-display path is not silently redefined
as analog-gauge or valve support. Its model, prompt, token/body limits, receipts,
budgets, serialization and stale-result guards are unchanged. No provider request
was made in this checkpoint.

Photographic collection cannot satisfy simulation correction prerequisites;
recovery policy and its private simulator boundary are unchanged. No integrated
AI recovery reasoning, correction authority or verified real maintenance is claimed.

## Activating later without losing a local run

Existing servers were not restarted. New collection controls require the backend
`/api/state` to advertise `photo_collection.version=1` and the assigned asset.
Without that capability, new photo inputs are disabled instead of accidentally
submitting to the older DP-analysis flow. Synthetic fixtures and existing report
controls keep their historical behavior. The current running preview can show
this compatibility notice; it has not loaded the new backend code.

A later, user-controlled backend restart must reuse the existing data directory
and keep FAULTTRACE_ALLOW_INFERENCE=0. Do not create a fresh directory, reset the
database or replay analysis to activate this UI. No restart is authorized or
performed as part of FT-009B. After activation, inspect the assigned observation
at the existing `/operator` URL and its persisted image at `/commander`.

## Public-repository photo source record

Keep working uploads private in ignored local storage. Before intentionally
adding a photograph to the public repo, record real source/license facts:

| Field | Required actual information |
| --- | --- |
| Asset path and checksum | The specific permitted file, not an extracted reference image |
| Creator / rights holder | Actual author or owner; do not invent an attribution |
| Source | Original capture record or exact permissioned source URL |
| Permission / license | Exact applicable license or retained written permission, scope and attribution requirements |
| Intended use | Public repository, demo, redistribution and modifications actually permitted |
| Changes | Cropping/resizing/redaction/orientation changes made |
| Evidence limitations | Synthetic/original/third-party status, visible tags, measurement/identity uncertainty |

If rights are unclear, do not commit the image. No source/license record is
fabricated by this checkpoint, and the reference supplies no reuse permission.

## Required separate vision evaluation

Factual analog-gauge reading and external valve-orientation accuracy remain unverified. Before proposing
a new model contract, evaluate original/permissioned held-out images with independent
human ground truth: ordinary versus differential instruments, units/ranges,
needle/parallax/lighting, unreadability, tag mismatches and unsupported instrument
types. Evaluate external valve position separately from internal valve condition;
a photograph alone cannot establish the latter. Define rejection rules and error
metrics before a bounded, separately authorized provider test. Retain sanitized
receipts/accounting and never turn an unverified reading into correction approval.
This checkpoint does not change the strict vision validator or run that evaluation.

Offline evidence: 111 backend tests, 30 frontend tests, TypeScript and production
build. Tests use generated in-memory JPEGs, fake XHR/transport and temporary data;
no real-photo accuracy or physical camera usability is established. Browser
inventory is empty and in-app browser opening fails: actual desktop/mobile,
camera/file picker, keyboard, upload progress/error and stored-preview visual
acceptance remain open. Static markup/build success is not browser verification.
