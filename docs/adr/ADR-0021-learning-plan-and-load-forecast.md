# ADR-0021 — Card quotas, learning goals and explainable load forecasts

## Status

Accepted for P2.5 on 2026-09-22, pending final quality gate.

## Context

Track configuration must remain understandable before the full P3 SRS engine is
available. The V1 specification requires card-based new/review quotas, optional
target date/coverage/retention goals, and approximate future workload at about
three weeks and three months.

The forecast must not confuse LearningItems with CardDefinitions and must not
pretend to know future lapses, leeches or individual difficulty before review
history exists.

## Decision

### Quotas count CardDefinitions

`max_new_per_day_cards` and `max_reviews_per_day_cards` are Track planning
limits expressed in cards. One LearningItem that exposes several enabled
CardDefinitions can therefore consume several new-card introductions.

The child/standard/intensive profile presets continue to supply their specified
new-card defaults (3/8/15). The specification does not define numeric preset
defaults for `max_reviews_per_day_cards`, so P2.5 deliberately requires an
explicit review ceiling rather than inventing one.

`max_notification_new_teasers` defaults to 2 and is additionally bounded by
the configured new-card quota.

### Goals are Track-owned settings

A Track learning plan persists:

- `target_date` (optional);
- `target_coverage` in (0, 1];
- `target_retention` in (0, 1];
- new/review card quotas;
- notification-new-teaser ceiling.

Target dates are evaluated using the Profile timezone. Coverage is applied to
the count of selected CardDefinitions.

P2.5 stores `target_retention` as goal metadata. P3 ReviewPolicy owns the
actual retention/SRS mechanics; P2.5 does not fabricate a retention model.

### Forecast model is deterministic and explicitly approximate

P2.5 uses the V1 base long-review intervals (1, 3, 7, 14, 30, 60 days) as a
success-only planning model. The intervals are accumulated in sequence and the
reported 3-week / 3-month review load is a seven-day average ending at each
horizon.

The estimate intentionally excludes future failures, relearning, leeches,
difficulty-factor changes and jitter. Existing due backlog is reported
separately as `due_now`.

This keeps the forecast explainable and avoids embedding P3 policy behavior
prematurely.

### Notification versus active-session share

The planning service compares horizon workload with the Profile
`daily_push_budget`. New-card notifications are additionally limited by
`max_notification_new_teasers`; remaining work is reported as active-session
load.

This is a capacity estimate only. P4 still owns actual scheduler windows,
notification selection and delivery.

### Structural warnings

The forecast exposes machine-readable warnings when:

- the target date requires more new cards/day than the configured quota;
- projected review load exceeds the review quota at either horizon;
- the current due backlog already exceeds the review quota.

A later Repairs integration may use sustained overload evidence; P2.5 only
provides the deterministic planning signal.

## Consequences

- UI can explain why a goal is infeasible without running the full scheduler.
- Quotas remain card-based even when one LearningItem produces many cards.
- Forecast assumptions are visible rather than hidden in a magic score.
- Review-preset values are not invented where the specification provides no
  numeric default.
- P3 can later replace/augment the forecast with real ReviewPolicy projections
  while preserving the persisted goal contract.
- P4 can consume the notification/active-session capacity split without
  duplicating goal arithmetic.

## Verification

P2.5 tests cover profile-preset new-card defaults, CardDefinition-based
coverage, target-date infeasibility, V1 interval forecasting, notification
capacity splitting and structural warnings. Final Ruff/mypy/resource/pytest
results are recorded after the quality gate.
