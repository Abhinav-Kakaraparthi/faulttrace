# Requirements audit — DRAFT / NOT SUBMITTED

Worker C, 2026-10-27 (America/New_York). Scope: committed base
`f2da0085a99061fe00f29ba91e5ba92b36d475fa`, branch `docs/finish-submission`.
No A/B branch behavior is included. Shared status and tracker are coordinator-only.

## Primary-source audit

Read-only access on 2026-10-27:

- [R: Official rules](https://nebiusglobalaihackathon.devpost.com/rules), sections 1, 3, 4, 6, 8 and 11.
- [F: Official FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs).
- [O: Official overview](https://nebiusglobalaihackathon.devpost.com/), Requirements.

Deadline verified: October 30, 2026, **1:00 p.m. America/New_York**
(10:00 a.m. Pacific / 17:00 UTC). Judging ends December 15 at 3:00 p.m.
New York time. R controls conflicts; recheck before entry. O says video may be
three minutes; R says less than three. Use the stricter limit.

| Requirement | Evidence / source | Status and missing decision |
| --- | --- | --- |
| Registration, eligibility, representative | R §§3–4; [tracker](submission.md) | Pending private entrant confirmation |
| NVIDIA runtime on Nebius | R §4; F; claim matrix below | Narrow calls verified; full product acceptance pending |
| Track | O; [description](submission-description.md) | Best Apps and Agents proposed; selection pending |
| Working demo/test-build URL | O; localhost records in [state](state.md) | Blocked: no judge URL verified |
| English description | R §4; owned drafts | Drafted; entrant review pending |
| Public licensed source and setup | O; MIT [license](../LICENSE), README; tracker API check dated October 24 | Historically verified public/MIT; current release reproduction pending |
| Public YouTube video, under three minutes | R §4; [script](demo-script.md) | Pending recording, permission review and link |
| Free judge access through judging end; private access instructions | R §4 | Pending access, budget and availability plan |
| Ownership, integration/asset rights | R §4; license and [photo guidance](photo-evidence.md) | Pending entrant/dependency/media review |
| Prior-project significant changes, if applicable | O; Git history | Pending history declaration |
| Platform/model feedback | O; draft feedback below | Drafted; entrant review pending |
| Tavily bonus; city award | R §8; F | No runtime Tavily; attendance unknown; no qualification claimed |
| Form completion and receipt | R §4; tracker | Pending; no entry sent |

FAQ clarification: app hosting outside Nebius is allowed with qualifying NVIDIA
Token Factory inference. Provisioning restrictions differ from entrant eligibility;
credits are not assumed. No country, identity, offer redemption or account state
was inferred. Physical AI's additional footage condition requires reassessment
only if the selected track changes (O).

## Claim → committed evidence matrix

“Verified” below is bounded by the evidence column; it is not final acceptance.
Private artifacts were not accessed/copied in this checkpoint.

| Claim | Evidence / commit / source | Classification and limit |
| --- | --- | --- |
| React/Vite, FastAPI, SQLite and private local images | [architecture](architecture.md); `frontend/package.json`, `faulttrace/workflow/storage.py`, `uploads.py` at base | Implemented locally; no public hosting/auth |
| Explicit NVIDIA/Nebius text and vision runtime | [state](state.md), [README](../README.md); probe `c75a50be54ffb53fc728f6be0f14521e7b775bd1`; workflow `4b15365e20ea0b7cacf1ad2d695163bf439690ec` | Recorded live evidence; connected clear fixture/restart browser observations are user-reported and audit-corroborated |
| Action-ID selection | [state](state.md), standalone verification at `c4eb08d` | User-reported validated escalation for one saved context; no task/browser acceptance or general reasoning proof |
| Real-photo observation contract | [photo evaluation](photographic-analysis.md), tested `5e41726b2d190eb4087d2cc5c0c31547bcebc0f1` | User-run, audited contract pass with `reasoning_effort=none`; 2610 ms, 1678/120/1798 tokens; reading 5000 psi disagreed with preliminary 800–850 bar estimates. Estimates are not calibrated truth; accuracy/cause unverified |
| Unified task → human evidence → approval → recovery | [unified guide](unified-investigation.md); implementation `b8fc87771c4906f5477dd515ab14407604b6764f`; [CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40534982605) | Offline doubles and simulated telemetry; not live adaptive end-to-end proof |
| Independent verifier rejects ineffective correction/relapse | `faulttrace/workflow/recovery_policy.py`; `tests/test_workflow_recovery.py`, `tests/test_unified_investigation.py` | Implemented/offline tested; fixture thresholds are not industrial limits |
| Current base checks | [base CI](https://github.com/Abhinav-Kakaraparthi/faulttrace/actions/runs/40568257106), exact base SHA above; [state](state.md) | Hosted success checked this session; recorded 175 backend/51 frontend, type/build. Reused for docs-only change; no browser claim |
| Desktop/mobile/keyboard/camera/upload progress | [state](state.md), [unified guide](unified-investigation.md) | Pending; HTTP readiness/build/static tests do not close these gates |
| Seeded review freshness | [state](state.md) | Controlled fixture clocks; not real freshness validation |
| LangSmith, Tavily, Toloka | [roadmap](architecture.md#partner-integration-roadmap) | Planned/conditional; LangChain/LangGraph absent from dependencies |
| Deployment, production roles, public API operations | [architecture](architecture.md) | Pending; B's unintegrated work is excluded |

Main failure mode: treating an implemented path, valid response contract, user
report or offline scripted success as a verified live product or accurate reading.
Keep diagnosis, maintenance completion and operating recovery distinct everywhere.

## Draft feedback and unresolved inputs

Token Factory supplied actual NVIDIA text/vision responses through the bounded
transport. Earlier structured-output attempts were rejected; later compatibility
checks were narrow. A completed photo response passed validation yet disagreed
with preliminary reviewers. This motivates separate contract, numeric-agreement
and abstention evaluation, rather than claiming general model accuracy.
See [photographic analysis](photographic-analysis.md) and [state](state.md).
No AI Cloud deployment experience is claimed.

Missing private inputs: `[ENTRANT/TEAM]`, `[AUTHORIZED REPRESENTATIVE]`, eligibility
confirmation, ownership/permissions attestation, project-origin declaration,
`[JUDGE DEMO/TEST BUILD URL]`, dedicated access instructions, budget/availability
commitment, `[PUBLIC VIDEO URL]`, and form/receipt review. Never place credentials
in these public drafts. Known usage is incomplete consumption, not billing.

## Coordinator handoff proposals (do not apply automatically)

- `docs/state.md`: record four draft paths and exact final Worker C SHA/CI result;
  retain visual/live/hosting blockers. Next action: sequential integration and
  full CI plus visual rechecking on the combined revision.
- `docs/submission.md`: record official-source check date/deadline and draft links.
  Keep recording, source/asset review, release CI, judge access and submission
  unchecked until their entire claims are verified. Resolve historical statements
  (for example FT-004A's pre-call status) as history, not current capability.
- Worker A overlap: coordinator should reconcile screenshots, browser journeys,
  camera, keyboard and responsive results only after integration; none is claimed here.
- Worker B overlap: coordinator should replace release/auth/startup statements
  only after direct-API authorization tests and clean setup verification integrate.
  No changes to A/B files requested by this worker.

Validation: official links fetched successfully; relative draft links and claim
consistency reviewed; scoped diff/secret checks reported in the final handoff.
No product edits, provider calls, account creation, external messages, deployment,
recording or submission occurred. No shared records edited.
