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

## Remaining Tavily-only terminal action

The two planning and one photo calls have already run. Do not rerun the combined
verification command below. For the unused one-search allowance, use only the
pinned `tools/verify_tavily_reference.py` command from the latest handoff. It tests
the public WIKA A-10 reference example through the production documentation route;
it neither identifies the photograph/F-17 nor supplies correction evidence. NVIDIA
calls and LangSmith exports are blocked. [Exact scope and sources](partner-integration.md).
Founder screenshots narrowly confirm the existing photo trace/attributes are visible;
that is user-reported browser evidence, with no resend or broader UI acceptance.

## Earlier combined terminal verification - historical procedure

Use the single pinned-SHA command in the delivery handoff:
` .venv/Scripts/python.exe tools/verify_sprint_live.py --expected-head <reviewed SHA> `.
Do not replace the reviewed SHA with an unreviewed current HEAD. The runner inherits
**your PowerShell process environment first**, then reads the four named Windows
user environment values if necessary: `NEBIUS_API_KEY`, `TAVILY_API_KEY`,
`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`. Nothing about the coding agent's environment
establishes whether your terminal has those values. No keys are accepted in arguments,
printed, written to reports or requested in chat. Presence is not an authentication
probe; validity is established only by each actual authorized service operation.

The runner uses the **real production demo/session, planning, photo, independent
report and documentation API routes through an in-process ASGI client**. It starts
no TCP server, restarts no preview, creates no workflow task from a mock/template,
and makes real outbound calls only after local preflight. It does not exercise a
browser or authorize correction/recovery. All preparation tests use explicit doubles.

Before contact it checks Python 3.12, exact clean branch/HEAD and unchanged production
code relative to `68634ad`, credentials, the real ledger, prior sprint artifacts and
the image. Default image is the retained hash-verified 960x960 submitted copy; optional
`--photo <path>` selects another original/permissioned compliant photograph. Production
upload validation/metadata removal runs first. Source/submitted hashes and dimensions
are stored privately; originals remain untouched. No filename, expected reading,
reviewer estimate or incident telemetry enters the photo request. Prompt, model,
2048-token cap, reasoning_effort=none, timeout/body bounds and validator are unchanged.

Read-only inventory covers project `.local` workflow/spending databases and known
receipt/ledger artifacts, excluding labeled provider doubles/worktrees. It counts
all relevant records since the conservative pre-sprint baseline `f1d7434` timestamp,
deduplicates attempt IDs and reserves pending/unknown attempts conservatively.
It never imports receipts or changes histories. If calls exist outside these audited
locations or were not saved, stop for reconciliation; do not confirm that there
were none. Do not run manual/other verification calls concurrently.

A shared ignored `.local/sprint-verification/limits.sqlite3` holds the verification
caps across reruns: **two planning / one photo / one Tavily search**. Existing attempts
reduce remaining slots; failures/uncertainties stop their affected path. No reset,
refund, automatic generation retry or fallback is offered. The unchanged production
spending reservations remain underneath this stricter verification gate. Checkout
is rechecked at admission. Do not edit/checkout the repository during execution.

Console flow: confirm balance and completeness of prior-call records, confirm a
known manufacturer/model (or skip search if unknown), inspect the actual first
proposal/photo claim, then enter an **independent** observation/refusal or skip it.
Human answers are blank; never copy the AI reading or fabricate a simulated report.
A valid escalation with no task blocks the photo branch rather than inventing an
assignment. The second planning call requires the genuinely updated context.
A failed photo is not repaired/retried; other permitted independent paths can continue.
Trace failure stops subsequent exports without retrying or failing inference.

The private `result.json` reports separately:

| Result | What a pass establishes | What it does not establish |
| --- | --- | --- |
| NVIDIA planning | Validated accepted/escalated production proposal, receipt/accounting | General reasoning reliability or successful recovery |
| Photographic contract | Stop, validated structured interpretation and receipt | Numeric accuracy, compatible measurement or asset identity; accuracy stays not_evaluated |
| Tavily retrieval | Completed bounded search with at least one allowlisted citation/time | Correct model applicability or observed evidence |
| LangSmith delivery | Per-operation `recorded` means the trace API acknowledged the metadata request | Dashboard visibility; verify that privately. No images, reasoning or account IDs are exported |

Exit 0 requires all four components; exit 1 means partial/failed results, exit 2 means
preflight/interruption. Status polling is read-only, never a generation retry.
Artifacts live under `.local/sprint-verification/investigations/<id>/`: image
provenance, result and application databases/images/per-run usage ledger. Available
receipts remain in production outboxes even on interruption; unknown usage stays
unknown. `.local/nebius-usage.json` is read-only and its hash is checked afterwards.
Review/share only sanitized result JSON or component summaries, not keys/images/raw
responses. Do not rerun after failure to obtain cleaner results; retain diagnostics.

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
