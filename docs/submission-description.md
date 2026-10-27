# FaultTrace — DRAFT / NOT SUBMITTED

Trace the cause. Verify the recovery.

Proposed track: Best Apps and Agents. Team: `[ENTRANT/TEAM]`.
Demo/test build: `[JUDGE URL PENDING]`. Video: `[PUBLIC VIDEO URL PENDING]`.
These placeholders are not working links or submission confirmation.

## Audience and problem

FaultTrace is a local investigation prototype for plant operators and incident
commanders. It explores how to connect telemetry, field observations and bounded
AI proposals while keeping a provisional diagnosis separate from maintenance
completion and measured operating recovery. Its current plant and equipment
actions are simulations. It does not control real equipment.
Evidence: [README](../README.md), [architecture](architecture.md).

## What currently works in code and offline tests

Commander and Operator have separate React pages backed by one FastAPI workflow.
Commander starts a simulated incident and explicitly requests an observation plan.
Registered tasks appear for Operator, who can collect a photograph, request its
analysis separately, enter an independent report, or report inability to observe.
Model values never prefill human measurements. Shared references connect task
evidence, planning, deterministic assessment, approval and audit history.
Evidence: [unified investigation](unified-investigation.md), implementation
`b8fc87771c4906f5477dd515ab14407604b6764f`,
`faulttrace/workflow/investigation_evidence.py`, `frontend/src/HumanObservation.tsx`.

Policy checks references, capabilities, revisions, budgets and evidence freshness.
Conflicts, unresolved refusals and incompatible evidence block approval; the
workflow can seek clarification or escalate. Commander approves a specific
eligible revision before Operator acknowledges the simulated replacement.
Maintenance completion does not establish recovery. A deterministic verifier
checks fresh post-action measurements across a sample window, independently of
the model and private simulator outcome. It can reject ineffective correction
or relapse. These are fixture constraints, not plant safety limits.
Evidence: [unified guide](unified-investigation.md),
`faulttrace/workflow/recovery_policy.py`, `tests/test_unified_investigation.py`.

## Actual NVIDIA and Nebius use

The backend integrates NVIDIA models through Nebius Token Factory:
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` for bounded observation planning and
`nvidia/Nemotron-3.5-Super-VL` for image interpretation. Provider responses pass
independent application validation; they grant no authority. Inference is opt-in
and disabled by default. Token Factory provides the hosted model inference;
no AI Cloud deployment or measured development-speed improvement is claimed.
Evidence: [architecture](architecture.md), [workflow guide](evidence-workflow.md),
`faulttrace/workflow/planning.py`, `faulttrace/workflow/photo_analysis.py`.

Recorded live results include standalone text/vision calls and a user-performed
connected clear synthetic-image interaction with audit-corroborated persistence.
One saved-context action-ID verification reported valid human escalation. These
bounded results do not establish useful general diagnosis or an adaptive live
recovery walkthrough. The complete unified journey is proven with offline
provider doubles and simulated telemetry. Demonstrations of those doubles must
display **OFFLINE TEST OUTPUT**. Evidence: [claim matrix](requirements-audit.md),
[state](state.md), [unified guide](unified-investigation.md).

## What the evidence does not establish

A completed real-photo call passed the response contract with
`reasoning_effort=none` but returned **5000 psi**, differing from preliminary
reviewers' **800–850 bar** estimates. Those estimates are not calibrated ground
truth. Numeric accuracy and the cause of the mismatch remain unverified.
A photograph does not establish assigned asset identity; pressure is not
differential pressure, and external handle orientation does not prove internal
valve condition. Model claims, human reports and deterministic assessment stay
distinct. Evidence: [photo evaluation](photographic-analysis.md).

The base records 175 backend and 51 frontend passing checks plus typecheck/build;
[base CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40568257106)
passed. Browser/mobile/keyboard/camera/upload-progress acceptance and the complete
live adaptive journey remain pending. Localhost readiness is not public hosting
or a judge URL; server-enforced identity and access are deployment gates.
SQLite and private local image files support a single local instance.
Evidence: [state](state.md), [architecture](architecture.md).

LangSmith, Tavily and Toloka remain planned or conditional; no integration or
bonus qualification is claimed. Orchestration is custom Python, without
LangChain/LangGraph. Evidence: [partner roadmap](architecture.md#partner-integration-roadmap).

## Entrant completion fields

`[CONFIRM ELIGIBILITY, REPRESENTATIVE AND OWNERSHIP/ASSET RIGHTS PRIVATELY]`.
`[STATE PROJECT ORIGIN; IF PRE-EXISTING, EXPLAIN SIGNIFICANT PERIOD UPDATES]`.
`[VERIFY FREE JUDGE ACCESS AND AVAILABILITY PLAN]`.
Draft platform feedback and remaining requirements: [audit](requirements-audit.md).
No spending, credit redemption, deployment, final acceptance or entry is asserted.
