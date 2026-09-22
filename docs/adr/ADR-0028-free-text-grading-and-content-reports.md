# ADR-0028 — Versioned free-text grading and recoverable content feedback

## Status

Accepted for P3.7 on 2026-09-22, pending final quality gate.

## Context

LockLearn V1 supports panel free-text answers with versioned grading metadata.
A grading result must distinguish a definitive wrong answer from a plausible
answer that the current dataset does not recognize.

The content model already stores stable grading-policy kind/version metadata and
script-aware normalization primitives. ReviewEvent already persists
`grading_result` and `normalization_version`. P3.7 connects those contracts
without moving session concurrency or full question persistence out of P3.8.

## Decision

### Supported V1 grading policies

P3.7 implements:

- `exact`: one explicit accepted answer, byte-for-byte text equality;
- `any_of`: exact membership in an explicit accepted-answer set;
- `fuzzy_normalized`: versioned script-aware normalization followed by a
  conservative fuzzy comparison.

`rule_based_reserved` remains reserved and is rejected in V1.

Every result carries both `grading_policy_version` and
`normalization_version`.

### Fuzzy-normalized is opt-in and script-gated

Fuzzy matching is unavailable unless the supplied NormalizationPolicy declares
explicit supported scripts. The generic core therefore does not infer
Japanese-, Latin- or other language behavior from a language tag.

After normalization, V1 accepts:

- an exact normalized match; or
- for normalized strings of length >= 4, a single insertion/deletion/
  substitution difference.

This behavior is part of grading-policy version semantics and must change only
through a new version.

If the only difference is Unicode diacritics on otherwise identical text, the
fuzzy typo rule does not auto-accept it. This preserves the normalization
contract that semantically meaningful accents are not silently erased.

### wrong and unrecognized are distinct

A normal unmatched answer is initially `wrong`.

When the learner invokes "Ma réponse devrait être acceptée", the grader converts
that non-correct result to `unrecognized`:

- `is_definitive_failure = false`;
- the answer becomes reportable;
- no automatic SRS failure is implied.

SignalPolicy already treats `unrecognized` as neutral, so P3.7 does not apply
a relapse or verified-wrong mutation.

A result that was already correct cannot be converted to unrecognized.

### Content report workflow

`locklearn/content/report` is a profile-scoped authenticated WebSocket command.

It requires backend `ANSWER` permission, validates the Track belongs to the
Profile, validates the exact active CardDefinition identity, and verifies the
card is enabled in that Track.

The report is persisted as a private `audit_events` row with
`event_type = content_report`. The payload stores:

- report kind;
- Track/CardDefinition identity;
- submitted and normalized text;
- grading policy kind/version;
- normalization version;
- active dataset generation;
- `grading_result = unrecognized`.

No new state schema is required because V1 only needs an append-only report
workflow, not a moderator/status queue. A future moderation workflow may promote
reports into a dedicated schema through an explicit migration.

### Dataset-generation authority

The WebSocket client does not choose the report's dataset generation. The
backend records the active content generation from ContentGenerationManager.

P3.8 will later persist generation identity per question/session so reports can
remain tied to an already-presented question across a concurrent content switch.

### ReviewEvent integration

P3.1 ReviewEvent already persists `grading_result` and
`normalization_version`. P3.7 returns both pieces of versioned grading metadata
for the answer pipeline to pass through unchanged.

P3.7 does not own session CAS or answer mutation; that integration remains P3.8.

## Consequences

- plausible unknown answers remain recoverable instead of becoming irreversible
  false failures;
- normalization behavior is explicit, versioned and script-aware;
- semantic diacritics are not accidentally accepted by generic typo tolerance;
- content feedback is private, ACL-checked and tied to exact content identity;
- report submission cannot mutate SRS state;
- P3.8 can compose the grader with persistent session answers without changing
  the grading contract.

## Verification

P3.7 tests cover exact/any-of membership, script-gated fuzzy normalization,
normalization-version propagation, semantic-diacritic protection, conversion to
unrecognized, no progress mutation from content reports, report persistence,
WebSocket ACL and ReviewEvent normalization-version persistence.

Final Ruff/mypy/resource/pytest results are recorded after the quality gate.
