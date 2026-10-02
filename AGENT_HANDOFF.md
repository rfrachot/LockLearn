# AGENT_HANDOFF.md

## Current mission

Qualify beta.5 calibration fix on `feat/beta5-no-dead-end-v03`.
Initial remote HEAD: `277374ddaf55f0f6c36f8e00166d793e29597cb0`.
The old CI run `36995062368` belongs to `9d8e175cc7bc7119205818274bb05791a1c17d52` and does not qualify this branch.

## Verified local state

The new regression test failed at the initial HEAD: calibration selected zero cards while Learn also selected zero. The previous fix only bypassed introduction-order constraints in availability; `session/start` still enforced them in `_async_candidate_pool`. That path now bypasses those constraints for calibration only. The test also checks that availability matches selection and Learn remains blocked.

Targeted selection tests: 31 passed. Full pytest after the final test assertion: 513 passed, 1 expected duplicate ZIP warning. Ruff format/lint, mypy, resource validation, frontend lint/typecheck, 64 Vitest tests, build, 7 Playwright E2E, generated docs contracts, and bundle budget passed.

## Next action

Commit this narrow fix, updated regression test, changelog, and handoff. Push the branch, dispatch CI on its exact candidate SHA, and verify all eight jobs. Do not deploy until CI is green. Then back up the HAOS test instance, deploy the complete integration tree using the qualified direct-copy procedure, verify deployed and served hashes, and perform the requested real-HA field checks. Preserve the existing state database.
