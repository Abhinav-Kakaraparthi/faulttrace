# Combined authentication: coordinator intake and founder review plan

Status: **WAITING FOR B'S FINAL CONTRACT; NOT AN IMPLEMENTATION ASSIGNMENT.**
No combined/authenticated preview has been created or integrated. No endpoint,
credential format, logout behavior or successful auth journey is assumed here.
Worker A's `e9efbb61db4b13b78d314ee0d562fa74f2366f0b` changes only its review
document: static checks/CI pass; actual browser acceptance is blocked. Do not ask
A to repeat the unavailable browser/native-helper attempts. Founder manual review
of the combined code is the acceptance path. Workers communicate through founder
relays; no cross-chat communication or partner work is initiated.

## Contract gate before preparing A's bounded follow-up

Coordinator needs B's exact immutable implementation/tested SHA, changed paths,
actual checks/CI, remaining gaps and finalized contract covering:

- Credential scheme, exact header/body fields, trusted identity/role configuration,
  issuance/verification endpoints if any, expiry and server-side permission matrix.
- Authenticated state reads, mutations, XHR image uploads and protected image GETs;
  resource scoping, Origin/CSRF requirements and same-origin/proxy expectations.
- Exact unauthorized/forbidden/expired/configuration error statuses and fixed codes;
  logout/revocation semantics if supported, including what cannot be revoked.
- Duplicate/idempotency behavior across identities and interrupted writes; secrets
  handling and reproducible local startup with inference disabled.

Resolve any conflict with the user's memory-only credential requirement before
assignment. Do not guess token endpoints, invent logout/revocation or silently
persist credentials to accommodate the backend. B-owned code stays unchanged by A.

Once finalized, prepare one A-only follow-up against that exact contract. Expected
boundaries: application-held credentials only in memory; no localStorage,
sessionStorage, IndexedDB, URLs/history, logs or frontend environment embedding.
Use the exact auth contract for JSON requests, uploads, thumbnails and full-image
inspection. If headers are required, direct `<img src>` cannot carry them: fetch
protected bytes through the authenticated request layer and manage/revoke local
object URLs. No credentials in image URLs, and no extra provider request.

Logout must clear credentials/private state, stop polling, abort in-flight work
and release image/draft object URLs. Late responses must not restore logged-out
or another identity's data. Call only the specified server logout mechanism and
report unconfirmed server revocation honestly. Handle 401/403/expiry distinctly
from connectivity faults, without endless polling or automatic write replay.
Preserve revision, idempotency, inference opt-in, budgets and uncertainty behavior.
Use mocked-contract tests including sentinel non-disclosure, access denial, image
access, logout/cancellation and stale responses. Static checks are not a browser pass.

## Sequential integration gate (nothing merged/cherry-picked)

1. Review B's actual server diff, independent auth/resource tests, startup checks,
   Linux fixture findings and finalized contract. Resolve ownership/API questions.
2. Prepare A's bounded assignment; review its actual contract-specific frontend
   diff and tests when relayed. Do not require repeated unavailable browser tries.
3. Only in a later authorized integration checkpoint, combine B then A sequentially
   and run full CI against each actual combined SHA. No automatic merge/cherry-pick.
4. Reconcile C's submission claims with the verified combined code and manual
   findings; do not describe unintegrated authentication as delivered.

## Manual acceptance setup — pending combined SHA and exact URLs

Coordinator will provide a fresh isolated, localhost-only pair:

| Item | Current status |
| --- | --- |
| Combined application/tested SHA and CI | Pending authorized integration |
| Commander URL / Operator URL | Pending B startup/proxy contract; do not invent URLs |
| Fresh data directory / synthetic auth subjects | Pending; never copy old runs or real credentials |
| Inference | Must remain disabled; seed model states with labeled offline doubles |
| Screenshots | Not captured; save privately with combined SHA/role/route/viewport |

The existing frozen 5190..5204 cases predate authentication and cannot establish
combined-auth acceptance. Their current review proxy does not forward auth headers
or cookies; do not reuse it unchanged or mistake its failures for frontend defects.
Use a contract-compatible isolated proxy and record any test-clock overrides. Keep
old servers, data, real usage ledger and screenshots untouched.

Run these in small groups, recording **PASS / FAIL / BLOCKED / NOT RUN** plus the
actual action and observed result. Never capture credential values in screenshots,
console exports or shared network logs. Use synthetic local auth fixtures only,
never the Nebius key as a browser credential.

1. **First group: access and overview.** In two clean tabs, authenticate Commander
   and Operator using B's finalized method. Check matching authorized incident,
   correct role/next action, no sensitive snapshot before access is granted and
   no assumed authority from the pathname. Start at 1440x900, then 390x844. Check
   labels and Tab/Shift+Tab focus. Pause for founder feedback before mutations.
2. **Memory and authorization.** Inspect application storage/URLs without exposing
   values: no credential persistence. Reload must not recover application-held
   credentials from storage. Exercise the specific forbidden-role/resource cases
   in B's matrix; verify meaningful access errors and no hidden data disclosure.
3. **Authenticated evidence.** Select/preview/replace/cancel/upload a permitted
   synthetic fixture. Inspect thumbnails and full images in both roles. Verify
   protected image access follows the contract and never places a credential in
   a URL. Exercise unauthorized/expired image responses; no stale private image
   should remain after access is cleared. Keep original model/human data separate.
4. **Logout and interruptions.** Log out while reads/images or a throttled upload
   are pending; inspect state clearing, object-URL cleanup and disabled writes.
   Verify late responses do not restore data. Reauthenticate as another test
   principal; do not silently replay writes or reuse the old identity's state.
   Distinguish local clearing from confirmed server revocation.
5. **Shared simulated journey.** With labeled test-created tasks/claims and no
   provider calls, review refusal, disputes and pressure-vs-DP rejection; human
   approval, Operator completion, progress, verified recovery, ineffective action
   and relapse. Attempt only role-permitted actions. Preserve audit references.
6. **Responsive/error/dialog coverage.** At both sizes check loading, disconnected,
   bad/expired credentials and denied resources, keyboard activation, visible
   focus, Escape/focus return, full-image scrolling and overflow. Upload progress
   requires actually observed throttled interaction; file selection does not pass
   real camera capture. Screenshots/HTTP/static tests alone pass none of these.

All manual items remain unrun until the combined application exists and the
founder exercises them. No current role, browser, deployment or submission gate
is closed by this plan.
