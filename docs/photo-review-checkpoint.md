# Real-photograph workflow review checkpoint

This isolated branch contains a focused adaptation following the
[PlantDebugger implementation review](plantdebugger-review.md).
PR #1 has been reviewed and merged into feat/finish-integrated. Final integration
CI/deployment evidence is tracked in state.md. The Windows browser-test path
containment check was corrected and desktop/mobile checks rerun successfully.

## Changes

- One explicit upload-and-analyze action, using the confirmed image identifier and fresh context.
- Prominent current-photo result, inspection and independent review link.
- Photographic confirmation offered only for the versioned photographic contract.
- Synthetic fixture entry restricted to explicit local developer mode; old records remain intact.
- Two real photograph references with visible attribution, licenses and provenance manifests.
- No backend policy changes, automatic replanning, approval or correction.

## Verification

- 113 frontend tests, TypeScript checks and normal/demo builds pass.
- 320 guarded backend tests pass; zero forbidden external network attempts.
- Release and demo combined API contracts pass without provider calls.
- Actual built demo UI checked in Chromium at 1440x900 and 390x844 with isolated offline results.
- Real JPEG upload bytes checked at a localhost receiver; keyboard activation, blank independent
  fields, inspection, Escape/focus return, navigation and page-width checks pass.
- Browser harness: `frontend/tests/real-photo-browser.mjs`.

No hosted records, budgets, service settings or historical reports were changed.
These checks do not establish hosted acceptance, live image accuracy, camera hardware support
or autonomous equivalence with the reference implementation.

A full reference-equivalent runner still needs durable authorized continuation and a coherent
catalog of additional interventions. The detailed review specifies those gaps and boundaries.

The existing state-history and submission files are deliberately unchanged in this branch.
Automatic approval review blocked retransmitting the state-history artifact because it includes
operational metadata; this minimal addendum contains only implementation and verification facts.
