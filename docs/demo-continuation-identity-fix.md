# Demo continuation identity correction

The demo registry indexes principals by workspace role (`commander`) but
authenticates them with a stable principal ID (`demo-commander`). Continuation
stored that stable ID and incorrectly assumed it was also the registry key.
Valid consent therefore stopped before planning with `continuation_access_ended`.

Continuation now resolves an exact, unique authenticated principal ID when the
registry key lookup fails. Commander role, current incident grant, revocation,
expiry and active demo session checks remain mandatory. No role-only fallback,
provider retry, budget reset or automatic consent is introduced.

Regression tests use the actual DemoRegistry adapter. Authenticated Commander
consent reaches one scripted planning request; Operator consent and a disabled
session guard cannot dispatch. All 16 continuation tests pass locally using
offline doubles. Hosted acceptance remains pending deployment.

After deployment, the same active demo can explicitly start guided investigation
again. Do not restart the demo or reset its allowance to work around this bug.
