# FT-005 local interactive preview

Open **http://127.0.0.1:5173/** on this computer while the local server runs.
This is a frontend preview, not deployed hosting. The persistent banner says
"Interactive demo — sample data" and "Live AI not connected". No provider
requests, credentials, cloud synchronization, equipment actions, or verified
recovery are part of this application.

## Install, start, and verify (PowerShell)

Node 22.12+ is required (verified 22.14.0; npm 10.9.2). Direct dependencies
are pinned: React/ReactDOM 19.3.1; Vite 8.3.5; TypeScript 7.0.2;
React/ReactDOM types 19.3.0. The npm v3 lockfile is committed. Only these six
direct dependencies were added. No UI, chart, icon, or browser-test framework
is required. The Node test runner uses its experimental type-stripping flag.

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd ci
npm.cmd run dev
```

The dev script binds to 127.0.0.1:5173 with strictPort. It will fail rather
than silently selecting another port. Keep that terminal open. For checks
in a second terminal:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace\frontend'
npm.cmd run test
npm.cmd run typecheck
npm.cmd run build
```

Python probes and tests remain independent and unchanged:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
& 'C:\Users\surya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

## What to review

Commander has baseline sample metrics, a clickable SVG process loop,
equipment-specific details, a fixed pressure trend with kPa/minute axes,
competing explanations, evidence gaps, active task, rationale, and an ordered
activity/evidence record. Mobile schematic/chart areas scroll internally
to preserve label size; mobile also has direct equipment selectors.

Start demo incident assigns a local observation request. Switch to Operator,
expand "Why this task?", and choose one committed synthetic fixture:
clear panel-a or opaque panel-b. Submit observation updates the same tab's
Commander state. This is a deterministic sample transcription, not AI analysis.
Cannot access, Wrong equipment, and Unreadable record different evidence gaps
with no invented numeric value. Optional notes stay local. Evidence inspection
shows the source, readability, and task-assigned/disputed identity, never
photographic proof of identity or action. The inspector is a native modal
dialog with Escape/close handling and focus restoration.

Reset starts over. Request another observation preserves earlier evidence
in the activity record. An already active incident disables the start button
with a visible reset explanation. Submitting without a fixture/response shows
a validation message. Operator before an incident has a no-task state.

All state is in React memory in this one tab, shared by the two views. Reload,
reset, or closing the tab clears it; other tabs/devices do not synchronize.
There is no camera, upload service, simulator, backend, telemetry connection,
model integration, inference accounting, or maintenance/recovery verification.
No model tokens/latency/confidence are displayed. Previously verified Python
provider evidence does not imply this UI uses those providers.

## Verification boundary

Frontend build/type check and six state-transition tests passed. All 35
Python offline tests passed with zero network attempts under a socket guard.
HTTP readiness and the served Operator module/fixture returned 200.

Actual browser verification was blocked: available browser inventory was
empty; createBrowserTab('iab', localhost) returned "Browser is not available:
iab". No browser was installed or alternate automation substituted. Therefore
desktop 1440x900, phone 390x844, real clicks, modal behavior, keyboard tab order,
focus visibility, rendered contrast, overflow, and image/error appearance
remain UNVERIFIED. Build and state tests do not establish visual correctness.
No screenshots were taken or inspected. Ignored verification metadata and
source hashes are saved under `.local/visual/ft-005/verification.json`.

Founder manual-review sequence:

1. At 1440x900, check the no-incident/empty record and Operator no-task state.
2. Start an incident; select P-04, F-17, V-08; inspect the chart and rationale.
3. Switch views; submit with no selection to check the validation error.
4. Select clear fixture; submit; return to Commander; open and close evidence.
5. Request another observation; submit obscured fixture. Confirm unknown reading.
6. Repeat with Cannot access, Wrong equipment, and Unreadable responses.
7. Check keyboard-only navigation, native details, SVG selectors, dialog Escape
   and focus return; check visible focus, readable contrast, and overflow.
8. At 390x844, repeat the Operator journey and view switching; check scroll
   regions without page-level horizontal overflow. Reset and confirm clearing.

Save sanitized screenshots from actual review under `.local/visual/ft-005/`.
Feedback should identify view/state, viewport, observed behavior, and screenshot.
Live AI, vision, backend integration, deployment, and full submission gates
remain separate checkpoints. Do not run inference to review this preview.
