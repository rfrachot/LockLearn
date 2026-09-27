# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS. P6.1 through P6.7 are PASS.

P6.8 — full test matrix and CI release gates — is implementation complete and
qualification-pending. No P6.9 implementation has started.

## P6.8 implementation

### Permanent access-contract gates

`tests/backend/test_p6_8_release_contracts.py` classifies all 56 registered
WebSocket commands into exactly one access boundary:

- authenticated/global;
- owner-bound import capability;
- Profile ACL;
- Track -> Profile ACL;
- Session -> Profile ACL;
- Home Assistant administrator;
- owner-bound long operation.

The test fails if a future command is unclassified or if a protected command
loses its expected backend guard.

`tests/backend/test_p6_8_acl_matrix.py` performs real negative WebSocket calls
for outsider, viewer and non-admin users across protected Profile/Track/Session,
dataset-admin, import-capability and operation endpoints.

The same release-contract suite scans critical `core/` domain logic and
rejects direct wall-clock calls outside `core/clock.py`.

### Dataset and frontend release gates

New `datasets/tools/validate_schemas.py` validates every committed JSON Schema
and each mapped committed registry/config instance.

Dataset CI explicitly gates resource/licence policy, provenance/signature/
archive contracts, bundled starter/assets/SVG and canonical-content
reproducibility.

Frontend CI now has an explicit source lint in addition to typecheck, Vitest,
no-polling/direct-network audit, build, gzip budget, committed-bundle diff and
Playwright E2E.

### Home Assistant compatibility

The historical matrix previously named HA versions but did not explicitly
install/verify the matrix HA package. P6.8 fixes this.

Full backend integration suites:
- minimum supported: HA 2025.2.5 + matching harness 0.13.215;
- current upstream harness: HA 2026.9.3 + harness 0.13.366.

HA 2026.9.4 was published on 2026-09-27 after harness 0.13.366, which explicitly
pins HA 2026.9.3. Until a matching harness is published, CI additionally runs
`scripts/p6_8_ha_smoke.py` against real HA 2026.9.4. Do not falsely label
2026.9.3 as latest stable.

HACS and hassfest remain mandatory CI jobs.

## Qualification — Luna executes only

Luna must not edit, format, commit, push, merge or start P6.9.

Run from the qualification worktree after pulling `feat/p6-hardening`:

~~~bash
git pull --ff-only origin feat/p6-hardening
git status --short --branch
git rev-parse HEAD

.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy custom_components datasets tests

.venv/bin/python datasets/tools/validate_resources.py
.venv/bin/python datasets/tools/validate_schemas.py

.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_p6_8_release_contracts.py \
  tests/backend/test_p6_8_acl_matrix.py

.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_state_foundation.py \
  tests/backend/test_lifecycle.py \
  tests/backend/test_storage_lifecycle.py

.venv/bin/python -m pytest -q --tb=short

.venv/bin/python scripts/p5_9_performance.py
.venv/bin/python scripts/p6_7_scale_validation.py

cd frontend
npm run lint
npm run typecheck
npm test
npm run check:no-polling
npm run build
npm run check:bundle
npm run test:e2e
cd ..

sha256sum custom_components/locklearn/frontend/locklearn-panel.js
git diff --check
git status --short --branch
git rev-parse HEAD
~~~

The local VM does not replace GitHub-hosted HACS/hassfest or the compatibility
matrix. After local gates are green, the branch must be exercised through the
CI workflow so these jobs are evidenced:

- backend-quality;
- dataset-contracts;
- HA minimum 2025.2.5;
- HA current-harness 2026.9.3;
- HA latest-stable 2026.9.4 smoke;
- frontend;
- frontend-e2e;
- home-assistant-validation (hassfest + HACS).

P6.8 remains pending until both local and GitHub-hosted gates are reviewed.
