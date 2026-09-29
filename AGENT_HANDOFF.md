# AGENT_HANDOFF.md

## Current state

Field-test beta.4 qualification completed on `release/1.0.0-beta.4`.

The committed frontend bundle was regenerated from source and pushed in:

- `8a89677c510c231ba3f889ce587dd31c0f90d372` —
  `build(beta4): regenerate field-feedback frontend bundle`;
- bundle SHA-256:
  `21e279603274fa10ff07e79e42629b90c3bcc676229e68bd2672bfda3700013f`.

The second Vite build was reproducible and left the worktree clean before
qualification. GitHub CI run `36626168374` passed all jobs: backend-quality,
frontend, frontend-e2e, dataset-contracts, home-assistant-validation, HA
minimum 2025.2.5, current harness 2026.9.3 and latest stable 2026.9.4.

Local verification passed:

- targeted session-selection tests: 27 passed;
- frontend targeted tests: 57 passed;
- full backend suite: 506 passed, one non-blocking duplicate-ZIP-name warning;
- Ruff format/lint, mypy, generated docs, resource and schema contracts;
- frontend lint, typecheck, tests, no-polling, bundle budget and E2E: 7 passed.

Real HA 2026.7.4 qualification:

- HACS `hacs/repository/download` used for repository `1371828774`, branch
  `release/1.0.0-beta.4`, then HA was restarted;
- LockLearn Config Entry is `loaded`, frontend protocol is `3`, panel module
  URL contains bundle digest `21e279603274`;
- served bundle SHA-256 matches the local bundle exactly;
- storage status: integrity `ok`, foreign keys `0`, schema `5`, WAL,
  writer initialized and reader off the event loop;
- system log query has no LockLearn warning/error/critical entries;
- existing qualification Profile/Track was reused; no Profile was created or
  deleted by this qualification.

Observed real Track readiness:

- Learn: `introduced_cards=32`, `new_cards=68`, `available_now=15`,
  `forceable_early=1`, `next_available_reason=scheduled_step`, and the next
  due/available timestamp is `2026-09-29T20:44:05.309081+00:00`;
- Quiz: `introduced_cards=32`, `available_now=15`, same scheduled-step
  timestamp, so the UI does not use the first-learning message;
- Stats: `learning=19`, `review=0`, confirming that completion of a short
  learning-step session does not imply review graduation.

The source/test contract covers persisted Track readiness copy, scheduled
learning steps, local new-card quota reset, availability/start parity, safe
early learning, and non-bypassable failed/relearning cooldowns. No deployment
or release action remains for this beta.4 field-test gate.
