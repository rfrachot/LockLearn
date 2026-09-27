# AGENT_HANDOFF.md

## Current state

Branch: `feat/p5-frontend-gate`.

P5.8 is **PASS** after automated qualification and the 2026-09-27 REAL HA
qualification.

Roadmap P5.9 — Frontend performance and compatibility gate — is
**PASS / AUTOMATED QUALIFICATION PASS / REAL HA PASS**.

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

## P5.9 REAL HA qualification — PASS (2026-09-27)

Branch: `feat/p5-frontend-gate`; HEAD:
`e00b4746e6052e93d6ce809a26ce988cf32cc2da`.

Home Assistant `2026.7.4` was qualified after deploying the complete
`custom_components/locklearn/` tree through the read-only-discovered Advanced
SSH & Web Terminal add-on. The Config Entry was `loaded`, frontend protocol
`3` matched, and local/remote bundle SHA-256 was
`c2749626ab152109402fe6fe207e876a31e82ec53299906235abf38a339a0be4`.

The deployed bundle and real authenticated HA WebSocket transport passed three
full reloads (72/75/76 ms in the harness), all nine routes (Home, Learn, Quiz,
Stats, Profiles, Tracks, Packs, Sources & Licences, Settings), and the
Home → Learn → Quiz → Stats → Profiles → Home cycle. No page error, console
error or failed request occurred. Thirty interaction-triggered LockLearn calls
were followed by zero `locklearn/*` calls during 180 seconds idle. The panel
created no separate network connection; one temporary harness WebSocket
carried the normal HA transport. Precise CPU/battery and memory-growth
measurement is a harness limit, not a product failure.

The final LockLearn log query contained no WARNING, ERROR or CRITICAL entries.
No temporary QA data, browser instrumentation or SSH helper remains, and no
backup/staging directory was left under `/config/custom_components`.

The local performance rerun passed: `session/answer` p95 2.186 ms,
next-card selection p95 96.841 ms over 20,000 candidates, scheduler day
generation p95 4.065 ms, and informational 20-card planning p95 228.894 ms.
The normative budgets remain unchanged. P5 and the P5 exit gate are now PASS.

The §101 minimum/latest HA compatibility gate is already automated and does not
need a real HA 2025.2 installation during this smoke unless one is actually
available.

Next action: **do not start P6.1 without explicit the maintainer decision**.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
