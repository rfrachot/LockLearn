# ADR-0013 — Immutable content generations and stable merge

## Status

Accepted for P1.6 on 2026-09-22.

## Context

LockLearn keeps reconstructible learning content in `content.db` and user state
in a separate `state.db`. Dataset packages are prebuilt and authenticated by the
P1.2 envelope. Runtime updates must not parse upstream corpora, mutate the
active catalog in place, delete user progress when content disappears, or keep
an arbitrary set of package databases attached.

Replacing a pathname is not by itself a reader-lifecycle policy. An open SQLite
connection may continue to reference the old inode, while new connections may
resolve the new pathname. Activation therefore needs an explicit boundary for
new readers and a drain contract for existing ones.

Stable progression identity is defined by ADR-0008 as the ordered tuple:

```text
(learning_item_id, prompt_facet_id, answer_facet_id)
```

Pack membership, text, tags, grading metadata and dataset versions do not
participate in `card_key` or `card_definition_id`.

## Decision

### Schema and version domains

Package databases and generated catalogs use the same normalized content
tables. A package has no `generation_metadata` row and declares exactly one
dataset package. A complete generation has exactly one immutable metadata row:

```text
generation_id
content_schema_version
built_at_utc
parent_generation_id
package_count
package_set_hash
```

These facts remain distinct from the LockLearn software version, signed
manifest version, dataset version and pack version. `schema_version` is the
content SQLite schema migration boundary. P1.6 establishes content schema v1;
future released changes require sequential migration or an out-of-place
rebuild.

The schema persists the P1.1–P1.5 objects and relations needed now: sources,
datasets and versions, Concepts, Terms, LearningItems, Facets,
CardDefinitions, ContentBlocks, Tags, immutable PackVersions, PackItems,
prerequisites, defaults, confusable groups, explicit stable-ID mappings and
lifecycle records. It deliberately does not introduce the P1.7 provenance
redesign or P1.11 Asset schema.

The generated catalog materializes only selection denominators needed by the
specified hot paths: total active items/cards per PackVersion, plus active item
counts by content type and tag. These are rebuilt and validated for every
generation. Runtime selection never uses `ORDER BY RANDOM()`.

### Out-of-place build and bounded merge

A build starts as a distinct hidden `.building` file. When a previous
generation exists, SQLite's backup API copies it into the work file so stable
identity rows and lifecycle history survive. Every previously active
LearningItem, Facet and CardDefinition is provisionally marked `removed`.

Packages are sorted by dataset ID, validated in read-only immutable mode, and
attached one at a time. `PRAGMA database_list` enforces at most `main` plus one
package; the temporary schema does not count as an attached database. Each
package is detached before the next package is opened. Stable ownership and
card tuple conflicts fail the build. Incoming rows reactivate the same stable
IDs by upsert; they do not allocate replacement identities.

After all packages are merged, current tombstones, lifecycle transitions and
pre-aggregates are rebuilt. The candidate must pass schema/table/index checks,
`integrity_check`, `foreign_key_check`, deterministic card identity validation,
tombstone consistency and aggregate recomputation. Only then is the hidden
work file renamed to the requested `content.next.db` candidate. A partial or
failed build is never an activation candidate.

### Tombstones and reactivation

`learning_items`, `facets` and `card_definitions` carry the current lifecycle:

```text
active | removed | superseded
```

`tombstones` contains the current inactive identity and an explicit replacement
for `superseded`. The full preserved rows remain available for history display
and for application-level references from `state.db`.
`content_lifecycle_history` records lifecycle transitions by generation.

An incoming active row deletes its current tombstone but not its lifecycle
history. Consequently:

```text
active → removed → active
```

reuses the exact LearningItem ID, Facet IDs, `card_definition_id` and
`card_key`. A genuine released-ID correction remains an explicit
`stable_id_migrations` record. P1.6 validates and carries those declarations;
future state-schema work owns transactional application to user-state rows.

No SQL foreign key crosses into `state.db`, and no content lifecycle operation
deletes progress.

### Activation, reader drain and rollback

Generated files live under `content/generations/<generation_id>.db`. Once
activated they are mode `0444` and all runtime opens are read-only. `current.db`
is a hard link to the active generation inode.

Activation follows this order:

1. stop granting new content reader leases;
2. wait for all leases and their real SQLite connections to close;
3. validate the candidate again and require its `parent_generation_id` to
   equal the currently active generation (generation-level CAS);
4. rename it into `generations/`;
5. persist and fsync a small switch-intent journal containing the from/to
   generation IDs;
6. create a temporary hard link to the candidate and atomically
   `os.replace()` that link over `current.db`;
7. persist secondary catalog bookkeeping, clear the switch journal when that
   bookkeeping succeeds, and fsync the relevant directories;
8. reopen the reader gate and retain the old active generation as rollback.

Cancellation of the asyncio caller does not reopen the reader gate while the
executor-side filesystem switch is still running. The switch is allowed to
finish, in-memory active-generation state is reconciled with the committed
inode, and only then is cancellation propagated. HA unload similarly marks the
manager closed and waits for any in-flight switch before shutting down storage
executors.

The reader lease pins the immutable generation path, not `current.db`. Existing
readers therefore finish deterministically on their original file. Readers
arriving during a switch wait and then receive the new active generation.
Cleanup happens only after drain and retains exactly the active and previous
valid generations.

Rollback revalidates the retained previous file and performs the same atomic
hard-link switch. A failed or merely staged generation is never a rollback
candidate.

`catalog.json` records active/previous IDs for restart, but it is not the switch
authority. The validated `current.db` inode is authoritative. A fsynced
`switch-journal.json` exists only across the commit boundary: if the pointer
swap commits but catalog persistence does not, startup accepts the journal only
when its `to_generation_id` matches the generation actually referenced by
`current.db`. This also preserves the rolled-away generation across a crash
during rollback, where the reactivated generation's historical
`parent_generation_id` cannot describe the reverse edge. A mismatched journal
is ignored. Once matching catalog state is durable the journal is removed.

### Failure and crash boundaries

- Failure during package validation/merge affects only the hidden work file.
- Failure before `current.db` replacement leaves the last-known-good active.
- A crash after the candidate enters `generations/` but before pointer replace
  leaves an unreferenced valid file and the old active; a journal targeting a
  different generation than `current.db` is ignored.
- A crash after pointer replace leaves the new complete validated generation
  active; the matching switch journal reconstructs the exact previous
  generation even when the committed operation was a rollback.
- The exact unreleased P0 benchmark schema is recognized as reconstructible
  cache. It is held aside, a fresh P1.6 generation is activated, and it is
  deleted only after success. `state.db` is untouched.

All build, validation, activation and SQLite reader work runs in executors, not
on Home Assistant's event loop.

## Alternatives considered

- Update active `content.db` in place: rejected because readers can observe
  partial logical updates and rollback becomes a reverse migration.
- Replace `current.db` while readers are untracked: rejected because pathname
  replacement does not define which generation a logical request uses.
- Attach every installed package at runtime: rejected because it creates a
  scale-dependent `SQLITE_MAX_ATTACHED` limit, complicates queries and makes a
  coherent generation boundary impossible.
- Copy the candidate directly over `current.db`: rejected because a crash can
  expose a partial file and because the immutable generation would no longer be
  the same inode readers open.
- Delete removed identity rows: rejected because `state.db` and history retain
  stable application-level references.

## Consequences

- Active content is a validated immutable snapshot with a one-step rollback.
- Disk use temporarily includes a build file plus active and previous
  generations; P1.9 will add download/update policy and user-facing storage
  reporting.
- Builds copy the previous catalog before merging. This favors correctness and
  simple failure isolation over minimum write amplification.
- The merge API accepts already-staged package database paths. Signature,
  archive and download orchestration remain P1.2/P1.9 responsibilities.
- Asset bytes remain outside this schema; P1.11 owns their complete metadata
  and serving boundary.
