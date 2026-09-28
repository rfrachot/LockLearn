# ADR-0038 — Multi-Track and target capacity arbitration

## Status

Accepted for P4.3 on 2026-09-24 after the full repository quality gate passed.

## Context

P4.1 materialized deterministic Profile-level time opportunities. P4.2 made
those opportunities robust to timezone, DST, restart and clock discontinuities.
P4.3 must allocate scarce Profile slots across multiple active Tracks and stable
notification targets without selecting pedagogical content early.

The V1 specification requires weighted round-robin arbitration when demand is
impossible, Track priority, target-level gaps/budgets, active-session
suppression, stable device identity and a Repair when scheduler demand remains
infeasible.

## Decision

### Track demand

Track scheduler demand is stored in the existing Track `settings_json`:

- `learning_count`;
- `quiz_count`;
- optional `target_ids`.

The existing Track `priority` is the arbitration weight. Counts are
non-negative integers. Target IDs override Profile inheritance; when omitted,
all enabled Profile targets are eligible.

P4.3 assigns only `track_id`, `target_id` and a generic slot class
(`learning` or `quiz`). CardDefinition/content selection remains a send-time
P4.5 decision.

### Weighted round-robin

Finite daily Track demand is expanded into deterministic per-Track unit queues.
A smooth weighted round-robin chooses the next Track using integer priority.
When capacity is smaller than total demand, every eligible positive-weight Track
can receive service before a greedy high-priority Track consumes all capacity.

A demand unit that cannot use a particular time because of target constraints
does not permanently block later demand from another Track.

### Target identity and constraints

`notification_targets.device_registry_id` is the stable physical identity.
The notify service string remains mutable delivery metadata and is not used for
scheduler identity.

The allocator enforces:

- target `daily_push_budget`;
- target `minimum_gap_seconds`, inheriting the Profile gap when null;
- target `maximum_notifications_per_hour`, inheriting the Profile limit when
  null;
- the same constraints against all already materialized slots sharing the same
  physical `device_registry_id`, including slots from another Profile.

This makes a shared physical device capacity-safe across Tracks and Profiles.

### Active session suppression

An active persistent session suppresses notification demand only for its own
Profile/Track. Other Tracks remain allocatable. Suppressed demand is not treated
as scheduler infeasibility because it is a deliberate temporary condition.

### Materialized-slot authority

P4.3 does not mutate already-created P4.1/P4.2 rows to retrofit Track or target
identity. Arbitration applies only to newly materialized future slots. Existing
rows remain historical authority.

Preview reads already materialized current-version rows and applies the same
remaining Profile, target and physical-device capacity rules as generation.

### Capacity Repair

Each Profile keeps a private settings projection
`scheduler_capacity_state_v1:<profile_id>`. A distinct local day with unmet
non-suppressed demand increments an infeasibility streak. Repeated evaluation of
the same day does not increment it.

After three consecutive infeasible local days, LockLearn creates the
`scheduler_configuration_infeasible` Home Assistant Repair. It includes only
the Profile ID, requested slot count and effective allocated capacity. A
subsequent feasible generated day resets the streak and clears the Repair.

## Alternatives

### Greedy priority ordering

Rejected. A high-priority Track can starve every lower-priority Track whenever
demand exceeds capacity.

### Bind a CardDefinition during arbitration

Rejected. Due state and notification selection policy can change between slot
creation and delivery. P4.5 owns send-time pedagogical selection.

### Treat notify service names as target identity

Rejected. Companion notify service names can change; the HA device registry ID
is the stable identity required by the spec.

### Raise a Repair on the first infeasible preview

Rejected. Preview must be side-effect free and a single overloaded day is not a
persistent configuration problem.

## Consequences

- Multi-Track demand is deterministic and non-greedy.
- Target/device constraints are enforceable before delivery.
- An active learning session does not compete with its own Track notifications.
- Persistent overload becomes visible through HA Repairs without alert churn.
- No state schema migration is required; the target table, Track settings,
  scheduled slot identity fields and settings store already exist.
- P4.4 still owns receptivity/routine conditions.
- P4.5 still owns which CardDefinition is sent and missed/pending/backoff policy.


## Final qualification gate — 2026-09-24

The final development-checkout gate passed:

- Ruff format: PASS, 220 files already formatted;
- Ruff lint: PASS;
- mypy: PASS, 123 source files;
- resource registries: PASS;
- pytest: PASS, 334 tests in 16.18 s.

P4.3 is therefore closed PASS. Multi-Track/target allocation remains a timing
and capacity decision only; CardDefinition selection, receptivity and
missed/pending notification policy remain owned by P4.4/P4.5.
