# Combined authenticated preview ? founder manual review

Status: founder sign-in/screenshots reported; revised layout acceptance PENDING.
The running frontend uses the latest `feat/finish-integrated` presentation source;
record its delivered SHA with new screenshots. Backend remains unchanged from
tested implementation `a5f7cb837d47fa2875a08a62fcdcaad46f0e3575`.
[Exact-SHA CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40614907584)
passes all three baseline jobs: 205 guarded backend tests, 76 frontend tests,
dependency/type/build checks and actual frontend classes against release ASGI.
Static/API checks do not establish browser, focus, upload-progress or camera acceptance.
No repeated unavailable browser/helper attempts were made.
The later bounded presentation revision passes 79 frontend tests, type/build and
the real ASGI contract check; its exact-SHA CI is reported with delivery. Existing
tabs may reload after the favicon HTML change; re-enter the same private token if
needed. No server/registry restart or credential rotation is required.

Next screenshot group only (before further interaction acceptance):

1. Desktop Operator 1440x900: session identity/access/logout and top assigned task.
2. Operator 390x844: initial viewport, stacked photo controls and blank answers.
3. Commander 390x844: initial current decision, concrete gaps and simulation/test labels.

Keep details closed initially; do not upload/submit/approve. Prior full checklist
below remains pending beyond the founder-reported sign-in and screenshot findings.

## Active isolated review

- Commander: http://127.0.0.1:5210/commander
- Operator: http://127.0.0.1:5210/operator
- Backend: localhost 8830, accessed through the frontend's same-origin `/api` proxy.
- Scenario: simulated plant, **TEST-CREATED F-17 observation assignment**, not
  AI-generated. No model output, diagnosis, correction or recovery is fabricated.
- Production release authentication/policy are active. Inference is disabled,
  key source is absent and a forbidden transport guards accidental provider use.
- Separate registry, workflow/images and empty ledger are under the ignored
  directory recorded in `.local/reviews/integrated-preview.json`. No old run was
  reused. Existing listener processes were preserved; old previews are not the
  acceptance target for this integrated build.

HTTP checks confirm both routes, strict unauthenticated 401, matching authenticated
incident/task state, role scoping and inference disabled. Review ledger has no
attempts, existing provider ledger is unchanged, and new logs contain no tokens.
These checks do not pass any manual interaction below.

## Private synthetic credential delivery

Tokens are local application credentials, never the Nebius key. They expire 24
hours after issuance. Do not paste them into chat, URLs, logs or screenshots.
From the repository root in your private PowerShell terminal, copy Commander
without displaying it, then paste only into the masked Commander form:

```powershell
$review = Get-Content -Raw .local/reviews/integrated-preview.json | ConvertFrom-Json
Get-Content -Raw (Join-Path $review.directory 'auth/commander.delivery') | Set-Clipboard
```

For the Operator tab, replace the clipboard contents privately:

```powershell
Get-Content -Raw (Join-Path $review.directory 'auth/operator.delivery') | Set-Clipboard
```

Clear the clipboard after pasting with `Set-Clipboard -Value ''`. Browser logout
clears memory only; server revocation is a separate local administrator operation.
Do not expose the registry or delivery files. Windows ACL isolation is unverified;
this remains a localhost rehearsal, not a production credential distribution system.

## First small manual group ? pause for founder observations

Record PASS / FAIL / BLOCKED / NOT RUN and actual observed behavior. Start at
1440x900, then repeat at 390x844 using a responsive browser viewport.

1. Open Commander and Operator in separate tabs. Before entry, see only masked
   access controls; Tab/Shift+Tab should reach the label/input/button with visible
   focus. Enter each privately delivered role token in its respective tab.
2. Confirm server-reported roles and role-specific navigation. Commander has
   investigation/planning/approval responsibilities; Operator has observation
   controls without incident creation or Commander approval. Visiting the wrong
   route must offer navigation to the authenticated role, not more authority.
3. Check the same incident ID in both tabs. Operator should show the assigned
   F-17 task, test-created provenance, clear evidence request and blank independent
   report fields. Keep simulation/test labels visible. Inference actions stay
   disabled. There is no submitted image or completed observation yet.
4. Check initial desktop/mobile spacing, readable controls and no horizontal
   page overflow. Do not pass camera, file selection, dialogs or upload progress
   without exercising them in a later group.
5. Log out in each tab: workspace/private content should disappear. Reload must
   require token re-entry. Logging out one tab must not invent logout or revocation
   in the other. Do not submit reports or start correction in this first group.
6. Return concrete observations before the next mutating review group. Save only
   credential-free screenshots under the review directory's
   `screenshots/a5f7cb837d47fa2875a08a62fcdcaad46f0e3575/desktop-1440x900/`
   and `mobile-390x844/`. Those directories currently contain no screenshots.

## Boundaries still open

Both worker histories are preserved by sequential B then A feature-branch merges.
Creation race and retained-inspection defects pass independent offline review.
Current authorized evidence alone drives inspection; access denial clears selection
and restored access does not reopen it. Actual dialog/focus behavior needs manual
review. Later groups must cover photo collection, grant denial/401, interrupted
writes and logout, disputes/refusals, approval, verification failure and relapse.
No provider request, live adaptive acceptance, photographic numeric accuracy,
Linux PNG-byte portability, verified Windows ACLs, TLS/hosting, durable registry/DB
atomicity or final submission is established. C drafts and partner features remain
unintegrated. Refer to [backend contract](release-preparation.md) and
[frontend handoff](visual-acceptance-review.md); do not relax policy for the review.
