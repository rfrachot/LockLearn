# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

Base: `955998b5ed676fc0da8d5bb81c2a2499ba4a50dc` (`docs(qualify): close P5.9 real HA gate`).

P5 and its real-HA exit gate remain PASS.

P6.1 — Database/config/content migrations and recovery — has an implementation candidate. Final qualification is intentionally pending so the full verification can be run separately.

## P6.1 implementation

- state migrations are now an explicit sequential registry: v1 -> v2 -> v3 -> v4 -> v5;
- a pre-migration recovery snapshot is created with `Connection.backup()`, validated, then atomically published without deleting the previous snapshot first;
- in-place steps mutate schema + `schema_version` in one transaction and validate integrity/foreign keys before commit;
- current-version state DBs are structurally validated instead of being silently repaired by rerunning `CREATE ... IF NOT EXISTS`;
- future/malformed state schema versions fail explicitly;
- `StateMigrationError` exposes the recovery snapshot path for later Repairs/recovery UX;
- Config Entry versioning now has a separate `async_migrate_entry()` boundary without an artificial version bump;
- content packages remain immutable inputs rebuilt into a new current content generation;
- `MIGRATIONS.md` documents the four separate migration/versioning domains.

## Added/updated tests

- historical state fixtures v1/v2/v3/v4 -> current;
- future/current-malformed state refusal;
- injected mid-chain failure: rollback, original backup integrity, preserved sentinel data, and deterministic retry;
- Config Entry current/legacy/future boundary;
- legacy content-schema package merged into a current generation without package mutation.

## Verification state

The full final gate has **not** been run in this handoff by design.

Recommended final verification:

```text
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy custom_components datasets tests
python3 datasets/tools/validate_resources.py
python3 -m pytest -q --tb=short
```

Run targeted migration/config/content tests first if a fast failure signal is wanted.

No frontend code changed, so frontend rebuild/tests are not expected to be necessary for P6.1 unless the final reviewer chooses to rerun the complete release matrix.

No P6.2+ implementation is included.
