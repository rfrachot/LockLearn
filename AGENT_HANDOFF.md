# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS.

P6.1 — database/config/content migrations and recovery — is implemented and
qualified PASS. The local qualification commit is at `HEAD` and has not been
pushed.

No P6.2+ implementation is included.

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

All P6.1 verification gates pass in the repository `.venv` (Python 3.14.4,
Home Assistant 2026.9.3):

```text
targeted pytest: 37 passed in 1.81s
ruff format --check: 261 files already formatted
ruff check: All checks passed!
mypy: Success: no issues found in 149 source files
resource validation: LockLearn resource registries: OK
full pytest: 399 passed in 22.46s
```

The only corrections required during qualification were Ruff formatting in the
P6.1 implementation/tests and one import-order fix in `config_flow.py`; no
behavioral migration defect was found. No frontend code changed, so frontend
rebuild/tests were not required for this P6.1 validation.
