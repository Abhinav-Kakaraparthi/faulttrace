# Manufacturer references and sanitized observability

Custom Python/SQLite remains the workflow; no LangChain/LangGraph or new runtime
dependency is added. This implementation is offline-tested. Actual Tavily source
retrieval and LangSmith trace visibility require later bounded verification;
mocked test output does not establish a live integration result.

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

## LangSmith metadata-only traces

Set `FAULTTRACE_LANGSMITH_TRACING=1`, server-only `LANGSMITH_API_KEY` and a
`LANGSMITH_PROJECT` containing only letters, digits, hyphen/underscore (1–64).
There is no automatic environment-triggered SDK instrumentation. The helper sends
one bounded REST trace to the fixed US endpoint, with a three-second timeout,
no retry, no redirect and no arbitrary endpoint parameter. A missing project/key
or failed export produces a fixed local result; it cannot retry inference or fail
the investigation. Multi-workspace routing is not configured; do not add tenant
identifiers to metadata to work around an account configuration error.

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
