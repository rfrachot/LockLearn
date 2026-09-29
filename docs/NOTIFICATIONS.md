# Notifications

LockLearn V1 treats Companion notification actions as a **single-use transport
capability**, not as strong user authentication.

## P4.6 persistent interaction contract

Every actionable notification stage is backed by a row in
`notification_interactions` containing an opaque random token, optional
replacement tag, Profile/Track/target/CardDefinition identity, protocol stage,
expiry and lifecycle status.

The actionable stages are `prompt`, `revealed` and `answered`. A renderer
that replaces a prompt with a revealed answer creates a **fresh token for the
new actionable stage**. The visible notification tag may stay the same for
replacement semantics; the bearer token does not.

Tokens are generated with cryptographically strong randomness in production and
must never be logged, copied to `audit_events`, exposed through diagnostics or
embedded in learned text. Action IDs are protocol identifiers and must likewise
remain content-free.

## Action consumption and replay protection

Incoming actions are handled in this order:

1. resolve the opaque token;
2. when Home Assistant supplies `context.user_id`, require Profile
   `ANSWER` permission;
3. atomically claim the interaction only while it is `pending` and unexpired;
4. return a claim that allows downstream pedagogical mutation only for the
   single `consumed` winner.

The SQLite claim runs under the dedicated state writer transaction. Concurrent
or repeated delivery therefore produces at most one `consumed` result.
Expired, replayed, unknown and ACL-forbidden attempts never authorize a
ReviewEvent/Progress mutation.

When Companion omits user context, as observed during P0 qualification on one
iPadOS path, the valid single-use bearer token remains the correlation gate.
This does **not** make the notification action strong authentication. Shared
device and signal-quality policy remain separate concerns.

P4.6 does not yet interpret `reveal`, `known`, quiz choice or other action
semantics. P4.7 owns renderers and platform behavior; later code may apply a
pedagogical result only after P4.6 returns a successful claim.

## Audit

Suspicious or invalid action attempts are recorded in `audit_events` with a
minimal reason and, when already known, interaction/target/stage/status
identifiers. Bearer tokens, notification tags and learned content are excluded.

Successful consumption also records a minimal transport audit so available HA
user context is retained without turning the HA event bus into a source of
truth.

## Storage and migrations

The P2 state foundation already reserved the complete
`notification_interactions` table required by P4.6, so P4.6 adds repository
and service behavior without changing state schema version 5.


## P4.7 capability-aware rendering and delivery

Learning notifications prefer prompt-first retrieval. Proven actionable targets
receive prompt-only Reveal/I-don't-know actions, then a second stage with the
same visible tag, `alert_once=true`, answer/explanation and post-retrieval
self-assessment actions. The second stage always uses a fresh P4.6 interaction
token even when the notification tag is reused.

If actionable prompt-first delivery is unavailable, the renderer uses direct
exposure and labels the pedagogical path `exposure_only`. Existing SignalPolicy
semantics keep that path neutral for box promotion.

Notification quiz is deliberately bounded to two answer choices plus
I-don't-know when the target proves at least three visible actions. Larger MCQ or
insufficient capability uses a panel handoff instead.

Android channel names are separated for learning/teaser, quiz/review and
relearning. Shared devices include the LockLearn Profile name in the visible
title. Default visibility is private, including child/shared usage; visibility
remains only an OS preference and never authorizes additional content.

Delivery resolves the persisted `device_registry_id` to the current mobile_app
notify action at send time. Dynamic service names are diagnostic metadata only.
Actionable payloads require a platform-data-capable route. Direct-exposure
fallback may use the generic notify entity as a plain message with Companion data
removed.

A missing or failing target raises the
`notification_target_unavailable` Repair and is not recorded as sent.

The private WebSocket command
`locklearn/notifications/unrecorded_responses` exposes recent action attempts
that arrived after interaction expiry. It is based on P4.6 rejection audit
events with `reason=expired`, so merely ignored notifications do not create a
false lost-response warning.


## P4.8 Companion action/result pipeline

Companion action events are decoded into the P4.6 single-use token and an opaque
protocol semantic. Only the atomic `consumed` winner may reach canonical
learning state.

The processor reloads Profile, Track, CardDefinition identity, Progress and
target trust state from repositories. New teaser Reveal/IDK remains an
introduction/exposure; learning and relearning use their short-step machine;
review/leech uses SignalPolicy and ReviewPolicy. Untrusted shared devices retain
reduced signal quality.

ReviewEvent and Progress commit before any `locklearn_*` result event is
emitted. Output event payloads contain no learned text or user-entered answer by
default. Firing a LockLearn result event back onto the Home Assistant bus has no
write authority.

`mobile_app_notification_cleared` may close the persistent interaction and
scheduler/receptivity state but creates no pedagogical evidence.
