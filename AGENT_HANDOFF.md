# AGENT_HANDOFF.md

## Current state

Beta.4 UX follow-up is integrated and deployed from
`release/1.0.0-beta.4`.

- UX branch initial SHA: `7d6e23c70402940ebb7b0b24dc5962fb6daa2b89`.
- `deployed_sha`: `c94cf72c7616f002fcd5eb896fb88a1027b3f8e7`.
- `documentation_head`: this doc-only handoff commit after the deployed SHA;
  it must not be redeployed.
- CI run `36675810188`: PASS for backend-quality, frontend, frontend-e2e,
  dataset-contracts, home-assistant-validation, HA minimum 2025.2.5, HA
  current-harness 2026.9.3 and HA latest stable 2026.9.4.
- Bundle SHA-256: `2c37e0818214e51a8ed0a666ed40c9710dcdb5b790f2e40f59ee794ff58d70bb`.
- HA target: `2026.7.4`.

The UX commits were pushed on `fix/beta4-ux-readiness`, then cherry-picked into
the release branch. The second frontend build was reproducible and left the
worktree clean before deployment.

## Deployment qualification

HACS `hacs/repository/download` was called for repository `1371828774` with
`release/1.0.0-beta.4`. Home Assistant returned after the resulting restart.

- Config Entry: `loaded`.
- Frontend protocol: `3`.
- HACS installed version: `release/1.0.0-beta.4`.
- Served bundle: HTTP 200, 232694 bytes, SHA-256 exactly matching local.
- Storage: integrity `ok`, foreign keys `0`, schema `5`, WAL, reader off the
  event loop, writer initialized.
- LockLearn warning/error/critical records after restart: `0`.
- No Profile or Track was created, deleted, applied, or answered during this
  qualification.

## Real Track field test

Existing Track: `Japanese Starter b37891dc`.

Read-only backend snapshot:

- Plan preview with new/day `8`, reviews/day `50`, teasers/day `2`, target
  date `2026-10-30`, coverage `1.0`, retention `0.9`:
  `selected_cards=100`, `introduced_cards=32`, `remaining_target_cards=68`,
  `required_new_per_day=3`, `planned_new_per_day=8`, `due_now=0`, reviews/day
  `7` at 3 weeks and `0` at 3 months, notifications/day `6` at 3 weeks and
  `0` at 3 months, feasible, warnings empty.
- Learn: `introduced_cards=32`, `new_cards=68`, `available_now=16`.
- Quiz: `introduced_cards=32`, `available_now=16`; no false first-learning
  message.
- Stats: learning `19`, review `0`, relearning `0`, new `81`.
- Preview did not persist a plan: `learning_plan=None` after the field test.

## UX results

- Learn: existing empty session initially shows only `Resume session`; after
  resume it shows the new-session explanation and only `Start learning`, never
  `Learning pause` while cards are available.
- Quiz: existing empty session initially shows only `Resume quiz`; after resume
  it shows the new-quiz explanation and only `Start quiz`, with `16 cards ready
  now`.
- Plan: real preview displays the 100/32/68 snapshot in context, workload
  explanations, and the too-close target-date warning. Preview was not Apply.
- Stats: plain-language explanations for spaced repetition, Learning, Review,
  Relearning, and verified retrieval evidence are visible.
- Mobile: 390 px viewport, no horizontal overflow (`0` px).

## Status

`PASS — ADRIEN PEUT RETESTER BETA.4`

Do not start beta.5, merge main, tag stable, or delete user data.
