# AGENT_HANDOFF.md

## Current state

Branch: `feat/p5-i18n-a11y`.

P5.7 is **PASS** after automated qualification and the 2026-09-27 REAL HA
qualification.

Roadmap P5.8 — FR/EN i18n, CJK and accessibility hardening — is **PASS**.

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

## REAL HA qualification — PASS (2026-09-27)

The complete tree at HEAD `5830fb0ae303837c7d7ad49387357029626e258a` was
deployed to Home Assistant 2026.7.4 through Advanced SSH & Web Terminal. The
add-on was discovered through the Supervisor WebSocket API in read-only mode;
the current SSH username was `root`, and no add-on option or credential was
changed. Config Entry state was `loaded`, frontend protocol `3` matched, and
the local/remote bundle SHA-256 was
`c2749626ab152109402fe6fe207e876a31e82ec53299906235abf38a339a0be4`.

Firefox verified the core routes in French, English and `en-GB` without raw
translation keys. A real temporary Japanese Starter Track rendered kana `あ`
with `lang="ja"`, the system Japanese/CJK stack and calculated size 59.5px;
the surrounding UI remained French. No ruby fixture was present:
`FIXTURE UNAVAILABLE`; automated tests cover `<ruby>/<rt>` and safe text
escaping. Visible controls had accessible names, tab traversal exposed a 3px
focus outline, and no essential hover-only action was observed.

Firefox clamped the requested 390×844 viewport to 500×758 CSS:
`HARNESS LIMIT`. At 500px, Home, Learn, Quiz, Stats, Tracks and Sources &
Licences had no horizontal overflow. Light theme was checked. The instance
and headless harness exposed no usable `default_dark_theme` resource, so dark
theme visual qualification is explicitly `HARNESS LIMIT`. Linux Firefox is
the only Han platform qualified; Windows, Android and iOS are
`FIXTURE UNAVAILABLE`.

Temporary Profile, Track and session state were removed through public
WebSocket APIs. The personal Profile has no QA Track, the final LockLearn log
query has no entries, no SSH askpass/password/known-host helper remains, and
no deployment stage remains under `/config/custom_components`.

No product bug was reproduced, so no correction or post-fix gate was needed.
P5.9 must not start without the maintainer's explicit decision.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
