# LockLearn migrations

`SPEC_V1.md` §72, §73 and §115 are normative. This document describes the current implementation.

LockLearn has four distinct versioned boundaries. They must not be collapsed into one migration mechanism:

1. Home Assistant Config Entry schema.
2. Persistent user state in `state.db`.
3. Reconstructible `content.db` generations and dataset package schema.
4. Stable content-ID mappings carried by dataset data.

## Home Assistant Config Entry

The Config Entry major version is `1`.

`LockLearnConfigFlow.VERSION` and the integration migration boundary share the `CONFIG_ENTRY_VERSION` constant. `async_migrate_entry()` accepts the current version and rejects unknown older or future major versions. There is deliberately no fake historical migration: version `1` is the first and only Config Entry schema so far.

When the Config Entry data shape changes:

1. decide whether the change requires a major or minor Config Entry version according to Home Assistant's migration contract;
2. bump the Config Flow version only with the actual data-shape change;
3. implement the explicit old -> new transformation with `hass.config_entries.async_update_entry()`;
4. add tests for every supported source version;
5. never use a Config Entry migration to mutate `state.db` or content data.

## `state.db`

`state.db` is persistent user state and is not reconstructible from datasets.

Current schema version: `5`.

Historical path:

| Source | Target | Purpose |
|---|---|---|
| 1 | 2 | Bridge the released P0/0.0.2 minimal state shape into the full application state schema. |
| 2 | 3 | Add the `leech` progress state. |
| 3 | 4 | Add scheduler deferral and receptivity state. |
| 4 | 5 | Add send-time notification-selection metadata. |

Migrations are registered as exact sequential steps. Opening a database at `N` runs `N -> N+1 -> ... -> current`; missing steps fail explicitly. A future schema version is never downgraded.

Before the first migration step, LockLearn:

1. checkpoints the WAL;
2. creates a coherent snapshot with `sqlite3.Connection.backup()`;
3. validates the snapshot;
4. atomically publishes it as `state.db.pre-migration-vN.bak`.

The previous recovery snapshot is not destroyed until the replacement snapshot has been created and validated.

Each in-place step runs inside `BEGIN IMMEDIATE`, updates `schema_version` in the same transaction and validates SQLite integrity/foreign keys before commit. The v1 -> v2 bridge is special: it builds a candidate database out of place, copies the released v1 rows, then atomically replaces `state.db`.

If a later step fails, completed earlier steps may remain committed, but the failing step is rolled back and the original pre-migration snapshot remains available. A later startup can continue deterministically from the last committed schema version. Repairs/recovery UX for surfacing and restoring that snapshot belongs to P6.2/P6.3, not to the migration engine itself.

A database claiming the current version is validated, not silently repaired by running `CREATE ... IF NOT EXISTS`. Released schema changes therefore require a version bump and an explicit migration.

## Content generations and dataset packages

Content is reconstructible and follows a different rule.

LockLearn does **not** migrate downloaded dataset SQLite packages in place. Supported package schema versions are validated as immutable inputs. The runtime builds a fresh `content.next.db`, validates it, drains old readers and atomically activates the new generation. The previous generation is retained by the content-generation lifecycle for rollback.

Current content schema version: `2`.

Supported package/content schema versions are defined by `SUPPORTED_CONTENT_SCHEMA_VERSIONS`. Support for an older package schema means “read and merge it into a new current generation”, not “rewrite the package”.

Raw upstream corpora are never parsed as part of this runtime migration path.

## Stable content IDs

`stable_id_migrations` belongs to dataset/content semantics. It maps released LearningItem/Facet/CardDefinition/card-key identities when a content update legitimately changes stable IDs. It is validated while building a new content generation.

It is not a `state.db` schema migration and must never be used as one.

## Recovery rules

- Never copy an active WAL-backed `state.db` with a raw filesystem copy.
- Never overwrite the only recovery copy before a replacement snapshot validates.
- Never downgrade a future state schema or Config Entry version.
- Never mutate a released state schema without increasing `DB_SCHEMA_VERSION`.
- Never migrate an official dataset package in place.
- Keep state-schema recovery and content-generation rollback independent.

## Adding a new `state.db` migration

For `N -> N+1`:

1. update `STATE_SCHEMA` to the target shape;
2. increment `DB_SCHEMA_VERSION`;
3. add exactly one migration function and register it at key `N`;
4. keep the schema/version mutation in one transaction whenever the migration is in place;
5. preserve all existing user rows or document an explicit, reviewed transformation;
6. update the required table/index contract when structural objects change;
7. add a historical `N -> current` fixture with sentinel data;
8. add failure/rollback coverage if the step has non-trivial mutation;
9. update this document and any affected ADR;
10. run the DB migration tests plus the full project gates before release.

Do not renumber or rewrite a schema version that has already shipped.
