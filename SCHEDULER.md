# Scheduler

The scheduler is deterministic and Profile-scoped. It materializes **generic
notification slots**; pedagogical content is selected at send time.

## Configuration

Normalized scheduler configuration includes:

- Profile timezone and version;
- active weekdays/windows;
- minimum gap;
- maximum notifications/hour;
- quiet hours;
- optional receptive condition;
- bounded deferral window.

Profile/Track/target budgets further constrain materialization and delivery.

## Quotas and arbitration

Profile push capacity is shared across active Tracks. Track demand distinguishes
learning and quiz demand and is allocated deterministically using priority-aware
smooth weighted round-robin.

Physical target limits are enforced in addition to Profile/Track demand:
per-target and shared-device gap/hour/day constraints cannot be bypassed by adding
more logical targets for one physical device.

## Randomization

V1 avoids non-reproducible random scheduling. Stable seeds and deterministic
selection produce repeatable slots while distributing work across eligible
windows.

## Quiet hours and windows

No slot is generated inside quiet hours. Active windows may cross midnight.
Minimum-gap and hourly limits are checked against existing and proposed slots.

## DST and timezone

Civil-time mapping handles spring-forward gaps and fall-back duplicate hours
explicitly. Persisted UTC high-watermark state prevents duplicate catch-up after
restart or clock changes.

Changing Profile timezone preserves sent/consumed history, cancels only future
unsent slots from obsolete configuration and regenerates future slots.

## Restart and clock jumps

On restart/reload, persisted scheduler state is reconciled before new slots are
created. Backward/forward wall-clock jumps do not create notification floods;
overdue unsent slots expire instead of being replayed indiscriminately.

## Pending/deferral behavior

Send-time notification selection may defer an unsent slot within a bounded
window. Deferral is pedagogically neutral: it does not create learning evidence.

Active sessions suppress conflicting Track notification demand.

## Missed slots

Expired/missed slots do not become retroactive learning events. Scheduler and
notification interaction history record operational outcomes separately from SRS
strength.

## Home Assistant integration

The HA bridge refreshes schedules after relevant mutations and may evaluate an
optional `receptive_when` HA template. Template failure surfaces as a scheduler
validation/Repair condition rather than silently weakening constraints.

Detailed rationale lives in ADR-0036 through ADR-0040.
