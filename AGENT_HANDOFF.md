# AGENT_HANDOFF.md

## Current mission

Qualify beta.5 calibration fix on `feat/beta5-no-dead-end-v03`.
Initial remote HEAD: `277374ddaf55f0f6c36f8e00166d793e29597cb0`.
The old CI run `36995062368` belongs to `9d8e175cc7bc7119205818274bb05791a1c17d52` and does not qualify this branch.

## Verified local state

The new regression test failed at the initial HEAD: calibration selected zero cards while Learn also selected zero. The previous fix only bypassed introduction-order constraints in availability; `session/start` still enforced them in `_async_candidate_pool`. That path now bypasses those constraints for calibration only. The test also checks that availability matches selection and Learn remains blocked.

Commit `dfa9c588cb1201fba3c0b106d9e294bb5136b6d7` passed CI run `37008623651` (8/8 jobs) and was deployed after HA backup `PRE_BETA5_CALIBRATION_FIX` (`b2e550b5`). A real calibration start on the existing Japanese Starter Track still produced `question_count=0`: `QuizSessionService.async_prepare_questions` discarded all `new` cards. Commit `d9d86d267b3e7b30761477f5362841a598cedaa3` fixed this, passed CI run `37009918361` (8/8), and was deployed with exact tree and served bundle verification.

Real UI calibration 20 then started with 20 questions and a hidden answer. It completed with 5 correct, 5 wrong, 10 IDK; canonical `session/get` reported `known=5`, `needs_learning=15`. The final UI lost the summary because `session/complete` returned an undecorated state. A reload of an active calibration also showed no Quiz resume action (while Learn offered the wrong resume action). These reproducible bugs are now fixed locally in the WebSocket completion contract and Learn/Quiz resume routing, with targeted tests. This third fix is not yet committed, CI-qualified, or deployed.

After the third local fix, the targeted WebSocket lifecycle test, 514 full pytest tests (1 expected duplicate ZIP warning), Ruff format/lint, mypy, resource validation, frontend lint/typecheck, 66 Vitest tests, build, 7 Playwright E2E, no-polling and bundle-budget checks, and generated docs contracts passed. The frontend bundle was rebuilt from this source.

## Next action

Commit the third fix, updated tests, changelog, and handoff. Push the branch, dispatch CI on its exact new candidate SHA, and verify all eight jobs. Do not redeploy until CI is green. Then deploy the complete integration tree using the qualified direct-copy procedure, verify deployed and served hashes, and repeat calibration completion/resume in the real UI before other field checks. Preserve the existing state database.
