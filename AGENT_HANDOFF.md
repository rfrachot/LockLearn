# AGENT_HANDOFF.md

## Mission

Qualify beta.5 on `feat/beta5-no-dead-end-v03` against the real HAOS instance. Initial branch SHA: `277374ddaf55f0f6c36f8e00166d793e29597cb0`. The maintainer authorized branch push, CI dispatch and HAOS deployment for this mission. Preserve the HA state database and keep rollback code outside `/config/custom_components/`.

## Verified state

- Calibration selection, new-card question preparation and final summary/resume were fixed in commits `dfa9c588`, `d9d86d26`, `f75d501b`. Each passed 8/8 CI jobs and was field tested. Real UI calibration 20 completed with a visible known/remaining summary and CTAs; 30/40 started with nonempty exact samples. Browser reload resumed calibration in Quiz; HA Config Entry reload preserved an active 40-card session.
- Legacy pending `known_already` verification in Quiz was fixed in `53022701` (CI `37013616468`, 8/8), deployed with exact integration tree and served bundle verification. The real Quiz first answer then advanced from 1/19 to 2/19 without error.
- A real Learn UI Undo showed a false success: the generic progress undo preserved `user_state=known_already`. The current uncommitted fix calls the canonical `cards/learn_instead` reversal. A new Playwright test verifies the UI command and success message. The real card still needs cleanup and post-deployment Undo retest.
- Current local gates: 516 pytest; Ruff format/lint; mypy; resource validation; frontend lint/typecheck, 66 Vitest, build, 8 Playwright; no-polling, bundle budget and generated docs contracts all pass. The tests emit one expected duplicate ZIP warning. An initial optional check used two wrong script names, then both correct commands passed.
- HAOS backup `PRE_BETA5_CALIBRATION_FIX` (`b2e550b5`) is complete. The current deployed and served SHA remains `530227018723e5f5aa4c2ed59434cf9ef4ccc5ef` until the next CI-qualified deployment.

## Next action

Commit this Undo fix and bundle, push, dispatch CI for the exact SHA and verify all 8 jobs. Deploy only after green CI, verify the complete file tree and served bundle, then retest Undo with the real UI and canonical card state. Continue the remaining beta.5 field scenarios and report PASS/BLOCKED/FAIL with evidence. Update this handoff before ending.
