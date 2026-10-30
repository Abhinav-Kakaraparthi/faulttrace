# Durable guided investigation

The investigation now resumes on the server after field evidence is returned.
Commander starts it explicitly with **Start guided investigation**. This consent
covers the remaining planning allowance for at most thirty minutes; it does not
reset either the run limit or the server/session spending limits.

## Implemented transitions

- Initial incident: request a validated model proposal and create its registered task.
- Assigned observation: wait for field evidence without issuing more planning calls.
- Collected photograph: wait for explicitly requested photo analysis.
- Compatible interpreted photograph: wait for an independent human review.
- Incompatible/unreadable interpretation: preserve it, hand it to planning, and
  request a new validated decision using that evidence.
- Independent task response: automatically rebuild current planning context and
  request the next decision. The model still chooses among registered observations
  or human escalation; no fixed F-17/V-08 sequence is imposed by the runner.
- Complete compatible evidence: wait for Commander approval of the current revision.
- Approved correction: wait for Operator acknowledgment; the runner cannot execute it.
- Completed simulated correction: start persisted independent recovery monitoring.
- Verified recovery: record the terminal result. Failed verification requires escalation.

## Persistence, authorization and interruptions

SQLite stores consent, owner, expiry, phase and a journal of continuation dispatches.
The loop lives in the API lifespan, independently of tabs, polling or page refreshes.
Waiting investigations resume after restart. A dispatch is journaled before calling
an existing operation. Ambiguous interrupted dispatches are marked uncertain and
stop; inference is never replayed to reconstruct a missing response.

Each step checks current Commander grants, revocation and expiry. Demo continuation
also checks the active visitor session/run, so end, expiry and restart remove its
authority. Pause prevents further continuation steps. A provider request already
in flight may finish and retain its receipt; pausing cannot recall a sent request.
The state response exposes phase/expiry/error, never a credential or owner record.

Existing task/context revisions, action validation, evidence citations, human
compatibility rules, freshness, idempotency, approval and recovery policies remain
in force. The existing planning/photo engines own all inference reservations,
provider calls, receipts, tracing and accounting. The continuation runner cannot
approve a correction, fabricate a human report or declare model-derived recovery.

## Verification

Backend tests cover no calls without consent, independent-report continuation,
photo review/follow-up, new evidence in planner context, approval boundaries,
monitoring only after execution, pause/expiry/revocation, interrupted dispatches,
restart of waiting investigations, exhausted allowances and role denial.

`frontend/tests/guided-browser.mjs` drives the real application and localhost API
with SQLite and explicitly labeled offline provider doubles. It closes Commander,
submits independent simulated reports in Operator, observes automatic cited
replanning, reopens Commander for approval, acknowledges completion in Operator,
and waits for automatically started independent monitoring and persisted recovery.
No browser POST to planning or monitoring is used. Desktop/mobile outcome screens
are checked. These are application behavior tests, not live model-accuracy claims.

Reproduce using an existing Python environment with backend dependencies, an existing
Node installation and Playwright/Chromium: `python tools/run_guided_browser.py`.
Set `FAULTTRACE_PLAYWRIGHT_MODULE` and `FAULTTRACE_CHROMIUM_PATH` (or the existing
`FAULTTRACE_CHROMIUM_EXECUTABLE`) when the browser runtime lives outside the project.
The launcher compiles local assets, creates a fresh ignored directory and loopback
service, runs the browser journey, retains its evidence and stops only its own service.
Integration found a Windows teardown race: cancelling the async loop could leave
its SQLite worker active. Shutdown now signals the loop and drains its active
tick before storage/instance locks close; a deterministic regression verifies it.
Local integration verification: 335 guarded backend tests, 114 frontend tests, typecheck,
normal/demo builds and both combined API contracts pass. The browser journey uses
zero external provider calls and no manual planning/monitoring requests.

The real-photo workflow from the preceding checkpoint is retained. This new
browser success case uses report-only simulated human input, not synthetic images
or invented readings attributed to a real photograph. Real-photo transport and
uncertainty paths have their separate tests and attribution.

No existing hosted records, budgets, reservations, secrets or service settings were
changed for development. No live provider/search call was made. Integration and
deployment must use the reviewed final revision. Additional intervention types
still require a coherent simulator/capability/policy implementation; the current
registered correction remains simulated F-17 replacement.
