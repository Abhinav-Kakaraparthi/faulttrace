# Sprint release package — offline Render deployment

**Decision, October 29:** the user approved one **new** `faulttrace-judge-demo`
Starter service and one 1 GiB persistent disk, quoted baseline **$7.25/month before
tax**. Manual deploys only; no other paid resources, upgrades or unrelated service
changes. Published pricing is unchanged. After the preserved HTTP 402 rejection
and explicit billing-readiness confirmation, one follow-up creation succeeded.
Public URL: **https://faulttrace-judge-demo.onrender.com/**. No external-storage
migration has begun. The earlier free-hosting assessment below is historical.

Package originated on `feat/sprint-release`; integrated deployment is
`1206161f139f1c63fb21c67d2fff6e9ecc62e737`, live according to Render and matching
[passing exact-SHA CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40950476913).
Later documentation is separate. Hosted HTTP checks are not browser acceptance.

## Package and data boundary

The multi-stage Dockerfile builds the existing lockfile with Node 22 and the demo
profile, then runs Python 3.12 with the pinned backend specification. It copies
only application code, compiled public assets and synthetic fixtures. No local
database, upload, ledger, delivery file, `.env` or credential enters the image.
No runtime secret is used as a build argument. Image tags are versioned; registry
digests should be recorded when the actual approved build is produced.

`tools/start_public_demo.py` requires an HTTPS origin, an absolute private data
root, explicit persistent-storage confirmation and one worker. Access logs and
proxy-header trust are disabled. In the container it changes only the mounted
directory owner and drops to UID/GID 10001 before application startup; existing
files are not recursively changed. The app preserves secure sessions and exact
Origin/CSRF rules. `/commander`, `/operator`, root and immutable build assets are
served by the same process/origin as `/api`; unknown/private paths return 404.
HTML has CSP/frame/permissions headers and no-store. `/healthz` reveals only `ok`.

Mount `/var/lib/faulttrace`; use `/var/lib/faulttrace/judge` for the entire demo
root. Preserve sessions, per-run workflow databases/images/ledgers and any global
reservation/accounting database inside that mount. Container code/build remains
read-only in normal operation. No multi-worker/replicated SQLite claim is made.
Disk snapshot/restore, resource load and the actual platform mount must still be
verified after approval. Existing local runs are never copied into the deployment.

Local package commands (developer only; judges need only the public URL):

```powershell
$revision = git rev-parse HEAD
docker build --build-arg "FAULTTRACE_BUILD_REVISION=$revision" --tag "faulttrace:$revision" .
# After approval, runtime env/private secrets are configured server-side.
# FAULTTRACE_DEMO_ORIGIN=https://<approved-host>
# FAULTTRACE_DEMO_ROOT=/var/lib/faulttrace/judge
# FAULTTRACE_PERSISTENT_STORAGE_CONFIRMED=1
# FAULTTRACE_DEMO_LIVE=0 and FAULTTRACE_ALLOW_INFERENCE=0 for offline review.
```

The wrapper factory also permits the existing explicitly opted-in loopback HTTP
mode for isolated tests; the public launcher refuses that exception. Live mode,
if enabled by later coordinator integration, must use its global/session spending
reservations and server-only keys. This release branch does not enable live calls.

## Fixture portability correction

The old Windows/Linux generation discrepancy was PNG compression bytes, with
identical decoded pixels/filter bytes. Canonical fixture encoding now uses fixed
row filters plus a small deterministic fixed-Huffman/LZ77 DEFLATE implementation;
it never depends on a platform compressor. Existing 64 KiB fixture and upload
bounds are unchanged. Exact historical files/manifest remain in
`fixtures/image-evidence/legacy/`; tests pin their old hashes and prove canonical
pixels match. Historical local uploads, provenance and receipts are not rewritten.
Strict current PNG/manifest regeneration byte equality remains enforced.

Both Windows and Ubuntu backend CI now run the full guarded suite, preserving
assertions. Local Docker daemon is unavailable. Existing Ubuntu WSL Python is
3.10 with no pip/backend dependencies; no tool/dependency installation was made
there. Actual Ubuntu/Windows CI and Docker build/restart smoke now pass, including
the integrated implementation `26521a7`; [exact CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40775523968).
The smoke runs with a fresh volume, read-only root/tmpfs and UID10001, verifies
Secure-cookie/role/image/CSRF controls and exact post-upload records/images after
restart. It is a loopback HTTP harness with HTTPS Host/Origin, not actual TLS,
browser or Render acceptance. No provider keys/requests/ledger were present.

## Actual approved hosting configuration

Created: **new** Render web service `faulttrace-judge-demo`, Docker runtime,
Oregon, one `0.5c-512mb` instance (approved Starter capacity), one 1 GiB disk mounted
`/var/lib/faulttrace`, manual deploys/previews off, Starter build pipeline. API
discovery confirmed the name unused before creation and exactly one added service
afterward; all four prior service IDs remain. The build and actual HTTPS origin
match the reviewed revision/assigned URL. No custom domain, managed database,
extra service, plan upgrade or unrelated Render change was made.

Public official pricing rechecked October 29, 2026: Starter compute **$7/month** and disk
**$0.25/GB/month**, baseline **$7.25/month**, prorated under Render's billing terms,
before tax, excess bandwidth or provider charges. Starter is 512 MiB; memory/load
capacity is not yet established. Free compute cannot attach durable disks, so it
does not meet this workflow's persistence requirement. Disk-backed deploys can
interrupt availability and cannot scale to multiple instances. The user has
approved this exact paid service/disk creation and privately completed billing.
The API confirms the configured capacity/disk, not an accrued invoice amount.

Initial environment explicitly sets `FAULTTRACE_DEMO_LIVE=0`,
`FAULTTRACE_ALLOW_INFERENCE=0`, `FAULTTRACE_TAVILY_ENABLED=0` and
`FAULTTRACE_LANGSMITH_TRACING=0`. Do not attach provider keys or inherited secret
groups for this offline acceptance deployment. No existing service is restarted.

Private access: sign in at `https://dashboard.render.com`, avatar → Account
Settings → API Keys. Save a key privately as the Windows user environment variable
`RENDER_API_KEY`; never send it in chat or commit it. The user completed the required
payment step privately. Neither that key nor provider keys were put on the service.
Hosted TLS/routes, both roles, isolation, Origin/CSRF, image access and upload
boundaries pass HTTP checks. Desktop/mobile/keyboard/camera acceptance is not claimed.

One restart changed only the new service's instance. Held sessions, the incident,
task, evidence/planning records and exact stored image survived; visitor isolation
remained enforced. The deployed revision remains `1206161`. The user confirmed
private-shell creation of a synthetic spending reservation before restart and its
unchanged=true/count=1 after-restart comparison. Attribute remote SQL verification
to the user; agent HTTP checks separately verified session/state/image persistence.
The 67,584 conservative admission units are synthetic test allowances, not actual
provider tokens or billing. No provider contact, ledger import or allowance reset.
No test endpoint or temporary public inference enablement is permitted to
manufacture that check. Actual browser
acceptance remains separate from HTTP/security checks.

Set non-secret `FAULTTRACE_BUILD_REVISION` to the exact selected 40-character SHA
for the build and runtime; Render exposes configured environment values as Docker
build arguments, and this Dockerfile declares only that non-secret argument.
The image build fails if it is missing/malformed. Runtime receipts can use this
validated revision when `.git` is intentionally absent. Record the resulting
image digest against that SHA; never pass keys as build arguments.

Official sources:
[pricing](https://render.com/pricing),
[persistent disks and limitations](https://render.com/docs/disks),
[Docker builds and secret handling](https://render.com/docs/docker),
[Blueprint fields](https://render.com/docs/blueprint-spec),
[free-service limitations](https://render.com/docs/free).

## Concrete free alternative — assessment only, October 28

Candidate: one Render Free Docker web service plus one Supabase Free project.
Postgres would be authoritative for investigations/tasks/evidence, sessions,
approvals, recovery schedules, receipt outbox and **global/session reservations**.
A private Storage bucket would hold metadata-stripped images, fetched only after
the API's visitor/asset authorization. No public bucket, browser service key or
ephemeral spending-record fallback is acceptable.

Render currently supplies 750 free instance hours per workspace/month, sleeps
idle services after 15 minutes and has approximately minute-long cold starts.
Local writes disappear on restart/spin-down; no free persistent disk. Free Render
Postgres expires after 30 days, before December 15 if created now, so it is not
this candidate's datastore. Free services also face shared bandwidth/build and
service-initiated-traffic limits. Existing account usage is unknown.
[Official free compute limits](https://render.com/docs/free).

Supabase Free currently includes 500 MB database, 1 GB file storage, 5 GB egress
plus 5 GB cached egress, and at most two active free projects. Available project
slots/quotas in the user's account are unverified. Its low-activity pause policy
can interrupt access after a week; data retention is not continuous availability.
There is no verified commitment of uninterrupted free access through December 15.
[Pricing](https://supabase.com/pricing),
[current pause policy](https://supabase.com/docs/guides/platform/free-project-pausing).
Free backups need an explicit export/restore plan; database dumps do not include
the image objects. [Backup scope](https://supabase.com/docs/guides/platform/backups).

| Required change | Free compute + external storage | Prepared Starter + disk |
| --- | --- | --- |
| Workflow database | Replace SQLite-specific transactions, rowid/JSON queries, triggers/UDFs and per-file run isolation with explicitly scoped Postgres transactions | Existing checked-in implementation preserved |
| Sessions/budgets/receipts | Remote authoritative atomic reservations, idempotency and outbox; fail closed when database is unavailable, including across restarts | Existing persistent SQLite/ledger implementation tested in Docker |
| Images | Private object adapter, bounded authenticated proxy and crash/orphan handling | Existing private filesystem/image checks tested |
| Startup/availability | Cold-start UX, connection pool, paused-project/quotas and genuine availability monitoring | No free idle spin-down; actual hosted setup still unverified |
| Delivery risk | New cross-cutting storage checkpoint and repeat full policy/security/concurrency/restart acceptance; not an environment-only change | Lower code-change risk; this exact compute/disk scope is now approved, private access pending |

The paid baseline remains $7/month compute + $0.25/month for 1 GB disk before
tax/bandwidth/providers. [Current pricing](https://render.com/pricing).
Both alternatives need hosted HTTPS/role/image checks and founder review. A free
hosting quota does not pay for NVIDIA/Tavily or establish credited balance.

If zero-cost remains mandatory, the next bounded implementation decision is a
new-run-only Postgres/private-object storage proof, preserving all local histories,
then failure-injection/concurrency/isolation/restart tests before public inference.
Do not upload a SQLite file periodically and call it durable global accounting:
an ephemeral crash could lose reservations and reopen spending allowance.
Use the existing [Supabase connection modes](https://supabase.com/docs/guides/database/connecting-to-postgres)
and [private bucket controls](https://supabase.com/docs/guides/storage/buckets/fundamentals)
as implementation references. No new accounts, free resources or data transfers
were created by this assessment, and no database dependency was installed.

After approval: deploy exact integrated SHA, confirm health/HTTPS, cookie flags,
both routes, protected images and independent visitors; create a synthetic run,
restart once and confirm the same state, session and accounting persist without
provider replay. Then perform founder desktop/mobile acceptance. No hosting,
restart persistence on Render, live accuracy or final submission gate is closed
by this package alone.
