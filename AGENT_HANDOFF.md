# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS. P6.1 through P6.8 are PASS.

P6.9 — documentation set and generated contracts — is implementation complete
and final qualification is pending. P6.10 has not started.

## P6.9 implementation

Human reference docs now exist for the SPEC §102–127 set, including:

- README/user entry point;
- architecture and data model;
- database and migration policy;
- pack/dataset/source/licensing contracts;
- permissions/privacy/security;
- SRS, scheduler and notifications;
- frontend and WebSocket API;
- development, testing, release and troubleshooting;
- roadmap.

Existing detailed documents were preserved where stronger than the new overview
(e.g. MIGRATIONS.md history).

Generated contracts:

- `scripts/generate_docs_contracts.py`;
- `docs/generated/STATE_DB.md`;
- `docs/generated/CONTENT_DB.md`;
- `docs/generated/WEBSOCKET_CONTRACTS.md`;
- `docs/generated/websocket-contracts.json`.

The generator reads runtime DDL/WebSocket sources and has a `--check` mode wired
into CI. `tests/backend/test_p6_9_documentation_contracts.py` gates the required
documentation set/sections. ADR-0053 defines the documentation source-of-truth
layers.

Official source documentation is now derived from the machine registries and
covers provider, format, adapter, licence/attribution, imported/excluded fields,
known risks and refresh policy.

README screenshots represent real rendered UI. The deterministic Playwright
capture test lives at `frontend/e2e/tests/docs-screenshot.spec.ts`. Its canonical
output is committed at `docs/assets/locklearn-home.png` and referenced by README;
the normal frontend-e2e CI job also uploads the full-resolution capture artifact.

Do not mark P6.9 PASS until all local/CI documentation gates are green.

## Next qualification work

1. run Ruff/lint/mypy, generated-doc check, P6.9 tests, full pytest, frontend
   lint/typecheck/Vitest/E2E/build and git diff check;
2. verify the committed screenshot and README reference;
3. run CI and verify every existing P6.8 job remains green plus the new generated
   documentation/P6.9 gates.

Known non-blocking warnings remain the duplicate `profile.json` test fixture and
GitHub's future ubuntu-latest migration notice.

Do not start P6.10 until P6.9 is PASS.
