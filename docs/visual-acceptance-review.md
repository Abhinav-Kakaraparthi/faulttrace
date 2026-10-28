# Worker A evidence-inspection correction

Current checkpoint: coordinator-confirmed rendering defect fixed; offline
transition/render checks pass. Browser and combined-backend acceptance remain
unverified. Earlier checkpoints below are historical.

Started clean on `feat/finish-visual` at
`450c31a20e4bfc51bf38a0b7f3991babec0213ba` in this worktree only.
Corrected implementation and clean tested SHA:
`4d8aa048f0de0f28edaf8df35a323b262f39abc1`.
The following handoff commit changes only this document; final SHA, verified
remote and exact-SHA CI are reported in the delivery message.

## Confirmed failure and correction

Coordinator review record: `8a4ac28c85b69c2c03b0415e6b347539478421f6`.
Read `.local/reviews/a-denied-dialog.mjs` in the coordinator tree without
modifying or executing it there. Its offline render probe showed a reachable
denied state displaying the previous report's ID and provenance via
`state?.evidence.find(...) ?? inspected`.

Before: a local adaptation read the original Connected source from immutable
`450c31a`, injected the denied state and selected report, and rendered the actual
connected component. Result: `denial_visible=true`,
`retained_record_visible=true`, `browser_test=false`. All generated artifacts
were confined to this worktree's ignored folders; no runtime data was read.

After: the workflow stores only an inspection ID. Each state transition clears
it when denied, state is absent or the ID is absent from the authorized evidence
snapshot. Connected resolves details exclusively from that current snapshot;
there is no cached-record fallback. Rendering drops details immediately, before
the effect synchronizes the native dialog closed. Restored access/evidence does
not reopen inspection. Updating the same authorized record shows its new details.

Changed paths and reasons:

- `frontend/src/Connected.tsx`: current-snapshot lookup, ID-only selection and
  dialog closing; no retained report/image object.
- `frontend/src/workflowController.ts`, `useWorkflow.ts`: atomic selection
  reconciliation with state/denial/removal and existing identity cleanup.
- `frontend/src/inspectionDialog.ts`: idempotent native-dialog synchronization,
  keeping an already-open refreshed inspection open and closing invalid selection.
- `frontend/tests/inspection-transitions.mjs`: six new lifecycle/render cases
  using the actual workflow/access classes and actual Connected rendering. The
  hook snapshot is injected; native open/close uses a deterministic double.
- `frontend/tests/presentation-entry.tsx`, `presentation.test.mjs`: exports and
  registration through the existing test command, without manifest changes.

## Verification and handoff

Clean implementation checks from frontend (Node 22.14.0 / npm 10.9.2):

- `npm.cmd test`: 76 passed, zero failed/skipped/cancelled; previous 70 retained.
- `npm.cmd run typecheck`: exit 0.
- `npm.cmd run build`: exit 0; TypeScript and Vite production build pass.
- Scoped diff/whitespace and credential review pass; source files below 500 lines.

Regressions cover: opening then denying both report/image inspection; state
clearing and blob revocation; selected-record removal while unrelated authorized
evidence remains; restoration/reintroduction without automatic reselection;
current-record refresh; logout, identity replacement, unmount, 401 and late
responses. Application inference-disabled 403 preserves authorized inspection
and identity; access-denied 403 clears denied state/selection without logout.
Existing authenticated fetching, blob cleanup, generation isolation, request
headers, no-write-replay and inference/recovery assertions continue to pass.

Sanitized results: `.local/visual/inspection-correction/verification.json` and
`{tests,typecheck,build}.txt`. No screenshots exist. Unavailable browser/native
attempts were not repeated, as requested. Tests establish offline rendering and
transitions, not actual native-dialog/focus/CSS behavior or combined backend
acceptance. The backend/auth contract and frontend profile configuration remain
unchanged. No backend/shared records/dependencies/CI changes, merges, cherry-picks,
provider/partner work, spending, deployment or existing-server/data changes.

Next: coordinator sequential integration with independently reviewed backend
`625c3e6be620b7dd21b5be951637cbba09901ade`, then combined checks. Manually open
report/image inspection at 1440x900 and 390x844, deny/revoke grants and refresh,
remove the selected record, restore access, refresh an authorized record and
logout during a pending response. Confirm content clears, dialog closes, focus
returns appropriately and nothing reopens until explicitly selected. Save
sanitized evidence against the combined SHA. No submission gate is newly met.

# Previous frontend authentication follow-up (historical)

Current status: implementation and offline contract checks pass; combined
backend and browser acceptance remain unverified. This authorized follow-up
supersedes the earlier no-implementation checkpoint retained below.

## Revisions and boundary

Workspace: `C:\Users\surya\Projects\faulttrace-visual`; branch:
`feat/finish-visual`. Started clean at the previous final SHA
`e9efbb61db4b13b78d314ee0d562fa74f2366f0b`.

Implementation and clean local tested SHA:
`bbc032908eb3cc64ebe60ead6bd897740a44f92a`.
The subsequent handoff commit changes only this document. Final SHA, remote
comparison and actual CI URL/result are supplied in the delivery message.

Read the immutable `docs/release-preparation.md` and relevant backend access/API
source using read-only `git show` at
`85d65c821d909783a09f87d4f360fe27e44002c5`. Worker B's tested application is
`e956bd423f8fce453491f8d1f15c2148db2cde4f`; its reported
[application CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40592354394)
is backend evidence, not a combined-branch result. No backend implementation
was merged, cherry-picked or copied into this branch.

## Behavior and changed paths

- `frontend/src/identity.ts`: strict validation of the approved identity shape,
  explicit profile match, server role, incident UUIDs and sole create capability.
  Operator cannot acquire create permission. No expiry or assignments invented.
- `frontend/src/AccessGate.tsx`, `access.css`: labeled masked token entry,
  verification/loading/error states, wrong-workspace navigation, Refresh access
  and browser logout. Input clears before awaiting authentication. Credentials
  live only in memory; reload and return from sample mode require re-entry.
- `frontend/src/access.ts`: one bearer layer for identity, state/JSON requests,
  fetch uploads, measured XHR uploads and protected image bytes. No tokens in
  URLs, persistence, diagnostics, analytics or frontend environment variables.
  Same-origin API paths only; fetch uses no-store and rejects redirects.
- `frontend/src/workflowController.ts`, `useWorkflow.ts`: bounded polling,
  preserved mutation bodies/UUID keys, no write replay, pending-request aborts,
  identity-generation checks and immediate private-state clearing. Old unmount
  cleanup cannot abort a newer identity's requests or revoke its image URLs.
- `frontend/src/api.ts`: safe typed errors distinguish 401 from application 403,
  access denial, stale/idempotency conflicts and sanitized internal failures.
  Every API 401 clears access. Inference-disabled 403 does not log the user out.
- `frontend/src/Connected.tsx`, `workspace.ts`: verify identity before mounting
  private workflow, restrict navigation to server role, retain explicit local
  role switching and show incident denial without private state.
- `frontend/src/CommanderPage.tsx`: preserve planning/approval/clock controls;
  creation requires the server capability in release. A permitted Commander can
  explicitly create after state access is denied, without a fabricated empty
  snapshot. Successful creation refreshes identity for the new creator grant.
- `frontend/src/OperatorPage.tsx`, `JourneyPanel.tsx`, `JourneyOutcome.tsx`,
  `journeyState.ts`: preserve assigned evidence/report/refusal/completion,
  telemetry and recovery. Release hides untasked simulation reports; missing
  correction approval IDs cannot enable execution. No history is invented.
- `frontend/src/EvidenceWorkspace.tsx`: both roles retain explicit authorized
  evidence analysis, with existing inference/capability/current-task gates.
- `frontend/src/photoUpload.ts`: typed object-URL dependency for cleanup tests;
  existing raw bytes, 2 MiB limit, purpose/fixture/revision headers and measured
  XHR behavior remain. Reference photos do not acquire fixture provenance.
- `frontend/tests/authentication-contract.mjs`, `presentation-entry.tsx`,
  `presentation.test.mjs`, `demo.test.mjs`: 19 new mock contract cases, existing
  assertions retained except explicit contract changes: Commander may analyze
  and executable corrections require an approval ID. The approved fixture now
  includes its ID and a missing-ID rejection is added. No manifest changes;
  the existing presentation test entry registers the new suite.

State ingestion ignores server-provided image URLs, fetches canonical protected
image endpoints with authentication, and supplies temporary blob URLs to both
thumbnails and inspection. Images are cached only within the current identity,
revoked when removed/replaced, on access refresh/logout/401 and on workspace
unmount. Existing photo draft effects release local selections on replacement,
cancel and unmount; auth transitions unmount the entire private workspace.
Aborting browser requests does not establish cancellation of server mutations.

## Exact nonsecret frontend configuration

`VITE_FAULTTRACE_PROFILE` is a **build/dev configuration**, never a credential:

- Unset, empty or `release`: release behavior; masked entry and valid release
  identity are mandatory before private state loads.
- Exactly `local`: user explicitly chooses local mode, then clicks Verify local
  server. `/api/identity` must return profile local, null principal/role, false
  create capability and no incident grants. No failure triggers local fallback.
- Any other value: configuration error; no private requests.

Example commands from this worktree's frontend directory:

```powershell
$env:VITE_FAULTTRACE_PROFILE = 'release'
npm.cmd run build
```

For explicit local rehearsal, set the same variable to `local` before starting
Vite or building. Never put a token into a VITE variable, shell command, URL,
configuration file or tracked artifact. Enter it only in the masked form.

The frontend still uses same-origin `/api` proxying. Its committed default is
127.0.0.1:5173 -> 127.0.0.1:8765; backend integration must supply an identity-aware
server. Existing frozen scenario backends lacking `/api/identity` are intentionally
incompatible, even with explicit local configuration. No server was restarted.

For a later coordinator-owned fresh combined rehearsal, use a separate ignored
Vite config with host 127.0.0.1, strict frontend port 5210, existing filesystem
denies and `/api` proxy to the coordinator's fresh release backend (for example
8830, in Worker B's launcher range). Set the backend's allowed preview origin to
`http://127.0.0.1:5210`; preserve browser Origin checks. Proposed frontend command:
`npm.cmd run dev -- --config ../.local/visual/combined-preview.config.mjs --port 5210`.
Proposed URLs: `http://127.0.0.1:5210/commander` and `/operator`.
No such config/server/data directory was created or run here. Administrator
credentials, grants and task assignments remain backend/coordinator work.

## Verification and remaining acceptance

At clean implementation `bbc032908eb3cc64ebe60ead6bd897740a44f92a`, Node
22.14.0 / npm 10.9.2, from frontend:

- `npm.cmd test`: 70 passed, zero failed/skipped/cancelled.
- `npm.cmd run typecheck`: exit 0.
- `npm.cmd run build`: exit 0; TypeScript and Vite production build passed.
- Scoped diff/whitespace and credential review passed; source/test files remain
  below 500 lines. Installed dependencies/lockfile were reused, unchanged.

Sanitized offline check output is ignored under
`.local/visual/worker-a-auth/{tests,typecheck,build}.txt`; summary in
`.local/visual/worker-a-auth/verification.json`. Synthetic sentinels only; no real
credential or private upload was used. Backend tests were not rerun locally.

Mocks exercise strict identity/local mode, all API header paths, raw uploads,
401 versus application errors, scoped controls, protected image failures and URL
revocation, logout/unmount during pending work, late identity/image/state/write
results, non-disclosure, no write replay and explicit creation/grant refresh.
Review found and fixed a race where delayed old-component cleanup could abort a
new identity request; a dedicated regression verifies owner-scoped cleanup.

Browser/native attempts were deliberately **not repeated**, per the user request.
The prior empty browser inventory/unavailable helper remains the browser blocker.
No screenshots, DOM interactions, camera, upload-progress, visual or focus pass
is claimed for this implementation. Mock/static checks do not prove combined
backend compatibility, live inference or photographic accuracy.

Manual review after sequential coordinator integration (fresh synthetic data,
inference disabled; label any seeded output OFFLINE TEST OUTPUT):

1. At 1440x900 and 390x844, exercise masked entry, keyboard labels/focus,
   checking/error states, wrong-workspace navigation and reload re-entry.
2. Verify Commander create true/false and Operator controls in separate sessions.
   Test an ungranted Commander with create permission, then creation, grant
   refresh, assigned-task visibility and missing correction approval IDs.
3. Select/preview/replace/cancel a photo; upload under throttling and inspect
   stored images/thumbnail/full-image scrolling. Verify requests carry bearer
   headers, not URL credentials; preserve purpose/revision/UUID headers.
4. Logout during polling/upload/analysis, with a draft and an open dialog. Confirm
   private data clears, object URLs release, late results remain absent and
   login never resubmits a write. Do not infer server cancellation from abort.
5. Change administrator grants/revoke a credential; use Refresh access. Check
   401 clears the session, access-denied 403 clears denied state without treating
   inference-disabled 403 as logout, and malformed/network failures stay closed.
6. Recheck disputes, independent blank answers, planning budgets, approval/stale
   approval, recovery progress/success/failure/relapse and empty histories.
   Save sanitized screenshots/results against the actual combined tested SHA.

Main failure mode: stale asynchronous responses or delayed cleanup crossing an
identity boundary. Offline generation/abort/cleanup tests pass; actual browser
lifecycle and combined backend enforcement remain integration gates. This branch
does not contain Worker B's backend and cannot itself claim release acceptance.

Ownership overlap was explicitly authorized by this follow-up. No backend,
dependency manifests, shared state/submission documents, CI, fixtures or other
worktrees changed. No provider calls, partner integrations, spending, deployment,
existing-server operations or historical-data changes occurred.

Proposed coordinator-owned state/submission text (not applied):

> Worker A adds memory-only bearer entry, strict identity/profile verification,
> server-role navigation, authenticated JSON/uploads/images and generation-safe
> logout cleanup. Clean implementation bbc032908eb3cc64ebe60ead6bd897740a44f92a
> passes 70 frontend tests, typecheck and build. Final handoff records remote/CI.
> Combined Worker B backend and browser acceptance are not established; no
> submission checkbox is newly satisfied. Next: integrate sequentially, configure
> same-origin fresh release rehearsal, then verify both roles, images, grant
> refresh and logout races at desktop/mobile sizes with inference disabled.

# Previous visual-only checkpoint (historical)

Status: **BLOCKED; no demonstrated visual defect and no visual pass.**
Review date: October 27, 2026 (America/New_York).

## Revision and scope

- Workspace: `C:\Users\surya\Projects\faulttrace-visual`.
- Branch: `feat/finish-visual`.
- Verified clean base and tested application SHA:
  `f2da0085a99061fe00f29ba91e5ba92b36d475fa`.
- Implementation: none. Application source, tests, dependencies and lockfile
  are unchanged. This document is the only tracked change.
- Final documentation SHA is supplied in the delivery handoff; it cannot be
  embedded in its own commit. Tests below apply to the identical application
  tree at that final SHA, not to any future combined/authentication revision.

Read AGENTS.md, the local Worker A brief, README.md, docs/state.md,
docs/submission.md, docs/unified-investigation.md and the read-only prepared
scenario manual. Its frozen application SHA is
`17b7ffeb4bf0af31a385ee120ad34113f89ab49a`; ports 5190..5204 do not load edits
from this worktree. Older previews and every existing scenario were preserved.

## Actual browser attempts and before/after findings

1. Browser/computer inventory returned `apps=[]`, `browsers=[]`.
2. Native computer-use initialization succeeded, but `sky.list_apps()` failed:
   `Computer Use native pipe is unavailable: failed to connect native pipe:
   The system cannot find the file specified. (os error 2)`.
3. Attempted in-app opening of `http://127.0.0.1:5190/commander`:
   `Browser is not available: iab`.
4. Attempted in-app opening of `http://127.0.0.1:5190/operator`:
   the same error, before page loading.

Neither route could be rendered at 1440x900 or 390x844. No application control
was clicked, no file selected/uploaded, no report submitted and no case mutated.
No before/after visual finding is possible. No frontend fix was invented from
static markup or passing tests. Graphite/teal styling, disclosures, independent
blank answers, human/model separation, evidence references, uncertainty,
approval and independent recovery behavior remain unchanged.

| Acceptance area, both routes and viewport sizes | Result |
| --- | --- |
| Overview, assignment, schematic labels, responsive overflow | BLOCKED |
| Tab/Shift+Tab, Enter/Space, visible focus, labels | BLOCKED |
| Inspect dialog, Escape/focus return, Fit/Enlarge and scrolling | BLOCKED |
| Photo selection, local preview, replace/cancel, stored photo | BLOCKED |
| Measured upload progress and injected upload failure | BLOCKED |
| Real device camera capture | NOT RUN |
| Human/model disputes, uncertainty, shared citations, handoff | BLOCKED |
| Approval, stale approval, completion and independent recovery | BLOCKED |
| Observing, verified, failed and relapse outcomes | BLOCKED |
| Empty, four-second loading and disconnected states | BLOCKED |

Private sanitized result record:
`.local/visual/worker-a-f2da0085/verification.json`.
Reserved screenshot directories beneath that folder are empty:
`screenshots/f2da0085a99061fe00f29ba91e5ba92b36d475fa/desktop-1440x900/`
and `mobile-390x844/`. There are no screenshot artifacts to review.

## Local checks

Node `22.14.0`, npm `10.9.2`; this worktree initially had no node_modules or
backend venv. Initial `npm ci` failed on sandbox access to the default external
cache. The approved retry from frontend used
`npm.cmd ci --cache ../.local/npm-cache`: exit 0, 23 packages installed from
the existing lockfile, audit reported zero vulnerabilities. No tooling upgrade.

From frontend, all at the base application SHA:

- `npm.cmd test`: exit 0; 51 passed, zero failed/skipped/cancelled.
- `npm.cmd run typecheck`: exit 0.
- `npm.cmd run build`: exit 0; TypeScript and Vite production build passed.

These are static/offline checks, not browser, model-accuracy or recovery
interaction evidence. Backend was unchanged and its tests were not rerun.
Final diff/staging, remote SHA and actual CI results are in the delivery handoff.

## Preview and exact manual continuation

No fresh preview/server or synthetic database was created: browser access failed
before review and there is no justified application change to serve. Ports 5210
and 8810 had no listener when checked; recheck before future startup. No old
server was stopped/restarted, and no database, ledger, uploads, credentials,
venv or node_modules were copied from another tree.

For a later review, use the committed `tools.offline_investigation_demo.py`
harness with a newly created backend environment in this worktree following
README setup. Do not reuse prepared scenario storage. Example backend command
from this workspace, after verifying ports are free:

```powershell
if (Get-NetTCPConnection -State Listen -LocalPort 5210,8810 -ErrorAction SilentlyContinue) { throw 'Ports occupied; preserve their owners' }
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
$env:FAULTTRACE_PREVIEW_ORIGIN = 'http://127.0.0.1:5210'
$env:FAULTTRACE_DEMO_DATA_DIR = Join-Path (Get-Location) ('.local/visual/worker-a-' + [guid]::NewGuid().ToString('N') + '/data')
.\.venv\Scripts\python.exe -m uvicorn tools.offline_investigation_demo:create_demo --factory --host 127.0.0.1 --port 8810 --no-access-log
```

Create an ignored Vite config with loopback host, strict port 5210, the same
filesystem denies as frontend/vite.config.ts, and `/api` proxy to
`http://127.0.0.1:8810`. From frontend run
`npm.cmd run dev -- --config ../.local/visual/worker-a-preview.config.mjs --port 5210`.
Future URLs: `http://127.0.0.1:5210/commander` and `/operator`.
These commands were **not executed**; no active preview/data directory is claimed.
The harness labels seeded results OFFLINE TEST OUTPUT and uses doubles, not
live AI. Any paused clock added for review must be disclosed as a controlled
fixture; this session added no clock override.

When a browser is available:

1. Review overview and F-17 assignment on both routes at both sizes. Check
   labels, task rationale, blank independent fields and keyboard access; record
   concrete findings before any changes.
2. In fresh local data, select panel-a, replace with panel-b, cancel and verify
   no record was created. Select/upload panel-a, inspect from both routes and
   exercise Fit/Enlarge, pan, Escape and focus return. Throttle the network to
   observe measured progress; a fast localhost upload is not a progress pass.
   Exercise real camera separately on an actual device.
3. Follow the seven groups in the prepared scenario manual for separate
   disputes/unreadability, explicit handoff/citations/escalation, approval/stale
   approval, observing/success/failure/relapse and empty/loading/error states.
   Preserve prepared scenarios; any mutating rehearsal uses fresh local data.
4. Save sanitized screenshots plus action/result records under ignored
   `.local/visual/`, tied to the actual tested SHA, routes and viewport sizes.
   Mark unexercised states unverified. Doubles never establish live accuracy.

## Ownership, risks and proposed coordinator updates

No Worker B auth overlap was edited. `api.ts`, `useWorkflow.ts`, `Connected.tsx`
and role navigation retain their existing contract. Coordinator must review
authentication integration and recheck the combined SHA separately. No Tavily,
LangSmith or Toloka work, provider request, spending, deployment or integration.

Main failure mode: static checks can pass while rendered layout, keyboard,
upload or recovery interactions fail. Those gates remain open. The exact next
action is to restore browser access, review group 1 and record actual defects
before implementing a bounded frontend fix.

Proposed docs/state.md addition (not applied):

> Worker A verified clean feat/finish-visual at f2da0085a99061fe00f29ba91e5ba92b36d475fa.
> Browser inventory is empty, in-app opening of both routes fails and native
> helper pipe is unavailable. No visual defect/pass or screenshot was invented;
> application code is unchanged. All 51 frontend tests, typecheck and build pass.
> See visual-acceptance-review.md and final handoff for CI/remote evidence.
> Next: restore browser access and review overview/assignment at both viewports.

Proposed docs/submission.md addition (not applied):

> Worker A browser review remains blocked; no product or submission checkbox
> is newly satisfied. Static frontend checks pass at the unchanged base
> application SHA. Desktop/mobile, keyboard/dialog, photo/progress/camera and
> recovery interactions remain unverified; see visual-acceptance-review.md.
