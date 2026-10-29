# Manufacturer references and sanitized observability

Custom Python/SQLite remains the workflow; no LangChain/LangGraph or new runtime
dependency is added. One useful WIKA A-10 reference citation is now verified from
a live Tavily call; two other-model results do not establish applicability. Three existing
metadata-only LangSmith runs are remotely readable in named Local with matching
receipt fingerprints; agent-environment/browser visibility remains open. Offline
doubles do not establish live service results.

## Tavily reference lookup

Commander explicitly supplies an independently confirmed manufacturer, model and
one registered official domain. Assignment and uncertain image text do not provide
that confirmation. Registered pairs are MAXIMATOR/maximator.de or maximator.com,
Emerson/emerson.com, WIKA/wika.com and Swagelok/swagelok.com. Unknown pairs and
arbitrary URLs are rejected; adding another manufacturer needs a reviewed mapping.

One explicit request calls `POST https://api.tavily.com/search`, basic depth,
three results, restricted `include_domains`, no generated answer, raw page content,
images or automatic parameter selection. There is no crawling, fetching a cited
URL, automatic retry or fallback. Timeout is eight seconds; the response is bounded
to 128 KiB. Source URLs are checked again for HTTPS and the registered domain,
including subdomains, excluding embedded credentials and unusual ports.
Titles/excerpts are plain text and bounded to 200/800 characters. UI links use
`noopener noreferrer`. Model applicability remains unverified even when a snippet
mentions the requested model. Retrieval time and original citations are retained.

References have their own private SQLite table; they never become telemetry,
observations, model context, correction approval or recovery authority. Text such
as “ignore policy” remains displayed data, never an instruction. Returned sources
can be irrelevant or malicious despite a trusted host; human review is required.

The endpoint accepts exactly `{manufacturer, model, domain, revision}` and requires
the normal idempotency key, Commander authorization and existing Origin/CSRF
boundary. Four attempts per run are reserved durably before calling; a duplicate
key reuses the record, conflicting keys fail, and another pending lookup blocks.
No database transaction spans the provider request. A changed evidence revision
marks the reference result stale. Interrupted reservations become uncertain on
recovery and are never replayed or silently refunded. The coordinator's persistent
global/per-session budget is mandatory before enabling search. Reported Tavily
usage credits remain separate from NVIDIA tokens; missing credits remain unknown.

Server-only configuration: `TAVILY_API_KEY`, explicit enabled registration and
the shared budget. Browser forms never accept or receive the provider key.

### Reference-example result and diagnostic limitation

Reference only: WIKA A-10 pressure transmitter / wika.com; independently checked
[product](https://www.wika.com/en-us/a_10.WIKA),
[data sheet](https://www.wika.com/media/Data-sheets/Pressure/Pressure-sensors/ds_pe8160_en_co.pdf),
[operating instructions](https://www.wika.com/media/Operating-instructions/Operating-instructions/Pressure/Pressure-sensors/oi_a_10_en_de_fr_es.pdf).
It does not identify the MAXIMATOR photograph, F-17 or installed equipment.

The one authorized search ran: `c4e1a86b` recorded 1 credit and zero retained
sources. Connectivity, parsing and accounting passed; useful cited retrieval did
not. Historical status=completed is operation completion, not citation usefulness.
Raw response/counts were discarded; its cause cannot be resolved retrospectively.
A valid empty array and a nonempty array of entirely rejected URLs both produce
sources=[] in that historical implementation. Model mention/exact preverified-path
checks run after filtering and never remove sources from production parse output.
No historical data is reconstructed or backfilled.

Future parse results add only safe aggregate source_diagnostics: returned_count,
examined_count, retained_count, filtered_count, not_examined_count, fixed
filter_reasons and provider-empty/all-filtered/sources-retained outcome. Rejected
URLs/bodies/headers are not persisted. Malformed envelopes still fail closed;
the three-citation cap is counted separately from filtering. The exact query,
registered domain, HTTPS protections, payload and no-retry policy are unchanged.
The CLI separately reports connectivity_contract_result and retrieval_outcome;
legacy source diagnostics remain unknown, not zero.

[Tavily's current Search contract](https://docs.tavily.com/documentation/api-reference/endpoint/search)
documents include_domains_mode=restrict as a hard domain filter. Our request is
`WIKA "A-10" manufacturer manual datasheet`, basic/general, three results,
restricted wika.com, usage enabled; no concrete request defect is established.
That proposed diagnostic was subsequently authorized and executed once, as
recorded below. Both grants are now consumed: do not reset limits, rerun either
command or make an automatic retry.
Search references remain untrusted and cannot authorize simulated correction.
No Tavily/NVIDIA requests or LangSmith exports during this diagnosis.

### Final separately authorized diagnostic - consumed, do not rerun

The user authorized exactly one additional identical request. Implementation
`c9ea6bd` used the production documentation route with an independent persistent
one-request grant, preserving the original consumed limit. Attempt `de27f94f`
returned 3 results, retained 3, filtered 0, no fixed rejection reasons; 1 credit,
2391ms. The exact A-10 product page is a useful independently checked citation.
The other results are the S-20 data sheet (A-10 is only a related-product mention)
and PSD-4 data sheet, not applicable A-10 instructions. All remain untrusted
reference material. No observed evidence/identity/correction policy changed.

The new receipt is unique and settled once. Original empty receipt/shared cap and
NVIDIA ledger are unchanged. Combined reported Tavily usage is 2 credits across
two distinct one-call authorizations; no dollar estimate. Original raw result
count remains unknown; the new response does not resolve that history. The new
fixed authorization has no remaining requests. No automatic retry/refund or new
search cycle is permitted. No NVIDIA or LangSmith call accompanied the diagnostic.
Private evidence: `.local/2026-10-29-one-additional-wika-a10-diagnostic/result.json`.

## LangSmith metadata-only traces

Set `FAULTTRACE_LANGSMITH_TRACING=1` and server-only `LANGSMITH_API_KEY`.
Choose exactly one destination: validated `LANGSMITH_PROJECT`, **or** both
`LANGSMITH_AGENT_ID` (DNS-label identifier) and `LANGSMITH_AGENT_ENVIRONMENT`
(local/development/staging/production). A project named Local is not an agent's
Local environment. Agent mode sends `address=lrn:agents/<id>/environments/<env>`;
it never also sends session_name. Conflicting/partial configuration stops export.
Agent addressing is beta and requires workspace support; no project fallback.

Optional `LANGSMITH_WORKSPACE_ID` is a UUID sent only as `x-tenant-id`, not trace
metadata. `LANGSMITH_ENDPOINT` accepts only documented US/EU/APAC/AWS cloud API
hosts; default remains US. No arbitrary host, redirect, retry or SDK installation.
The three-second/4096-byte export bounds and empty inputs/outputs remain unchanged.
`recorded` preserves the historical local acknowledgment convention: no exception,
not verified remote creation. It never establishes dashboard visibility.

For the existing October 29 run, use the single pinned command from the delivery:
`.venv/Scripts/python.exe tools/diagnose_langsmith.py --expected-head <reviewed SHA>`.
It uses inherited credentials first, named Windows user settings second, never
prints keys, and performs only workspace/project discovery and read-only queries.
It checks the three receipts against SQLite and the isolated ledger without
changing them. Search is bounded to the current organization's key-visible scope,
10 workspaces, 200 projects/workspace, three query pages and 80 total HTTP calls,
8 seconds/request, 256 KiB success/8 KiB error bodies, no retries or redirects.
Only the historical US endpoint and explicitly configured allowlisted region are
queried. Scope limits/401/403/404/422/429 and malformed/oversized results remain
visible diagnostics, never evidence of absent runs across all accounts.

Reports under `.local/langsmith-diagnostics/` contain safe project/run IDs and
SDK-constructed dashboard URLs, never raw bodies/headers/images/prompts/reasoning.
Exit 0 locates all three receipt fingerprints in remotely readable runs; exit 1
is partial/not found; exit 2 is local preflight failure. Original run UUIDs were
not retained, so fingerprint matches are candidates, not direct ID correlation.
Dashboard navigation still needs human confirmation. No resending is implemented.
If absent, review diagnostics before a separately bounded metadata-only repair:
persist deterministic repair IDs first and acknowledge that unknown historical
IDs make duplicates possible. Never replay inference to repair tracing.

Official references: [agent environments](https://docs.langchain.com/langsmith/agent-environments),
[SDK addressing](https://github.com/langchain-ai/langsmith-sdk/blob/main/python/langsmith/_internal/_addressing.py),
[wire format and validation](https://github.com/langchain-ai/langsmith-sdk/blob/main/python/langsmith/address.py),
[workspace discovery](https://docs.langchain.com/langsmith/smith-api/workspaces/list-workspaces),
[run query](https://docs.langchain.com/langsmith/smith-api/run/query-runs).

### Resolved projection failure; no repair for this run

The preserved wider search returned three rows in each query. The parser rejected
all of them because start_time had no timezone suffix. One subsequent bounded
read-only query established the actual structure: valid UUIDs/project scope,
ISO timestamps such as `2026-10-29T00:24:06.134321`, and allowlisted metadata.
Trace diagnostics now interpret this observed UTC API representation as UTC;
explicit offsets normalize to UTC. Invalid timestamps, scope and time bounds
remain strict, with fixed rejection codes instead of silent projection loss.
This normalization never applies to equipment evidence/freshness policy.

Safe snapshot/reprojection evidence is in ignored
`.local/langsmith-followup/projection-safe.json` and `located.json`. Three remote
named-Local records match each receipt's operation/model/tokens/latency/contract
status, with returned correlation_id equal to run ID. Historical run-ID mappings
were discarded, so matches are fingerprints rather than direct ID proof. Direct
links are generated from remotely returned IDs; no browser acceptance is claimed.
Original search/acknowledgment/ledger records are not rewritten as success.

**Do not execute the prior repair procedure or repeat the model runner.** Existing
traces have been located; repairing would risk duplicates. The dormant reviewed-
plan implementation remains for history, but no plan was prepared for this run.
Future exports should choose project OR agent/environment explicitly; named Local
is not agent Local. Agent-based routing still needs its own bounded acceptance.
Sources: [query fields](https://docs.langchain.com/langsmith/smith-api/run/query-runs),
[run data format](https://docs.langchain.com/langsmith/run-data-format).

The export is a fresh allowlisted projection: operation (`planning`,
`photo_analysis`, `documentation`), measured latency, one supported NVIDIA model,
available valid integer token counts/reasoning-token count, contract outcome and
a bounded error category. Inputs and outputs are empty. Correlation is a fresh
opaque UUID, not an incident, evidence, attempt or user ID. Missing numeric values
stay absent. Cookies, keys, image bytes, raw labels, manufacturer/model queries,
request/response bodies, source excerpts and raw reasoning are excluded.

Coordinator integration hooks:

```python
from faulttrace.workflow.documentation import register
register(app, enabled=explicit_search_enabled, budget=shared_session_budget)

from faulttrace.partners.tracing import emit_trace
trace_result = emit_trace('planning', sanitized_receipt)
# Same helper with photo_analysis or documentation, after accounting is persisted.
```

The route authorizer must allow only Commander for `/api/documentation` and retain
resource grants, exact-Origin/CSRF and demo session scoping. The component is
Commander-only; route placement alone is not authorization. Live search/tracing
must remain off in offline test runners.

## Verification and remaining gates

Twelve focused backend tests cover restricted payloads, off-domain/unsafe source
filtering, injection-as-data, malformed/duplicate responses, credential redaction,
no-transaction transport, duplicates/concurrency, revision changes, missing keys,
four-call bounds, interrupted records, numeric/unknown trace metadata and tracing
failure isolation, including rejecting a provider key accidentally entered as
equipment context before storage or transport. Four static frontend checks cover explicit confirmation,
disabled offline search, source/uncertainty/time presentation, escaped markup and
URL restrictions, denied history and malformed records. Access changes remount
the documentation state; denial clears retained references and late/unmounted
responses cannot restore them. TypeScript and production build pass. The full
guarded backend suite passed 229 tests with zero external attempts before the
final focused redaction/lifecycle tests; 84 existing frontend tests also passed.
Static checks do not
establish browser layout, keyboard or dialog acceptance; known-unavailable browser
helpers were not retried.

Later bounded acceptance: use a permissioned, independently identified equipment
model, perform one explicit Commander search, inspect a relevant official citation
and retrieval time, then verify the sanitized trace in the configured project.
Do not infer relevance from a snippet alone or send private images to Tavily.
No provider call was made by this implementation worker.

Official contracts checked October 28, 2026:
[Tavily Search](https://docs.tavily.com/documentation/api-reference/endpoint/search),
[LangSmith REST tracing](https://docs.langchain.com/langsmith/trace-with-api).
