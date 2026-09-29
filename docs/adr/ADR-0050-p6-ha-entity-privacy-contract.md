# ADR-0050 — P6.5 Home Assistant entity privacy contract

## Status

Accepted and qualified for P6.5 on 2026-09-27.

## Context

LockLearn ACLs and Home Assistant entity permissions are distinct security
boundaries. A learner may legitimately have private Profile/Track state that a
Home Assistant administrator or another dashboard user can observe once it is
published into the HA state machine.

V1 therefore permits optional aggregate sensors but does not require them for
1.0. The detailed learning dashboard remains the preferred private surface.

## Decision

### V1 ships no optional learning SensorEntity platform

The 1.0 integration continues to forward only the existing public dataset
`UpdateEntity` platform. `Platform.SENSOR` is not forwarded and P6.5 does
not add `sensor.py`.

This is deliberate, not missing scope: the V1 specification explicitly permits
optional sensors to remain unimplemented at 1.0.

Dataset UpdateEntity metadata is public content/update provenance and is
separate from private learner statistics.

### Stable identity and logical Device model

Future optional learning sensors are Track-scoped:

- the existing canonical Track UUID is the stable entity identity input;
- the stable `unique_id` is `<track_uuid>:<metric_key>`;
- Home Assistant display names and `entity_id` values never participate in
  identity and may be renamed freely;
- sensors for Tracks belonging to the same Profile are grouped under one
  logical LockLearn Device identified by `(locklearn, profile:<profile_uuid>)`.

Profile and Track IDs must be canonical UUIDs before they may become entity
identity. Human-readable Profile/Track names are not part of Device/entity
identifiers.

### Explicit privacy opt-in

No future private learning sensor is enabled by default.

The executable contract requires double opt-in:

1. Profile settings explicitly enable HA sensor exposure;
2. Track settings explicitly enable HA sensor exposure and enumerate an
   allowlist of metric keys.

ACL membership, owner/editor/viewer role, HA administrator status, Track
existence, dashboard visibility, services or events never imply sensor consent.

Unknown metric keys fail closed.

### Aggregate-only state

Allowed V1 contract metrics are aggregate numeric/counter values such as:

- mastery;
- quiz accuracy;
- due count;
- streak;
- last exam score;
- consecutive correct/wrong;
- session accuracy;
- daily goal progress.

Default state attributes are empty. The entity contract forbids content-bearing
attributes by default; vocabulary, translations, Card/Facet/LearningItem IDs,
answers, annotations, notification targets and human-readable Profile/Track
names stay out of the state machine.

The private LockLearn panel remains the correct surface for detailed statistics
and learning history.

### Recorder and publish cadence

Future sensors have a minimum five-minute publish/debounce interval. Per-answer
or per-click state publication is not allowed.

Recorder guidance is part of each metric contract:

- historically meaningful measurements may be kept if the user wants HA
  history;
- noisy snapshot/counter metrics are marked `exclude_recommended`.

Documentation recommends excluding optional learning sensors from Recorder when
HA history is not explicitly useful. `state.db` remains the canonical
learning history.

### state_class semantics

`SensorStateClass.MEASUREMENT` is reserved only for metrics that are actual
point-in-time measurements for which HA history semantics are meaningful:

- mastery;
- quiz accuracy;
- last exam score.

Counts and transient/snapshot percentages such as due count, streak,
consecutive-correct/wrong, session accuracy and daily-goal progress deliberately
have no `state_class`.

No LockLearn learning metric uses `TOTAL` or `TOTAL_INCREASING`.

## Consequences

- P6.5 can pass while 1.0 ships zero optional private learning sensors.
- A future sensor implementation must import and obey
  `ha_entity_contract.py`; inventing a separate identity/privacy policy is a
  contract violation.
- Publishing aggregate sensors is an explicit privacy tradeoff because HA ACL
  semantics are not LockLearn ACL semantics.
- Long-term statistics cannot be used as a dumping ground for internal metrics.
- P6.7 may add internal structured metrics, but those metrics do not
  automatically become HA entities.
