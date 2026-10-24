# FaultTrace

**Trace the cause. Verify the recovery.**

FaultTrace is a planned investigation assistant for plant operators:
combine telemetry, field observations, and adaptive AI-guided tasks to
investigate equipment anomalies.

## Status

Standalone synthetic Nebius text probe and offline validation tests exist.
Application runtime integration, simulation, CI, and hosting are not implemented.
There is no website yet; browser testing is not applicable to FT-003.

## Planned workflow

Anomaly -> investigation -> operator task -> evidence -> revised plan ->
permitted simulated action -> independent recovery verification.

NVIDIA models through Nebius will propose investigation steps.
Application policy will authorize permitted simulated actions.
Deterministic code will verify recovery independently of the model.
Temporary recovery will remain distinct from completed repair.

Initial demonstration: a simulated plant with commander and operator
workspaces, hidden fault scenarios, evidence clarification, and refusal.

## Proposed architecture

React/TypeScript frontend; Python/FastAPI API and worker; PostgreSQL;
private evidence storage; isolated simulator; Nebius model inference.

These are proposed choices, not implemented capabilities.
Provider capabilities must be verified before selecting model identifiers.

## Development and submission

- Public source repository; MIT license.
- Never commit credentials or private field evidence.
- [Submission checklist](docs/submission.md)
- [Checkpoint state](docs/state.md)
- [Engineering instructions](AGENTS.md)

## FT-003 provider probe

Requires Python 3.12 (verified: 3.12.14), Git, and no third-party dependencies.
From the repository root in PowerShell, select the available interpreter:

```powershell
$py = 'C:\Users\surya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py --version
& $py -m unittest discover -s tests -v
```

On other machines, set `$py` to your Python 3.12 executable. No installation
or package setup is needed. Offline tests never call Nebius.

To run exactly one live synthetic request, provision `NEBIUS_API_KEY` in the
process environment through your secret manager (never paste it into source
or a recorded command). Then run:

```powershell
& $py -m faulttrace.probe --live
```

Without `--live`, the command refuses inference. Missing credentials produce
a sanitized JSON error. Exit codes: 0 validated, 1 failed, 2 no live opt-in.
The JSON receipt reports source HEAD, latency and usage; missing usage is null.
Run from a clean committed checkout so HEAD identifies the tested source.
The endpoint is `https://api.tokenfactory.nebius.com/v1` and the exact model is
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

Every probe invocation gets an attempt ID and records a sanitized receipt in
the gitignored `.local/nebius-usage.json` ledger (including failures and runs
without live opt-in). Inspect or import receipts without contacting a provider:

```powershell
& $py -m faulttrace.probe --ledger-summary
& $py -m faulttrace.probe --import-receipt 'C:\path\to\sanitized-receipt.json'
```

Use `--ledger 'C:\path\to\usage.json'` to select another local file. Reimporting
the same receipt is idempotent; conflicting attempt IDs fail. Legacy receipts
get a stable import ID and unknown usage. Partial sums are not total consumption
or billing. See the founder guide for accounting and persistence limitations.
FT-003 standalone text-probe acceptance is satisfied by corrected live
evidence against `c75a50be54ffb53fc728f6be0f14521e7b775bd1`: validation passed,
1609 ms, 79 input / 146 output / 225 total tokens. The local ledger also
retains one failed attempt with unknown usage. A separate historical manual
success used 155 / 112 / 267 tokens, giving cross-record known sums of
234 / 258 / 492. These sums are incomplete consumption, not billing.
The manual record lacks an exact timestamp and source revision and remains
outside the ledger. See state.md for provenance and the sanitized live receipt.
Application integration and all other unverified product gates remain open.

See [founder guide](docs/founder-guide.md) for limits and trust boundaries,
and [checkpoint state](docs/state.md) for separate historical and executable evidence.
