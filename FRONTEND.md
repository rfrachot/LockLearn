# Frontend

The LockLearn panel is TypeScript + Lit, bundled by Vite and served locally by the
Home Assistant custom integration.

## Architecture

`locklearn-panel.ts` owns the application shell, Profile switcher, routing and
initial bootstrap. Feature views are split into Learn, Quiz, Stats, dataset/source
and management components. Pure model/helpers are unit-tested separately.

Routes:

```text
/locklearn
/locklearn/learn
/locklearn/quiz
/locklearn/exam
/locklearn/stats
/locklearn/profiles
/locklearn/tracks
/locklearn/packs
/locklearn/sources
/locklearn/settings
```

## State management

There is no global third-party state framework. Lit component state plus backend
authoritative WebSocket responses form the state model. Long-lived session changes
use backend subscriptions rather than polling.

## WebSocket interface

All application calls use Home Assistant `hass.callWS`. The panel has no direct
database or runtime HTTP API.

Protocol mismatch is fail-visible: frontend/backend protocol version is compared
and an older loaded custom element triggers a hard-reload overlay instead of
silently running mixed contracts.

See `API.md`.

## Rendering and sanitization

Dataset HTML is never injected. Content rendering supports text, ruby and the
strict rich-text AST using Lit escaping and an explicit node allowlist. Frontend
CI forbids `unsafeHTML`, `eval`, dynamic Function and direct `innerHTML=`.

Public dataset assets are resolved from the verified local cache; no runtime CDN
is required.

## Responsive design and themes

Views use Home Assistant CSS custom properties and responsive layouts. CJK content
uses a broad local system/CJK font stack rather than bundled remote fonts.

## Accessibility

Interactive controls have visible `:focus-visible` outlines. E2E tests exercise
keyboard focus, core routes and CJK ruby rendering. Semantic headings/roles and
native buttons/selects are preferred.

## Home Assistant internals

The panel minimizes dependence on undocumented HA frontend internals; it primarily
uses standard custom elements/CSS and the public `hass` object/WebSocket boundary.
Compatibility lanes and Playwright protect the integration from frontend drift.

## Build

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run check:no-polling
npm run build
npm run check:bundle
npm run test:e2e
```

The committed production bundle is
`custom_components/locklearn/frontend/locklearn-panel.js`.
