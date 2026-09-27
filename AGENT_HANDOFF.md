# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS.

P6.1 — database/config/content migrations and recovery — is qualified PASS at
`38656cc`.

P6.2 — backup hooks, unload/reload and uninstall/recovery UX — has an
implementation candidate. Final qualification is intentionally pending.

## P6.2 implementation

- existing state databases are validated through a read-only SQLite connection
  before any writer/journal mutation is allowed;
- integrity or foreign-key failure prevents runtime startup and creates the
  focused `state_integrity_failure` Home Assistant Repair;
- HA pre-backup holds the write gate, checkpoints WAL and atomically publishes a
  validated `Connection.backup()` snapshot at
  `.storage/locklearn/snapshots/ha-backup-latest.db`;
- backup preparation releases its write gate on all exceptions/cancellation;
- the 10-second HA backup-hook timeout remains in `backup.py`;
- HA 2025.2 cannot safely exclude LockLearn's per-integration content cache, so
  the Options Flow reports that policy honestly instead of claiming exclusion;
- Options Flow surfaces state/cache/asset/recovery sizes and provides explicit
  content-cache purge/rebuild;
- cache purge and snapshot recovery unload the Config Entry before touching
  files, then set it up again;
- recovery validates the snapshot and replacement candidate, quarantines the
  current DB/WAL/SHM first, then atomically publishes the restored DB;
- recovery retention is bounded: one HA backup snapshot, three migration
  snapshots, two pre-recovery quarantines;
- Config Entry Options persist one explicit uninstall policy:
  `keep_user_data`, `delete_user_state`, `delete_content_cache` or
  `delete_everything`;
- default/unknown uninstall policy preserves user data;
- `async_remove_entry` performs only the persisted deletion choice;
- no P6.3 diagnostics catalogue or P6.4 personal-data export/delete work is
  included.

ADR-0047 records the lifecycle/recovery/uninstall decision and ADR-0004 remains
the source for the HA 2025.2 backup-exclusion limitation.

## P6.2 test coverage added

- coherent HA recovery snapshot with persisted sentinel state;
- corrupt live state rejected before writer mutation;
- explicit recovery restores the snapshot and quarantines the corrupt live copy;
- all four uninstall policies delete only their selected roots;
- storage-size/backup-policy reporting;
- Config Entry Options persist the uninstall policy;
- explicit cache purge runs offline before setup/rebuild;
- integrity failure creates a persistent Repair without a runtime;
- HA remove hook applies the selected cache-only policy.

## Verification state

The final P6.2 gate has **not** been run by design. The implementation was
prepared without the full test matrix so Luna can perform final qualification.

Recommended targeted gate:

```text
python3 -m pytest -q --tb=short \
  tests/backend/test_storage.py \
  tests/backend/test_storage_lifecycle.py \
  tests/backend/test_lifecycle.py \
  tests/backend/test_config_flow.py \
  tests/backend/test_state_foundation.py
```

Then run:

```text
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy custom_components datasets tests
python3 datasets/tools/validate_resources.py
python3 -m pytest -q --tb=short
```

No frontend source file is changed by P6.2. Frontend build/tests are not
required unless qualification changes frontend code.
