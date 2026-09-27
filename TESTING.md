# Testing

LockLearn uses a layered test pyramid with deterministic domain tests at the base
and real HA/browser compatibility gates at the top.

## Backend/unit/integration

```bash
python -m pytest -q --tb=short
```

Tests cover domain policies, repositories/SQLite, WebSocket ACL, migrations,
dataset packages, scheduler/notifications, sessions/SRS and HA integration.

Time-sensitive tests inject fake/fixed Clock implementations rather than relying
on wall time.

## Database tests

Temporary SQLite databases use the real schemas/migrations. Integrity, FK and
cross-domain validation are explicit. P6.7 additionally materializes five years
of representative state and a 60k-card content generation.

## Dataset tests

Resource registries, JSON schemas, signatures, provenance/licensing, hostile ZIP,
assets/SVG and reproducibility are CI-gated.

## Frontend

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

Vitest covers pure/frontend component contracts; Playwright exercises the compiled
panel shell/routes, keyboard focus and real browser rendering against a deterministic
HA WebSocket harness.

## ACL/security contracts

P6.8 classifies every WebSocket endpoint and runs negative outsider/viewer/admin/
owner-bound cases. Security tests cover rich text/SVG, archive extraction, SQL
filters, replay/private assets and diagnostics redaction.

## Performance

Normative wall-clock budgets are qualified on documented P6.7 reference hardware:

- session answer p95 < 100 ms;
- next-card p95 < 150 ms;
- scheduler slot generation < 250 ms/Profile/day.

GitHub-hosted runners execute the same hot paths as telemetry but are not normative
performance hardware.

## CI

`.github/workflows/ci.yml` gates:

- backend format/lint/types/tests;
- generated/resource/schema contracts;
- dataset policy/reproducibility;
- HA minimum/current/latest smoke;
- frontend + E2E;
- hassfest + HACS.

## Generated-doc drift

`python scripts/generate_docs_contracts.py --check` must pass so database/API
reference docs cannot silently drift from runtime source.
