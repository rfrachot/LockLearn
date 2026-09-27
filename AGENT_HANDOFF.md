# AGENT_HANDOFF.md

## Current state

Branch: `feat/p5-i18n-a11y`.

P5.7 is **PASS** after automated qualification and the 2026-09-27 REAL HA
qualification.

Roadmap P5.8 — FR/EN i18n, CJK and accessibility hardening — is
**IMPLEMENTED / AUTOMATED QUALIFICATION PASS / REAL-HA PENDING**.

P5.8 changes are frontend-only and preserve existing backend contracts.

Implemented scope:
- FR/EN catalog retained as a frontend-owned UI catalog independent from taught
  languages;
- locale resolution is explicit exact locale → base language → English;
- automated FR/EN translation-key parity prevents silent partial localization;
- Learn and Quiz now use one shared safe content renderer;
- content language metadata is preserved with `lang`;
- Japanese content uses a system CJK/Japanese font stack with readable minimum
  sizing;
- validated `ruby_segments` and allowlisted rich-text ruby nodes render as
  native `<ruby>/<rt>`;
- malformed ruby metadata falls back to safe plain text;
- raw dataset strings are never interpreted as HTML/unsafeHTML;
- shared `:focus-visible` affordances and long-text containment are applied to
  panel, management, dataset, stats, Learn and Quiz shadow roots;
- HA theme variables remain the styling authority; no fixed light-only theme was
  introduced;
- no essential hover-only interaction was introduced.

Automated qualification on 2026-09-27:
- source gate: `f7f6a198f5efe1ae289a95c409d2d399c85faf90`;
- Ruff format PASS — 259 files;
- Ruff lint PASS;
- mypy PASS — 149 source files;
- resource registries PASS;
- pytest PASS — 393 tests;
- HA 2025.2.5 PASS — 300 backend tests;
- HA 2026.9.3 PASS — 300 backend tests;
- TypeScript PASS;
- Vitest PASS — 15 files / 48 tests;
- Vite PASS — 33 modules, 185.58 kB / 37.56 kB gzip;
- generated bundle materialized at
  `7039fe466af5207ebed7a339746424181bf82f6e`;
- committed-bundle reproducibility PASS at
  `d39ff77be7dee511fce43fff00296f7074f81b92`;
- temporary P5.8 branch-only CI removed after qualification.

The automated renderer tests cover:
- exact/base/English locale fallback;
- full FR/EN key parity;
- valid and malformed ruby metadata;
- plain-text handling of HTML-like dataset strings;
- Japanese system-font stack and ruby styling;
- visible keyboard focus styling.

## Remaining gate

REAL HA P5.8 has not been executed in this session because the real HA/browser
harness is not available here.

Qualify on the development Home Assistant instance:
1. deploy the complete `custom_components/locklearn/` tree from
   `feat/p5-i18n-a11y`;
2. smoke the core routes in both French and English HA locales and verify the
   panel follows locale changes/fallback without mixed-language missing keys;
3. run Learn and Quiz against Japanese starter content and inspect actual DOM
   `lang="ja"`, readable Han/kana rendering and the effective system CJK font
   path available in the browser;
4. if a real content fixture carrying `ruby_segments` exists, verify visible
   `<ruby>/<rt>`; otherwise mark the manual ruby scenario
   `FIXTURE UNAVAILABLE` and retain automated evidence;
5. keyboard-smoke navigation, form controls, Learn/Quiz actions, Stats,
   Sources/Licences and management routes with visible focus and no
   hover-required action;
6. test long labels/content/URLs and the available narrow viewport for blocking
   overflow; if Firefox still clamps requested 390 px to 500 px, record
   `HARNESS LIMIT`;
7. smoke both HA light and dark themes and verify readable contrast/layout
   without hard-coded theme breakage;
8. inspect LockLearn system logs after route/session activity;
9. clean all temporary fixtures and SSH_ASKPASS helper.

The spec also asks for Han rendering on Windows, Linux, Android and iOS. Record
each platform actually exercised during REAL HA qualification. Do not claim a
platform PASS if the harness/device is unavailable; use `FIXTURE UNAVAILABLE`
or `HARNESS LIMIT` and preserve automated CJK evidence.

After REAL HA PASS, mark P5.8 complete and proceed to P5.9 only after explicit
the maintainer decision.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
