# ADR-0019 — state.db v2 foundation, repositories and cross-domain references

## Status

Accepted for P2.1 on 2026-09-22.

## Context

P0 shipped a deliberately tiny persistent state schema for storage/session spikes.
P2 requires the durable V1 state boundary before Profile, ACL, Track, SRS,
scheduler and notification behavior can be implemented.

`state.db` must remain independently persistent while `content.db` generations
are reconstructible and replaceable. SQLite cannot enforce foreign keys across
those physical database boundaries.

Existing P0 installations may already contain session, session-answer, progress
and audit rows, so the schema transition must preserve them.

## Decision

### State schema v2 is the V1 persistence skeleton

Schema v2 creates the tables reserved by §69:

- profiles and profile_members;
- tracks, track_pack_versions, track_card_rules and track_content_weights;
- notification_targets;
- progress and review_events;
- user_annotations;
- sessions, session_items and session_answers;
- exam_attempts;
- scheduler_config and scheduled_slots;
- notification_interactions;
- stats_daily;
- settings;
- the existing privacy-minimal audit_events table.

The schema includes the required hot-query indexes for due cards, review history,
scheduled slots, notification interactions and session resume.

P2.1 defines storage shape and repository primitives only. P2.2–P2.6 own the
business rules, ACL decisions, Track configuration UX and public CRUD APIs.

### Progress remains lazy

No Profile or Track creation path pre-seeds progress rows.

`ProgressRepository.async_create_if_absent()` is the explicit materialization
boundary used by future exposure/review mutations. It validates the exact active
CardDefinition identity and inserts one row only when the card is first needed.

This preserves the §69 anti-join model for discovering new cards.

### Cross-domain integrity is application-enforced

There are deliberately no SQLite foreign keys from state tables into
`content.db`.

Repositories validate new references against the active content generation:

- Track PackVersion pinning validates `pack_version_id`;
- progress materialization validates the full tuple
  `card_key + learning_item_id + prompt_facet_id + answer_facet_id`.

`async_cross_domain_integrity_issues()` audits existing state references in:

- track_pack_versions;
- progress;
- review_events;
- session_items.

This catches stale/corrupt state after dataset-generation changes without making
state lifecycle depend on attached-content SQL foreign keys.

### Application repositories are the state access boundary

P2.1 introduces repositories for:

- Profile persistence;
- Track persistence and explicit PackVersion pinning;
- lazy Progress materialization;
- deterministic JSON settings.

They intentionally expose persistence primitives, not P2.2/P2.3 policy.
Existing P0 SessionService remains compatible and can be migrated to a dedicated
repository later without changing its storage contract.

### v1 → v2 migration is out-of-place

State schema migration does not issue a chain of destructive ALTER statements
against the live database.

Before migration:

1. checkpoint WAL;
2. create a coherent SQLite backup with `Connection.backup()`;
3. retain it as `state.db.pre-migration-v1.bak`.

Then LockLearn:

1. creates a separate v2 candidate database;
2. initializes the complete v2 schema;
3. copies compatible v1 P0 rows inside one migration transaction;
4. writes schema version 2 in that transaction;
5. runs integrity_check and foreign_key_check;
6. checkpoints the candidate WAL;
7. atomically replaces state.db.

Failure leaves the original state.db and migration backup untouched. Candidate
SQLite sidecars are cleaned before retries.

The preserved P0 data is:

- sessions;
- session_answers;
- progress;
- audit_events.

New v2 columns receive explicit schema defaults.

### P0 compatibility

P0 WebSocket sessions still use temporary `p0-probe:*` profile IDs until P2.2
creates real Profile/HA-user mappings.

For that reason, P2.1 does not retroactively add Profile/Track SQL foreign keys
to the P0 session/progress prototype tables. Business-level ownership is added
by later P2 work, while the durable data model already contains the real Profile
and Track tables.

## Consequences

- state.db can survive arbitrary content-generation rebuilds.
- P2.2–P2.6 can implement behavior on stable persistence primitives.
- P3 review/progress code can rely on the complete event/projection columns
  without another conceptual state-schema rewrite.
- Dataset removal/update can query persistent PackVersion pins.
- Cross-domain drift is explicit and diagnosable rather than silently enforced
  by an impossible cross-file FK.
- Migration recovery has a coherent pre-migration snapshot.

## Verification

Final P2.1 GitHub gate:

- `python -m ruff format --check .`: pass, 148 files already formatted;
- `python -m ruff check .`: pass;
- `python -m mypy custom_components datasets tests`: pass, 77 source files;
- `python datasets/tools/validate_resources.py`: pass;
- `python -m pytest -q --tb=short`: pass, 206 tests in 13.70 s.
