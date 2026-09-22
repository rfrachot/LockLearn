# ADR-0003 — Home Assistant compatibility floor

## Status

Accepted for P0 implementation on 2026-09-21.

## Context

`SPEC_V1.md` names HA 2025.2 as the candidate V1 floor. P0 must test the APIs
used by Config Flow, single-entry manifests, asynchronous static paths, custom
panels, backup hooks, device registry and WebSocket subscriptions.

## Decision

LockLearn V1 keeps **Home Assistant 2025.2** as its support floor. CI pins
`2025.2.5` with Python 3.13 and separately tests current stable HA with its
required Python. `hacs.json` advertises `2025.2.0` because HACS expresses the
monthly floor, while the compatibility evidence names the tested patch.

Frontend development uses Node 22 in CI. Local Node 24 is also verified.

## Evidence

The same Config Flow, setup/unload/reload, SQLite, session CAS, WebSocket and
security tests pass on HA 2025.2.5/Python 3.13.15 and HA 2026.9.3/Python 3.14.4.

## Consequences

- Code may use Python 3.13 language features but not require Python 3.14.
- CI must retain distinct minimum/latest pins; a floating dependency is not a
  compatibility test.
- Raising the floor before 1.0 requires evidence and an ADR update.
