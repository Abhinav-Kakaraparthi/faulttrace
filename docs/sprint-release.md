# Sprint release package — approval required before hosting

Prepared from `f1d7434eee50660cb0bfac15f6483d94c0fa960c` on
`feat/sprint-release`; final integrated SHA must be selected after coordinator
integration and CI. This is a deployable package, not a deployment or visual pass.

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
there. Actual Linux acceptance must come from the new Ubuntu CI, not a Windows
build or an unexecuted Dockerfile. Container build remains separately unverified.

## Exact hosting proposal (not executed)

Candidate: **new** Render web service `faulttrace-judge-demo`, Docker runtime,
Oregon, one Starter instance, one 1 GiB disk mounted `/var/lib/faulttrace`, manual
deploys only. `render.yaml` is an approval-required proposal; applying a same-name
Blueprint can modify a service, so first verify that this is a new unused name.
Select the reviewed integrated commit explicitly, not stale `main` or an arbitrary
latest branch revision. Configure the actual HTTPS origin privately. No custom
domain, managed database, extra service or unrelated Render change is proposed.

Pricing checked October 28, 2026: Starter compute **$7/month** and disk
**$0.25/GB/month**, baseline **$7.25/month**, prorated under Render's billing terms,
before tax, excess bandwidth or provider charges. Starter is 512 MiB; memory/load
capacity is not yet established. Free compute cannot attach durable disks, so it
does not meet this workflow's persistence requirement. Disk-backed deploys can
interrupt availability and cannot scale to multiple instances. The user must
approve this exact paid service/disk creation before it is provisioned; no billing
details, accounts, infrastructure or public URL were created here.

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

After approval: deploy exact integrated SHA, confirm health/HTTPS, cookie flags,
both routes, protected images and independent visitors; create a synthetic run,
restart once and confirm the same state, session and accounting persist without
provider replay. Then perform founder desktop/mobile acceptance. No hosting,
restart persistence on Render, live accuracy or final submission gate is closed
by this package alone.
