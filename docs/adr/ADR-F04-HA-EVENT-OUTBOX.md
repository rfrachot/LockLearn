# ADR — F04: durable Home Assistant pedagogical event outbox (design gate)

Status: **PROPOSED — NOT IMPLEMENTED**  
Parent integration: `chore/self-hosted-ci` at `770f357`.

## Problem confirmed in the code

The mobile answer path persists `ReviewEvent`, token consumption, progress and daily stats in one SQLite transaction. Afterwards, `NotificationActionProcessor._emit_committed_events` emits `locklearn_answered` and conditional events directly to Home Assistant through a synchronous callback.

A process crash after commit but before `hass.bus.async_fire` can permanently omit the HA event even though the pedagogical answer was recorded. A retry of the mobile action is correctly rejected as a replay, so the lost event is not reconstructed.

## Required invariant

For every committed, assessable mobile answer, the same SQLite transaction must atomically persist:
1. the canonical `ReviewEvent` and progress/stat projections;
2. the consumed notification token;
3. a durable, uniquely keyed delivery intent for the HA event family.

A failed SQLite transaction must persist **none** of the three. Delivery must run only after commit and must not roll back the pedagogical result.

## Proposed solution

- Add a versioned `notification_event_outbox` table through an explicit state-schema migration and recovery snapshot. Key each intent by `ReviewEvent.id` and store immutable event data sufficient to reconstruct the HA payload and conditional event names without depending on later mutable counters.
- Insert the outbox intent in `ReviewEventsRepository.async_commit_mobile_answer` in its existing `BEGIN IMMEDIATE` transaction. Never create an intent for `exposure_only` unless that path explicitly produces a public HA event.
- Persist an ordered batch of event names and payloads. Keep the existing `locklearn_answered`, quiz-result, relearning, leech, mastery, confusion and goal transitions semantically unchanged. `event_id` is the stable deduplication key.
- Drain pending intents after runtime startup and after each successful answer; use bounded batches, bounded retries and structured warning/metrics for stuck deliveries.
- Acknowledge an intent only **after** the event bus accepts the call. The delivery guarantee is **at least once**, not exactly once: a crash between `async_fire` and acknowledgement may duplicate the event. Consumers should deduplicate by `event_id` plus event type.
- Keep non-mobile learning paths out of scope unless the same durable contract is implemented for them.

## Non-negotiable tests

1. SQL failure rolls back the token, canonical ReviewEvent, projection and outbox intent together.
2. Crash simulated immediately after SQLite commit leaves a pending intent, recovered on fresh runtime startup.
3. Emission failure retains the intent and retries; replayed mobile action does not produce another intent.
4. Crash after emission but before acknowledgement may re-emit the **same** stable `event_id`; no second pedagogical result.
5. Two concurrent identical mobile actions create exactly one canonical event and one outbox intent.
6. Conditional event names and the full event payload match the existing contract for quiz correct/wrong/idk, relearning, leech, mastery and daily/track goals.
7. Existing schema v5 migrates explicitly to the new version without data loss, backed up and recoverable; new and restored DBs pass required table/index checks.
8. HA reload/unload does not leave an outbox dispatcher running after SQLite closes; no access to production HA required.

## Scope exclusions

No change to `send_now` batching, ThermalTwin, signed-dataset publication, main branch, or production Home Assistant.

## Release gate

**Do not declare F04 corrected or merge an implementation PR** until the above tests and a fresh 8/8 integration CI pass on the exact implementation SHA.
