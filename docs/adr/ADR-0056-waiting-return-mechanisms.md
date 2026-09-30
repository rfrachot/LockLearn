# ADR-0056 — Waiting surfaces use one-shot return mechanisms

## Context

Spacing is pedagogically correct, but “come back later” is an interaction dead end if the UI neither refreshes at the real eligibility time nor offers a reliable way back. Permanent polling conflicts with LockLearn's performance and Home Assistant integration goals.

## Decision

Waiting views schedule a local one-shot refresh for the current `next_available_at_utc` plus a small margin and refetch on visibility/focus/pageshow/reconnect. Relative countdown display may update locally without network calls.

When a compatible Companion target exists, the user may arm exactly one persistent reminder for `profile + track + mode`. Its identity is deterministic, it is cancellable/idempotent, and the backend revalidates effective availability at fire time. If ready, a privacy-safe panel-handoff notification is sent; if the date moved, the reminder is rescheduled; if no reliable date remains or the opportunity was consumed, it is cancelled. The general notification scheduler and SRS are not altered.

## Alternatives considered

- Permanent frontend polling: rejected for unnecessary wakeups and battery/network cost.
- Reuse ordinary pedagogical notification slots as-is: rejected because readiness reminders are user-requested return affordances, not learning events and must not consume or mutate SRS evidence.
- Fire at the originally predicted time without revalidation: rejected because it can notify falsely.

## Consequences

Reminder persistence may reuse materialized state but must remain distinguishable from pedagogical slots. No reminder payload contains learned content. Runtime startup restores pending one-shot timers and revalidates overdue reminders immediately.

**Status:** Accepted — 2026-09-30.
