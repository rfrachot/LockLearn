# ADR-0025 — Verified retrieval gate and signal weighting

## Status

Accepted for P3.4 on 2026-09-22, pending final quality gate.

## Context

LockLearn receives learning evidence from several channels whose evidentiary
strength is not equivalent. A revealed-answer self-assessment, MCQ, free-text
answer, hinted answer and shared-device notification action must not all have
the same effect on long-term SRS promotion.

The V1 specification also requires a configurable verified gate (recommended
box 2), periodic verified retrieval above that gate, weaker hinted/shared-device
signals, and a strict separation between notification responsiveness and
cognitive retrieval strength.

## Decision

### Normalize interactions before SRS mutation

P3.4 introduces a SignalPolicy that maps interaction semantics into a
SignalDecision with:

- positive / negative / neutral outcome;
- signal_quality;
- retrieval_occurred;
- verified;
- gate_eligible;
- reward_difficulty;
- an explainable reason.

ReviewPolicy remains responsible for deterministic scheduling; SignalPolicy
decides whether the current evidence is strong enough to invoke promotion,
demotion or only weak scheduling.

### Visible-answer self-assessment is never positive retrieval evidence

A positive self-assessment produced after the answer was already visible is
normalized to a neutral signal. It causes no long-box promotion.

A post-retrieval self-assessment before reveal remains a weak, non-verified
positive signal and may support early progression up to the verified gate.

### Verified gate

The default V1 gate is box 2.

A promotion whose target box is above the gate requires either:

- a gate-eligible verified retrieval in the current interaction; or
- a verified success already recorded in the current box.

When a box promotion consumes that evidence,
`verified_success_since_box` resets to zero. Therefore a card above the gate
must periodically obtain new verified evidence instead of climbing
indefinitely on weak self-assessment alone.

### Signal strength

V1 normalizes evidence as follows:

- exposure: neutral / no retrieval;
- post-retrieval self-assessment: weak, non-verified;
- MCQ correct/wrong: medium verified evidence;
- free-text/cloze/exam retrieval: strong verified evidence;
- hinted correct retrieval: verified but weak and no difficulty reward;
- IDK: distinct retrieval failure used for planning/relearning;
- unrecognized free-text: neutral, never automatic SRS failure.

The exact quiz/grading implementations remain P3.6/P3.7; P3.4 only defines how
their normalized outcomes affect SRS confidence.

### Shared devices

An untrusted shared-device answer is downgraded to reduced quality and is not
treated as gate-eligible verified evidence. It may still affect early weak
progression below the gate.

A profile may explicitly trust the shared-device signal; only then can it count
as verified evidence for the gate.

### Weak negative evidence

A weak self-assessed negative response can enter relearning, but does not apply
the verified relapse box penalty, verified-wrong counter or difficulty-factor
penalty. Those mutations require verified failure evidence.

### Latency boundary

SignalPolicy has no notification delivery/action latency input.
`delivery_to_action_ms` remains audit/receptivity data only.

Cognitive `presentation_to_answer_ms` remains a fluency statistic in V1 and is
also not an automatic SRS-strength modifier.

## Consequences

- weak self-assessment cannot indefinitely promote cards;
- visible-answer "I knew it" cannot become retrieval evidence;
- shared devices are conservative by default;
- hint usage is persisted and weakens confidence without discarding a genuinely
  verified retrieval;
- ReviewPolicy remains deterministic and reusable independently from UI/channel
  semantics;
- future P3.6/P3.7 grading engines can emit normalized signals without
  duplicating gate logic.

## Verification

P3.4 tests cover visible-answer blocking, weak progression up to the gate,
verified crossing and periodic refresh, shared-device trust, hinted evidence,
IDK, unrecognized answers and the absence of notification-latency inputs from
SignalPolicy. Final Ruff/mypy/resource/pytest results are recorded after the
quality gate.
