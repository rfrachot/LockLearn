# ADR-0036 — Materialized deterministic scheduler slots

## Status

Proposed for P4.1 on 2026-09-24 pending repository quality gates.

## Context

LockLearn needs deterministic notification opportunities without turning future
randomization into runtime truth. The V1 specification requires active windows,
quiet hours, minimum gaps, hourly limits and stable behavior after configuration
changes. Later P4 work owns DST/restart reconciliation, multi-track/target
arbitration, receptivity, missed/pending behavior and notification interactions.

Selecting a CardDefinition while generating a time slot would couple SRS state to
an arbitrarily early planning decision. Recomputing already-created slots after a
Profile edit would make the schedule non-auditable and could rewrite consumed or
sent history.

## Decision

P4.1 treats `scheduled_slots` as authoritative once a row exists.

The scheduler:

- resolves Profile timezone, active weekdays/windows, quiet hours, minimum gap,
  maximum notifications/hour and daily push budget;
- derives a deterministic seed from Profile ID, local date and scheduler config
  version;
- distributes generic `notification` opportunities across eligible local
  minutes with deterministic hash-based selection;
- stores all slot timestamps as UTC;
- persists only Profile/time/config identity at P4.1: `track_id` and
  `target_id` remain null and no CardDefinition/content identity is stored;
- exposes `locklearn/scheduler/preview` through backend Profile READ ACL;
- uses the same generation primitive for preview and materialization;
- increments scheduler config version only when scheduling semantics change;
- inserts materialized rows idempotently and never updates an existing slot's
  time, seed, config version or terminal/consumed status.

Content selection is explicitly deferred to send time. P4.3 will arbitrate Track
and target demand. P4.4/P4.5 will evaluate receptivity and pending/missed policy.
P4.6/P4.7 will own notification interaction/rendering state.

P4.1 accepts only same-local-day active windows. Cross-midnight active-window
semantics, nonexistent/duplicated local times, timezone changes, clock jumps and
restart reconciliation are deliberately deferred to P4.2 rather than being
partially implemented here.

## Alternatives

### Recompute the whole future day after every Profile edit

Rejected. It can rewrite an already-observed schedule and makes sent/consumed
history dependent on current settings instead of the configuration that created
it.

### Persist CardDefinition/Track/target at slot creation

Rejected. Due state, user state, target availability and arbitration can all
change before send time. Early binding would create stale pedagogical decisions
and improperly pull P4.3/P4.5 scope into P4.1.

### Use non-deterministic random sampling

Rejected. Preview, tests and operational diagnosis need reproducible generation.

## Consequences

- Materialized slots form a small auditable scheduling ledger.
- A config change can create new-version future opportunities without mutating
  older materialized rows; later reconciliation policy decides what to do with
  superseded scheduled opportunities.
- Preview remains side-effect free.
- The deterministic seed is useful only for future/preview generation, never as
  authority over an existing row.
- P4.2 remains responsible for the difficult temporal reconciliation cases.
