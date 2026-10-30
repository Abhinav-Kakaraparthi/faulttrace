# FaultTrace submission copy - draft, not submitted

Public demo: **https://faulttrace-judge-demo.onrender.com/**
Current deployed application: **359aa808efc4fd2565d9df680a41990ceb81b62f**
Video: **[FOUNDER: reviewed final video URL, under three minutes]**
Repository: https://github.com/Abhinav-Kakaraparthi/faulttrace

The founder's current live incident `9f470d1b-53c5-4ddc-8cfe-8f323bceff10`
contains reported real NVIDIA V-08 planning, a scripted simulated intermediate
report, real F-17 replanning citing that report, and real fixture analysis returning
180 kPa. Its unknown-identity review correctly remains blocked. It was not retried,
reidentified or converted into a successful recovery.

Separately, actual Chromium drove the complete connected application through an
isolated local backend/SQLite with labeled provider doubles and scripted synthetic
human evidence: upload, analysis, review, cited next task, human approval, Operator
completion, independent monitoring and sample-derived recovery. Both views retained
the result after reload. This demonstrates application transitions, not live AI
reasoning/accuracy or one completed hosted live recovery journey. See
[connected evidence](unified-investigation.md) and [2:50 video script](final-video-revision-plan.md).

HTTPS/session/isolation/upload/restart hosting evidence remains valid. This
checkpoint made zero provider/search/export calls, used no new spending and did
not change the hosted incident or limits. Do not publish or finalize Devpost from
this draft. Camera hardware, arbitrary-photo accuracy and full live recovery remain
open. MAXIMATOR public-image rights and calibrated numeric ground truth are not
established. The real-photo 5000 psi output failed preliminary reviewer comparison;
reviewer estimates were not calibrated ground truth.

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
and correction are explicitly simulated. Hosted inference and partners are explicit
and durably budgeted; offline templates are not NVIDIA output, and recorded service
evidence must be labeled separately.

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
  planning and image-output contracts. Earlier saved runs include human escalation;
  the current founder-reported run instead selected V-08 then F-17, citing the
  simulated human report, and extracted 180 kPa from the synthetic fixture. Unknown
  identity still blocks approval. This is narrow evidence, not general planning
  reliability or a complete live recovery success.
- A separately authorized Tavily call returned three results and retained all
  three for one reported credit. The WIKA A-10 product page is a useful exact-model
  reference example. The S-20 and PSD-4 documents concern other models and are not
  applicable A-10 instructions. None identifies the MAXIMATOR photo or F-17.
- Three existing LangSmith records were remotely readable with matching receipt
  fingerprints. The founder confirmed the photo trace and its attributes in
  browser screenshots; this is separate from automated checks.
- Chromium now completed a separate connected journey through real local API and
  SQLite, using labeled provider doubles and synthetic human inputs, with upload,
  analysis, review, cited replanning, approval, completion, monitoring, recovery
  and desktop/mobile persistence screenshots/recording. No provider call occurred.
  The founder also previously completed the simulated recovery journey in both views.
  Offline integration tests cover rejection, stale evidence/approval, disputes,
  duplicate operations, persistence, ineffective correction and relapse. Provider
  doubles are labeled offline tests, not live AI behavior.
- Guarded backend, frontend/build, combined-contract and exact-SHA CI evidence is
  recorded in state.md. Actual browser evidence is separate from static assertions.

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
broader image evaluation, hosted live-journey acceptance and operational
capacity remain separate gates. Existing provider authorizations are spent; no new
inference or search is needed to manufacture a more convenient video result.

## What's next

Record the truthful under-three-minute demo using the existing founder-operated
live evidence and the separately labeled completed offline browser recording.
Review the final edit and publish only with founder approval. Broader photo evaluation and
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
