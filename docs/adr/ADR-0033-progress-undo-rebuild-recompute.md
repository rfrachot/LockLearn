# ADR-0033 — Progress undo, historical rebuild and explicit recompute

## Status

Accepted for P3.12 on 2026-09-23 after the repository quality gate passed.

## Context

LockLearn persists immutable ReviewEvents as the learning audit source while
Progress and stats_daily are projections. P3.12 must support three operations
that are intentionally not interchangeable:

- undo one admissible progress mutation;
- restore projection integrity from what was historically applied;
- deliberately recompute history under a target algorithm version.

P3.10 also introduced user-owned Progress overlays
(`user_state`/`suspend_until_utc`) that are not ReviewEvents, so a rebuild
must not silently erase them.

## Decision

### Undo is append-only compensation

Undo never deletes a ReviewEvent and never decrements counters manually.

The latest not-yet-undone ReviewEvent in the requested profile/track/card scope
is selected. Undo restores that event's `pre_state_snapshot` through a new
non-retrieval `undo_compensation` ReviewEvent and records the target relation
in a private `progress_undo` audit event.

The write rechecks the current Progress snapshot transactionally before
committing, so a concurrent progress mutation makes the undo fail rather than
overwrite newer state.

Independent P3.10 overlays are preserved when restoring the SRS snapshot.

### Historical rebuild replays stored snapshots

`rebuild_progress` does not reinterpret old interactions. It selects the
latest historical `post_state_snapshot` per card, including compensating
events, and rebuilds Progress exactly from that applied history.

Replacement preserves current independent user/content overlays. A Progress row
that exists only because of a non-default overlay such as `known_already` or
`suspended` is retained even when no ReviewEvent exists for that card.

### Algorithmic recompute is explicit and fail-closed

`recompute_progress(policy_version=<target>)` is a deliberate admin operation.

V1 currently supports target policy version 1 only. The replay clock is set to
each historical event timestamp before applying the target policy. Supported
learning/review signal modes are recalculated. LeechPolicy V1 is recalculated
from the resulting trusted verified history.

Explicitly undone source events are omitted from algorithmic replay;
`undo_compensation` events are control records and are not treated as learning
evidence.

If an event lacks enough semantics for honest algorithmic replay, the report
records an `insufficient_replay_semantics` fallback. If any fallback exists,
the recompute is fail-closed: `applied=false` and Progress is not replaced.

A successful recompute reports card-level divergences and changed projection
fields before replacing Progress. ReviewEvents are never rewritten.

### stats_daily rebuild is independent

`rebuild_stats` rebuilds stats_daily separately from ReviewEvents using the
historical local_date/timezone/UTC offset stored on each event.

Original ReviewEvents that were explicitly undone and their compensation
control events do not contribute to rebuilt learning statistics.

P3.12 establishes rebuildability; P3.13 owns the final dashboard/statistical
semantics and streak/calibration surfaces.

### Long operations expose results

Admin rebuild/recompute commands run through the existing OperationRegistry.
Operations now expose an optional terminal `result` payload through
`operations/subscribe`, allowing recompute divergence reports to remain
observable without blocking the WebSocket request.

## Security and authorization

- profile-scoped undo requires `MANAGE_PROGRESS`;
- rebuild_progress, rebuild_stats and recompute_progress are admin-only;
- operations remain private to the HA user who started them;
- no admin operation runs automatically during an ordinary update.

## Consequences

- ReviewEvents remain append-only and canonical.
- Undo is auditable and concurrency-safe.
- Integrity rebuild preserves both historical SRS state and independent user
  overlays.
- Policy migration is an explicit operation with a divergence report.
- Unsupported or incomplete replay semantics never silently mutate Progress.
- stats_daily can be rebuilt independently and respects explicit undo.
- No state schema migration is required for P3.12.
