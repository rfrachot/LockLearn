# AGENT_HANDOFF.md

## Current state

Beta.4 UX follow-up implemented on `fix/beta4-ux-readiness`, based on
`release/1.0.0-beta.4` at `e9a47cd45270d0fc90a3bd6879116012478e74f9`.

The follow-up keeps one contextual action visible after a Learn/Quiz session
is opened, shows concrete Learn readiness counts before starting, and shows
Quiz started/ready counts when no review is due. The E2E readiness fixture now
includes the complete availability timing contract. The existing planning
snapshot fix remains in place and zero-card forecasts are rejected by the
backend rather than displayed as a useful estimate.

The follow-up bundle was regenerated from source. Its current local SHA-256 is
`2c37e0818214e51a8ed0a666ed40c9710dcdb5b790f2e40f59ee794ff58d70bb`.

The previously committed frontend bundle was regenerated from source and pushed in:

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
- follow-up frontend source/tests/build and backend full checks: backend 506
  passed; frontend 57 passed; E2E 7 passed; Ruff, mypy, resource validation,
  no-polling and bundle budget passed.

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
early learning, and non-bypassable failed/relearning cooldowns.

Real HA read-only qualification was completed on the existing qualification
Track `Japanese Starter b37891dc` without creating or changing any Profile or
Track. The direct `locklearn/tracks/plan_preview` response used
`max_new_per_day_cards=8`, `max_reviews_per_day_cards=50`,
`max_notification_new_teasers=2`, target date `2026-10-30`, coverage `1.0`
and retention `0.9`, and returned:

- `selected_cards=100`, `introduced_cards=32`, `target_cards=100`,
  `remaining_target_cards=68`;
- `required_new_per_day=3`, `planned_new_per_day=8`, `due_now=0`;
- `reviews_per_day_in_3_weeks=7`, `reviews_per_day_in_3_months=0`;
- `notification_deliverable_in_3_weeks=6`,
  `notification_deliverable_in_3_months=0`;
- all feasibility flags true and `warnings=[]`.

The same real Track reported `introduced_cards=32`, `new_cards=68` and
`available_now=16` for both Learn and Quiz at qualification time; no future
availability timestamp was needed. The deployed instance reported backend
version `1.0.0-beta.3` and frontend protocol `3`. The local UX follow-up is
committed but not pushed or deployed; deployment still requires the normal
authorized release/development deployment path.
