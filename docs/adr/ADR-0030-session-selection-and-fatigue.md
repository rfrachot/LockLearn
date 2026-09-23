# ADR-0030 — Fatigue-aware session selection and interleaving

## Status

Accepted for P3.9 implementation on 2026-09-23. Final quality gate is pending.

## Context

P3.8 established persistent sessions, prepared question identity, optimistic CAS and
cross-client resume, but intentionally did not decide which cards belong in a
session. P3.5 already owns card eligibility constraints such as prerequisites,
new/review sibling burial and confusable introduction spacing.

P3.9 must prepare bounded session sequences without creating a second scheduler,
without mutating SRS state merely because a card was selected, and without
silently turning fatigue mitigation into a learning-history rewrite.

The V1 specification also requires content-type interleaving, no new cards in
the final quarter of a bounded session, and an advisory response when recent
verified accuracy drops.

## Decision

### Selection is a read-only backend policy

`SessionSelectionService` reads:

- the Track's enabled CardDefinitions and pinned PackVersion;
- active content type and Pack position;
- lazy Progress when it exists;
- Track content weights;
- P3.5 `SelectionConstraintService` decisions;
- the profile-local daily introduction count.

It does not create Progress, append ReviewEvents, reserve cards, or change due
dates. A selected card becomes learning history only through the normal
interaction/event pipeline.

### Candidate classes and priority

Candidates are classified from canonical Progress:

- absent Progress -> `new`;
- `learning`, `relearning`, or `review` -> eligible only when due.

Short-step `relearning` and `learning` are served before ordinary
review/new arbitration. New-card capacity is bounded by the profile/Track
daily card quota and actual introduction events already recorded for the
profile's local date.

The selector reuses P3.5 eligibility instead of duplicating prerequisite,
sibling, or confusable timing logic.

### Interleaving and bounded-session tail

Within each eligible state pool, content types are chosen against their Track
weights using deterministic served-count/weight debt, with stable card ordering
as the tie-breaker.

For a bounded requested length N, the first index at which new cards are
forbidden is `ceil(0.75 * N)`. If the remaining pre-tail positions are all
needed to satisfy the selected new-card target, new cards take priority before
that boundary so the final quarter cannot force premature truncation.

The plan also avoids pre-queuing multiple new/review sibling CardDefinitions
from the same LearningItem and avoids putting two new items from the same
confusable group in one prepared sequence. Learning/relearning short steps are
not blocked by that prospective sibling guard.

A session may legitimately contain fewer than the requested number of cards
when constraints, quotas, due state or the final-quarter rule leave no safe
candidate.

### Explainability

Each prepared SessionQuestion persists selection metadata:

- content type;
- progress state at selection time;
- selection reason;
- Pack position;
- configured content weight.

The active content generation is still pinned by the P3.8 SessionService
boundary, not accepted from the client.

### Fatigue is advisory only

Fatigue uses the ten most recent trusted verified retrieval outcomes associated
with the session in canonical `review_events`.

Only verified MCQ/free-text/cloze/exam modes with real retrieval and
non-reduced signal quality participate. Exposure, self-assessment and
untrusted shared-device signals do not.

P3.9 uses a configurable accuracy threshold with a conservative default of
0.60. Fewer than ten qualifying retrievals never trigger fatigue advice.

When the ten-result accuracy falls below the threshold while the session is
active, the API offers exactly:

- finish;
- recognition_only;
- continue.

The signal changes neither ReviewEvents nor Progress. A later user choice may
change only the remaining session presentation mode or lifecycle through its
own explicit action.

### Public session start

When `locklearn/session/start` contains a Track, backend selection prepares the
SessionQuestions before handing them to the P3.8 persistence/CAS boundary.
Clients cannot provide raw prepared questions.

Profile-only legacy starts remain valid and may produce an empty session.

## Alternatives considered

### Put ranking inside P3.5

Rejected. P3.5 is deliberately an eligibility layer reused by both later
session and scheduler policies. Mixing ranking into it would couple unrelated
delivery surfaces and make constraint tests harder to reason about.

### Materialize reservations in Progress

Rejected. Merely selecting or pre-queuing a card is not a learning event and
must not alter SRS history or consume an introduction.

### Recompute fatigue from session_answers

Rejected. P3.8 session answers are transport/session persistence, not canonical
pedagogical evidence. `review_events` remains the audit source of truth.

### Automatically switch mode when fatigue is detected

Rejected. The spec requires an offer, not an invisible behavior change.
Automatic switching could reinterpret subsequent learning interactions without
the learner's choice.

## Consequences

- P3.8 real-HA `session/answer` CAS can now be qualified through the public
  start path once an eligible Track/card exists.
- Session planning is deterministic, explainable and side-effect free.
- New-card quotas count actual introductions, not speculative prepared cards.
- Fatigue mitigation cannot silently rewrite SRS history.
- P3.10 still owns known/suspend/bury/calibration and P3.11 still owns
  leech/confusion/annotation behavior.
- P4 remains responsible for notification/scheduler arbitration.

## Verification

P3.9 adds focused selection/fatigue tests and converts the existing two-client
WebSocket CAS test to start a session through the public backend-selection path.

The repository-wide Ruff/mypy/resource/pytest gate must pass before P3.9 is
marked PASS.
