# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS.

P6.1 — database/config/content migrations and recovery — PASS.

P6.2 — backup hooks, unload/reload and uninstall/recovery UX — PASS.

P6.3 — Repairs and diagnostics — PASS at `aadab0b` and pushed before P6.4
started.

P6.4 — secure export/import and data deletion — has an implementation
candidate. Final qualification is intentionally pending.

## P6.4 implementation

### Private export/import

- new `profile_transfer.py` implements Profile export schema v1;
- private transfers live under the OS temporary directory, outside HA config,
  LockLearn static paths and normal backup roots;
- temp directory/file modes are 0700/0600;
- runtime startup wipes abandoned transfer files, runs TTL cleanup, and unload
  removes the private transfer root;
- export tokens are random, authenticated-user-bound, five-minute, one-shot
  capabilities;
- export download is an authenticated HA HTTP route with `no-store`;
- import upload is authenticated, size-bounded and user-bound for fifteen
  minutes;
- export/apply use the existing cancellable OperationRegistry;
- import dry-run validates without mutating state;
- archive manifest contains exact member size + SHA-256.

Hostile import validation rejects traversal/absolute/backslash/NUL paths,
directories, links/special files, encryption, unsupported compression,
unexpected members, duplicates/casefold collisions, oversized members/archive,
excessive expansion, membership mismatch, size/hash mismatch and unsupported
Profile preset/timezone/settings.

Import always remaps Profile/Track/Session IDs, creates the importing HA user as
the sole owner, strips source ACL/notification targets/scheduler target IDs, and
creates the Profile and Tracks archived. Missing PackVersions remain unbound;
missing cards remain progress tombstones.

### Profile deletion

- existing `profiles/delete` defaults to safe archive for older clients;
- archive pauses active sessions, cancels future slots and clears pending
  notification interactions while preserving history/statistics;
- permanent delete requires owner ACL plus exact `DELETE <profile_id>`;
- deletion cascade removes Profile-scoped user state;
- ProfileService performs the private-export cleanup callback after permanent
  deletion, so the cleanup invariant is not WebSocket-specific;
- frontend now separates Archive Profile from Delete permanently and requires
  the exact confirmation phrase.

### Content tombstones

Content generation activation/rollback now reconciles
`progress.content_status` against the active card lifecycle. Removed/absent
content becomes `removed`, superseded remains `superseded`, and restored
stable identities become `active`. Rows/history are preserved.

ADR-0049 records the transfer/deletion/tombstone design.

No P6.5 entity/sensor implementation and no P6.6 general threat-test expansion
is included.

## P6.4 test coverage added/updated

- export/import round-trip with new identity mapping;
- one-shot owner-bound private export capability;
- dry-run counts/missing-content mapping;
- missing-card tombstone preservation;
- Track rules/weights and review/session history round-trip;
- hostile ZIP traversal rejection and import owner mismatch;
- archive quiescence;
- permanent deletion strong confirmation and personal-data cascade;
- WebSocket permanent-delete contract;
- content generation removed -> rollback-active progress tombstone
  reconciliation.

## Verification state

The final P6.4 gate has **not** been run by design.

Recommended targeted backend gate:

```text
.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_profile_transfer.py \
  tests/backend/test_profiles.py \
  tests/backend/test_websocket_crud.py \
  tests/backend/test_content_generations.py \
  tests/backend/test_lifecycle.py \
  tests/backend/test_operations.py
```

Then backend full gate:

```text
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy custom_components datasets tests
.venv/bin/python datasets/tools/validate_resources.py
.venv/bin/python -m pytest -q --tb=short
```

P6.4 changes frontend source. Qualification must also run:

```text
cd frontend
npm run typecheck
npm test
npm run build
```

If the build updates the committed HA frontend bundle, include that generated
artifact in the qualification commit after verifying its expected hash/path.

Do not start P6.5 during qualification.
