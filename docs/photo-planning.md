# FT-011: photographs inform observation planning

Offline implementation; live and browser acceptance remain open. No inference or
server restart was performed. Existing runs, uploads and receipts are preserved.

Validated `photo-observation-v1` results now enter the bounded planner context as
**model claims**, retaining evidence/task IDs, assigned asset, upload source and
wall-clock timestamp, analysis status, original number/unit, measurement type,
readability and uncertainty. Label text is excluded; a bounded tag mismatch flag
does not assert identity. Assignment and even a matching model-read tag prove
nothing about photographed identity. Human reports remain separate records.

Each photo has an application assessment: usable planning claim, disputed,
incompatible, unresolved or stale. Even a usable claim has unconfirmed identity
and never satisfies a measurement or correction requirement. Ordinary pressure
cannot satisfy DP; external handle orientation cannot prove internal position.
Unreadability, wrong equipment, human/model readability or numeric disagreement,
and missing/failed analysis remain explicit. Numeric disagreement comparison uses
public human DP reports and recognized unit conversions, with a 1e-6 kPa rounding
tolerance, not an operating limit. Original claim values are never converted.
Unsupported comparison units remain uncorroborated; reports are never overwritten.

Planning freshness is conservatively limited to 30 wall-clock minutes from
upload, not a claim about when a photograph was captured. Future/invalid times,
superseded uploads, stale analysis and explicitly reissued observations are stale.
This window does not alter the independent recovery policy.

## Connected flow

1. Operator explicitly analyzes a collected photo (inference opt-in still required).
2. **Send photo for follow-up planning** explicitly releases the awaiting task
   into `needs_evidence`. It does not accept a reading or complete the task.
   Handoff requires the current task/revision and latest, non-stale validated
   photo. It is idempotent and audited; pending tasks are never silently replaced.
3. Commander explicitly chooses the next observation. The unchanged registered
   action catalog permits F-17 DP, V-08 human position observation, or escalation.
   Cited photos require a clarification/unreadability/human-review explanation.
   Unavailable assets stay excluded, including after a handoff.
4. Commander shows the accepted proposal's citations with Inspect actions.
   Operator's resulting observation links to its source photographs and asks for
   independent confirmation using the registered instructions.

Budgets, one attempt per context, stale completion rejection, reservations,
receipts, accounting and no automatic retry remain enforced. Hidden simulator
state is excluded. The independent simulated correction assessment is unchanged
and does not consume photographic claims. No integrated AI recovery claim is made.

## Offline checks and preview

```powershell
Set-Location C:\Users\surya\Projects\faulttrace
.\.venv\Scripts\python.exe -m unittest discover -s tests
Set-Location frontend
npm test
npm run build
```

159 backend tests (including 11 new provider-double integration tests) and 45
frontend tests pass, as do TypeScript and production build. The full backend
suite ran with external sockets forbidden, zero forbidden attempts. Static React
checks cover both workspaces, claims/disagreements, citations, source-photo links,
handoff gates and compatibility with historical backends. Mock choices establish
policy behavior, not live adaptive reasoning or photographic accuracy.

Browser inventory was empty and in-app opening failed: desktop/390x844, keyboard,
modal focus/scroll and real interaction acceptance remain unverified. No new
screenshots exist. Local results: `.local/visual/ft011-offline/verification.json`.
Existing 5180/8780 and 5181/8781 instances were left untouched; their older backend
does **not** expose this bridge. Refreshing their frontend cannot activate it.

For later manual review, start a separate inference-disabled instance in a new
directory. Do not stop the old instances or reuse their data. First verify ports
8782/5182 are free; if either is occupied, stop these instructions.

```powershell
# Backend terminal, from project root. No inference is enabled.
if (Get-NetTCPConnection -State Listen -LocalPort 8782,5182 -ErrorAction SilentlyContinue) { throw 'Preview ports occupied' }
$env:FAULTTRACE_DATA_DIR = Join-Path (Get-Location) ('.local/visual/ft011-' + [guid]::NewGuid().ToString('N') + '/data')
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
$env:FAULTTRACE_PREVIEW_ORIGIN = 'http://127.0.0.1:5182'
.\.venv\Scripts\python.exe -m uvicorn faulttrace.workflow.main:app --host 127.0.0.1 --port 8782
```

```powershell
# Frontend terminal, from project root. Explicit proxy for this isolated instance.
@'
export default { server: { host: '127.0.0.1', port: 5182, strictPort: true,
  fs: { strict: true, deny: ['.env', '.env.*', '*.{crt,pem}', '**/.git/**', '**/.local/**', '**/.venv/**'] },
  proxy: { '/api': { target: 'http://127.0.0.1:8782', changeOrigin: true } } } };
'@ | Set-Content -Encoding utf8 .local/visual/ft011-preview.config.mjs
Set-Location frontend
npm run dev -- --config ../.local/visual/ft011-preview.config.mjs --port 5182
```

Open http://127.0.0.1:5182/commander and http://127.0.0.1:5182/operator.
Fresh state can review empty/loading/disabled planning and recovery-only simulation;
no task or analyzed photograph is invented. Full photo-to-clarification acceptance
still needs an explicitly prepared offline test assignment/provider double or a
separately authorized live journey. Do not enable inference merely for visual QA.
Check at 1440x900 and 390x844: assessment explanations, cited/source-photo Inspect,
keyboard Tab/Shift+Tab/Enter/Space, Escape/focus return and full-image scrolling.

Next: visual acceptance with an isolated, clearly test-created photo/planning
scenario; then separately authorize a bounded live planner-context evaluation.
