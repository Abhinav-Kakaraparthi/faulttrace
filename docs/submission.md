# Hackathon submission checklist

Event: Nebius x NVIDIA Global AI Hackathon
Deadline: October 30, 2026, 1:00 p.m. America/New_York
Internal submission target: October 29, 2026
Recommended track: Best Apps and Agents

Official sources:
- https://nebiusglobalaihackathon.devpost.com/rules
- https://nebiusglobalaihackathon.devpost.com/details/faqs

Recheck official requirements before final submission.
Check an item only after recording evidence or a verified link.

FT-007 ships offline-tested explicit text planning: bounded public evidence
context, strict observation/escalation policy, durable four-turn reservations,
stale/duplicate rejection and V-08 human reports. FT-007A adds strict schema
requests, fixed precise diagnostics and an accessible disabled-state treatment.
FT-007B adds status-derived HTTP diagnostics without retaining error bodies or
headers; historical fields remain unknown. 78 backend tests, 10 frontend tests
and type/build checks pass offline. The
first live planner request rejected with invalid_proposal (564/1483/2047 known
tokens, recorded once); its discarded output cannot establish the exact cause.
An isolated live request subsequently failed with provider_http_error and missing
usage (attempt 76a24b31-3b2e-4954-9954-dee9749ce7fa, recorded once); historical
HTTP status/cause are unrecoverable. No inference ran in FT-007B coding and no
successful live planner or agent-operated browser review occurred; adaptive reasoning, mobile,
connected unreadable/refusal browser journeys, CI and hosting remain unverified.
No broad submission gate is checked by this checkpoint. Existing FT-006 user
browser evidence below remains attributed to that earlier implementation.

Subsequent user diagnostic 17da531f-147f-4dc6-bf49-19c5580d739f implicated
uniqueItems (HTTP 400, BadRequestError; unknown usage, user reports ledger
recorded). Only that provider schema keyword was removed; application duplicate
rejection remains strict. All 79 backend tests pass. Corrected live compatibility
is pending the reserved single verification call; FT-007 remains PARTIAL and no
submission gate changes. This does not recover an earlier discarded response.

FT-006 current scope: server-backed local incident/task/evidence persistence,
explicit image analysis path, and two-tab polling are implemented and tested
offline with fake transport. SQLite is temporary local architecture, not hosted
PostgreSQL. Connected clear-image submission/interpretation and user-reported
restart persistence are narrowly verified at implementation
4b15365e20ea0b7cacf1ad2d695163bf439690ec, with read-only SQLite/ledger
corroboration. Browser observations belong to the user, not agent automation.
No mobile/broad browser coverage, hosting, diagnosis, authorization, or recovery
is proven.
The two supplied standalone vision successes are recorded in state.md without
reimport/repeat calls. Full product/browser/runtime/deployment/eligibility gates
below remain open beyond the two bounded checks that follow.
See [workflow guide](evidence-workflow.md).

## FT-006 bounded verification evidence

- [x] Connected clear synthetic panel-a upload and actual NVIDIA interpretation: readable 180 kPa; user-performed browser verification, evidence a757eca7-445b-4d0c-b2ae-c70980b3f20d, attempt 1b6b653c-abc9-4ec2-a9be-96d24aba38cc. SQLite/ledger match, recorded once.
- [x] User-reported inference-disabled restart retained identical evidence, attempt, interpretation, and usage in Commander/Operator; no additional recorded analysis/ledger attempt.
- [ ] Connected unreadable/refusal paths verified in the browser.
- [ ] Mobile/accessibility/overflow review completed.

FT-007B read-only known ledger: 1937 input / 2712 output / 4649 total across 7
attempts (5 complete contributors). Separate historical manual record:
155 / 112 / 267. Cross-record known: 2092 / 2824 / 4916 plus TWO failed
requests with unknown consumption. No billing or complete-consumption claim.
Full checklist gates remain unchecked unless their whole claim is verified.

FT-003 standalone synthetic text-probe acceptance is satisfied by corrected
live evidence at implementation c75a50be54ffb53fc728f6be0f14521e7b775bd1.
State.md records the sanitized executable result and separate external
manual evidence. Known cross-record usage is 234 input / 258 output / 492
total tokens, plus one failed request with unknown usage. The local ledger
covers only 79 / 146 / 225 known tokens plus that failed request; it excludes
the manual record, whose timestamp/revision are unavailable. No complete
consumption or cost claim follows. This does not verify application runtime
integration or the full platform claims below; those checkboxes remain open.
No website exists, so browser verification is not applicable to FT-003.

FT-004A prepares synthetic image fixtures and an offline evidence contract.
No authenticated model discovery or real image call has run; NVIDIA
`nvidia/Nemotron-3.5-Super-VL` is only a public-catalog candidate. Vision and
application runtime claims remain unverified. Fixtures were visually inspected,
but this is neither browser verification nor arbitrary analog-gauge accuracy.
See [image-probe guide](vision-probe.md). No submission checkboxes change.

FT-005 adds a local React/Vite interactive demo with sample Commander/Operator
views in one browser tab. It has no backend/provider connection or cross-session
sync. Browser access was unavailable to the agent, so desktop/mobile visual
and accessibility verification is pending; no screenshots were taken.
The checklist items below remain open. Local preview is not deployed hosting,
a completed live application, or independent recovery verification.

## Entry and eligibility

- [ ] Registration and eligibility confirmed.
- [ ] Team members and authorized representative confirmed.
- [ ] Track selected and fit explained.
- [ ] Ownership and third-party asset/dependency permissions checked.
- [ ] Project history assessed; significant updates explained if applicable.

## Required platform and product

- [ ] Actual NVIDIA open-model runtime inference through Nebius verified.
- [ ] Exact model identifiers and runtime integration documented.
- [ ] Commander/operator workflow works across browser sessions.
- [ ] Hidden faults produce evidence-dependent investigations.
- [ ] Uncertain/conflicting evidence and operator refusal handled.
- [ ] Independent verification rejects stale or transient recovery.
- [ ] Restart, duplicate submission, and stale proposal handling checked.
- [ ] Measured evaluation includes scenario count, latency, usage, and cost.
- [ ] Desktop/mobile browser review and relevant accessibility checks pass.
- [ ] Working demo URL verified from a fresh browser session.
- [ ] Judge testing instructions and dedicated access provided if needed.
- [ ] Free judge access maintained through December 15, 2026.
- [ ] Hosting and inference budget covers the judging period.

## Public source and reproducibility

- [x] GitHub repository verified PUBLIC (repository API, October 24, 2026).
- [x] MIT LICENSE present and automatically detected by GitHub (SPDX MIT; repository and license APIs rechecked October 24, 2026).
- [ ] Necessary source and permitted assets included.
- [ ] Clean setup and run instructions verified independently.
- [ ] Configuration examples contain no secrets.
- [ ] Dependencies and supported environment documented.
- [ ] CI passes for the submission revision.
- [ ] Tested release, deployment, and source SHA match.

## Submission materials

- [ ] English description explains audience, problem, and functionality.
- [ ] Actual NVIDIA/Nebius usage and workflow benefits explained.
- [ ] Other services and integrations disclosed accurately.
- [ ] Screenshots reflect the submitted application.
- [ ] Public YouTube video is under three minutes.
- [ ] Video shows actual application behavior and model integration.
- [ ] Video has no unlicensed music or third-party material.
- [ ] Nebius/NVIDIA feedback reflects actual experience.
- [ ] Limitations and measured claims are accurate.
- [ ] Prior-project significant-update explanation included if applicable.
- [ ] Physical AI footage requirement checked if track changes.
- [ ] City award claimed only with qualifying in-person attendance.
- [ ] Tavily bonus claimed only for useful functional runtime integration.

## Final submission

- [ ] Current official rules and FAQ checked for changes/conflicts.
- [ ] Every required form field completed and reviewed.
- [ ] Demo, repository, video, and documentation links tested.
- [ ] Entry submitted before the deadline.
- [ ] Submission confirmation retained.
- [ ] Final release and submission materials preserved.
