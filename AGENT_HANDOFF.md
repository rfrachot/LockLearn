# AGENT_HANDOFF.md

## Current mission

Qualify beta.5 calibration fix on `feat/beta5-no-dead-end-v03`.
Initial remote HEAD: `277374ddaf55f0f6c36f8e00166d793e29597cb0`.
The old CI run `36995062368` belongs to `9d8e175cc7bc7119205818274bb05791a1c17d52` and does not qualify this branch.

## Verified local state

The new regression test failed at the initial HEAD: calibration selected zero cards while Learn also selected zero. The previous fix only bypassed introduction-order constraints in availability; `session/start` still enforced them in `_async_candidate_pool`. That path now bypasses those constraints for calibration only. The test also checks that availability matches selection and Learn remains blocked.

Commit `dfa9c588cb1201fba3c0b106d9e294bb5136b6d7` passed CI run `37008623651` (8/8 jobs) and was deployed after HA backup `PRE_BETA5_CALIBRATION_FIX` (`b2e550b5`). A real calibration start on the existing Japanese Starter Track still produced `question_count=0`: `QuizSessionService.async_prepare_questions` discarded all `new` cards. Commit `d9d86d267b3e7b30761477f5362841a598cedaa3` fixed this, passed CI run `37009918361` (8/8), and was deployed with exact tree and served bundle verification.

Real UI calibration 20 then started with 20 questions and a hidden answer. It completed with 5 correct, 5 wrong, 10 IDK; canonical `session/get` reported `known=5`, `needs_learning=15`. The final UI lost the summary because `session/complete` returned an undecorated state. A reload of an active calibration also showed no Quiz resume action (while Learn offered the wrong resume action). The third fix addressed both issues.

Commit `f75d501b38121099689e0b3c8fd0dc48e648f3cf` passed CI run `37011621995` (8/8) and was deployed. HA startup initially failed because hidden rollback directories under `/config/custom_components/` confused integration discovery. They were preserved under `/config/locklearn-code-backups/`, after which HA loaded the exact tree and served the matching bundle. On this SHA, a real UI calibration 20 completed with `known=1`, `needs_learning=19` and both appropriate CTAs; 30/40 each started with nonempty exact samples. Browser reload resumed an active calibration on Quiz, and HA Config Entry reload preserved the active 40-question session with clean LockLearn logs. The 30/40 sessions were completed early with no answers through the public API.

Real Quiz started with 19 questions, but the first answer failed with `unknown_error`. HA traceback showed a legacy `known_already` card in `state=learning` entering `ReviewPolicyV1.review_success`, which requires review/leech. A fourth narrow local fix normalizes such pending records to review box 1 before applying verified Quiz success/failure. This fix is not yet committed, CI-qualified, or deployed.

After the fourth local fix, 516 full pytest tests (1 expected duplicate ZIP warning), Ruff format/lint, mypy, resource validation, frontend lint/typecheck, 66 Vitest tests, build, 7 Playwright E2E, no-polling and bundle-budget checks, and generated docs contracts passed. The frontend bundle rebuilt reproducibly without changes.

## Next action

Commit the fourth fix, updated tests and deployment documentation, changelog, and handoff. Push the branch, dispatch CI on its exact new candidate SHA, and verify all eight jobs. Do not redeploy until CI is green. Then deploy the complete integration tree, keeping rollback code outside `/config/custom_components/`, verify deployed and served hashes, and retry the real Quiz answer before other field checks. Preserve the existing state database.
