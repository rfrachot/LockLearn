# ADR-0044 — Frontend shell, WebSocket protocol and routing

## Status

Proposed for P5.1. Mark Accepted only after the backend/frontend quality gate and
bundled-artifact verification pass.

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
