# Scheduler

LockLearn V1 separates **time opportunities** from **pedagogical selection**.

## P4.1 contract

A Profile scheduler resolves:

- Profile timezone;
- active weekdays and active windows;
- quiet hours;
- minimum gap between notifications;
- maximum notifications per local hour;
- Profile daily push budget.

Generation is deterministic for `(profile_id, local_date, scheduler_config_version)`.
`locklearn/scheduler/preview` uses the same rules as materialization but writes
nothing.

Once a row exists in `scheduled_slots`, that row is authoritative. Later
Profile/config edits do not rewrite its timestamp, seed, config version or
status. A later config version may materialize additional future rows; P4.2+
owns reconciliation/cancellation policy.

P4.1 slots deliberately contain no CardDefinition and do not bind a Track or
notification target. Content is selected at send time so current SRS state is
used rather than stale planning state.

## P4.1 boundaries

Cross-midnight active windows, DST duplicated/nonexistent times, timezone
changes, restart/clock-jump reconciliation are P4.2.

Multi-track/target arbitration and capacity Repairs are P4.3. Receptivity and
routine hooks are P4.4. Missed/pending/backoff policy is P4.5. Notification
interactions/rendering are P4.6/P4.7.

## P4.2 temporal reconciliation

All slot timestamps are persisted in UTC while active windows are interpreted
in the Profile timezone.

LockLearn resolves each local wall-clock minute explicitly:

- nonexistent spring-forward minutes are skipped;
- duplicated fall-back minutes produce both real UTC instants;
- both folds share the same local-hour capacity budget;
- cross-midnight windows use the weekday on which the window starts.

A persisted scheduler UTC high-watermark prevents a backwards NTP adjustment
from reopening time the scheduler has already passed. Config Entry startup and
reload reconcile against that watermark and expire only overdue unsent
`scheduled`/`deferred` rows. Sent/consumed history is never changed.

A Profile timezone change creates a new scheduler config version, cancels only
future unsent rows from older versions, and generates new opportunities using
the new timezone. P4.5 remains responsible for ordinary missed/pending/backoff
policy.


## P4.3 Track and target arbitration

When Tracks declare notification demand, newly generated Profile slots are
allocated with deterministic smooth weighted round-robin using Track
`priority`. Track scheduler settings contain `learning_count`, `quiz_count`
and optional `target_ids`; omitted target IDs inherit all enabled Profile
targets.

Target constraints are applied before a slot is materialized:

- daily push budget;
- minimum gap;
- maximum notifications per local hour;
- the same physical-device constraints across every target sharing a
  `device_registry_id`, including another Profile.

An active session suppresses only its own Track's notification demand. The slot
still does not contain a CardDefinition: P4.5 chooses pedagogical content at
send time.

A Profile with unmet non-suppressed demand for three consecutive generated local
days raises the `scheduler_configuration_infeasible` Home Assistant Repair.
A later feasible day clears it. Preview is side-effect free and never advances
the Repair streak.


## P4.4 send-time receptivity and routine hooks

`receptive_when` is a native Home Assistant template evaluated only when a
materialized slot is about to be sent. If it is absent, context filtering is
bypassed. If it is false, LockLearn defers the slot no later than
`scheduled_for_utc + defer_window_minutes`; this never creates a ReviewEvent or
SRS failure.

Actual delivery initializes an observational receptivity sample with Profile
timezone, weekday, local hour and delivery state. Later clear/answer observations
may attach `delivery_to_action_ms`. V1 stores these features only; it does not
learn or move future schedule windows automatically.

Profiles may opt into routine entity hooks:

```json
{
  "scheduler": {
    "routine_triggers": {
      "pre_sleep_consolidation": ["binary_sensor.in_bed"],
      "morning_first_review": ["input_boolean.morning_routine"]
    }
  }
}
```

A transition to `on` creates a content-free routine slot while still honoring
P4.3 Profile/target/device capacity and active-session suppression. The actual
same-day or previous-day CardDefinition is deliberately left to P4.5 send-time
selection.


## P4.5 notification selection, pending and backoff

A materialized Track slot receives its CardDefinition only when it is actually
ready to send. The binding is persisted on the slot as immutable content
identity plus a machine-readable selection reason; rendered learned text is
never copied into `state.db`.

V1 selection priority is:

1. relearning due;
2. review due;
3. due leech/difficult recoverable;
4. calibration needed;
5. at most two new learning teasers per Profile-local day.

Normal future reviews are not pulled forward merely to fill a slot. Quiz slots
never introduce a new teaser.

Routine slots use the same send-time binding: pre-sleep restricts the pool to
cards introduced today, while morning-first-review restricts it to yesterday's
introductions.

The default pending policy is `skip_if_pending`: if the same Profile/target
already has an unanswered sent slot, the later slot expires as
`pending_existing`. Missed unsent slots expire rather than catch up.

Recent expirations and explicit clears reduce only notification-channel
capacity: three consecutive failures apply a 75 % budget multiplier, six apply
50 %, and successful interactions restore 25 points at a time. These outcomes
never mutate Progress or ReviewEvent.

