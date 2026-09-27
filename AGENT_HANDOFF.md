# AGENT_HANDOFF.md

## Current state

Branch: `feat/p5-frontend-gate`.

P5.8 is **PASS** after automated qualification and the 2026-09-27 REAL HA
qualification.

Roadmap P5.9 — Frontend performance and compatibility gate — is
**IMPLEMENTED / AUTOMATED QUALIFICATION PASS / REAL-HA PENDING**.

P5.9 is primarily a durable quality gate rather than a new product surface.

Implemented scope:
- permanent 500 KiB gzip budget for the initial panel bundle;
- static frontend audit rejecting `setInterval`, direct `fetch`, direct
  `WebSocket`, `EventSource` and `XMLHttpRequest` transport regressions;
- Playwright Chromium harness mounting the real `<locklearn-panel>` against a
  contract-faithful Home Assistant `callWS` stub;
- E2E smoke covering Home, Learn, Quiz, Stats and Profiles, Japanese ruby
  rendering, quiz answer handling and visible keyboard focus;
- normal CI now runs frontend typecheck/Vitest/no-polling/build/bundle-budget,
  Playwright, HA minimum/latest compatibility and the P5.9 performance script;
- repeatable §80 benchmark separating next-card selection from complete
  finite-session planning.

Authoritative automated gate:
`653f24a88f58e05e2f2805389d5e923aa1e745be`.

Results:
- Ruff format PASS — 260 files;
- Ruff lint PASS;
- mypy PASS — 149 source files;
- resource registries PASS;
- pytest PASS — 393 tests;
- HA 2025.2.5 PASS — 300 backend tests;
- HA 2026.9.3 PASS — 300 backend tests;
- TypeScript PASS;
- Vitest PASS — 15 files / 48 tests;
- Playwright Chromium PASS — 2/2;
- no-polling/direct-network audit PASS;
- Vite PASS — 33 modules, 185.58 kB / 37.56 kB gzip;
- explicit gzip measurement: 185,575 bytes raw / 37,247 bytes gzip;
- bundle target: 512,000 bytes gzip;
- committed bundle and frontend lockfile reproducibility PASS.

§80 performance gate on the authoritative CI runner:
- `session/answer` p95: **1.12 ms** / budget **100 ms**;
- next-card selection p95: **139.47 ms** / budget **150 ms** over 20,000
  candidates and 40 samples;
- scheduler day generation p95: **6.702 ms** / budget **250 ms**;
- complete 20-card session planning p95: **377.864 ms** over 20,000 candidates,
  10 samples; informational only because §80 defines no whole-session budget.

Important benchmark boundary:
- do not call the 20-card session-plan metric “next-card”;
- next-card is intentionally measured with `requested_cards=1`;
- the earlier 514 ms failure was a benchmark-definition error, not a production
  regression;
- do not raise or weaken the normative §80 budgets without an explicit project
  decision.

The temporary branch-only P5.9 workflow has been removed. All durable gates are
in `.github/workflows/ci.yml`.

## Remaining REAL HA gate

P5.9 still needs final qualification on the development Home Assistant instance.

Qualify:
1. fetch `feat/p5-frontend-gate` and deploy the complete
   `custom_components/locklearn/` tree;
2. confirm Config Entry loaded, frontend protocol compatible and deployed panel
   byte-identical to the branch bundle;
3. full-reload the panel and verify core routes load and remain responsive;
4. inspect browser network/runtime activity for several minutes and verify
   LockLearn creates no permanent polling loop or separate mobile/network
   connection; ordinary HA WebSocket traffic is expected;
5. exercise Home, Learn, Quiz, Stats and management navigation; verify no
   regressions from Playwright/package changes;
6. measure/record an ordinary initial panel load and a few route switches if the
   browser harness exposes stable timing, but do not invent a new normative
   frontend timing budget;
7. verify browser memory/network activity does not grow obviously under a short
   idle period; report harness limits honestly;
8. inspect LockLearn logs after the smoke;
9. clean temporary QA fixtures and SSH_ASKPASS helper.

The §101 minimum/latest HA compatibility gate is already automated and does not
need a real HA 2025.2 installation during this smoke unless one is actually
available.

After REAL HA PASS:
- mark P5.9 PASS;
- mark the P5 exit gate complete if no new product failure is found;
- **do not start P6.1 without explicit the maintainer decision**.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
