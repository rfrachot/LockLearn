# ADR-0055 — Availability means effective selectability

## Context

A raw SRS `next_due_at` can be earlier than the moment a card is actually selectable because quotas, sibling/confusable spacing, burial, prerequisites and user state are independent gates. Beta.4 improved counts but still lacked a complete explainable blocker model.

## Decision

`locklearn/session/availability` is a read-only projection over the **same candidate and eligibility rules as `session/start`**. For every relevant CardDefinition it composes temporal gates and non-temporal blockers. `next_available_at_utc` is the minimum effective timestamp among cards that can become selectable without another user action; a prerequisite with no predictable completion time contributes a blocker with `until_utc=null` and never manufactures a date.

The API returns stable aggregate fields and `blockers[] = {code,count,until_utc,forceable}`. The V1 codes are `scheduled_step`, `known_already_verification`, `new_quota`, `sibling_gap`, `confusable_gap`, `buried`, `prerequisite`, and `suspended`.

## Alternatives considered

- Keep separate simplified availability logic: rejected because it can disagree with session/start.
- Return every per-card reason by default: rejected for payload cost and privacy/noise; aggregate blockers plus a scoped detail endpoint is sufficient.
- Use the earliest raw due timestamp: rejected because it produces false promises.

## Consequences

Selection constraints remain the authority for per-card eligibility; availability becomes an explainable projection, not a second scheduler. Frontend waiting copy and reminder timing consume this contract. Tests must assert availability/start parity.

**Status:** Accepted — 2026-09-30.
