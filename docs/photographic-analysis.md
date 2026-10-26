# FT-010 photographic observation analysis

Implemented offline, not live-accuracy verified. No provider request or server
restart occurred in this checkpoint. Existing uploads, fixtures, runs and receipts
remain intact. This is interpretation of visible evidence, not incident assessment,
asset identification, equipment authorization or recovery reasoning.

## Support-confirmed photographic reasoning control

The user relayed Nebius Support confirmation for the exact
`nvidia/Nemotron-3.5-Super-VL` alias: top-level `reasoning_effort="none"` disables
reasoning; image JSON object/simple strict schema modes work; numeric reasoning
usage is `usage.completion_tokens_details.reasoning_tokens`. This is attributed
support evidence, not an agent-operated live verification or recovered response.
Only the photographic builder now sends reasoning_effort=none. Its prompt,
model, 2048 cap, 60s timeout, 256 KiB response bound and strict validator are
unchanged; no response_format, retry, fallback or fixture-contract change.

Sanitized receipts/ledger preserve optional numeric reasoning_tokens. Missing
details stay null; real zero stays zero; invalid booleans/types/negative counts
are unknown with fixed diagnostics. Counts exceeding a known completion count
are retained with an inconsistency diagnostic. This is a subset of completion
tokens and is not added to consumption totals again. Legacy absence stays absent
for idempotency; raw reasoning is never retained in ordinary receipts.

Seven focused offline tests include a frozen historical serialized-payload hash
proving that only the new top-level field changes, numeric/missing/rejected-output
accounting and legacy ledger compatibility. All 148 backend tests pass under an
external-socket guard (zero forbidden attempts); 40 frontend tests, typecheck and
build pass. Latest UI refinements are unchanged. No inference or server restart.

Next: one separately executed standalone request using the retained hash-verified
960x960 photo and committed production builder, without filename/answer/incident
hints. The provided PowerShell block records one receipt and interpretation and,
only for this support diagnostic, saves bounded successful-response JSON privately
under ignored storage after scanning raw/decoded JSON for the actual credential.
Credential exposure blocks capture; persistence failures are reported separately
and never trigger another request. Raw reasoning is not printed or committed.
HTTP error bodies remain unavailable through the unchanged transport. A valid
interpretation is not factual reading accuracy; absent numeric reasoning details
do not prove zero reasoning. Existing servers remain untouched and disabled.

## Non-stop completion investigation (offline follow-up)

### Repeated truncation: request audit and unsent support question

Experimental attempt `b2e90f31-9383-45e8-a88e-4df019c0796a` occurs once in the
ledger, exactly matching its saved receipt: 1676 input / 4096 completion / 5772
total, valid usage, `finish_reason=length`, 12906 ms, no validated interpretation.
Response ID: `chatcmpl-1ace4eb02ec74b7d6bf0ba5eb3bf49ca`. The 4096 override was
standalone; production remains 2048. Length confirms truncation, not a reasoning
loop, schema defect, incorrect reading or any particular discarded content.

Rebuilt the request from committed code, saved neutral reference/configuration
and hash-verified retained image, then verified the exact serializer with a mocked
HTTP opener. This establishes current serialization, not a recovered wire capture.
Top-level keys are only model, max_tokens, stream, messages; system instructions
are 3055 characters, and the serialized experimental body is 803635 bytes. User
content is one PNG data URL. No filename, incident data or expected reading enters
the payload. There is no response_format, tool schema or reasoning-control field:
JSON is requested only through prose and a JSON-encoded field specification,
which is not a JSON Schema. All nine fields and principal uncertainty outcomes
are represented; some conditional rules are implicit and others repeated. No
contradictory requirement to invent a reading was found. Repetition or model
difficulty applying these rules is hypothetical, not an established truncation
cause. The prompt's ban on reasoning in the answer is not an API reasoning toggle.

Parsing captures accounting/allowlisted finish reason first, rejects non-stop
completions before content parsing, and validates only assistant message.content
as strict JSON. reasoning/reasoning_content are neither parsed as answers nor
persisted. Null interpretation proves rejection, not absent provider content.
No partial output is recovered, repaired or fabricated. Strict validation and
production/fixture requests remain unchanged; no concrete defect warrants a code
change based on these records.

The [Nebius structured-output guide](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
requires response_format for constrained decoding and directs users to model-card
JSON support. The [generic API reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion)
lists reasoning_effort (including none), but gives no exact-alias compatibility
guarantee. The maintained [Nemotron cookbook index](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/README.md)
and [example notebook](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/run_nemotron.ipynb)
do not demonstrate reasoning controls for 3.5 Super VL. The maintained
[Nebius workbench guide](https://github.com/nebius/nebius-physical-ai/blob/main/docs/workbench/token-factory.md)
distinguishes verified defaults for other models from generic overrides that
providers may ignore or reject. None establishes an exact supported control for
our alias; NVIDIA NIM support alone does not do so either.

Unsent support draft (no image, prompt content, filename or credential):

> For nvidia/Nemotron-3.5-Super-VL at POST
> https://api.tokenfactory.nebius.com/v1/chat/completions, response
> chatcmpl-1ace4eb02ec74b7d6bf0ba5eb3bf49ca (2026-10-26T02:59:21Z) ended with
> finish_reason=length: 1676 input / 4096 completion / 5772 total tokens. Request:
> max_tokens=4096, stream=false, one 960x960 PNG and system instructions requesting
> bounded JSON; no response_format or reasoning control. No retries; client timeout
> 60s and response bound 256 KiB. Which raw HTTP parameter, nesting and values are
> supported to disable reasoning for this exact hosted alias? Does it support
> json_object or json_schema with image input? Do completion_tokens include
> reasoning, and are separate numeric reasoning-token counts available? Can you
> identify the termination cause from this response ID without an image or key?

Smallest next experiment is conditional on an exact-alias support answer: one
separately authorized standalone call using the same hash-verified image, production
2048 cap/prompt and only the confirmed reasoning-off setting; strict validation,
receipt/ledger, timeout/body bound and no retries unchanged. Do not combine prompt,
schema or budget experiments, and do not replay a workflow analysis.

Offline checks: six photographic-contract tests and seven completion-diagnostic
tests pass; mocked wire serialization and all nine prompt fields checked. Ledger
known totals now 8634 / 16703 / 25337 across 19 attempts, with four missing-usage
attempts. Separate historical success 155 / 112 / 267 gives cross-record known
8789 / 16815 / 25604; consumption is incomplete. No imports, inference, server
operations, historical-record writes or application changes in this audit.

Standalone attempt `50740c31-0635-4d56-af69-f4b4f7a64073` is present once in
the existing ledger and matches the saved local receipt. Usage is valid:
1675 input / 2048 completion / 3723 total tokens; latency 6891 ms. Validation
failed with `non_stop_completion`, with no validated interpretation. The saved
960x960 PNG matches its private provenance hash. Receipt, image, provenance and
ledger are preserved, with no imports or replay. The exact finish reason was
discarded: neither `length`, empty content, an image-reading error nor reasoning
token consumption can be established retrospectively. Hitting the configured
completion count suggests budget pressure, not a proven cause or token split.

[NVIDIA's exact-model API reference](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-super-vl-120b-a12b-infer)
documents reasoning modes (`none`, `low`, `high`) and chat-template controls for
its own endpoint. [Nebius's release note](https://nebius.com/blog/posts/three-new-open-weight-models-from-us-companies-give-builders-more-choice)
identifies our hosted alias and warns that reasoning can exhaust a small output
budget. Its [chat API reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion)
describes `max_completion_tokens` as including visible and reasoning tokens,
but does not establish a model-specific reasoning toggle for this alias.
NVIDIA endpoint settings are not proof of Nebius deployment support. No new
parameter, prompt change or limit increase is justified yet; photo and fixture
requests remain unchanged (2048 tokens, 60s timeout, 256 KiB body, no retries).

Future sanitized receipts retain only `stop`, `length`, `tool_calls`,
`content_filter` or `function_call` from a single-choice envelope, before content
validation. Missing, malformed and unknown values stay null. Legacy receipts
remain without that field; no historical finish reason is backfilled. Ledger
validation rejects arbitrary persisted strings. Strict stop/content/proposal
validation remains unchanged; neither content nor reasoning is retained by this
diagnostic. Seven focused mocked tests cover rejection/accounting, allowlisting,
secret non-disclosure, unchanged photo payload and legacy ledger idempotency.

Proposed later verification, not executed or authorized by this investigation:
one standalone request using the existing validated private 960x960 copy and
unchanged production builder, with the new receipt field. Verify its hash first,
send only the production instructions/image/neutral reference, record once and
stop on any result, with no retry, workflow task or image-analysis replay. This
would establish a future finish reason, not recover the old one. Confirm Nebius's
exact-model reasoning-off support before separately proposing that configuration.

Ledger known usage is 6958 / 12607 / 19565 across 18 attempts, with four missing
usage attempts; separate historical manual success is 155 / 112 / 267, giving
cross-record known totals 7113 / 12719 / 19832. These are incomplete consumption
totals, not billing estimates. FT-010 remains PARTIAL; live accuracy is unverified.
All 136 backend tests pass, including the seven new tests and existing fixture
regressions, with zero forbidden external socket attempts. Hashes of the original,
submitted image, provenance, saved result and ledger remain unchanged. No UI change
requires a new browser claim; no live request or server operation was performed.

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
