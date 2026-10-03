# ADR-0028 — Versioned free-text grading and recoverable content feedback

## Status

Accepted for P3.7 on 2026-09-22, amended for Beta.5 on 2026-10-04.

## Context

LockLearn V1 supports panel free-text answers with versioned grading metadata.
A grading result must distinguish a definitive wrong answer from a plausible
answer that the current dataset does not recognize.

The content model already stores stable grading-policy kind/version metadata and
script-aware normalization primitives. ReviewEvent already persists
`grading_result` and `normalization_version`. P3.7 connects those contracts
without moving session concurrency or full question persistence out of P3.8.

Beta.5 user testing exposed an important natural-language case: Latin-script
answers such as romaji must not become wrong merely because a mobile keyboard
changed `ko` to `Ko`. Case is not pedagogically meaningful for that answer, but
the runtime panel grader previously bypassed normalization for `exact` and
`any_of`.

## Decision

### Supported V1 grading policies

P3.7 implements:

- `exact`: one explicit accepted answer, exact comparison with no edit-distance tolerance;
- `any_of`: exact membership in an explicit accepted-answer set, with no edit-distance tolerance;
- `fuzzy_normalized`: versioned script-aware normalization followed by a conservative fuzzy comparison.

By default, `exact` and `any_of` preserve their historical raw-membership semantics. A caller may define a scoped natural-language normalization contract, as the panel does below; that does not turn either policy into fuzzy matching.

`rule_based_reserved` remains reserved and is rejected in V1.

Every result carries both `grading_policy_version` and `normalization_version`.

### Natural-language Latin quiz case handling

The runtime panel policy `quiz_free_text` normalizes `exact` and `any_of` before comparison. For `Latn`, it applies Unicode `casefold()` in addition to the existing Unicode/whitespace/punctuation normalization.

This rule is selected from script metadata rather than a Japanese language hardcode: romaji is one consumer, but the mechanism is generic for natural-language Latin-script panel answers. Non-Latin scripts keep their declared case behavior unchanged.

Within `quiz_free_text`, `exact` still means exact after normalization. It never enables the fuzzy single-edit rule, so case-insensitivity does not make `ka` equivalent to `ko` or `rests` equivalent to `rest`.

This is a pre-1.0 correction to the panel grading contract discovered during Beta.5 real user testing. Future behavioral changes after 1.0 require an explicit version increment/migration as appropriate.

### Fuzzy-normalized is opt-in and script-gated

Fuzzy matching is unavailable unless the supplied NormalizationPolicy declares explicit supported scripts. The generic core therefore does not infer Japanese-, Latin- or other language behavior from a language tag.

After normalization, V1 accepts:

- an exact normalized match; or
- for normalized strings of length >= 4, a single insertion/deletion/substitution difference.

This behavior is part of grading-policy version semantics and must change only through a new version.

If the only difference is Unicode diacritics on otherwise identical text, the fuzzy typo rule does not auto-accept it. This preserves the normalization contract that semantically meaningful accents are not silently erased.

### wrong and unrecognized are distinct

A normal unmatched answer is initially `wrong`.

When the learner invokes "Ma réponse devrait être acceptée", the grader converts that non-correct result to `unrecognized`:

- `is_definitive_failure = false`;
- the answer becomes reportable;
- no automatic SRS failure is implied.

SignalPolicy already treats `unrecognized` as neutral, so P3.7 does not apply a relapse or verified-wrong mutation.

A result that was already correct cannot be converted to unrecognized.

### Content report workflow

`locklearn/content/report` is a profile-scoped authenticated WebSocket command.

It requires backend `ANSWER` permission, validates the Track belongs to the Profile, validates the exact active CardDefinition identity, and verifies the card is enabled in that Track.

The report is persisted as a private `audit_events` row with `event_type = content_report`. The payload stores:

- report kind;
- Track/CardDefinition identity;
- submitted and normalized text;
- grading policy kind/version;
- normalization version;
- active dataset generation;
- `grading_result = unrecognized`.

No new state schema is required because V1 only needs an append-only report workflow, not a moderator/status queue. A future moderation workflow may promote reports into a dedicated schema through an explicit migration.

### Dataset-generation authority

The WebSocket client does not choose the report's dataset generation. The backend records the active content generation from ContentGenerationManager.

P3.8 will later persist generation identity per question/session so reports can remain tied to an already-presented question across a concurrent content switch.

### ReviewEvent integration

P3.1 ReviewEvent already persists `grading_result` and `normalization_version`. P3.7 returns both pieces of versioned grading metadata for the answer pipeline to pass through unchanged.

P3.7 does not own session CAS or answer mutation; that integration remains P3.8.

## Consequences

- plausible unknown answers remain recoverable instead of becoming irreversible false failures;
- existing non-panel `exact`/`any_of` callers keep their raw-membership behavior;
- the natural-language panel can apply explicit normalization without inheriting fuzzy typo tolerance;
- `ko`, `Ko` and `KO` are equivalent for the Latin natural-language quiz policy;
- non-Latin scripts are not blindly case-transformed;
- semantic diacritics are not accidentally accepted by generic typo tolerance;
- content feedback is private, ACL-checked and tied to exact content identity;
- report submission cannot mutate SRS state;
- P3.8 can compose the grader with persistent session answers without changing the grading contract.

## Verification

P3.7 tests cover exact/any-of membership, script-gated fuzzy normalization, normalization-version propagation, semantic-diacritic protection, conversion to unrecognized, no progress mutation from content reports, report persistence, WebSocket ACL and ReviewEvent normalization-version persistence.

Beta.5 regression tests additionally cover `ko` / `Ko` / `KO` equivalence for `Latn`, no edit-distance tolerance for exact/any-of, and preservation of non-Latin script behavior.

Final Ruff/mypy/resource/pytest results are recorded after the quality gate.
