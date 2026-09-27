# Migrations

LockLearn has distinct migration families. They must never be conflated.

## Home Assistant Config Entry

Config Entry version is declared in `const.py`. HA migration updates integration
configuration only; it is not a database migration.

## state.db

`state.db` is private mutable user state. Released schema changes use sequential
migrations with a coherent pre-migration backup, candidate validation and explicit
recovery behavior.

Current schema version is declared by `DB_SCHEMA_VERSION`.

Important historical migrations include the Profile/Track foundation, leech state,
scheduler/receptivity changes and later lifecycle/recovery metadata. Tests cover
old-supported schema -> current and failure recovery.

## content generation/catalog schema

Generated `content.db` is reconstructible. Schema evolution is handled by building
a new immutable generation and atomically activating it after validation. Runtime
does not mutate the active generation in place.

Current content schema is `CONTENT_SCHEMA_VERSION`; supported historical package
versions are explicitly declared in `SUPPORTED_CONTENT_SCHEMA_VERSIONS`.

## Dataset package/content schema

Signed packages declare schema compatibility in their manifest. Package validation
occurs before content generation build. Unsupported or invalid package schema never
replaces last-known-good active content.

## Recovery

Migration/build/activation failure must preserve a usable prior copy where one
exists and surface Repairs/diagnostics. Never downgrade by deleting or manually
rewriting user state.

The technical sources of truth are migration code/tests and
`custom_components/locklearn/storage/schema.py`. Generated schema contracts live
under `docs/generated/`.
