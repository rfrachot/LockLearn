# ADR-0027 — Deterministic quiz construction and safe distractors

## Status

Accepted for P3.6 on 2026-09-22, pending final quality gate.

## Context

LockLearn V1 needs panel MCQ and grammar cloze-MCQ questions that are
pedagogically plausible without teaching false associations. The quiz layer must
also preserve explicit "Je ne sais pas", immediate corrective feedback outside
exam mode, deterministic example rotation and reproducible question generation.

P3.6 must not absorb free-text grading (P3.7), persistent session concurrency
(P3.8), or the later session selector/ranker (P3.9).

## Decision

### Quiz construction consumes a bounded/indexed candidate pool

The core QuizEngine receives candidate answers from a caller-owned indexed pool.
It never performs corpus-wide random SQL selection.

P3.6 deliberately keeps storage lookup and quiz construction separate:
repository/query code may narrow candidates by indexed Pack/content metadata,
while QuizEngine performs only deterministic safety filtering and selection.

No `ORDER BY RANDOM()` exists in QuizEngine.

### Panel MCQ size and explicit IDK

Panel MCQ questions contain 4–6 answer options. `Je ne sais pas` is represented
as a distinct action outside those answer options and remains available on every
question.

Selecting IDK returns an explicit `idk` result; it is never converted into a
guessed wrong option.

### Distractor safety filtering

Before final selection, QuizEngine excludes at minimum:

- the correct answer itself;
- another answer from the current LearningItem when relevant;
- explicitly identified sibling answers;
- an answer whose normalized form is already accepted;
- answers tied to the same native concept;
- explicit synonym relations supplied by the content/pool metadata;
- duplicate answer IDs or duplicate normalized answers.

Confusable candidates are rejected for `new`, `learning` and
`relearning`; they are eligible only for `review`, reusing the P3.5
stability rule.

### Distractor strategy and deterministic resampling

Candidates may carry one or more strategy labels:

- same_level;
- same_type;
- similar_semantics;
- same_tag;
- confusable;
- random_fallback.

The engine ranks safe candidates by strategy priority and a stable SHA-256 value
derived from `card_key + presentation_index + answer_id`.

Including `presentation_index` means distractors are re-sampled across
presentations while an identical presentation can be reproduced exactly for
debugging.

### Correct-answer position balance

The correct answer index is derived from the persisted
`answer_position_balance` counter modulo the current option count.

After construction, the engine returns the next balance value. Repeated
questions therefore rotate the correct position instead of accumulating a
position bias.

### Example rotation

When a LearningItem exposes several examples, QuizEngine selects one from the
persisted `example_rotation_index` and returns the next index.

Rotation is deterministic and independent from distractor sampling.

### Grammar cloze-MCQ

`cloze_mcq` is accepted only for `content_type = grammar` and requires an
explicit masked/cloze prompt produced by the content/rendering layer.

Its distractor pool is additionally restricted to grammar candidates. This
prevents a grammar exercise from accidentally becoming a vocabulary-reading
difficulty test.

### Corrective feedback

Outside exam mode:

- correct answer -> immediate positive feedback;
- wrong answer -> immediate reveal of the correct answer;
- IDK -> immediate reveal of the correct answer;
- known confusable distractors may attach contrastive feedback.

Every question is marked reportable for the later dataset-quality workflow.

Exam mode records the result but suppresses immediate reveal/feedback.

### Context hints

QuizPrompt carries an optional context hint produced by the CardDefinition/content
layer. The engine preserves it unchanged; it does not synthesize
language-specific disambiguation logic.

## Consequences

- quiz generation is deterministic and reproducible without corpus-wide random
  SQL;
- accepted answers and same-concept alternatives cannot silently become wrong
  distractors;
- weak/stabilizing states are protected from confusable interference;
- answer-position and example rotation remain testable state rather than UI
  randomness;
- P3.7 can grade free-text answers independently;
- P3.8/P3.9 can persist/question-select without reimplementing quiz safety.

## Verification

P3.6 tests cover 4–6 options, explicit IDK, safety exclusions, confusable
stability, deterministic resampling, answer-position balance, example rotation,
grammar-only cloze distractors, immediate/contrastive feedback, exam feedback
suppression and invalid quiz construction.

Final Ruff/mypy/resource/pytest results are recorded after the quality gate.
