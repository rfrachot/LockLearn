# ADR-0023 — Explicit introduction and short learning-step state machine

## Status

Accepted for P3.2 on 2026-09-22, pending final quality gate.

## Context

A new LockLearn card must not be treated as something the learner has already
forgotten. V1 requires an explicit encoding/introduction phase, followed by
short learning steps before the card becomes eligible for the long review
policy. Failed learning/relearning attempts must never be re-tested
immediately from working memory.

P3.2 must implement that behavior without prematurely owning P3.3 long-review
boxes/intervals or P3.4 signal weighting.

## Decision

### First presentation is introduction, never failure

The P3.2 state machine exposes an explicit `introduction` transition.

For a `new` card it produces:

- `state = learning`;
- `mode = introduction`;
- `retrieval_occurred = false`;
- `last_result = exposure`;
- no verified-wrong increment;
- first short-step due time.

The first encounter therefore cannot create an SRS failure.

### Short learning steps are deterministic

Default V1 delays are:

```text
learning_steps_minutes   = [1, 10, 60]
relearning_steps_minutes = [10, 60]
```

The state machine uses the current short-step success streak to decide the next
delay. A failure resets the short-step streak and schedules the first delay of
the current state.

All short-step delays are strictly positive, so a failed card is never eligible
for immediate re-test.

### Long review remains a separate policy boundary

Completing every short step returns `ready_for_long_review = true` and clears
the short `next_due_at_utc`, but does not itself switch the card into the
long-review queue.

The card remains in `learning` or `relearning` until P3.3 ReviewPolicy
consumes the graduation signal and assigns the long-review state/interval.

This is deliberate. P3.2 owns short-step sequencing; P3.3 owns boxes,
long-interval calculation, relapse penalties and deterministic jitter.

### Signal semantics remain a later layer

P3.2 distinguishes only policy-neutral short-step outcomes:

- introduction;
- success;
- failure.

It does not decide whether a particular UI action, MCQ, free-text answer,
self-assessment or shared-device response is strong enough to count as verified.
That mapping remains P3.4 scope.

### Interleaving is not implemented by the state machine

P3.2 guarantees a positive due delay after introduction/failure, which makes
immediate re-test impossible at the state level.

Actual selection of several other cards before the due card is served belongs
to session selection/interleaving in P3.9. P3.2 therefore does not duplicate a
scheduler.

## Consequences

- First exposure cannot be misclassified as forgotten material.
- Learning and relearning stay separate from the long review queue.
- Failed cards cannot be immediately re-tested from working memory.
- P3.3 can add long-review policy without rewriting introduction semantics.
- P3.4 can map verified/self-assessed signals without duplicating timing logic.
- P3.9 can interleave due cards without owning learning-state transitions.

## Verification

P3.2 tests cover introduction semantics, V1 1/10/60 learning steps, V1 10/60
relearning steps, positive failure delays, short-step reset behavior, graduation
boundary, invalid states and invalid step configuration. Final Ruff/mypy/
resource/pytest results are recorded after the quality gate.
