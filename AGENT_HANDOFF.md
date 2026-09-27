# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS.

P6.1 — database/config/content migrations and recovery — PASS.

P6.2 — backup hooks, unload/reload and uninstall/recovery UX — PASS at
`2e2cbfd` and pushed before P6.3 started.

P6.3 — Repairs and diagnostics — PASS, qualified locally at final commit.

## P6.3 implementation

Minimum V1 Repair catalogue is now covered:

- dataset obsolete: existing `dataset_sources_stale`;
- notification target unresolved: existing
  `notification_target_unavailable` for missing, disabled, mismatched or
  unroutable targets;
- scheduler infeasible: existing
  `scheduler_configuration_infeasible`;
- DB integrity failure: P6.2 `state_integrity_failure`;
- migration failure: new `state_migration_failure`;
- invalid dataset signing key/signature: new
  `dataset_signature_invalid`;
- reconstructible cache unexpectedly present under persistent state:
  `backup_cache_anomaly`.

Dataset trust failures are separated from generic installation failures:
`TrustError` creates the signature-specific Repair; other install failures
remain `dataset_install_failed`. Success clears both variants.

A new Home Assistant `diagnostics.py` config-entry diagnostic surface emits
only:

- LockLearn/HA/config/schema versions;
- aggregate SQLite health/migration status;
- aggregate Profile/dataset/pack counts;
- aggregate dataset state/error categories;
- aggregate scheduler listener/routine counts;
- storage byte counts and backup policy;
- active Repair categories/counts.

It intentionally excludes identifiers, Profile names, target names, learned
content, card keys, answers, annotations, notification contents, private stats,
URLs, Repair placeholders and raw exception messages.

`async_redacted_diagnostic_status()` is separate from older internal/session
diagnostics so support output cannot accidentally inherit detailed session
fields.

ADR-0048 records the Repairs/diagnostics privacy boundary.

No P6.4 export/import/data-deletion implementation and no P6.5 sensor/entity
work is included.

## P6.3 test coverage added/updated

- diagnostics privacy regression seeds private Profile/content/answer/target
  sentinel values and asserts none appear in serialized diagnostics;
- migration startup failure creates the dedicated migration Repair without a
  runtime;
- unexpected cache bytes under persistent state create the backup-cache warning;
- invalid Ed25519 trust/signature failures create the signature Repair rather
  than the generic install Repair;
- dataset diagnostics expose only aggregate error categories.
- missing notification targets create the target-unavailable Repair.

## Verification state

Final P6.3 qualification completed successfully.

Recommended targeted gate:

```text
.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_diagnostics.py \
  tests/backend/test_lifecycle.py \
  tests/backend/test_storage.py \
  tests/backend/test_storage_lifecycle.py \
  tests/backend/test_scheduler.py \
  tests/backend/test_notification_delivery.py \
  tests/datasets/test_dataset_manager.py
```

Then run:

```text
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy custom_components datasets tests
.venv/bin/python datasets/tools/validate_resources.py
.venv/bin/python -m pytest -q --tb=short
```

No frontend source is changed by P6.3. Frontend tests/build are unnecessary
unless qualification changes frontend code.

Qualification result:

- targeted P6.3 tests: 59 passed;
- full gate: Ruff format/check, mypy, resource validation and 418 backend tests
  passed;
- no frontend changes;
- local commits only, no push.

Next concrete action: begin P6.4 only after an explicit mission request.
