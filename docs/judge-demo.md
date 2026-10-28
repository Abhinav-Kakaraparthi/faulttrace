# Judge demo access

The separate **demo** frontend opens with **Try demo**. No account, terminal,
administrator grant or copied workspace token is needed by the visitor.
Cookie bootstrap alone does not create an investigation. Try demo creates an
isolated simulated run and an application-template F-17 observation assignment.
Commander/Operator switching and the second-tab link share that visitor's run.
Refresh/reopening resumes it until the two-hour absolute session expiry.

One visitor is deliberately permitted to use both workspaces. This is not
production separation between two employees. Administrative bearer access remains
on the separate release service; a demo cookie cannot authenticate there.

## What is real and what is simulated

Storage, cookie authorization, uploads, independent human reports, approval,
duplicate/stale checks and sample-based recovery verification are the application
workflow. Equipment and telemetry are explicitly simulated. Initial and explicit
demo observations use registered application templates with honest provenance,
not mocked NVIDIA output. Commander can assign another available observation or
escalate through **Demo observation templates — no AI inference**. Active tasks,
inaccessible assets, revisions and a four-assignment demo budget remain enforced.
That budget is separate from the existing four-call model-planning budget.

Inference is hard-disabled with an absent key source and forbidden transport,
regardless of inherited inference environment flags. Explicit model controls stay
visible but disabled. No photo interpretation, usage or latency is fabricated.
Photographs are collection-only: an unreviewed photo can block approval. A fresh
report-only investigation can demonstrate simulated recovery without pretending
an image was analyzed. Human answers remain blank and independently entered.
Pressure cannot satisfy a differential-pressure requirement. Conflicts/refusals
and stale reports still block correction; Operator completion is not recovery.

## Session and security contract

- Cookie is opaque and HttpOnly; only its hash is stored server-side. HTTPS uses
  a host-only `__Host-` cookie with Secure, SameSite=Strict and Path=/. Explicit
  loopback HTTP development uses a separately named non-Secure cookie, Path=/api.
  No bearer credential is returned to JavaScript or stored in browser storage.
- Session/run metadata and a synchronizer CSRF token are fetched into memory.
  All API reads require the demo custom header and reject cross-site/same-site
  fetch metadata. Every mutation requires exact configured Origin plus matching
  CSRF. No CORS permission is enabled. Tokens/cookies never enter URLs or logs.
- Server-generated run IDs choose private databases/images/ledgers. Incoming
  bearer headers are rejected; client cookies are never forwarded to child apps.
  Internal role credentials exist only in server memory. Both workspace headers
  are allowed only inside the visitor's own session, with normal role/resource
  checks applied by the existing workflow.
- A run header prevents old tabs/in-flight operations from targeting a replacement
  investigation. Restart uses idempotency and retains prior data. End demo revokes
  the server session. Other tabs clear on their next request; no writes are replayed.
- Local bounds: 32 total session rows per instance, three retained investigations
  per session, four collected photos per investigation (normal upload bounds still
  apply), four template assignments and existing report/clock/model budgets.
  Expired rows/files are retained, not silently deleted or recycled. Capacity
  errors require host review; this is not a production retention system.
- One process owns each demo root. Child lifespans are explicitly managed; sessions
  and assignments resume across a controlled server restart without copying history.

## Developer startup (not judge instructions)

Use installed Python/backend dependencies and the existing frontend lockfile.
Preserve all occupied ports. New backend terminal from the repository root:

```powershell
if (Get-NetTCPConnection -State Listen -LocalPort 8840,5211 -ErrorAction SilentlyContinue) { throw 'Ports occupied; preserve existing listeners' }
$env:FAULTTRACE_DEMO_ROOT = Join-Path (Get-Location) ('.local/judge-demo-' + [guid]::NewGuid().ToString('N'))
$env:FAULTTRACE_DEMO_ORIGIN = 'http://127.0.0.1:5211'
$env:FAULTTRACE_DEMO_LOCAL_HTTP = '1'
$env:FAULTTRACE_ALLOW_INFERENCE = '0'
.venv\Scripts\python.exe -m uvicorn faulttrace.workflow.demo_app:create_demo --factory --host 127.0.0.1 --port 8840 --workers 1 --no-access-log --log-level critical
```

Frontend: use a separate ignored Vite config with localhost/strict port 5211,
the project's private-file denies, and same-origin `/api` proxy to 8840; set
`VITE_FAULTTRACE_PROFILE=demo` in that terminal. Example (project root):

```powershell
New-Item -ItemType Directory -Force .local/demo-config | Out-Null
@'
export default { server: { host: '127.0.0.1', port: 5211, strictPort: true,
  cors: false,
  fs: { strict: true, deny: ['.env', '.env.*', '*.{crt,pem}', '**/.git/**', '**/.local/**', '**/.venv/**'] },
  headers: { 'X-Frame-Options': 'DENY', 'Content-Security-Policy': "frame-ancestors 'none'" },
  proxy: { '/api': { target: 'http://127.0.0.1:8840', changeOrigin: true } } } };
'@ | Set-Content -Encoding utf8 .local/demo-config/vite.config.mjs
$env:VITE_FAULTTRACE_PROFILE = 'demo'
Set-Location frontend
npm.cmd run dev -- --config ../.local/demo-config/vite.config.mjs --port 5211
```

Visitor URL: http://127.0.0.1:5211/ — click Try demo, then switch workspaces or
open Operator in a second tab. Use a separate browser profile/private context to
review another isolated visitor. Do not reuse admin tokens in this flow.

Offline contract checks, from frontend with the existing Python interpreter:

```powershell
$env:FAULTTRACE_TEST_PYTHON = (Resolve-Path ../.venv/Scripts/python.exe).Path
node tests/combined-contract.mjs
node tests/demo-contract.mjs
```

## Remaining public deployment and paid-inference gates

No hosting or live judge walkthrough is verified. Before public access, review
TLS/ingress and trusted-proxy configuration, HTML CSP/frame protection, secret/
directory ACLs, session/upload creation rate limits and byte quotas, request
timeouts, storage capacity, retention/backup and operational log redaction.
Current caps bound this local prototype, not adversarial internet traffic.
No multi-worker/hosted durability or general tenant-security audit is claimed.

Before any live inference: confirm credited Nebius balance, add server-authoritative
global and per-visitor spend/token/request caps across new sessions/restarts,
concurrency/rate/abuse controls, reservation/accounting and a hard kill switch.
Per-investigation budgets alone do not prevent public spending abuse. This demo
cannot enable inference merely by setting an environment flag; a separately
reviewed change and bounded live acceptance would be required. Numeric photo
accuracy, general adaptive reasoning and submission acceptance remain unverified.

Security/framework references checked October 28, 2026:
[Starlette cookie response controls](https://starlette.dev/responses/),
[FastAPI child lifespan limitation](https://fastapi.tiangolo.com/advanced/events/#sub-applications),
[OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
[MDN cookie attributes/prefixes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).
