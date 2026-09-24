# Home Assistant actions and pedagogical events

P4.8 exposes a native Home Assistant action surface while keeping
`state.db`/ReviewEvent authoritative.

## Services

The loaded LockLearn Config Entry registers:

- `locklearn.start_session`
- `locklearn.send_now`
- `locklearn.snooze`
- `locklearn.pause_track`
- `locklearn.resume_track`

Calls carrying `context.user_id` use normal Profile ACL. Calls without a user
context are rejected unless the Profile explicitly enables
`allow_unattended_actions` and the action belongs to the narrow unattended
allowlist. Successful unattended calls are written to the durable audit log.

`start_session` is intentionally not unattended.

`send_now` materializes and prepares an immediate scheduler slot using the same
target capacity, active-session suppression and send-time CardDefinition
selection as normal scheduling. It does not inject prompt/answer text into user
state or bypass renderer privacy rules.

## Companion inputs

LockLearn listens only to the Companion input event types:

- `mobile_app_notification_action`
- `mobile_app_notification_cleared`

Action IDs contain a P4.6 single-use token plus a content-free semantic. The
token must atomically win before any learning transition is attempted.

A clear can close pending notification state and receptivity metadata, but it
never creates ReviewEvent/Progress evidence.

## Output events

After a canonical ReviewEvent+Progress commit, LockLearn may emit:

- `locklearn_answered`
- `locklearn_quiz_correct`
- `locklearn_quiz_wrong`
- `locklearn_quiz_idk`
- `locklearn_card_entered_relearning`
- `locklearn_card_mastery_threshold_reached`
- `locklearn_leech_detected`
- `locklearn_confusion_detected`
- `locklearn_track_goal_reached`
- `locklearn_daily_goal_reached`

Notification clear emits `locklearn_notification_cleared` only after the
persistent clear/slot state has been updated.

The generic answer event includes stable identifiers plus automation counters:
`streak_correct`, `consecutive_correct`, `consecutive_wrong`,
`session_accuracy` when applicable, and `daily_goal_progress`.

Learned prompt/answer text and user-entered response are not included by default.

## Authority rule

Output events are observation only. Firing a fabricated `locklearn_answered`
or quiz-result event cannot mutate Progress or create a ReviewEvent.

Automations that react to LockLearn events may perform ordinary Home Assistant
effects (lights, media, notifications, etc.), but must call an authenticated
LockLearn service if they want to request a LockLearn state change.
