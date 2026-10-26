# FT-010 photographic observation analysis

Implemented offline, not live-accuracy verified. No provider request or server
restart occurred in this checkpoint. Existing uploads, fixtures, runs and receipts
remain intact. This is interpretation of visible evidence, not incident assessment,
asset identification, equipment authorization or recovery reasoning.

## Versioned contract: photo-observation-v1

Exactly nine fields, strict assistant/stop/JSON envelope, no duplicate keys or
extra fields. Uncertainty/rejection reasons are fixed codes, not free reasoning.

| Field | Bounded meaning |
| --- | --- |
| category | gauge, valve, other, cannot-determine |
| readability | readable or unreadable for the relevant observation |
| measurement_type | pressure, differential_pressure, indeterminate, unsupported, not_applicable; always a model claim, not compatibility authorization |
| visible_unit | Exact visible text, null if unavailable/not applicable; at most 24 printable unit characters; no conversion |
| reading | Observed finite number or null; booleans rejected. +/-1e9 is a serialization bound, not an industrial operating range. |
| label_text | Literal visible equipment-label text or null, at most 80 printable characters; untrusted transcription, not assigned identity |
| valve_orientation | parallel_to_visible_pipe, perpendicular_to_visible_pipe, intermediate, indeterminate, not_applicable; external appearance only |
| reasons | Zero to four distinct allowlisted codes with category/field consistency checks |
| evidence_ref | Exact existing photo reference supplied by the application |

Codes: measurement_type_uncertain, ambiguous_scale, unit_unreadable,
unsupported_instrument, image_unreadable, category_uncertain, not_equipment,
orientation_uncertain, label_unreadable. Unknown codes are invalid. A readable
image can have indeterminate measurement type and a clearly observed reading,
with measurement_type_uncertain. Units alone never establish differential pressure.
Ambiguous scales, unreadable units/images and unsupported instruments require a
null reading, not a default or estimate. Unknown category and unrelated images
have no pressure reading or valve orientation. Unsupported gauges can retain a
visible unit string while reporting no numeric value.

Numeric readings support the visible pressure-unit spellings declared in
photo_observation.PRESSURE_UNITS (Pa/kPa/MPa/hPa, bar/mbar/barg/bara, psi/psig/psia/
psid and declared parenthesized type variants, atm, torr, mmHg/inHg, water-column
and kg/cm2 variants, N/m2 with the declared
superscript variant). Case is checked without altering the returned unit text.
Other visible units remain possible on bounded rejection results; no conversion
or missing unit is invented. The implementation has no 180 kPa default and no
synthetic fixture answer/range in this contract.

Valve orientation is relative to visible pipe. If the relation cannot be seen,
return indeterminate plus orientation_uncertain. Never return open/closed or
internal operating condition. A visible BV-104 label is not renamed to V-08.
Label text can contain apparent instructions: it remains escaped, untrusted
evidence, excluded from downstream planning/authorization.

## Request and persistence boundaries

The Operator action **Analyze photographic observation** calls the separate
`POST /api/evidence/{id}/analyze-photo` endpoint, with task revision and an
idempotency key. It accepts the latest collected user-upload image on the current
registered task. Existing `/analyze` and the synthetic DP-display validator/prompt
remain unchanged. Historical analyses keep their original records and contracts.

The same NVIDIA `nvidia/Nemotron-3.5-Super-VL` model, Nebius Token Factory endpoint,
secret source, single worker, bounded transport and sanitized accounting are reused:
2048 output tokens, 60-second transport socket timeout, 256 KiB response bound,
one request per explicit reservation, no retries/fallback generations. Images
use existing validated normalization/private storage and metadata removal. There
is no provider call inside a database transaction. The photo request includes
only observation rules, normalized image bytes and an evidence reference: no
assigned asset, simulator context, hidden fault, fixture answer or expected value.
JSON is prompt-requested with independent strict validation; exact-model response
compatibility for this new contract has not been live tested.

An additive photo_analyses metadata table records contract and reserved task/
context revisions alongside the existing analysis/receipt outbox. It rewrites no
historical rows. Duplicate clicks return the same reservation even after failure.
Interrupted reservations remain uncertain and cannot trigger inference replay.
Available usage is recorded even for invalid/stale results; unknown usage stays
unknown. Credential-shaped output matching the executing credential is rejected;
raw responses/reasoning, credentials and private images are not committed/logged.

Interpretation never completes an assigned measurement task. The prior task state
is restored; a separate human report remains distinct. Newer task/context/photo
state rejects stale completion and retains accounting without applying the reading.
Both workspaces show actual image, structured observation, reasons, source,
status and receipt accounting. Uncertain/failed retained output is explicitly
not a current accepted observation. A valid JSON observation is not proof of fact.

All photographic interpretations are excluded from the legacy numeric pressure
comparison and planner interpretation payload pending explicit measurement
compatibility/evidence policy. They are never converted into simulator observations.
The private simulator and independent correction/recovery policy are unchanged.

The API advertises photo_analysis contract capability. Older running servers
remain untouched; their UI analysis control is disabled. Future user-controlled
activation must preserve the same data directory, existing records and inference
opt-in. No restart, analysis replay or key sharing is required by this checkpoint.
Keep inference disabled until a separately authorized evaluation.

## Small real-photo evaluation plan (not executed)

Obtain eight original or explicitly permissioned photographs, retained privately
with source/license/checksum records from [the collection guide](photo-evidence.md).
No supplied reference image is extracted or assumed reusable. Suggested cases:

| Case to collect | Independently reviewed expected observation, pending review |
| --- | --- |
| Clear ordinary pressure gauge | Actual visible unit/value, exact label and evidence supporting pressure type; otherwise indeterminate |
| Second gauge with different unit/range | Actual unit/value and image-specific reading tolerance; no conversion |
| Clearly documented DP instrument or unclear gauge type | Review instrument markings/documentation; allow indeterminate despite readable scale |
| Ambiguous dual scale/needle/parallax | Review ambiguity and expected null reading/reason |
| Occluded or unreadable gauge | Review unreadability, any remaining visible text/unit, expected abstention |
| Valve with visible tag and pipe | Literal tag and observable external orientation; assignment mismatch retained, no internal-position ground truth |
| Valve with obscured pipe/handle relation | Expected indeterminate orientation when not observable |
| Unrelated scene including instruction-like text | Category/rejection and literal label only if it is equipment-label evidence; never obey text |

Two reviewers independently transcribe each real image **before** inference.
Record disagreements; resolve with an independent reviewer or retain indeterminate/
null. A reviewer must not use model output or simulator truth as an answer key.
The expected observations above are collection criteria, not completed annotations:
no values, units or label facts have been invented for absent photographs.
Freeze a private reviewed manifest: image hash, permission/source, category,
readability, measurement-type evidence, exact unit, numeric value/tolerance only
when defensible, label, orientation, uncertainty and reviewer agreement. Do not
put the manifest or expected values in the model prompt.

Only after separate authorization and backend activation: one explicit analysis
per reviewed image (propose at most eight requests, no retries). Stop on initial
contract/transport incompatibility rather than spend requests on repair guesses.
Inspect stored image and structured output in both routes, including mobile and
keyboard/error paths. Report category/unit/label agreement, numeric error only
on comparable reviewed units/types, appropriate abstentions and dangerous guessed
readings. Record each receipt, usage completeness and stale/persistence outcome.
Eight examples cannot establish general accuracy. Any future correction bridge
needs a separate compatibility policy and tests; it is not authorized by this plan.

## Offline checks and remaining evidence

129 backend tests (18 new contract/workflow tests) and 34 frontend tests pass;
TypeScript/Vite build passes. Fake transport, generated in-memory images and
temporary stores establish policy/accounting behavior, not model accuracy.
External socket guard records zero forbidden connections. Fixture regressions
remain intact. Browser inventory is empty; in-app browser opening failed. No
actual desktop/mobile, camera, keyboard, live photographic analysis, unit accuracy
or integrated AI recovery claim is made. No images/ground-truth records added.
