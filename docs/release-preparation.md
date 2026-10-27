# Worker B: authenticated local release preparation

Base `f2da0085a99061fe00f29ba91e5ba92b36d475fa`, branch
`feat/finish-release`. Backend-only checkpoint; no deployment or combined UI
acceptance. Frontend, README/state/submission, dependencies, fixtures, generator
and CI remain unchanged. Initial auth proposal was replaced by the coordinator's
approved contract before implementation.

## Observed blockers and trust model

The base API lacked authenticated identity, roles and resource authorization.
X-FaultTrace-Local, Origin and workspace pathname were not credentials. State and
image reads exposed the local run, and startup defaulted to historical data.

Release now validates a backend registry before workflow initialization and
requires an opaque bearer token on every `/api` request. Tokens use 256 random
bits; the registry stores only SHA-256 hashes, principal ID, server role, Unix
expiry, revoked flag, explicit create permission and incident grants. It also
records the administrator-selected Operator per incident. Registry writes use a
process lock/atomic replacement; requests reload identity/grants without restart.
Missing/malformed configuration fails closed. No default credential, cookie,
HTTP token issuance, client role header or URL token is accepted.

Commander requires create permission; creation grants the singleton incident to
its authenticated creator. Concurrent creators cannot both acquire it. All other
incident grants require local administration. New tasks and correction approvals
persist their assignee atomically with insertion, reading trusted registry state
at insertion time, including asynchronous planner output. Operator access requires
both incident grant and matching task assignee. Existing tasks/approvals stay
unassigned; restart preserves recorded assignees. Assign Operator **before**
planning/approving. Later administrator assignment changes affect future records;
no automatic old-task assignment or historical migration is provided.

Commander owns create/start, planning, reopen, approval and clock steps. Operator
owns assigned uploads, reports/refusal, independent observations, photo follow-up
and approved simulated execution. Both can explicitly analyze authorized fixture
or photographic evidence. Existing inference gates, budgets, revisions, duplicate
handling, approval and independent recovery policy still run after authorization.
Untasked legacy `/api/simulation/observe` is denied in release: use assigned task
observations. Commander cannot submit Operator reports or execute correction.

## Exact frontend contract for Worker A

Every API/image request uses same-origin `Authorization: Bearer <opaque-token>`.
X-FaultTrace-Local is unnecessary in release and never replaces authentication.
Existing bodies, revision and idempotency headers remain required.

`GET /api/identity` returns exactly this shape (values vary):

```json
{
  "profile": "release",
  "principal_id": "example-principal",
  "role": "commander",
  "capabilities": {"create_incident": true},
  "incident_ids": ["incident-uuid"]
}
```

Role is commander/operator. Commander create permission may be false; Operator's
is always false. Explicit local mode returns profile local, null principal/role,
false create permission and empty incident_ids; this is not release identity.

- Missing/invalid/expired/revoked identity: 401
  `{"error":"authentication_required"}`.
- Role/resource denial: 403 `{"error":"access_denied"}`, including unknown IDs,
  without disclosing existence.
- Once authorized, existing errors remain, including inference-disabled 403 and
  stale/duplicate 409. Not every 403 means invalid identity.
- Sensitive API/image responses use Cache-Control: no-store. No cookie is issued
  or accepted as identity. Existing mutation Origin checks remain; cross-origin
  forms/cookies grant no authority, and OPTIONS enables no CORS permission.
- State requires the current incident grant. Commander sees that run; Operator
  gets only assigned tasks/evidence and their asynchronous analysis results.
  Operator planning/events are empty. Source-photo/conflict/evidence references
  are filtered. Shared simulated telemetry, assessment and recovery remain
  available for the granted incident; private simulator truth remains excluded.
  An unassigned correction's approval ID is hidden. Other snapshot fields retain
  their existing shape. Direct evidence/image endpoints authorize independently.

Worker A owns masked token entry, memory-only storage, logout and clearing stale
in-memory responses/state when identity changes. Reload requires re-entry. Images
need authenticated fetch and temporary blob URLs, revoked on replacement/logout/
unmount. Never store tokens in browser persistence or infer roles from pathname.
No frontend file was changed; integration and visual checks remain pending.

## Administrator CLI and reproducible startup

Use Python 3.12 and this worktree's new `.venv` with unchanged
`requirements-backend.txt`; verify `python -m pip check`. Dependency installation
was approved explicitly; no manifest changed. From repository root on Windows:

```powershell
.venv\Scripts\python.exe -m faulttrace.workflow.auth_admin --registry .local/auth/registry.json init
.venv\Scripts\python.exe -m faulttrace.workflow.auth_admin --registry .local/auth/registry.json issue --principal commander-review --role commander --hours 4 --create --token-file .local/auth/commander.delivery
.venv\Scripts\python.exe -m faulttrace.workflow.auth_admin --registry .local/auth/registry.json issue --principal operator-review --role operator --hours 4 --token-file .local/auth/operator.delivery
$env:FAULTTRACE_AUTH_REGISTRY = (Resolve-Path .local/auth/registry.json).Path
.venv\Scripts\python.exe tools/start_release.py --port 8830
```

The CLI writes a generated token only to an exclusive private delivery file, never
stdout, argv, receipts or registry. Deliver it privately, then remove the delivery
copy under administrator control. Never paste it into recorded commands/logs/Git
or URLs. CLI paths are restricted to ignored `.local`; new files use mode 0600.
Verify Windows ACLs privately: POSIX mode bits do not establish Windows isolation.
Registry write access is administrative authority.

After creation, use the nonsecret incident UUID:

```powershell
.venv\Scripts\python.exe -m faulttrace.workflow.auth_admin --registry .local/auth/registry.json assign-operator --principal operator-review --incident <incident-uuid>
.venv\Scripts\python.exe -m faulttrace.workflow.auth_admin --registry .local/auth/registry.json grant --principal commander-review --incident <incident-uuid>
.venv\Scripts\python.exe -m faulttrace.workflow.auth_admin --registry .local/auth/registry.json revoke --principal operator-review
```

Grant alone does not assign an Operator. Issue lifetime must be positive and at
most 30 days. Principal names are unique; renewal/rotation requires a new
principal and explicit grants/future assignments. No public admin endpoint exists.

The launcher validates auth, reserves a 127.0.0.1 socket (ports 8830..8839 only),
then creates a unique empty `.local/release-rehearsal/<uuid>/` with separate data
and ledger. The reserved socket passes to uvicorn, avoiding a probe/bind race.
Occupied ports fail without stopping listeners. Inference stays off regardless
of inherited opt-in; access logs are disabled and errors sanitized. No existing
data argument, migration, deletion or frontend server is provided.

Direct workflow.main startup requires explicit FAULTTRACE_PROFILE (local/release)
and FAULTTRACE_DATA_DIR; release additionally requires FAULTTRACE_AUTH_REGISTRY.
It no longer silently selects historical data. The factory's local default keeps
offline harness/test compatibility and rejects nonloopback clients. Prefer the
fresh launcher for rehearsal. No old server was stopped or restarted.

## Verification and deployment limits

Focused synthetic tests cover identity/expiry/revocation, forged roles, create
permission, concurrent creators, no-cookie/Origin boundaries, live grants,
cross-incident/task/image denial, persisted assignees, scoped results, analysis
gates, private attribution, CLI issue/grant/revoke, duplicate planning/reports/
approval/execution, stale reports/approval and a role-separated full recovery
journey with fake transport. Startup tests launch only their own loopback child,
verify 401/200 and inference-off despite inherited opt-in, then stop that child.
Final counts, tested SHA and CI links are in the handoff.

Private access audit records principal, read/mutation category, status and time;
existing workflow events/accounting remain intact. No headers, raw URLs, tokens,
bodies or uploads are logged. Registry and workflow database are separate
durability boundaries: crash/registry-lock failure between creation and creator
grant can leave an inaccessible incident, requiring explicit administrator grant.
Audit failure can likewise return an error after a workflow commit. Use existing
idempotency keys; never assume an error proves no operation occurred.
Such failures are sanitized/no-store; failed denial auditing never permits access
or replaces the identity/resource denial with internal diagnostic details.

TLS, managed identity/secret lifecycle, rate limiting, verified directory ACLs,
retention, backup/restore, multi-instance execution and deployment remain gates.
This is singleton local simulation, not production tenancy or equipment control.
Public use requires separately reviewed TLS/ingress. Frontend integration and
visual/combined acceptance belong to the coordinator. API tests prove no hosting.

## Linux fixture findings

Reproduced in existing Ubuntu WSL with Python 3.12.10 and an isolated official
Pillow 13.0.0 cp312 manylinux wheel. No system Python/package change. Windows
Python 3.12.14/Pillow 13.0.0 also compared; preinstalled Windows Pillow 12.3.0 was
checked separately. Both Windows versions reproduce committed bytes, pixels and
manifest exactly. FreeType reports 2.14.3 on both platforms; Linux zlib is 1.3.1,
Windows 1.3.1.zlib-ng.

Linux PNGs have identical decoded RGB pixels, IHDR/IEND and **decompressed IDAT
bytes**. Only compressed IDAT payload differs: panel-a 6529 versus committed 6489
bytes; panel-b 5398 versus 5375. This reproduction rules out font/raster/filter
differences and isolates PNG mismatch to compression encoding. Exact internal
compressor decisions were not instrumented. Manifest non-hash fields match;
PNG hashes differ and Linux emits LF versus this Windows checkout's CRLF. Git's
index stores LF (`git ls-files --eol`); the newline observation reflects checkout
serialization, not a second established cause of the original Linux CI failure.

Committed SHA-256:

- panel-a: `865db39953a926433d00de7be42eedc07f5795940bc07d78dc5c44d90dd16da6`
- panel-b: `0b787644c7315751357ed5e4bee087810d37d1ed1f976a264cd15505bad4547a`

Sanitized reports: ignored `.local/linux-fixture-report.json` and
`.local/windows-fixture-report.json`. New diagnostic tests compare pixels/filtered
bytes without weakening existing byte equality. [Original failed Linux run](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40398484966):
162 tests, only PNG regeneration failed, zero forbidden attempts; its first
reported IDAT length mismatch matches this reproduction.

No fixture/generator/assertion/dependency/CI correction is claimed. Matching the
Windows compressor on Linux needs a reviewed compatible implementation, or a
coordinator-reviewed canonical encoder plus fixture/manifest migration. Next test:
compare these same filtered bytes with matched zlib-ng builds before proposing
dependencies. Linux byte readiness stays blocked; do not switch CI to claim it.

## Coordinator records and next action

Initial `.local` contained only the ignored brief, with no historical workflow,
uploads or ledger here. No other tree/server/data was opened or copied. All test
identities/data were fresh and synthetic. No providers, cloud resources, spending,
deployment, merge/cherry-pick or Tavily/LangSmith/Toloka work occurred.

Proposed README/state/submission updates: record backend auth/startup checks,
Linux compression/newline findings and final CI link. Keep frontend/session,
visual, TLS/retention/hosting and Linux byte gates unverified; no checkbox implies
combined acceptance. Proposed CI change: none pending Linux review. Next action:
relay this contract to A, integrate sequentially, run combined CI and visually
recheck both roles, images, logout and errors before selecting the release.

## Checkpoint handoff evidence

Implementation and clean local tested SHA:
`a695ef3c15b1b11deb3145621bee5f8878ce5bb5`.
Remote branch was verified at the identical SHA after its scoped push. The later
handoff documentation commit changes no implementation; final SHA/remote/CI
status are reported in the delivery message.

Exact local checks at that clean implementation:

- `.venv/Scripts/python.exe tools/run_offline_tests.py`: 194 passed in 63.454s;
  zero forbidden external network attempts. Output is ignored
  `.local/worker-b-clean-offline.txt` (synthetic tests only).
- `.venv/Scripts/python.exe -m pip check`: no broken requirements.
- `git diff --check` and staged whitespace review: pass; staged credential-pattern
  review found no credentials. All source files remain below 500 lines.
- Separate Linux Python 3.12.10/Pillow 13.0.0 diagnostic: identical pixels and
  decompressed IDAT, differing compressed bytes/hashes/newlines as recorded above.
  This is a confirmed negative portability outcome, not a passing Linux suite.
- Official isolated Linux wheel SHA-256:
  `42d63be3af4f9b951b199b0a9d23365d37ab14687e6d77b74940432c8515c4ca`.

[Implementation CI 40591338759](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40591338759)
failed one new administrator test on the fresh runner: its ignored `.local`
parent did not exist. Other 193 backend tests, dependency checks and frontend
tests/typecheck/build passed; zero forbidden attempts. The test now creates that
parent explicitly; no product or shared test setup changed. See delivery for the
corrected commit/CI outcome; no Linux backend matrix was added.

Owned changed paths:

- `faulttrace/workflow/api.py`
- `faulttrace/workflow/main.py`
- `faulttrace/workflow/storage.py`
- `faulttrace/workflow/access.py`
- `faulttrace/workflow/auth.py`
- `faulttrace/workflow/auth_admin.py`
- `faulttrace/workflow/startup.py`
- `tests/test_auth_release.py`
- `tests/test_access_release.py`
- `tests/test_access_journey.py`
- `tests/test_startup_release.py`
- `tests/test_fixture_portability.py`
- `tools/start_release.py`
- `docs/release-preparation.md`

Latest clean application test SHA:
`e956bd423f8fce453491f8d1f15c2148db2cde4f`: 195 backend tests passed in
53.689s, zero forbidden external attempts, dependency/diff checks passed. This
includes the fresh-checkout setup correction and sanitized audit-failure test.
Its [exact-SHA CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40592354394)
and final documentation-only commit status are reported in the delivery. The
preceding [fresh-checkout correction CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40591960336)
passed. No frontend visual acceptance or Linux byte pass follows from these runs.
