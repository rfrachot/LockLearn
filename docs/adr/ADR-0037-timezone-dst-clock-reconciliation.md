# ADR-0037 — Timezone, DST and clock reconciliation

## Status

Accepted for P4.2 on 2026-09-24 after the full repository quality gate passed.

## Context

P4.1 materialized deterministic Profile-level scheduler slots and made each
persisted row authoritative after creation. P4.2 must make that planning robust
to civil-time discontinuities and process lifetime without pulling later
notification policy into the scheduler.

The V1 specification requires:

- timestamps persisted in UTC;
- active windows evaluated in the Profile timezone;
- explicit handling for nonexistent and duplicated local times;
- timezone changes;
- Home Assistant restart reconciliation;
- clock/NTP jumps without duplicate floods.

The scheduler must also preserve the P4.1 rule that sent/consumed slots are
historical facts and never rewritten by later configuration or clock changes.

## Decision

### Civil-time mapping

Scheduler windows remain expressed in Profile-local wall time. Generation
enumerates local wall-clock minutes, then maps each minute through `zoneinfo`
using round-trip validation:

- a spring-forward nonexistent minute maps to zero UTC instants and is skipped;
- a normal minute maps to one UTC instant;
- a fall-back duplicated minute maps to two distinct UTC instants.

The local hourly capacity bucket intentionally ignores `fold`, so both
occurrences of a duplicated local hour share the same
`maximum_notifications_per_hour` budget and cannot create a duplicate flood.

Cross-midnight active windows are supported. The active-day rule belongs to the
local date on which the window starts.

### UTC authority and local-day bounds

Persisted `scheduled_for_utc` remains an aware UTC timestamp. Local-day query
bounds are resolved through the same round-trip-valid civil-time mapping rather
than assuming that local midnight has a fixed UTC offset.

### Monotonic scheduler time

A private `settings` entry named `scheduler_time_state_v1` persists a UTC
high-watermark. Reconciliation compares the current injected wall clock with
that watermark:

- first observation: `initial`;
- Home Assistant reload/restart: `restart`;
- observed time before the watermark: `clock_backward`;
- timer observation jumping forward by more than five minutes:
  `clock_forward`;
- otherwise: `advance`.

The scheduler uses `max(observed_now, high_watermark)` as its effective
planning cutoff. A backwards NTP correction therefore cannot recreate a window
that the scheduler has already passed.

### Restart and jump reconciliation

On reconciliation, unsent `scheduled` or `deferred` slots strictly before the
effective cutoff are marked `expired`. This is a temporal safety action only:
P4.5 still owns ordinary missed-slot selection policy, pending notification
policy and adaptive backoff.

`sent`, `consumed`, `expired` and `cancelled` rows are never rewritten by
this reconciliation.

The runtime performs reconciliation after storage opens during every Config
Entry setup, including Home Assistant reload.

### Timezone changes

When the Profile timezone changes, the scheduler increments the normal
scheduler config version. Future unsent slots from older config versions are
cancelled; already sent/consumed history is retained. New slots are generated
against the new timezone and config version.

The cancellation is deliberately limited to timezone changes in P4.2. General
same-timezone config-change reconciliation remains governed by the P4.1
materialized-slot contract and later scheduling policy.

## Alternatives

### Let Python attach `tzinfo` directly and trust the result

Rejected. `zoneinfo` permits constructing wall times that do not exist during
spring-forward transitions. Round-trip validation is required to distinguish
real civil times.

### Pick only fold 0 during fall-back

Rejected. It silently discards a real hour. Both folds are valid instants, while
capacity policy prevents accidental duplicate flooding.

### Rewind scheduler time after a backward NTP correction

Rejected. It can regenerate or redeliver opportunities the scheduler already
passed.

### Regenerate every future row on restart

Rejected. Materialized rows are authoritative and restart must be idempotent.

## Consequences

- DST transitions are explicit and deterministic.
- Restart and clock correction cannot generate catch-up floods.
- Historical sent/consumed rows remain stable across timezone changes.
- The `settings` high-watermark adds no state schema migration.
- P4.3 still owns Track/target arbitration and shared capacity.
- P4.4 still owns receptivity/defer evaluation.
- P4.5 still owns normal missed/pending/backoff notification policy.


## Final qualification gate — 2026-09-24

The final development-checkout gate passed:

- Ruff format: PASS, 219 files already formatted;
- Ruff lint: PASS;
- mypy: PASS, 123 source files;
- resource registries: PASS;
- pytest: PASS, 328 tests in 15.51 s.

P4.2 is therefore closed PASS. The scheduler remains temporally decoupled from
SRS interval calculation: persisted slot timestamps are delivery opportunities,
while P3 review state continues to derive elapsed scheduling evidence from real
retrieval/response timestamps rather than theoretical slot time.
