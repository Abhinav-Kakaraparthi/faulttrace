# Integrated sprint acceptance

Equipment, telemetry and correction are simulated. Model claims, independent
human reports, reference documents and deterministic recovery remain distinct.
Passing offline provider doubles does not establish live reasoning or photo accuracy.

## Time and monitoring

The preserved 5211 run `12a834ac-7831-4e3e-a67d-98caa6c589df` recorded both reports
at simulation tick 0. Wall-clock receipt times were 20:23:33 and 20:29:50 UTC on
October 28: over six minutes apart, exceeding the existing 120-second wall-clock
freshness policy. This establishes the blocker without changing any timestamp.

New demo runs explicitly use paused walkthrough time for simulated human reports.
Advancing simulation time can still expire them. Uploaded-photo review keeps its
wall-clock freshness; release/local mode always enforces wall-clock freshness,
even if opening a database bearing a demo marker. Audit timestamps and the
two-hour cookie expiry never pause. Legacy reports are not retrospectively fresh.
Commander can request a new observation, including an older task's asset; it has
a new task/report identity, blank independent answers and retained history.
Unavailable assets, contradictions, active tasks and evidence budgets still block.

After explicit approval and Operator completion, Commander chooses **Start
simulated recovery monitoring**. One real second schedules one ten-second
simulator sample, up to six samples. The existing five-consecutive-sample/40-second
minimum, bands and alarms remain authoritative. A sixth sample exercises continued
observation; relapse can revoke verification. Durable progress resumes on authorized
run reopening without repeating correction; storage failures expose interruption.

## Live versus offline

Default is offline. Live demo requires `FAULTTRACE_DEMO_LIVE=1`,
`FAULTTRACE_ALLOW_INFERENCE=1`, a server-only `NEBIUS_API_KEY` and persistent
spending storage. Live entry starts without an automatic task; Commander explicitly
requests a NVIDIA proposal. The four-turn policy and strict application validation
are unchanged. Photo analysis retains the production prompt, validator, model,
2048-token cap and `reasoning_effort="none"`; there are no automatic retries.

**Start new offline demo** is explicit and retains the live run. It creates
application-template assignments, never replacement NVIDIA output. Restart and
new visitor sessions do not refund existing global allowances.

`spending.sqlite3` reserves requests atomically across sessions and worker threads before
provider contact. Defaults: 12 global requests / 1,200,000 token-admission units,
six requests / 600,000 units per visitor, two pending operations globally. Each
text call reserves 67,584 units; photo/fixture calls 264,192; a documentation search
reserves a request but no NVIDIA tokens. Full allowances remain consumed even
after valid usage; unknown, pending and interrupted calls are never refunded.
Actual known usage remains separate in receipts/ledgers. These conservative
admission units are not provider tokenization guarantees, billing or dollar cost.
Reported overruns increase the charge and prevent further admission as necessary.
Thirty-two retained visitor sessions, three runs/session and four 2 MiB images/run
bound this prototype; two global upload/decode slots prevent parallel image decoding
from growing with the visitor count. They are not a general internet-abuse or capacity audit.

Tavily is separately opted in with `FAULTTRACE_TAVILY_ENABLED=1` and server-only
`TAVILY_API_KEY`. It needs human-confirmed manufacturer/model and a registered
official domain. Documents stay untrusted references, outside measurement policy.
LangSmith uses explicit `FAULTTRACE_LANGSMITH_TRACING=1`, server-only key/project,
and allowlisted metadata only. See [partner boundaries](partner-integration.md).

## One later bounded live walkthrough — not executed

Credentials were unavailable in process and Windows user environment. No NVIDIA,
Tavily or LangSmith requests were executed in this sprint. First privately verify
credited balance and configure existing keys; never paste them into chat or URLs.
Use a **new** isolated persistent root and unused localhost port; do not restart
the old previews. Build the demo frontend and run the production wrapper factory
with the explicit loopback exception. The exact launch command accompanies delivery.

Developer-only procedure, from the clean project root, **after** privately setting
`NEBIUS_API_KEY`, `TAVILY_API_KEY`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` in that
terminal and confirming balance. This starts a new instance, not the old previews:

```powershell
$faulttraceRequired = 'NEBIUS_API_KEY','TAVILY_API_KEY','LANGSMITH_API_KEY','LANGSMITH_PROJECT'
foreach ($name in $faulttraceRequired) { if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) { throw 'Configure required provider credentials privately first' } }
if (git status --porcelain) { throw 'Use the reviewed clean checkout' }
if (Get-NetTCPConnection -State Listen -LocalPort 8851 -ErrorAction SilentlyContinue) { throw 'Port occupied; preserve its listener' }
$env:FAULTTRACE_DEMO_ROOT = Join-Path (Get-Location) ('.local/sprint-live-' + [guid]::NewGuid().ToString('N'))
$env:FAULTTRACE_DEMO_ORIGIN = 'http://127.0.0.1:8851'
$env:FAULTTRACE_FRONTEND_DIST = (Resolve-Path '.local/visual/final-sprint-b4a2fb3c1d3248fe95a0b599a27fabe1/frontend').Path
$env:FAULTTRACE_DEMO_LOCAL_HTTP = '1'
$env:FAULTTRACE_DEMO_LIVE = '1'
$env:FAULTTRACE_ALLOW_INFERENCE = '1'
$env:FAULTTRACE_TAVILY_ENABLED = '1'
$env:FAULTTRACE_LANGSMITH_TRACING = '1'
.venv/Scripts/python.exe -m uvicorn faulttrace.workflow.public_app:create_public_app --factory --host 127.0.0.1 --port 8851 --workers 1 --no-access-log --log-level critical
```

Open http://127.0.0.1:8851/ and follow these bounds once. Do not run another
verification if a prior sprint request was already made; reconcile its records first.

1. Open Commander, **Try demo**. Make at most two explicit **Choose next
   observation** calls, separated by an independent Operator report/refusal.
   Inspect the accepted citations, human/model distinction and remaining budget.
2. On an assigned observation, optionally upload one original/permissioned compliant
   photograph and make **one** explicit photographic-analysis call. Supply no
   expected answer, filename hint or incident telemetry to the model. Inspect its
   actual structured claim, uncertainty, finish reason, receipt and image in both
   workspaces. Wrong/incompatible/unreviewed photographs must block correction.
   An ordinary pressure gauge is not F-17 differential-pressure evidence.
3. Perform at most **one** Tavily search after independently identifying a real
   manufacturer/model; inspect the actual official citation and retrieval time.
   Verify corresponding metadata-only LangSmith traces privately, not from a
   fabricated screenshot. Failure must not replay inference.
4. If compatible fresh evidence is sufficient, explicitly approve, acknowledge
   completion in Operator, then start monitoring in Commander. Otherwise show the
   clarification/escalation honestly; do not force a successful journey. Stop an
   affected live path after failure. Preserve every receipt once, including unknowns.

This is a maximum of two NVIDIA text calls, one NVIDIA photo call and one Tavily
search, with tracing for those operations. Do not repeat previous successes.

## Consolidated founder browser acceptance

Use the newly supplied same-origin review URL, not an old backend. At 1440×900
and 390×844: Try demo, switch roles/second tab, refresh, inspect task and decision.
Exercise keyboard focus, independent blank fields, refusal, photo preview/replace/
cancel/upload/error, full-image dialog and protected image loading. Verify
insufficient/conflicting/stale evidence blocks approval; test new observation
renewal, explicit approval, Operator completion and automatic monitoring.
Test separate private-browser visitors and End demo. Camera capture is unverified
until an actual camera is exercised. HTTP/static checks are not visual acceptance.
Known-unavailable browser helpers were not retried. No video was recorded/published.

Paid hosting was declined. The [free-storage assessment](sprint-release.md) must
be resolved before deployment: authoritative external reservations/state/images,
then hosted HTTPS, isolation, restart and founder acceptance on the deployed SHA.
No broad migration has begun. Do not enable public inference on ephemeral budgets
or finalize Devpost from local/static checks.
