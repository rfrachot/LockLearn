# AGENT_HANDOFF.md

## Current mission

Qualify beta.5 calibration fix on `feat/beta5-no-dead-end-v03`.
Initial remote HEAD: `277374ddaf55f0f6c36f8e00166d793e29597cb0`.
The old CI run `36995062368` belongs to `9d8e175cc7bc7119205818274bb05791a1c17d52` and does not qualify this branch.

## Verified local state

The new regression test failed at the initial HEAD: calibration selected zero cards while Learn also selected zero. The previous fix only bypassed introduction-order constraints in availability; `session/start` still enforced them in `_async_candidate_pool`. That path now bypasses those constraints for calibration only. The test also checks that availability matches selection and Learn remains blocked.

Commit `dfa9c588cb1201fba3c0b106d9e294bb5136b6d7` passed CI run `37008623651` (8/8 jobs) and was deployed after HA backup `PRE_BETA5_CALIBRATION_FIX` (`b2e550b5`). The deployed tree and served bundle matched that SHA. A real calibration start on the existing Japanese Starter Track still produced `question_count=0`: `QuizSessionService.async_prepare_questions` discarded all `new` cards. A second narrow fix now allows new cards only for calibration. It is not yet committed, CI-qualified, or deployed.

After the second fix, 39 targeted quiz/selection tests and 514 full pytest tests passed (1 expected duplicate ZIP warning). Ruff format/lint, mypy, resource validation, frontend lint/typecheck, 64 Vitest tests, build, 7 Playwright E2E, and generated docs contracts passed.

## Next action

Commit the second fix, updated regression test, changelog, and handoff. Push the branch, dispatch CI on its exact new candidate SHA, and verify all eight jobs. Do not redeploy until CI is green. Then deploy the complete integration tree using the qualified direct-copy procedure, verify deployed and served hashes, and repeat the real calibration start before other field checks. Preserve the existing state database.
