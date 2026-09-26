# ADR-0046 — Server-authoritative Quiz panel answer flow

## Status

Accepted for P5.4 on 2026-09-26.

## Context

The P3 quiz engine, free-text grader, SignalPolicy and persistent session CAS
already define the pedagogical primitives required by the V1 Quiz panel. P5.4
must expose those primitives without making the frontend a grading or security
authority.

Two requirements create a deliberate asymmetry:

- MCQ, cloze-MCQ and explicit IDK may reveal the correction immediately, but a
  verified SRS signal must already correspond to the submitted answer when that
  correction is revealed.
- Free-text must let a learner mark an unmatched but plausible answer as
  "should be accepted" so the attempt can become neutral `unrecognized`
  evidence instead of an automatic SRS failure.

A non-mutating endpoint that revealed the correct answer for arbitrary attempts
would be an answer oracle: a client could inspect the correction and then
submit the known answer as a verified success.

## Decision

### Choice questions and IDK commit before correction reveal

MCQ, cloze-MCQ and direct IDK use `locklearn/quiz/answer`.

The backend:

1. rechecks Profile `ANSWER` permission and current session identity;
2. grades the submitted answer using the P3 QuizEngine;
3. derives the verified signal through SignalPolicy;
4. persists ReviewEvent, progress projection and session CAS atomically;
5. only then returns the corrective feedback and resulting session snapshot.

Generic `locklearn/session/answer` rejects Quiz sessions, so a client cannot
advance a Quiz while bypassing grading.

The persisted session question contains options and presentation metadata but
never a `correct_index` or `correct_answer` marker.

### Free-text uses a non-revealing provisional grade

`locklearn/quiz/evaluate` is restricted to free-text questions.

The first provisional answer is kept server-side for that session/question and
cannot be replaced by a different answer while the runtime remains loaded. The
provisional response may say whether the answer matched, but it does not reveal
the accepted answer.

The learner can then:

- accept the grade, causing `locklearn/quiz/answer` to persist that exact
  attempt before any correction is revealed; or
- invoke "this answer should be accepted", which first creates the existing
  private content report and then persists the same attempt as
  `unrecognized`. SignalPolicy treats that result as neutral, so no automatic
  SRS failure is applied.

If Home Assistant restarts while a provisional answer is pending, the
in-memory provisional lock is lost, but no accepted answer was disclosed. The
question can therefore be evaluated again without converting leaked correction
content into verified evidence.

### New cards are not Quiz material

Quiz sessions use `session_type = quiz`. The P3 session selector assigns no
new-card quota to that session type. P5.4 also filters any defensive
`progress_state = new` candidate before question preparation.

A card must therefore be introduced through Learn before Quiz can test it.

### Cloze is content-driven

P5.4 does not infer language-specific blanks. Cloze-MCQ is prepared only for a
grammar card whose content contains an explicit non-`none`
`mask_strategy`.

If no safe maskable content exists, that card is not emitted as cloze-MCQ.

### Free-text normalization remains explicit

The P3 grader supports `fuzzy_normalized` when supplied with an explicit
script-aware NormalizationPolicy.

The current content/runtime catalog persists `normalization_version` but does
not expose the complete NormalizationPolicy needed to reconstruct those
transformations. P5.4 therefore enables panel free-text automatically for
`exact` and `any_of`, whose semantics are self-contained, and refuses to
guess a fuzzy policy.

This does not remove `fuzzy_normalized` from the generic core. A future
dataset/runtime contract may expose the explicit policy required by ADR-0028;
at that point the panel can enable it without changing the answer-flow
architecture.

## Consequences

- frontend code never decides correctness or SRS mutation;
- corrective answers cannot be turned into verified successes through the
  normal WebSocket contract;
- free-text quality reports remain recoverable and neutral;
- Quiz cannot silently introduce new cards;
- cloze behavior remains generic and dataset-driven;
- unsupported normalization metadata fails closed instead of applying hidden
  language assumptions;
- no state.db migration is required for P5.4.

## Verification

P5.4 automated coverage includes:

- safe MCQ payloads without a correct marker;
- 4–6-option QuizEngine constraints inherited from P3;
- explicit IDK;
- non-revealing provisional free-text grading;
- prevention of changing a provisional answer;
- `unrecognized` recovery/report semantics;
- explicit cloze masking;
- rejection of generic session-answer bypass;
- atomic WebSocket Quiz grading, ReviewEvent persistence and progress update;
- frontend permissions, format routing and WebSocket contracts.
