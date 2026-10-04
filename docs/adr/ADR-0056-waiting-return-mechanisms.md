# ADR-0056 — Waiting surfaces use explicit return mechanisms

## Context

Spacing is pedagogically correct, but “come back later” is an interaction dead end if the UI neither refreshes at the real eligibility time nor offers a reliable way back. Permanent frontend polling conflicts with LockLearn's performance and Home Assistant integration goals.

A Learn track can legitimately have two independent states at the same time: a new session may already be constructible from unseen cards while an already-started card has a short learning/relearning step due later. Treating generic Learn session readiness as the condition for the return reminder therefore suppresses a useful reminder and conflates introduction capacity with spaced follow-up.

Field qualification also showed that a one-shot Learn reminder is not sufficient: after one reminder is delivered, requiring the learner to opt in again for every following short step defeats the return mechanism. Learn reminder intent therefore has to outlive one delivery while still avoiding duplicate notifications for the same unchanged scheduled step.

## Decision

Waiting views schedule a local one-shot refresh for the current effective availability deadline plus a small margin and refetch on visibility/focus/pageshow/reconnect. Relative countdown display may update locally without network calls.

When a compatible Companion target exists, the user may enable exactly one persistent reminder intent for `profile + track + mode`. Its identity is deterministic, cancellable and idempotent.

The reminder contract is mode-specific:

- **Learn** is a persistent opt-in subscription to the next reliable `scheduled_step` for an already-started card. It may be enabled even when a new Learn session is already available. At fire time, the backend reruns effective Learn selection and sends the privacy-safe panel-handoff notification only if a non-`new` card is actually selectable. After a successful send, the intent remains enabled but records that exact scheduled step as already announced. The same unchanged step is not sent again. When canonical learning activity produces a distinct next `scheduled_step`, the backend automatically arms that new deadline. If no reliable step currently exists, the reminder waits rather than silently disabling itself. Explicit user cancellation is the normal way to disable the Learn reminder intent.
- **Quiz** keeps the one-shot generic readiness contract: it is armed only while no Quiz card is currently selectable, uses effective `next_available_at_utc`, revalidates Quiz availability at fire time, and is removed after successful delivery.

Return reminders remain separate from ordinary pedagogical notification slots. A return reminder never creates pedagogical evidence.

## Alternatives considered

- Permanent frontend polling: rejected for unnecessary wakeups and battery/network cost.
- Reuse ordinary pedagogical notification slots as-is: rejected because readiness reminders are user-requested return affordances, not learning events and must not consume or mutate SRS evidence.
- Fire at the originally predicted time without revalidation: rejected because it can notify falsely.
- Keep Learn tied to generic `available_now == 0`: rejected because unseen cards can make a session available while a previously introduced card still has a meaningful short-step deadline.
- Delete Learn reminder state after every successful send: rejected after field use because it forces repeated manual opt-in and makes multi-step spaced learning easy to miss.

## Consequences

Reminder persistence remains distinguishable from pedagogical scheduler slots. No reminder payload contains learned content. Runtime startup restores enabled reminder intents and their current deadlines. A lightweight backend monitor discovers a new distinct Learn `scheduled_step` after learning activity without frontend polling.

Frontend wording must keep Learn and Quiz deadlines distinct: Learn describes the next reminder for an already-started card, while Quiz describes the next card becoming available for a quiz.

**Status:** Accepted — 2026-09-30; amended 2026-10-04 for persistent Learn reminder subscriptions.
