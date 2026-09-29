# ADR-0032 — Leech state, confusion evidence and private remediation

## Status

Accepted for P3.11 on 2026-09-23 after the repository quality gate passed.

## Context

The V1 specification defines `leech` as a scheduling state, with versioned
thresholds, reduced automatic frequency, targeted remediation, confusion
visibility, personal mnemonic priority and manual reactivation.

Before P3.11, the domain already anticipated `leech` in short-step handling,
but state schema v2 restricted Progress.state to `new`, `learning`,
`review` and `relearning`. ReviewEvents already persisted
`expected_answer_id` and `answer_id`, and `user_annotations` already
existed in the state schema.

## Decision

### Leech is a real SRS state

State schema v3 widens only the Progress.state constraint to include `leech`.
The v2→v3 migration rebuilds the Progress table transactionally, preserves all
rows and indexes, and relies on the existing pre-migration backup boundary.

A leech remains review-compatible. Verified success/failure may update its box,
difficulty, due timestamp and counters, but the state remains `leech` until an
explicit manual reactivation. This prevents one accidental success from hiding
a persistent difficulty.

### Detection is versioned and committed with the canonical ReviewEvent

LeechPolicy V1 uses the normative thresholds:

- at least 6 verified failures among the 10 most recent verified attempts in
  the previous 60 days; or
- at least 8 verified relapses in the previous 60 days.

Only trusted verified retrievals participate. Reduced-confidence shared-device
signals do not trigger the threshold.

Detection occurs before the current ReviewEvent is appended. When the threshold
is crossed, that event's post-state snapshot is written directly as `leech`
with explainability metadata (policy version, reason and trigger counts).
There is no post-hoc projection-only mutation.

### Automatic frequency is reduced by ranking, not invented intervals

P3.11 does not introduce an arbitrary new leech interval multiplier. Existing
SRS due timestamps remain authoritative.

In ordinary session preparation, due leeches do not consume the normal due
target and are selected only after relearning, learning, normal reviews and
eligible new cards leave spare capacity. Their sibling spacing uses the normal
review gap.

A targeted session is explicit through `settings.leeches_only=true`.

### Confusion matrix remains derived from ReviewEvents

No confusion table is added. The backend aggregates canonical ReviewEvents by:

- card_key;
- expected_answer_id;
- chosen answer_id;
- count.

Only actual wrong/IDK choices with distinct expected/chosen identifiers are
counted. This keeps the metric rebuildable from the audit source.

### Personal annotations are profile-private remediation

The existing `user_annotations` table is used for notes and mnemonics targeted
to exactly one LearningItem or CardDefinition.

Profile READ permission exposes annotations to explicitly shared viewers.
MANAGE_PROGRESS is required to create, update or delete them. Non-members see
the normal privacy-preserving not-found behavior.

The difficulties surface recommends creating a personal mnemonic first when a
leech has no annotation, then editing the existing mnemonic before increasing
repetition.

### Manual reactivation is canonical

Reactivation emits a non-retrieval ReviewEvent
(`mode=leech_reactivation`, `result=reactivated`) whose post-state returns the
card to `review`. Because it is not a verified retrieval, old leech evidence is
not re-evaluated merely because the user reactivated the card.

## Consequences

- state.db schema version becomes 3;
- P3.11 requires an explicit v2→v3 migration;
- leech detection is explainable and rebuildable from ReviewEvents;
- confusion statistics require no additional persistent projection;
- automatic leech exposure is reduced without distorting SRS intervals;
- targeted leech sessions are available through the existing session boundary;
- personal remediation remains private to Profile ACL;
- P3.12 still owns general undo/rebuild/recompute semantics.
