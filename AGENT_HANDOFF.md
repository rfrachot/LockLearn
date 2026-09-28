# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS. P6.1 through P6.10 are PASS.

P6.10 was independently qualified after the privacy-preserving history rewrite on
HEAD `93ca19eea3b9e9347fc6f4cd15afe30e3575b49b`. GitHub Actions run
`36474980367` passed every required backend/dataset/frontend/HA/HACS gate.

P6.11 — final V1 end-to-end acceptance — is implementation complete and requires
independent qualification. No 1.0 tag or GitHub Release has been created.

## P6.11 implementation

- `docs/P6_11_ACCEPTANCE.md` maps every §129 mandatory capability, all 32 §133
  invariants, all §135 Adrien/Camille/Zoé steps and the five resilience scenarios
  to permanent AUTO/E2E/REAL-HA/CI evidence.
- `tests/backend/test_p6_11_v1_acceptance.py` exercises a fresh real bundled
  starter through public WebSocket APIs: Profile, scheduler window, Pack/Dataset,
  Track, 20-card Learn session, cross-client resume, dashboard and stats.
- `tests/backend/test_p6_11_acceptance_contracts.py` gates the evidence IDs,
  critical test nodeids, real-HA evidence and explicit V1.1/V2 non-blockers.
- CI has a dedicated `P6.11 V1 acceptance` backend-quality step; the normal full
  Python, HA compatibility, frontend/Playwright, HACS and hassfest jobs remain the
  authoritative release matrix.

## Independent qualification

Do not modify code during qualification. Run the targeted P6.11 tests first, then
all existing backend/dataset/frontend/Playwright/release gates and the full GitHub
Actions matrix. Verify that the acceptance documentation actually supports every
§129/§133/§135 claim and that no V1.1/V2 feature has slipped into the 1.0 gate.

P6 becomes PASS only after this independent qualification. If PASS, the next action
is the final documented 1.0 publication sequence; do not publish/tag as part of the
qualification itself.
