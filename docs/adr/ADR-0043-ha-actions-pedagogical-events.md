# ADR-0043 — Home Assistant actions and post-commit pedagogical events

## Status

Proposed for P4.8. Mark Accepted only after the normal repository quality gate
passes.

## Context

P4.6 made notification action tokens persistent and single-use. P4.7 rendered
content-free action identifiers carrying those tokens and added the Home
Assistant target/delivery boundary.

P4.8 must expose native Home Assistant actions and useful pedagogical events
without turning the Home Assistant event bus into application state or allowing a
duplicate Companion action to apply learning twice.

The P3 ReviewEvent log remains the canonical audit. Progress is only a projection
of that log.

## Decision

### Native Home Assistant services

V1 registers these services while the singleton LockLearn Config Entry is loaded:

- `locklearn.start_session`;
- `locklearn.send_now`;
- `locklearn.snooze`;
- `locklearn.pause_track`;
- `locklearn.resume_track`.

With `context.user_id`, the service checks normal Profile ACL. Home Assistant
administrator status alone does not grant Profile access.

Without user context, the existing unattended policy is reused. The Profile must
set `allow_unattended_actions=true` and the action must be in the explicit
non-reading/non-destructive allowlist. Every allowed unattended call is durably
audited before execution. `start_session` remains forbidden unattended.

Pause/resume use TrackService, snooze uses the persisted scheduler defer
primitive, and start-session delegates to the same SessionSelection/SessionService
path as the WebSocket API.

`send_now` creates an immediate persistent `manual_send_now` scheduler slot and
runs the normal send-time selection policy. It may consume the same bounded new
teaser allowance as a normal learning slot. It does not inject learned text into
state.db or bypass the notification renderer.

The current content model does not yet provide a generic runtime mapping from an
arbitrary CardDefinition facet to its rendered text for every bidirectional card.
P4.8 therefore does not invent a lossy content resolver inside the service
boundary. The immediate slot remains the durable request/source of truth for the
notification delivery pipeline.

### Companion action authority

Only `mobile_app_notification_action` is accepted as a Companion action input.
The visible action ID is decoded into:

- a P4.6 bearer token;
- a content-free protocol semantic such as `reveal`, `known`, `review`,
  `choice_0` or `idk`.

The token is atomically consumed before any pedagogical mutation. Every
non-`consumed` disposition stops immediately.

The processor then reloads Profile, Track, CardDefinition identity, Progress and
target trust state from persistent repositories. The Home Assistant event payload
never supplies authoritative progression state.

### Canonical learning transition

Notification outcomes reuse the existing P3 state machines:

- new teaser reveal/IDK -> introduction/exposure only;
- learning/relearning -> LearningStateMachine short steps;
- completed short steps -> ReviewPolicy graduation;
- long review/leech -> SignalPolicy + ReviewPolicy;
- mobile MCQ -> verified MCQ signal;
- post-reveal known/review -> self-assessment-after-retrieval signal;
- untrusted shared-device verified responses retain reduced signal quality and
  cannot satisfy the verified promotion gate alone.

A new teaser is never failed merely because the learner selected
`I don't know` before it had been introduced.

The resulting ReviewEvent and Progress projection are committed atomically by
ReviewEventService.

### Post-commit events

Only after ReviewEventService returns successfully may P4.8 emit pedagogical Home
Assistant events.

`locklearn_answered` is the generic result event. Convenience events include
quiz correct/wrong/IDK plus state/threshold events such as relearning entry,
mastery threshold, leech, confusion, Track goal and daily goal.

The canonical ReviewEvent ID is reused as `event_id`; the consumed persistent
notification interaction ID is exposed as `interaction_id`. A duplicate
interaction cannot reach this point twice because P4.6 has a single atomic
winner.

Payloads contain identifiers, mode/result, signal-derived counters, content type
and language metadata only. Prompt text, answer text and user-entered response
are excluded by default.

Automation counters are derived from committed state/history:

- `streak_correct` from post-state;
- `consecutive_correct` / `consecutive_wrong` from canonical ReviewEvents;
- `session_accuracy` from canonical events when a session ID exists;
- `daily_goal_progress` from the existing StatsService due-queue goal.

Goal events are emitted only on a non-success -> success transition to avoid
repeated rewards.

### Clear events

A Companion `mobile_app_notification_cleared` event may atomically change the
matching pending interaction to `cleared`, record the observational receptivity
sample and expire the sent scheduler slot with reason `cleared`.

It never creates a ReviewEvent or SRS result.

After those state changes, LockLearn emits a privacy-minimal
`locklearn_notification_cleared` output event with a deterministic event ID and
no bearer token, notification tag or learned content.

### Bus trust boundary

LockLearn output events are observation only. There are no listeners that turn
`locklearn_answered`, `locklearn_quiz_correct` or other pedagogical output
events back into Progress mutations.

Firing a fabricated output event therefore grants no write authority. The only
mobile inputs are the dedicated Companion action/clear event types, and
pedagogical actions still require P4.6 token consumption and ACL when user
context is present.

## Alternatives

### Apply Progress directly from the Companion event

Rejected. It would make the HA bus a source of truth and bypass ReviewEvent
audit/rebuild semantics.

### Emit events before the database transaction

Rejected. Automations could observe a result that was never committed.

### Put prompt/answer text in event payloads

Rejected. HA event visibility is broader than LockLearn Profile ACL.

### Trust the action semantic without a persistent token

Rejected. Duplicate/replayed Companion delivery would be able to apply multiple
results.

### Make every service available unattended

Rejected. Start-session and other reading/interactive behavior require a user
context; unattended access stays narrowly allowlisted and audited.

### Invent a P4.8 CardDefinition-to-text resolver

Rejected. The current normalized content model does not expose a generic,
unambiguous facet-value rendering relation for every bidirectional card. P4.8
does not persist learned text in state.db merely to work around that boundary.

## Consequences

- native HA actions share the same backend state machines as the private UI;
- unattended actions remain narrow and auditable;
- duplicate mobile actions apply and emit at most one pedagogical outcome;
- ReviewEvent/Progress commit precedes every pedagogical output event;
- event payloads are automation-friendly without exposing studied text;
- clear events close pending notification state without SRS mutation;
- `send_now` is a durable immediate scheduler request rather than a content
  bypass;
- no state schema migration is required for P4.8.
