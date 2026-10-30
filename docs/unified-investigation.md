# Shared investigation-to-recovery demonstration

Both routes consume one persisted incident/task/evidence/recovery stream.
NVIDIA proposes an observation; deterministic policy validates it and creates the
registered task. Independent human evidence, not model claims alone, supports a
registered simulated correction. Completion and recovery remain separate.

## Transition acceptance

| Transition | Current evidence |
| --- | --- |
| Incident - validated proposal - assigned Operator task | Real hosted V-08 then F-17 results reported by founder; offline browser/API journey passed |
| Upload - explicit structured analysis | Founder used fixture analysis; isolated browser used the production photographic route with a scripted double |
| Image claim - independent human review | Blank identity/type/value/unit fields exercised; model claim alone blocked approval |
| Human evidence - next decision | Second offline proposal cited the canonical human-report reference; founder reports real second proposal cited V-08 report |
| Complete compatible evidence - approval | Browser explicitly checked current-revision consent; no approval before F-17 and V-08 evidence |
| Approval - Operator acknowledgment | Browser exercised actual assignment/completion route; recovery still unverified immediately afterward |
| Monitoring - independent recovery | Browser explicitly started persisted monitoring; >=5 samples / >=40 simulated seconds established recovery |
| Persistence and shared views | Actual SQLite records, explicit-local API, both tabs and reload checks; complete screenshot/recording evidence retained |

## Live result - preserve the unresolved branch

Founder-reported incident `9f470d1b-53c5-4ddc-8cfe-8f323bceff10` contains real
NVIDIA V-08 selection, a scripted simulated intermediate report, real F-17
selection citing that report, and real fixture analysis of synthetic panel-a
returning 180 kPa. Review recorded unknown identity with differential pressure.
`observed_identity_unresolved` / `photo_claim_unresolved` correctly block approval.
No agent inference/replay or hosted record change was made for this checkpoint.
This is not a completed live recovery journey or arbitrary-photo accuracy proof.

## Separate successful browser rehearsal

Actual Chromium drove production frontend/API routes on a new isolated localhost
backend, using the existing deterministic provider doubles and a separate SQLite,
image store and test-only ledger. Credentials and external networking were disabled.
Every view displays OFFLINE TEST OUTPUT. Creator-declared synthetic scene identity
and scripted human transcriptions are test inputs, never genuine field reports.
The successful order was F-17 photo/review then V-08 report; it is **not** the same
incident/order as the founder's live V-08 -> F-17 branch.

The browser exercised incident creation, planning, ordinary file selection and
upload, explicit photographic analysis, independent review, cited replanning,
approval, completion, monitoring, sample-derived recovery and both-view reload.
All states used the real server and persisted records, not intercepted API responses.
Readonly audit found one incident, two tasks, three evidence records, two planning
attempts, one analysis, one approval and seven samples. Double usage is unknown;
no fake tokens/costs were assigned. Hidden simulator outcome/answer keys were absent
from saved planner contexts. Existing histories and the real ledger were untouched.

Successful preview remains available (local profile, not employee role isolation):
- http://127.0.0.1:8893/commander
- http://127.0.0.1:8893/operator

Choose Verify local server to view the retained completed rehearsal. No new
incident or analysis is needed. Desktop and 390x844 outcome screenshots plus two
WebM recordings: ignored `.local/connected-browser/5f00c24d612544ccae16807395f377e2/browser/`.
The earlier incomplete test run is preserved separately. Initial test CSP/label
locator failures were corrected without changing application security or policy.

Reproducible harness: `tools.connected_browser_demo:create_demo` requires a new
ignored FAULTTRACE_BROWSER_REVIEW_ROOT, compiled local-profile build in its `dist`,
and localhost FAULTTRACE_PREVIEW_ORIGIN. Start with uvicorn on a verified-free port.
`frontend/tests/connected-browser.mjs` uses the current ignored review descriptor
and existing Playwright/Chromium, blocks external browser traffic, and performs all
mutations through UI controls. Python's audit guard forbids external provider sockets.
Do not deploy the test harness or point it at historical/hosted data.

## Boundaries and remaining limitations

- Pressure cannot satisfy DP; assigned identity is not photographed identity.
  Human/model sources, original units, conflicts, stale evidence and refusals remain.
- Existing 120-second freshness, agreement bands, revision/idempotency rules,
  planning limits and independent recovery verifier remain unchanged.
- No conflict/access-clearance workflow is invented. Clarify or escalate unresolved
  evidence instead of force-clearing it; no live recovery is claimed for the founder run.
- Browser completion proves the application transitions with doubles, not live
  adaptive reasoning or vision accuracy. Camera hardware was not exercised.
- Current orchestration remains Python/SQLite. No framework/storage replacement,
  provider calls, trace resend, budget reset or paid-resource change was needed.
