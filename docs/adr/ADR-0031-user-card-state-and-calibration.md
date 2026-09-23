# ADR-0031 — User-owned card state and initial calibration

## Status

Accepted for P3.10 on 2026-09-23 after the repository quality gate passed.

## Context

The V1 model already stores `user_state` and `suspend_until_utc` on Progress,
separately from `content_status`, but P3.10 must define their behavior without
turning user preference into pedagogical evidence.

The same scope adds an optional initial calibration sample of roughly 20–40
cards. Calibration should let a learner skip obvious material, but declaring a
card already known is not a verified retrieval and must not fabricate review
history, mastery, boxes, due dates or seen counters.

P3.9 selection is deliberately read-only, so timed hiding must also avoid a
background mutation just to make an expired card selectable again.

## Decision

### User state is an overlay, not an SRS transition

The supported states are:

- `active`: normal scheduling;
- `known_already`: excluded until explicitly reactivated;
- `suspended`: excluded indefinitely until explicitly reactivated;
- `buried`: excluded until an explicit future `suspend_until_utc`.

Changing user state preserves SRS state, counters, mastery, due dates and
content lifecycle. A card with no Progress row is lazily materialized in
`state = new` with zero learning counters.

Every mutation writes a private `audit_events` row of type
`progress_user_state`. It does not write a `review_events` row.

### Timed burial is resolved at selection time

P3.9 receives the stored user-state facts with each candidate. A buried card is
effectively active once its timezone-aware `suspend_until_utc` has elapsed.
The selector does not rewrite the row merely because time passed.

This preserves P3.9's read-only selection contract.

### Calibration is deterministic and read-only

`locklearn/calibration/sample` returns a deterministic spread over enabled,
still-new, effectively-active CardDefinitions in Pack order. The requested
sample size is bounded to 20–40, while small packs legitimately return fewer
cards.

Sampling itself creates no Progress row and consumes no daily new-card quota.
The learner's explicit decisions are applied through the same
`locklearn/progress/set_user_state` boundary, typically `known_already` for
trivial cards.

### Rebuild boundary remains P3.12

P3.10 does not reinterpret user-state mutations as ReviewEvents merely to make
the existing P3.1 projection rebuild preserve them. P3.12 owns the final
integrity-rebuild/recompute contract and must explicitly preserve/replay these
audited non-pedagogical overlays.

## Alternatives considered

### Encode known-already as a successful ReviewEvent

Rejected. This would manufacture retrieval evidence and could accidentally
promote SRS state.

### Add a new table for user state

Rejected for P3.10. The state schema already reserves
`user_state`/`suspend_until_utc` on Progress and the separation from
`content_status` is explicit. A second table would duplicate identity and add
migration complexity without improving V1 semantics.

### Automatically mutate expired buried rows to active

Rejected. Time-based eligibility can be derived at selection time and does not
require a hidden write.

### Persist a dedicated calibration session

Rejected for V1. The specification requires an optional sample, not resumable
calibration workflow state. P3.8 sessions remain for actual learning/quiz
sessions.

## Consequences

- Known/suspended/buried cards are excluded before P3.5 eligibility/ranking.
- Expired buried cards become selectable without a scheduler/background task.
- Calibration cannot falsely increase seen/review/verified counters.
- Viewer ACL remains read-only; owner/editor `MANAGE_PROGRESS` is required for
  calibration and state changes.
- No state-schema migration is required.
- P3.11 remains responsible for leech/annotations.
- P3.12 must preserve/replay audited user-state overlays during rebuild/recompute.
