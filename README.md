# FaultTrace

**Trace the cause. Verify the recovery.**

FaultTrace is a planned investigation assistant for plant operators:
combine telemetry, field observations, and adaptive AI-guided tasks to
investigate equipment anomalies.

## Status

Documentation foundation only. Application code, live inference,
simulation, browser verification, CI, and hosting are not implemented.

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

Executable setup and run instructions will accompany application code.
