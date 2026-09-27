# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P6.5 qualification fixes are committed locally (not pushed).

P5 and its real-HA exit gate remain PASS.

P6.1 — database/config/content migrations and recovery — PASS.

P6.2 — backup hooks, unload/reload and uninstall/recovery UX — PASS.

P6.3 — Repairs and diagnostics — PASS.

P6.4 — secure export/import and data deletion — PASS at `8f1a0ab` and pushed
before P6.5 started.

P6.5 — HA entity/sensor privacy contract and optional integration boundary —
PASS after review and qualification on 2026-09-27.

## P6.5 implementation

P6.5 deliberately does **not** add `sensor.py` or forward
`Platform.SENSOR`. LockLearn 1.0 may therefore ship no optional private
learning sensors and still satisfy the V1 spec.

A new executable `ha_entity_contract.py` defines the rules any future optional
learning sensor implementation must obey:

- Track-scoped stable unique IDs use canonical Track UUID +
  `:<metric_key>`;
- Profile UUID defines the logical LockLearn Device identifier;
- HA display names/entity IDs never participate in stable identity;
- every optional learning sensor is disabled by default;
- exposure requires explicit double opt-in in Profile and Track settings;
- Track opt-in names an allowlist of known metric keys; unknown metrics fail
  closed;
- ACL membership, HA-admin status or dashboard visibility never imply sensor
  consent;
- metrics are aggregate-only;
- default extra-state attributes are empty;
- minimum publish/debounce interval is five minutes;
- Recorder guidance is explicit per metric;
- only mastery, quiz accuracy and last exam score use
  `SensorStateClass.MEASUREMENT`;
- due/streak/consecutive/session/daily-goal snapshot counters deliberately use
  no `state_class`;
- no learning metric uses TOTAL/TOTAL_INCREASING.

The existing dataset `UpdateEntity` platform remains separate: it exposes
public dataset/update/provenance metadata, not private learner state.

`PRIVACY.md` now reflects the shipped P6.4 export boundary and the P6.5
entity/privacy contract.

ADR-0050 records the logical-device, identity, opt-in, Recorder and state-class
decision.

No optional private SensorEntity implementation is included. No P6.6 threat
matrix work is included.

## P6.5 test coverage

New `tests/backend/test_ha_entity_contract.py` verifies:

- 1.0 forwards only `Platform.UPDATE`, not `Platform.SENSOR`;
- every future optional sensor contract is disabled by default,
  aggregate-only, attribute-empty and debounced >= 5 minutes;
- only valid measurement metrics receive `MEASUREMENT`;
- UUID-based identity rejects names/noncanonical UUIDs;
- no content-bearing attribute/key surface is allowed;
- Profile + Track double opt-in is required;
- unknown opt-in metrics fail closed.

`tests/backend/test_dataset_update_entity.py` verifies that the existing public
dataset `UpdateEntity` exposes provenance/update metadata only and remains
separate from private learning state. Review also fixed strict canonical UUID
validation (including uppercase rejection), rejected non-string metric keys,
and aligned the attribute-surface test with the allowed `session_accuracy`
aggregate metric.

## Verification state

The originally requested targeted command could not start because the
referenced `tests/backend/test_dataset_update_entity.py` file was absent. The
missing separation test was added, after which the targeted gate passed:

```text
12 passed in 0.71s
```

Recommended targeted gate:

```text
.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_ha_entity_contract.py \
  tests/backend/test_dataset_update_entity.py \
  tests/backend/test_lifecycle.py
```

Then run:

```text
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy custom_components datasets tests
.venv/bin/python datasets/tools/validate_resources.py
.venv/bin/python -m pytest -q --tb=short
```

P6.5 changes no frontend source and no generated frontend artifact. Do not run
or rebuild frontend unless qualification changes frontend code.

The complete backend gate passed:

```text
275 files already formatted
All checks passed!
Success: no issues found in 159 source files
LockLearn resource registries: OK
440 passed, 1 warning in 21.77s
```

The warning is the expected duplicate ZIP member warning from the hostile
archive test fixture. No P6.6 work was started.

Do not start P6.6 during qualification.
