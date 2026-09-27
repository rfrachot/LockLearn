# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS. P6.1 through P6.9 are PASS.

P6.10 — release packaging, versioning and HACS readiness — is implementation
complete and requires independent qualification. P6.11 has not started.

## P6.10 implementation

- Runtime release candidate bumped to `1.0.0` in both Home Assistant manifest and
  `INTEGRATION_VERSION`.
- HACS support floor deliberately remains `2025.2.0`; the minimum tested patch remains
  HA `2025.2.5`, with current harness `2026.9.3` and latest-stable smoke `2026.9.4`.
- The private npm frontend package version is explicitly non-authoritative; the shipped
  frontend is identified by integration version plus bundle hash.
- `scripts/p6_10_release_smoke.py` validates a HACS-like isolated copy containing only
  `custom_components/locklearn/`, checks runtime imports/resources, the signed bundled
  starter, frontend artifact and absence of private-key material.
- `tests/backend/test_p6_10_release_readiness.py` anchors the upgrade smoke to the exact
  state schema shipped by real GitHub release `v0.0.2` and verifies migration to the
  current schema without loss of legacy session/progress/audit rows.
- CI runs the P6.10 payload smoke in backend quality, minimum/current HA matrix lanes
  and the latest-stable HA smoke. HACS/hassfest remain release gates.
- `RELEASE.md` now defines the SemVer authority, HACS payload boundary, v0.0.2 upgrade
  floor, preflight, publication and rollback procedures.

No tag, GitHub Release, PR, merge or P6.11 work is part of this implementation.

## Independent qualification

Run targeted P6.10 tests and payload smoke first, then the full P6.9/P6.8/backend/
frontend/Playwright gates. GitHub Actions must remain green for backend, datasets,
frontend, minimum/current/latest HA and HACS/hassfest.

P6.10 becomes PASS only after that independent qualification. Then the next work is:

`P6.11 — V1 end-to-end acceptance scenarios`.
