# ADR-0034 — Honest dashboard statistics, calibration and streak semantics

## Status

Proposed for P3.13 on 2026-09-23. Implementation pending repository quality gate.

## Context

The V1 dashboard must prioritize pedagogically honest statistics. Exposure,
self-assessment and verified retrieval are not interchangeable. Historical
local dates must remain stable when a profile timezone changes, while daily
streaks must be based on due-queue completion rather than one arbitrary answer.

P3.12 already established `stats_daily` rebuildability from canonical
ReviewEvents. P3.13 makes that projection live and adds the private dashboard
read model.

## Decision

### stats_daily is maintained on committed ReviewEvents

Every successful ReviewEvent append rebuilds the affected
`(profile_id, track_id, local_date)` row inside the same state-writer
transaction. Undo compensation rebuilds both the historical day containing the
undone source event and the compensation day.

The full admin `rebuild_stats` operation remains available and uses the same
per-day aggregation helper, so live materialization and repair cannot drift.

Explicitly undone source events and `undo_compensation` control events do not
contribute to learning statistics.

### Verified statistics exclude self-assessment

Verified accuracy and latest-retention fields use only trusted verified
retrieval modes:

- verified MCQ;
- verified free text;
- verified cloze;
- exam retrieval.

Exposure and `self_assessment_after_retrieval` remain separately counted.
Hints may reduce signal strength but still remain verified evidence when the
stored signal quality is trusted.

### Metacognitive calibration is card based

The calibration window defaults to seven local days.

A declaration that a card is known comes from either:

- an explicit P3.10 `known_already` user-state audit; or
- a positive post-retrieval self-assessment.

Each card is counted once using its first declaration in the window. LockLearn
then examines the first trusted verified retrieval after that declaration and
reports correct, wrong/IDK or still awaiting verified follow-up.

This avoids inflating calibration statistics through repeated self-assessment
clicks.

### Due today uses the full local calendar day

`due_today` includes active learning/review/relearning/leech cards whose
`next_due_at_utc` occurs before the next local midnight. It therefore includes
cards scheduled later today, not only cards already overdue at request time.

Known-already, suspended and still-buried cards are excluded.

### Streak reconstructs the historical due denominator

The default streak parameters are:

- due-goal fraction: 80%;
- absolute minimum: 1 card, capped by the actual due queue;
- grace days: 1.

Profile settings may override these values with
`daily_due_goal_fraction`, `daily_due_goal_min_cards` and
`streak_grace_days`.

For each historical local day, the service reconstructs card state at local
midnight from ReviewEvent pre/post snapshots and counts cards scheduled before
the following local midnight. A day with no due cards is neutral. A due day is
successful when the number of due cards actually treated reaches the goal.

Historical timezone names stored with events/stats are used when available;
days without an event carry forward the last known historical timezone.
Current profile timezone is only the initial fallback.

One missed due day may be skipped by the default grace day. Neutral days neither
extend nor break the streak.

### Mastery remains secondary

Global mastery is the mean of the current time-decayed ReviewPolicy mastery
labels for active, user-eligible materialized Progress rows. It is returned
explicitly as a secondary indicator and never replaces due/verified metrics.

### API and privacy

`locklearn/stats/get` is profile-private and requires backend Profile READ
permission. An explicitly shared viewer may read the same dashboard statistics;
an outsider receives the normal privacy-preserving not-found behavior.

No detailed learning statistic is exposed through Home Assistant entities in
P3.13. Sensor exposure remains the opt-in privacy boundary of later phases.

## Consequences

- no state schema migration is required;
- stats_daily becomes a continuously maintained rebuildable projection;
- dashboard accuracy cannot be boosted by visible-answer self-assessment;
- metacognitive calibration remains explainable at card level;
- timezone changes do not rewrite persisted historical local dates;
- streaks are based on reconstructed due workload, with neutral no-due days and
  one configurable grace day;
- confusion views reuse canonical non-undone ReviewEvents;
- notification receptivity remains dependent on the P4 notification runtime and
  is not fabricated in P3.13.
