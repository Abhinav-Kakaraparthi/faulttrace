# Worker A visual acceptance review

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
