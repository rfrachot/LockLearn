# ADR-0040 — Send-time notification selection, pending and backoff

## Status

Proposed for P4.5 on 2026-09-24 pending the full repository quality gate.

## Context

P4.1-P4.4 create authoritative Profile/Track/target time opportunities and
evaluate delivery context. P4.5 must decide which pedagogical CardDefinition
uses a scarce notification slot only when the slot is actually ready to send.

The V1 specification requires:

- explicit notification priority:
  1. relearning due;
  2. review due;
  3. difficult but recoverable;
  4. calibration needed;
  5. tightly limited new teaser;
- no use of far-future reviews merely to fill a slot;
- missed slots expire rather than catch up;
- default `skip_if_pending`;
- adaptive target/profile channel backoff driven by expirations and explicit
  clears, with progressive recovery after interaction;
- no SRS mutation from ignore, clear, expiry or backoff.

## Decision

### Send-time CardDefinition binding

P4.5 adds a dedicated `NotificationSelectionService`. The scheduler invokes it
only after pending and receptivity checks have passed.

The selected immutable CardDefinition identity is persisted on the materialized
slot:

- `card_key`;
- `learning_item_id`;
- `prompt_facet_id`;
- `answer_facet_id`;
- `selection_reason`.

No prompt, answer or learned text is copied into `state.db`.

Selection is idempotent: once a pending slot has a CardDefinition, retries and
restarts return that same binding instead of re-ranking current Progress.

Legacy Profile-only slots without a Track remain readable/deliverable without a
new content binding; normal P4.3+ Track slots use P4.5 selection.

### Ranking

Only Track-enabled active CardDefinitions that pass the existing P3.5 selection
constraints are candidates.

General notification order is:

1. `relearning_due`;
2. `review_due`;
3. `difficult_recoverable` — represented by due leech cards;
4. `calibration_needed` — prior self-assessment exists and the latest observed
   interaction is newer than the last verified retrieval, or no verified
   retrieval exists;
5. `teaser_new`.

A normal review whose `next_due_at_utc` is in the future is not selected just
to fill a notification slot.

New teasers are available only for learning slots, never quiz slots, and are
bounded to two selected teasers per Profile-local day in V1.

### Routine-slot content

`pre_sleep_consolidation` restricts candidates to CardDefinitions introduced
on the current Profile-local date.

`morning_first_review` restricts candidates to introductions from the previous
Profile-local date.

P4.4 still owns creating the routine slot; P4.5 chooses the content only when
delivery is prepared.

### Missed and pending policy

The default pending policy is `skip_if_pending`.

If a target already has an unanswered `sent` slot, a later pending slot for
the same Profile/target is expired with
`expired_reason = pending_existing`. It is never stacked or sent later.

Time reconciliation expires overdue unsent slots with
`expired_reason = missed`. Receptivity defer exhaustion expires with
`expired_reason = missed_not_receptive`.

A slot with no currently eligible CardDefinition is expired as
`no_candidate`. This is a system scheduling outcome, not user disengagement,
and does not contribute to adaptive backoff.

Explicit clear closes a sent slot as `expired/cleared` so it no longer blocks
future notifications. This remains observational only.

### Adaptive channel backoff

Backoff is computed from recent target/Profile channel outcomes and affects only
the effective daily notification capacity for that target.

V1 policy:

- 3 consecutive `expired`/`cleared` outcomes → 75 % budget;
- 6 consecutive `expired`/`cleared` outcomes → 50 % budget;
- each leading successful `answered`/`consumed` interaction restores one
  25-point step, capped at 100 %.

Neutral system expiries such as `no_candidate` are ignored.

If a target has its own daily budget, backoff applies to that budget; otherwise
it applies to the Profile daily push budget inherited by the target. A positive
base budget retains a minimum effective capacity of one slot.

Backoff never changes ReviewEvent, Progress, boxes, difficulty, due dates or
mastery.

A day whose unmet demand is caused by an active adaptive-backoff multiplier does
not advance the P4.3 persistent-capacity Repair streak. Backoff is deliberate
channel throttling, not evidence that the configured scheduler is infeasible.

### Schema migration

State schema v5 adds the CardDefinition identity, `selection_reason` and
`expired_reason` columns to `scheduled_slots`.

The migration is backup-first v4→v5 and preserves all prior rows.

## Alternatives

### Select content when the day schedule is generated

Rejected. SRS due state, session activity and eligibility can change before the
actual send time.

### Re-rank a selected slot on every retry

Rejected. That makes notification identity unstable across restart or delivery
retry.

### Send all missed slots after Home Assistant restarts

Rejected. It creates catch-up storms and violates the explicit V1 missed policy.

### Treat clears/expiry as SRS failures

Rejected. No retrieval evidence was observed.

### Persist rendered question/answer text on the slot

Rejected. It duplicates content data into user-state storage and increases
privacy exposure.

## Consequences

- notification content follows current SRS state without rewriting schedule
  history;
- retries are deterministic after first content binding;
- pending notifications do not accumulate;
- ignored/cleared/missed slots remain pedagogically neutral;
- target notification pressure adapts without contaminating SRS data;
- state schema advances to v5;
- P4.6 still owns persistent interaction tokens, replay protection and atomic
  pedagogical action consumption;
- P4.7 still owns notification rendering and platform capability behavior.
