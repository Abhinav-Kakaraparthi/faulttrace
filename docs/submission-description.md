# FaultTrace submission copy - draft, not submitted

Public demo: **https://faulttrace-judge-demo.onrender.com/**
Deployed revision: **1206161f139f1c63fb21c67d2fff6e9ecc62e737**
Video: **[FOUNDER: final reviewed video URL, under three minutes]**
Repository: https://github.com/Abhinav-Kakaraparthi/faulttrace

Render reports this exact passing-CI revision live on the approved single compute
instance and 1 GiB disk. HTTPS routes, role/session isolation and upload boundaries
passed HTTP checks, including same-session/state/image persistence across restart.
The user verified synthetic reservation persistence via private Shell read-back;
founder browser review remains pending. No external calls are enabled.
Do not publish or finalize Devpost
from this draft.

## Short description

FaultTrace is an AI-assisted investigation workspace that turns equipment anomalies
into bounded observation tasks, preserves field evidence and human judgment, and
verifies simulated recovery from independent telemetry.

## Inspiration

Industrial investigations often scatter observations across dashboards, messages
and maintenance notes. Teams can mistake a plausible explanation for a diagnosis,
or a completed action for recovered operation. We built FaultTrace around the
evidence chain between those decisions: what was observed, who reported it, what
remains uncertain, and which measurements establish recovery.

## What it does

Commander and Operator are distinct views of the same server-backed investigation.
Commander reviews simulated telemetry, process equipment, competing explanations
and evidence gaps. A validated NVIDIA proposal can create a bounded observation
task. Operator can upload a photograph, provide an independent structured report,
or report unreadability, wrong equipment or inability to access it.

Photographic interpretations stay separate from human reports. An assigned asset
does not prove the image's identity, ordinary pressure is not differential pressure,
and a valve handle's orientation is not proof of internal valve condition. Conflicts,
staleness and incompatible evidence remain visible rather than silently satisfying
the simulated correction policy.

Only compatible evidence permits an explicitly approved, registered simulated
correction. Operator completion records maintenance progress; it cannot declare
recovery. A deterministic verifier checks fresh post-action samples against
declared recovery bands, an observation window and alarm conditions. The journey
also handles ineffective correction and relapse.

The judge demo intentionally lets one visitor switch between both workspaces
without account creation or copied tokens. This is a demonstration privilege,
not a claim of production separation between two employees. Equipment, telemetry
and correction are explicitly simulated. The initial hosted preview must keep
inference and external partner calls disabled; offline templates are not NVIDIA
output, and previously recorded service evidence must be labeled separately.

## How we built it

The frontend uses React, TypeScript and Vite. Both routes consume one FastAPI
workflow with SQLite investigation records, private evidence files, revision checks,
idempotent operations and durable request reservations. Orchestration is custom
Python; LangChain and LangGraph are not dependencies. A private simulator supplies
public measurements while keeping hidden faults and answer keys out of investigator
and model context.

NVIDIA text and vision inference runs through Nebius Token Factory:
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` for bounded observation planning and
`nvidia/Nemotron-3.5-Super-VL` for photographic interpretation. Strict application
validation remains independent of model output. Provider requests are explicit,
bounded and accounted for; rejection, interruption or unknown usage cannot silently
refund a planning turn or trigger a retry.

Tavily provides restricted official-manufacturer reference lookup. Retrieved text
is untrusted reference context, outside measurement and correction authority.
LangSmith receives an allowlisted metadata projection rather than private images,
prompts, credentials or raw reasoning. The prepared Docker package serves the
frontend and API from one origin and places sessions, investigations, images and
spending records under a persistent mount. Hosted behavior must be verified on
the actual deployed revision before it is described as accepted.

## What we verified

- Real NVIDIA calls exercised the integrated production application paths for
  planning and photographic output contracts. In a saved run, the first proposal
  created an observation task and the second result escalated to a human. This is
  narrow evidence, not general planning reliability or a live browser-driven
  diagnosis-to-recovery success.
- A separately authorized Tavily call returned three results and retained all
  three for one reported credit. The WIKA A-10 product page is a useful exact-model
  reference example. The S-20 and PSD-4 documents concern other models and are not
  applicable A-10 instructions. None identifies the MAXIMATOR photo or F-17.
- Three existing LangSmith records were remotely readable with matching receipt
  fingerprints. The founder confirmed the photo trace and its attributes in
  browser screenshots; this is separate from automated checks.
- The founder previously completed the simulated recovery journey in both views.
  Offline integration tests cover rejection, stale evidence/approval, disputes,
  duplicate operations, persistence, ineffective correction and relapse. Provider
  doubles are labeled offline tests, not live AI behavior.
- The latest recorded guarded backend suite passed 314 tests with zero forbidden
  external network attempts. Exact-SHA CI and any new hosted checks belong in the
  coordinator's current release evidence; static tests are not browser acceptance.

## Challenges and limitations

The main design challenge was preserving the distinction between an AI suggestion,
a human observation, authorization and independently verified outcome. A completed
JSON contract is not proof of a correct measurement. One real-photo evaluation
returned 5000 psi, conflicting with preliminary reviewer estimates of 800-850 bar.
Those estimates are not calibrated ground truth, and photographic numeric accuracy
remains unverified. We retain that limitation rather than tuning a demonstration
to one answer.

FaultTrace currently demonstrates one bounded simulated restriction scenario.
There are no real equipment-control connections, verified industrial diagnosis or
production-readiness claims. The complete browser-driven live AI recovery journey,
broader image evaluation, hosting security/persistence acceptance and operational
capacity remain separate gates. Existing provider authorizations are spent; no new
inference or search is needed to manufacture a more convenient video result.

## What's next

Complete hosted HTTPS, session/isolation, protected-image, upload-limit and restart
persistence acceptance with all external calls disabled. Then record the truthful
under-three-minute demo using existing provider evidence and a separately labeled
offline simulated recovery. Broader independently labeled photo evaluation and
carefully budgeted live walkthroughs would need separate approval. Public inference
must never run with ephemeral spending-limit records.

## Coordinator handoff before submission

- Insert only the verified public URL and deployed SHA; record the actual hosted
  checks, billing configuration and remaining limitations in shared status files.
- Confirm rights for every public image/clip. The provided MAXIMATOR photograph
  has no automatically established public reuse permission.
- Confirm the final video is under three minutes and labels recorded real service
  results, simulations and offline doubles. Do not imply one connected live success.
- Recheck the official submission gates, repository visibility/license, final link
  accessibility and exact-SHA CI. No account/offer eligibility or bonus acceptance
  is established merely by naming an integration.
- Publish the video and finalize Devpost only after the user's separate instruction.
