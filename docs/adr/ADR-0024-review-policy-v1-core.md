# ADR-0024 — Deterministic ReviewPolicy V1 core

## Status

Accepted for P3.3 on 2026-09-22, pending final quality gate.

## Context

P3.2 separates introduction and short learning/relearning steps from the long
review queue. P3.3 now needs a deterministic, versioned and explainable
ReviewPolicy for long review scheduling without pulling P3.4 signal weighting,
P3.5 sibling/prerequisite policy or P3.11 leech detection into scope.

The V1 specification requires boxes, base intervals, elapsed-time adjustment,
deterministic jitter, bounded difficulty_factor, relapse demotion and mastery as
a non-terminal derived label.

## Decision

### Stable policy version

ReviewPolicy V1 exposes `policy_version = 1`. ReviewEvent persistence already
records the policy version used for each mutation.

### Base boxes and intervals

The long-review schedule uses:

```text
box 1 = 8 h
box 2 = 1 day
box 3 = 3 days
box 4 = 7 days
box 5 = 14 days
box 6 = 30 days
box 7 = 60 days
```

Successful long reviews advance by at most one box, capped at box 7.

Short-step graduation enters long review through an explicit handoff from
P3.2. Learning graduation starts at box 1. Relearning graduation preserves the
demoted box floor and returns to review only after the short relearning steps
complete.

### Elapsed-time adjustment

ReviewPolicy derives:

- `scheduled_interval_days` from the prior verified timestamp and prior due
  timestamp when available;
- `elapsed_days` from the real verified timestamp to the current injected
  Clock value.

For a remembered overdue card, the next effective interval is never shorter
than the demonstrated elapsed retention. This prevents an overdue success from
being artificially shortened back toward the nominal schedule.

### Difficulty factor

`difficulty_factor` is bounded in `[0.6, 2.0]` and follows the V1 factors:

- verified failure: multiply by 0.85;
- verified success without hint: multiply by 1.05;
- verified success with hint: no increase.

The result is clamped to the configured bounds.

### Deterministic jitter

Long-review intervals receive deterministic jitter derived from stable inputs:

```text
card_key
policy_version
target_box
historical verified-attempt ordinal
```

The hash-based jitter is deterministic for identical state/history and defaults
to ±10 percent. The overdue demonstrated-retention floor is applied after
jitter, so jitter cannot shorten proven retention.

### Relapse

A failed long review:

- increments verified failure state;
- resets the long correct streak;
- applies the V1 difficulty multiplier;
- demotes by `relapse_penalty = 2` boxes, bounded at zero;
- enters P3.2 relearning, whose first default delay is 10 minutes.

The card is not reset unconditionally to box zero.

### Mastery is derived, never terminal

Mastery is calculated from the current box, verified accuracy and time since the
last verified retrieval. It decays over time.

`is_mastered()` is only a display predicate. It never changes the persistent
planning state and a mastered card remains a review card.

### Clock boundary

All time-sensitive policy behavior uses the injected Clock. No
`datetime.now()` call appears in ReviewPolicy domain logic.

## Consequences

- identical state/history under policy version 1 yields reproducible due dates;
- late remembered reviews preserve demonstrated retention;
- long scheduling stays separate from P3.2 short-step mechanics;
- P3.4 can decide whether a signal is verified/strong enough before invoking a
  long-review success/failure transition;
- P3.11 can add leech policy without changing the V1 interval engine;
- historical ReviewEvents can later be replayed or recomputed explicitly under
  P3.12.

## Verification

P3.3 tests cover deterministic success scheduling, hint behavior, relapse
demotion, bounded difficulty, overdue elapsed-time floors, mastery time decay,
short-step graduation, invalid long-review states and invalid policy
configuration. Final Ruff/mypy/resource/pytest results are recorded after the
quality gate.
