# AGENT_HANDOFF.md

## Mission and branch

Qualify beta.5 on `feat/beta5-no-dead-end-v03`. Initial SHA `277374ddaf55f0f6c36f8e00166d793e29597cb0`. The maintainer authorized push, CI dispatch and deployment to the HAOS test instance. Preserve `/config/.storage/locklearn/state.db` and keep rollback code outside `/config/custom_components/`.

## Verified state

- Calibration fixes `dfa9c588`, `d9d86d26`, `f75d501b` passed CI (8/8 each) and real UI checks: 20 completed with visible known/remaining summary and CTAs; 30/40 started at exact nonzero sizes; browser and integration reload preserved active calibration.
- Legacy known-card Quiz fix `53022701` passed CI 8/8 and field Quiz answer progressed 1/19 to 2/19.
- `48c9b37a4655a2fdc524319340512185b73be9cb` passed CI `37015756211` (8/8) and is currently deployed: 91 tracked files match; served bundle SHA-256 `dbbbcf6bf56d43dae0bb0932c197b60fcfa920ed4cc29b15479fb2b8d1b0793b` matches. HA 2026.7.4 loaded after restart. Real Learn Undo returned a card to `active/new/box 0`, with zero verified counts. A QA Track proved the five-total bulk guard appeared after K,K,introduce,K,K,introduce,K, with both CTAs and no additional session mutation; a sixth K did not retrigger it.
- The concerned-cards UI showed known pending (6), suspended (1), buried (1); Learn it instead removed one pending card. No current Track exposed prerequisite or waiting-context blockers for their UI entry paths.
- A real Quiz readiness reminder had `available_now=0` and a future `next_available_at_utc`. Arm/status/cancel/rearm succeeded. At due time, availability was rechecked, became 0/null, and the reminder was cancelled without a false notification. The temporary QA notification target was disabled afterward.
- Real browser offline banner appeared and disappeared on reconnect. Controlled 10-second bootstrap timeout showed Retry, Home and Copy diagnostic after three failures; Retry recovered, Home returned to HA. Controlled answer latency >8 seconds showed Check status and Retry answer; canonical verification, one actual retry and a rejected stale CAS produced exactly three ReviewEvents for three answers.
- `643f8ec0d98ae9502516cd3ec3e3e5ee7f9d5a9b` passed CI `37020220216` (8/8), deployment tree and served bundle matched. Real Save and leave now saves and navigates to the chosen Profile. Calibration 20/30/40, correct/wrong/IDK, summary, Quiz progression and calibration persistence were rechecked. Waiting-context concerned-cards UI displayed 23 cards; prerequisite UI remains unavailable (active content has zero prerequisite records).
- Dirty guard route Stay/Discard, Profile change dialog, Back, refresh beforeunload dialog and mobile sticky save were field checked. Headless tab close did not emit a dialog, so that proof remains BLOCKED. A reproduced local Discard bug emptied Lit property-bound fields: this commit remounts only the discarded Track details/plan form from saved values and adds E2E coverage.
- Current local gates after that fix: 516 pytest, Ruff, mypy, resources, generated docs, frontend lint/typecheck, 66 Vitest, build, 10 Playwright E2E, no-polling and bundle budget pass. One expected duplicate ZIP warning remains. The QA Track name was restored after tests.

## Next action

Push this Discard correction, dispatch CI on its exact SHA, require 8/8 green, deploy complete tree and verify served hash. Retest local Discard for details/plan and preserved neighboring dirty forms on HAOS; finish reload/log smoke. Report prerequisite UI and tab-close proof as BLOCKED unless a real scenario becomes available. Calibration, Undo, bulk guard, reminder, CAS and recovery evidence above is retained; no state database was edited. Final qualification results belong in the session report; this handoff records the pre-deployment state of this correction.
