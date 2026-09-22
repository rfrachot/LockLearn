# ADR-0026 — P3.5 selection constraints: prerequisites, siblings and confusables

## Status

Accepted for P3.5 on 2026-09-22, pending final quality gate.

## Context

LockLearn V1 needs new-card prerequisite filtering, sibling burial and
confusable-introduction spacing before the later P3.9 session selector and P4
scheduler rank eligible cards.

The content model already stores pack-owned prerequisite card keys, generic
unlock thresholds and confusable groups. Progress and review history live in
state.db. P3.5 must combine those domains without moving user state into
content.db or duplicating later scheduler ranking.

## Decision

### Eligibility is separate from ranking

P3.5 introduces `SelectionConstraintService`. It answers only whether one
enabled Track CardDefinition is eligible now and why it may be blocked.

It does not choose the next card, interleave content types, enforce fatigue
policy or arbitrate tracks/targets. Those remain P3.9/P4 responsibilities.

### Candidate identity is Track-scoped

The service requires:

- profile_id;
- track_id;
- exact card_key;
- learning_item_id;
- current progress state.

The repository rejects cards that are not enabled in the Track's current card
rules and reads prerequisite/confusable metadata only from the Track's pinned
PackVersion.

### Prerequisites

For a new card, every declared prerequisite_card_key must have matching progress
for the same Profile and Track.

When `unlock_when` thresholds are declared, every prerequisite card must
satisfy every generic threshold. V1 supports:

- verified_correct_count;
- mastery;
- box.

When a prerequisite is declared without any explicit unlock threshold, P3.5
uses the conservative minimum semantic "introduced at least once"
(`seen_count >= 1`). This avoids treating a bare prerequisite declaration as a
no-op while not inventing an arbitrary mastery/box threshold.

Prerequisite checks apply only to new-card introduction. Existing
learning/relearning/review cards are never retroactively locked by later content
metadata.

### Sibling burial

CardDefinitions sharing one LearningItem are siblings.

The repository derives the latest sibling interaction from ReviewEvent history,
excluding the candidate card itself. P3.5 applies configurable defaults:

```text
new sibling gap    = 1440 minutes
review sibling gap = 240 minutes
```

Track settings may override these values with non-negative integer minutes.

Learning and relearning short-step cards are not delayed by sibling burial;
their timing remains owned by P3.2. This prevents sibling spacing from starving
same-day learning/relearning obligations.

### Confusable introduction spacing

ConfusableGroup metadata remains PackVersion-owned. For a new candidate,
P3.5 finds the latest first introduction of any other LearningItem in each
shared confusable group and blocks the candidate until
`min_intro_gap_days` has elapsed.

The check is introduction-only: existing review cards are not hidden merely
because a confusable neighbor was introduced recently.

### Confusable distractor boundary

P3.5 exposes one explicit rule for downstream quiz code:
confusable distractors are allowed only for cards already in `review`.

They remain forbidden for `new`, `learning` and `relearning`, matching the
V1 content-interference rule. Actual distractor generation remains P3.6.

### Time and determinism

All spacing comparisons use the injected Clock and persisted UTC timestamps.
The service returns machine-readable reasons and the latest
`blocked_until_utc` needed to explain eligibility.

No direct `datetime.now()` is used.

## Consequences

- prerequisite and spacing rules are deterministic and testable independently
  from session ranking;
- one sibling interaction cannot immediately prime another CardDefinition into
  a false success;
- strongly confusable LearningItems cannot be introduced inside their declared
  spacing window;
- urgent learning/relearning steps remain controlled by P3.2 rather than being
  accidentally postponed by sibling burial;
- Track pinning continues to determine which PackVersion's pedagogical
  constraints apply;
- P3.6 can reuse the explicit confusable-distractor state gate without
  reinterpreting content metadata.

## Verification

P3.5 tests cover prerequisite threshold success/failure, bare-prerequisite
exposure semantics, new/review sibling gaps, learning/relearning exemption,
Track gap overrides, confusable introduction spacing, confusable distractor
eligibility, Track-card membership and content-backed repository reads.

Final Ruff/mypy/resource/pytest results are recorded after the quality gate.
