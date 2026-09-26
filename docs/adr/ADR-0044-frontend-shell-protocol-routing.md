# ADR-0044 — Frontend shell, WebSocket protocol and routing

## Status

Accepted design, with P5.1 implementation qualification temporarily reopened on
2026-09-26 after a live-panel regression was observed: Home Assistant repeatedly
reassigns the `hass` property while the panel is open, and the original shell
restarted bootstrap on every such update. A regression fix is implemented and
must pass repository/frontend gates plus real-HA requalification before P5.1 is
closed PASS again.

## Context

P0.7 proved that a bundled Lit panel can be served by Home Assistant and survive
HACS install/update/restore. P5.1 promotes that bootstrap artifact into the
actual V1 frontend shell.

The V1 frontend must use TypeScript, Lit and Vite, communicate only through the
authenticated Home Assistant WebSocket API, keep backend ACL authoritative and
handle stale browser modules explicitly.

## Decision

### Explicit protocol handshake

The panel first calls `locklearn/bootstrap`. The response contains:

- `frontend_protocol`;
- `backend_version`;
- `panel_path`;
- authenticated HA user identity;
- optional personal Profile bootstrap state.

The compiled frontend has its own `FRONTEND_PROTOCOL_VERSION`. If it does not
match the backend response, no Profile or product data is loaded. The panel
renders an explicit hard-reload state.

The bootstrap remains intentionally small. Visible Profiles are loaded through
the existing paginated `locklearn/profiles/list` command.

### Routing

P5.1 implements dependency-free panel routes:

- Home;
- Learn;
- Quiz;
- Exam;
- Stats;
- Profiles;
- Tracks;
- Packs;
- Settings.

Unknown URLs fall back to Home. Navigation uses browser history under the
`/locklearn` panel path.

P5.1 routes render shell placeholders only. Product-specific dashboard/session
screens belong to later P5 milestones.

### Permission-aware visibility, not authorization

The frontend derives navigation visibility from backend-returned Profile roles.
Settings is hidden unless at least one visible Profile is owned by the current
HA user.

This is presentation only. It grants no permission and never replaces backend
ACL checks. Direct WebSocket commands remain authorized independently.

### Custom element reload safety

Each frontend constructor exposes the compiled frontend protocol as static
metadata.

When no `locklearn-panel` element is registered, the module defines it once.
When an existing constructor carries the same protocol, the new module reuses it.
When the existing constructor is missing protocol metadata or carries another
protocol, the module never attempts a second `customElements.define()`.
Instead it shows a full-page hard-reload overlay.

A backend/frontend protocol mismatch after the element is running uses the same
hard-reload UX inside the panel.

### Bundle and cache busting

The Vite production build continues to write the single bundled ES module to:

`custom_components/locklearn/frontend/locklearn-panel.js`

There are no runtime CDN dependencies.

The Home Assistant panel URL is cache-busted with both:

- the LockLearn integration release version;
- the first 12 hexadecimal characters of the committed bundle SHA-256.

This preserves release provenance while ensuring that any rebuilt committed
artifact receives a distinct browser module URL even before the next formal
release bump.

### i18n boundary

P5.1 keeps the independent frontend FR/EN catalogue introduced by P0. Exact
locale falls back to base language, then English.

## Alternatives

### Put every Profile and route in the bootstrap payload

Rejected. Bootstrap is a protocol handshake, not an authorization cache or
application-state dump.

### Trust hidden navigation as permission enforcement

Rejected. Frontend never owns permissions.

### Redefine the custom element after an update

Rejected. Browsers prohibit redefining an already registered custom element and
the result is version-dependent breakage.

### Use a runtime CDN for Lit or router code

Rejected. V1 must remain self-contained and HACS-installable offline.

### Cache-bust only by integration version

Retained as release identity but insufficient during development/rebuilt
artifacts. The committed bundle digest is appended as an additional immutable
asset discriminator.

## Consequences

- P5.1 has an explicit frontend/backend protocol contract;
- stale frontend bundles fail closed before loading private product state;
- route visibility can react to Profile roles without weakening ACL;
- browser history supports stable panel deep links;
- every committed bundle maps to a deterministic module URL;
- the P5.1 qualification gate must include Vite typecheck, tests and build, and
  must verify that the generated bundle is committed exactly as built.

## Final qualification — 2026-09-25

Repository gate on `feat/p5-frontend`:

- Ruff format: PASS, 247 files already formatted;
- Ruff lint: PASS;
- mypy: PASS, 141 source files;
- resource registries: PASS;
- pytest: PASS, 379 tests in 18.82 seconds;
- TypeScript typecheck: PASS;
- Vitest: PASS, 6 files and 14 tests;
- Vite: PASS, 23 modules, 34.19 kB bundle and 10.48 kB gzip;
- bundle reproducibility: PASS. Two consecutive builds produced SHA-256
  `a92882a7fc77e59428941852438aaabd1ea24a5a2b96ae50673f83990a653dce`,
  with no source or lockfile drift under `frontend/`.

The committed branch was explicitly downloaded through HACS onto the existing
Home Assistant 2026.7.4 development instance and Core was restarted. Exactly one
loaded LockLearn Config Entry and one panel remained. The real bootstrap returned
frontend protocol 1, backend version 0.0.2 and `/locklearn`; the served bundle
matched the committed SHA-256 byte for byte. The registered module URL was
`/locklearn_static/locklearn-panel.js?v=0.0.2-a92882a7fc77`, and no LockLearn
ERROR/CRITICAL system-log record was present.

Firefox 156 real-browser qualification passed sidebar loading, owner navigation
to Home, Quiz and Settings, unknown-route fallback to Home, and a hard refresh at
`/locklearn/quiz`. A fresh browser document with a protocol-999 stale
`locklearn-panel` constructor retained that constructor, did not redefine the
tag and displayed the full-reload overlay. The deployed bundle's bootstrap
mismatch path displayed the same explicit reload UX and stopped after
`locklearn/bootstrap`, before Profile data loading. Only one owner token was
available, so the optional viewer/editor visibility scenario was not executed;
backend ACL and permission-derived navigation remain covered by automated tests.
