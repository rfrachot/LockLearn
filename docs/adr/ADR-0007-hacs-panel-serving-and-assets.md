# ADR-0007 — HACS panel serving and asset isolation

## Status

Accepted after P0.7 real-instance qualification on 2026-09-21.

## Context

The LockLearn panel must install through the normal HACS custom-integration
path, work without a runtime CDN, update without stale browser code and unload
without leaving duplicate HA registrations.

## Decision

- Ship the compiled panel inside `custom_components/locklearn/frontend` in each
  release artifact.
- Serve that directory through HA's authenticated/runtime static-path API and
  register one non-iframe custom panel.
- Use the integration release version plus the committed bundle SHA-256 prefix as the module URL cache-buster.
- Keep the frontend/HA WebSocket protocol explicit and independently versioned.
- Register immutable process-wide commands/static paths once; register and
  remove the mutable panel per loaded Config Entry.
- Use no runtime CDN or third-party HTML. Future media/assets follow the same
  local, versioned and allowlisted boundary.
- Use HACS only for published tags/releases. Development branches deploy the
  complete `custom_components/locklearn/` tree directly to the development
  instance so backend and frontend remain on the same revision.

## Evidence

HACS installed `v0.0.1` from the public custom repository and upgraded it to
`v0.0.2`. Config Flow enforced one entry. The bundled JavaScript loaded with a
matching hash, the panel disappeared on unload and returned on reload, an old
subscription did not survive reload, and a forced browser refresh rendered the
panel at `/locklearn_static/locklearn-panel.js?v=0.0.2`. The panel and protocol
also returned after a real HAOS restore.

## Consequences

- Every user-visible frontend change requires a rebuilt committed artifact; formal releases also bump the integration release version.
- Reliance on HA frontend internals stays isolated in the panel integration
  boundary and remains part of the compatibility matrix.
- HACS installation/update is the release qualification path; direct deployment
  is reserved for development branches and must never be a frontend-only copy.
- HACS “Redownload” must not restore an older public release over a development
  instance whose `state.db` already uses a newer schema. The database is not
  downgraded or rewritten to accommodate old code.
