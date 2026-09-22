# ADR-0022 — ReviewEvent audit source and rebuildable progress projection

## Status

Accepted for P3.1 on 2026-09-22, pending final quality gate.

## Context

LockLearn needs an auditable learning history that survives algorithm changes,
content updates and projection corruption. The V1 specification makes
`review_events` the source of truth while `progress` and `stats_daily`
remain rebuildable projections.

P3.1 must establish that persistence boundary without prematurely implementing
P3.2 learning-state transitions or the P3.3 ReviewPolicy.

## Decision

### ReviewEvent is append-only audit state

Every persisted learning interaction records:

- Profile, Track and exact CardDefinition identity;
- mode, question type, result and signal quality;
- answer IDs, hint/retrieval flags and grading metadata when available;
- stable policy, dataset-generation and normalization versions;
- complete pre/post progress snapshots;
- separate cognitive and notification latency fields;
- session/notification linkage when present;
- UTC timestamp plus historical local date, timezone and UTC offset.

Event IDs are immutable and generated outside SQLite.

### Progress is a materialized projection

`progress` remains keyed by `profile_id + track_id + card_key`.
The event append and post-state projection update occur in the same SQLite writer
transaction.

The post-state snapshot contains the full progress row necessary to reconstruct
that projection. Identity fields in the snapshot must exactly match the event
identity before persistence is allowed.

P3.1 does not decide how a review changes boxes, mastery, due dates or
difficulty. Callers must supply pre/post state produced by later domain policy.
This keeps the audit/projection boundary independent from SRS semantics.

### Rebuild follows historical snapshots

Integrity rebuild clears the selected progress scope and replays ReviewEvents in
stable `created_at_utc, id` order, retaining the latest post-state snapshot for
each card.

This is an integrity rebuild under the historical event/policy result. It is not
an algorithmic recompute under a newer ReviewPolicy; that distinction remains
owned by P3.12.

### Latency fields are intentionally independent

`presentation_to_answer_ms` is cognitive response latency measured after the
question is actually rendered.

`delivery_to_action_ms` is notification/receptivity latency and can include
minutes or hours before the learner notices a notification.

P3.1 persists them independently and never derives one from the other. Later
ReviewPolicy code may use cognitive latency where explicitly allowed, but
delivery latency must never influence memory strength.

### Historical timezone is event data

The service derives `local_date`, `timezone_name` and
`utc_offset_minutes` from the Profile timezone at event time. These values are
stored on the event and are not retroactively rewritten when the Profile timezone
changes.

## Consequences

- Progress corruption can be repaired without losing the original learning
  history.
- Future policy migrations can compare historical rebuild with deliberate
  algorithmic recomputation.
- Card/facet identity remains explicit throughout the audit trail.
- Dataset and normalization versions remain attributable for grading and content
  migrations.
- Notification responsiveness cannot silently contaminate SRS strength.
- P3.2/P3.3 can focus on state-transition policy rather than persistence
  semantics.

## Verification

P3.1 tests cover atomic event/progress persistence, exact CardDefinition
identity, policy/dataset/normalization metadata, historical timezone fields,
independent latency semantics and progress reconstruction from the latest event
snapshot. Final Ruff/mypy/resource/pytest results are recorded after the quality
gate.
