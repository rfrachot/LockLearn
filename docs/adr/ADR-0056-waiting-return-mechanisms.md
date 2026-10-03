# ADR-0056 — Waiting surfaces use one-shot return mechanisms

## Context

Spacing is pedagogically correct, but “come back later” is an interaction dead end if the UI neither refreshes at the real eligibility time nor offers a reliable way back. Permanent polling conflicts with LockLearn's performance and Home Assistant integration goals.

A Learn track can legitimately have two independent states at the same time: a new session may already be constructible from unseen cards while an already-started card has a short learning/relearning step due later. Treating generic Learn session readiness as the condition for the return reminder therefore suppresses a useful reminder and conflates introduction capacity with spaced follow-up.

## Decision

Waiting views schedule a local one-shot refresh for the current effective availability deadline plus a small margin and refetch on visibility/focus/pageshow/reconnect. Relative countdown display may update locally without network calls.

When a compatible Companion target exists, the user may arm exactly one persistent reminder for `profile + track + mode`. Its identity is deterministic, cancellable and idempotent.

The reminder contract is mode-specific:

- **Learn** targets the next reliable `scheduled_step` for an already-started card. It may be armed even when a new Learn session is already available. At fire time, the backend reruns effective Learn selection and sends the privacy-safe panel-handoff notification only if a non-`new` card is actually selectable. If that scheduled step moved, the reminder is rescheduled; if no reliable started-card step remains, it is cancelled.
- **Quiz** keeps the generic readiness contract: it is armed only while no Quiz card is currently selectable, uses effective `next_available_at_utc`, and revalidates Quiz availability at fire time.

The general notification scheduler and SRS are not altered. A return reminder never creates pedagogical evidence.

## Alternatives considered

- Permanent frontend polling: rejected for unnecessary wakeups and battery/network cost.
- Reuse ordinary pedagogical notification slots as-is: rejected because readiness reminders are user-requested return affordances, not learning events and must not consume or mutate SRS evidence.
- Fire at the originally predicted time without revalidation: rejected because it can notify falsely.
- Keep Learn tied to generic `available_now == 0`: rejected because unseen cards can make a session available while a previously introduced card still has a meaningful short-step deadline.

## Consequences

Reminder persistence may reuse materialized state but must remain distinguishable from pedagogical slots. No reminder payload contains learned content. Runtime startup restores pending one-shot timers and revalidates overdue reminders immediately.

Frontend wording must keep Learn and Quiz deadlines distinct: Learn describes the next reminder for an already-started card, while Quiz describes the next card becoming available for a quiz.

**Status:** Accepted — 2026-09-30; amended 2026-10-04 for mode-specific Learn reminder semantics.
