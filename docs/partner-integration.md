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

Follow-up after the saved narrow search returned HTTP200 but no matches:
run only the delivered pinned `tools/followup_langsmith.py` command. It uses a
48-hour explicit start_time filter plus one unfiltered recent named-Local query
(max100 rows each); it neither clips the latter to the old window nor exports
traces. A durable marker prevents automatic repeated searches. Results and any
prepared plan live in `.local/langsmith-followup/`, outside Git.

Only a complete empty search prepares a plan, labeled **not executed**. Review
its exact faulttrace/local address, resolved-project expectation, three stable
run IDs, reconstructed timestamps, metadata-only bodies and SHA256 first. A
later separate `--execute-reviewed-plan <private plan.json>` plus
`--reviewed-plan-sha256 <reviewed hash>` invocation is required for writes; do
not execute this while reviewing. It allows at most three POST /runs calls and
one selected-field GET read-back per posted run, no retries. HTTP acknowledgment
and verified read-back stay separate. It persists reservations/status before
continuing; interrupted/started plans cannot be replayed. Address resolution
must match the privately saved agent-Local project before contact with /runs.
Original random UUIDs were lost, so duplicate historical traces are possible
even with deterministic repair IDs. Read-back verifies remote records, not UI
acceptance. Historical workflow/ledger/trace acknowledgments remain unchanged.
Sources: [query ordering/fields](https://docs.langchain.com/langsmith/smith-api/run/query-runs),
[address resolution](https://docs.langchain.com/langsmith/smith-api/sessions/resolve-an-address-to-its-tracing-project-beta),
[selected-field read-back](https://docs.langchain.com/langsmith/smith-api/runs/get-a-single-run).

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
