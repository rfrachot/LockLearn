# AGENT_HANDOFF.md

## Current state

Branch: `feat/p5-stats-ui`.

P5.6 remains **PASS** after the 2026-09-27 REAL HA qualification and the
executor fix for bundled registry loading.

Roadmap P5.7 — Basic stats, difficulties and metacognitive views — is
**PASS / AUTOMATED QUALIFICATION PASS / REAL HA PASS**.

P5.7 is a frontend/product surface over the existing P3.13/P3.11 backend truth.
It does not recompute SRS/statistics in the browser.

Implemented surfaces:
- dedicated Stats route with optional active-Track filter;
- due-today and current SRS state counts;
- latest trusted verified retention and recent verified accuracy;
- explicit visual separation of learning exposure from verified retrieval;
- due-queue streak;
- self-known-vs-later-verified metacognitive calibration;
- explicitly secondary mastery estimate with time-decay explanation;
- persistent leeches with confusion evidence;
- bounded recent daily activity aggregated by local date across Tracks before
  applying the 14-day UI window;
- owner/editor remediation actions: personal mnemonic create/edit,
  `leeches_only` targeted Learn session and manual leech reactivation;
- viewer read-only presentation, with backend ACL still authoritative;
- targeted session handoff from Stats to the existing Learn view.

Important honesty rules:
- `learning_exposures` never count as verified accuracy;
- verified accuracy comes only from the backend P3.13 trusted verified retrieval
  projection;
- mastery is secondary/synthetic and never replaces due dates or verified
  evidence;
- frontend role hiding is convenience only; P3.11/P2.3 backend ACL rechecks all
  annotation/reactivation/session mutations.

Automated qualification on 2026-09-27:
- source gate: `edff8a702fff1014c952c034000c95ba504643c3`;
- Ruff format PASS — 259 files;
- Ruff lint PASS;
- mypy PASS — 149 source files;
- resource registries PASS;
- pytest PASS — 393 tests;
- HA 2025.2.5 PASS — 300 backend tests;
- HA 2026.9.3 PASS — 300 backend tests;
- TypeScript PASS;
- Vitest PASS — 14 files / 43 tests;
- Vite PASS — 32 modules, 182.68 kB / 36.54 kB gzip;
- bundle materialized at `daf01d285a162453a663c6d5e98441e3cb9a7947`;
- committed-bundle reproducibility PASS at
  `b51385f046e875c292940e0b67abd3dae5832dfd`.
- temporary P5.7 branch-only CI removed after qualification.

The automated frontend tests specifically verify that exposure totals remain
separate from verified retrieval totals, multi-Track daily rows are aggregated
by local date before the recent-day window, owner/editor vs viewer remediation
visibility, and the exact P3.11 WebSocket mutation contracts.

## REAL HA qualification (2026-09-27)

The complete tree from `eed01692e7ee6de96e99367e7c88c6a23ddc1994` was deployed
to Home Assistant 2026.7.4. The Config Entry loaded after Core restart,
frontend protocol 3 matched, and the deployed bundle was byte-identical to the
local bundle. Empty-state honesty, Stats rendering, keyboard traversal, Track
filtering, rapid Track switching, daily aggregation and clean LockLearn logs
passed.

The temporary Profile `QA P5.7 20260927-025928` and Tracks A/B were created,
used and deleted through public WebSocket APIs. The fixture demonstrated three
exposures versus two trusted verified retrievals, `1/2` accuracy, correct/IDK,
calibration and separate Track values. No leech/confusion fixture was made: the
normal leech threshold was not reasonably reachable during this run. Leech
presentation/remediation, targeted-session handoff, reactivation, confusions
and viewer ACL are `FIXTURE UNAVAILABLE` (no second HA token); automated P3.11
and ACL coverage remains authoritative. Firefox's requested 390 px viewport was
limited to 500 px; no blocking overflow was observed there (`HARNESS LIMIT`).

P5.7 is closed PASS. Do not start P5.8 without an explicit the maintainer decision.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
