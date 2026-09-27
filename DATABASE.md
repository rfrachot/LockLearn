# Database contract

LockLearn uses SQLite for runtime persistence with two deliberately separate
databases.

## state.db

Private mutable state: Profiles, membership, Tracks, notification targets,
Progress, ReviewEvents, sessions, scheduler state, interactions, annotations,
stats, settings and audit/recovery metadata.

Source of truth: `STATE_SCHEMA` in
`custom_components/locklearn/storage/schema.py`.

Generated DDL, indexes and ER relationships:
`docs/generated/STATE_DB.md`.

## content.db

Immutable generated public/reconstructible content: datasets, source snapshots,
licenses/provenance, Concepts, Terms, LearningItems, Facets, CardDefinitions,
ContentBlocks, Assets, Packs/PackVersions, lifecycle history and pre-aggregates.

Source of truth: `CONTENT_SCHEMA` in the same schema module.

Generated DDL, indexes and ER relationships:
`docs/generated/CONTENT_DB.md`.

## Separation invariant

`state.db` and active `content.db` are never collapsed into one database.
Cross-database references such as `card_key` and `pack_version_id` are checked
by application integrity code because SQLite cannot enforce a durable FK across
an independently replaceable content generation.

## Access model

- no blocking SQLite I/O on the Home Assistant event loop;
- one serialized writer path;
- thread-confined/separate readers;
- transactions around atomic state mutations;
- WAL is checkpointed/cohered before backup snapshots.

## Index policy

Hot paths have explicit indexes (for example due Progress, review history,
Profile membership and content normalized lookup). Required index sets are tested.
Generated contracts show the current exact list.

## Constraints

Schemas use PK/FK/UNIQUE/CHECK constraints for supported enums, non-negative
counters, lifecycle consistency and stable relationships. Application validation
adds cross-database, ACL and immutable-generation invariants.

## Migration policy

Released schema changes require explicit sequential migrations. Config Entry,
state DB and content/package schemas are distinct migration families.

A state migration is built/recovered transactionally with a coherent pre-migration
backup. Migration failure must not silently corrupt the only state copy.

See `MIGRATIONS.md`.

## Backup/recovery

Backup hooks quiesce/checkpoint SQLite rather than copying an active WAL state.
Reconstructible content cache can be excluded/rebuilt; user state is preserved
unless the user explicitly chooses a destructive uninstall/recovery action.

See `MIGRATIONS.md`, `SECURITY.md` and P6 lifecycle ADRs.
