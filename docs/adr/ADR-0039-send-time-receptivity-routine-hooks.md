# ADR-0039 — Send-time receptivity and routine hooks

## Status

Proposed for P4.4 on 2026-09-24 pending the full repository quality gate.

## Context

P4.1-P4.3 materialize authoritative notification opportunities, reconcile civil
time and allocate scarce capacity across Tracks and stable targets. P4.4 must
make delivery context-aware without turning absence or environmental
unavailability into a pedagogical result.

The V1 specification requires:

- a Profile-level `receptive_when` Home Assistant condition evaluated at send
  time;
- bounded `defer_window_minutes` when the condition is false;
- no disinterest/failure signal from such a defer;
- routine slots `pre_sleep_consolidation` and `morning_first_review` that can
  be triggered by Home Assistant entities/automations;
- collection of `weekday`, `local_hour`, `delivered`, `cleared`,
  `answered` and `delivery_to_action_ms` for a future receptivity profile;
- no automatic schedule learning in V1.

## Decision

### Send-time condition

`receptive_when` is interpreted as a native Home Assistant template and is
rendered only when a materialized slot is about to be delivered. The scheduler
core receives an injected boolean evaluator; Home Assistant template rendering
stays in the integration runtime adapter.

An absent condition is an explicit bypass and makes the pending slot ready.

A malformed template fails closed with a scheduler validation error rather than
silently sending.

### Bounded defer

When `receptive_when` is false and the original slot still lies within its
configured defer window, the row becomes `deferred` and stores:

- `deferred_until_utc`;
- `defer_reason = receptive_when_false`.

The defer deadline is bounded by
`scheduled_for_utc + defer_window_minutes`. Re-evaluation cannot extend the
window indefinitely.

Once the window is exhausted P4.4 reports
`not_receptive_defer_window_exhausted` but does not convert that state into a
learning result. P4.5 owns eventual missed/expired policy.

### Observational receptivity samples

A new `receptivity_samples` state table is created only when delivery is
actually recorded. It stores the Profile timezone at delivery plus:

- local weekday/hour;
- delivered;
- cleared;
- answered;
- first delivery-to-action latency.

These rows are observational. They never write ReviewEvent, Progress, mastery,
boxes, difficulty or SRS due dates. V1 does not use the samples to move future
slots automatically.

### Routine hooks

Profiles may opt into entity triggers through
`settings.scheduler.routine_triggers`:

```json
{
  "pre_sleep_consolidation": ["binary_sensor.in_bed"],
  "morning_first_review": ["input_boolean.morning_routine"]
}
```

The Home Assistant bridge listens only to configured entities and triggers on a
state transition to `on`. Listener registrations are rebuilt after Profile CRUD
and removed on integration unload.

Routine slots remain content-free. P4.4 assigns only routine type, eligible
Track and stable target. Existing P4.3 daily budget, target/device gap/hour
limits and active-session suppression are enforced before materialization.
P4.5 later chooses the actual same-day/previous-day pedagogical content implied
by the routine type.

No Home Assistant event is accepted as write authority and no new service/action
is introduced here; P4.8 remains responsible for the documented service/action
surface.

### Schema migration

State schema v4 adds `deferred_until_utc` and `defer_reason` to
`scheduled_slots`, plus `receptivity_samples`. Existing state databases
migrate v3→v4 through the normal backup-first migration path.

## Alternatives

### Evaluate context while generating the day

Rejected. Presence, driving, sleep and cinema state are ephemeral; generation
time is not delivery time.

### Record a false condition as an ignored notification

Rejected. The notification was intentionally withheld, so no user behavior was
observed.

### Reuse ReviewEvent for receptivity telemetry

Rejected. ReviewEvent is pedagogical audit authority. Delivery context is
observational and must not fabricate retrieval evidence.

### Learn preferred hours automatically in V1

Rejected. V1 collects the necessary features but leaves schedule adaptation for
V1.1.

### Use arbitrary HA bus events to create routine slots

Rejected. HA events are observational and must not become unauthenticated write
authority. Explicit configured entity transitions provide an understandable,
opt-in hook.

## Consequences

- Context-aware delivery is bypassable and explainable.
- Deferred slots remain pedagogically neutral.
- Routine automation hooks integrate naturally with HA while preserving unload.
- Receptivity data is available for future adaptation without changing V1
  scheduling behavior.
- State schema advances to v4 with an explicit migration.
- P4.5 still owns send-time CardDefinition selection and ordinary
  missed/pending/backoff policy.
- P4.6/P4.7 still own interaction replay protection and notification rendering.
