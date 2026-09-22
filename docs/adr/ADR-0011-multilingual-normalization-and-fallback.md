# ADR-0011 — Versioned multilingual normalization and locale fallback

## Status

Accepted for the P1.4 multilingual normalization contract on 2026-09-22.

## Context

LockLearn stores multilingual Terms and later grades free-text answers. A single
normalization algorithm cannot be applied safely to every language or script:
case folding, width normalization, punctuation handling and other transforms
have different semantic consequences depending on the dataset and writing
system.

The core must remain content-agnostic and must not contain branches such as
`if language == "ja"`. At the same time, normalization behavior must be
versioned so persisted `normalized_text` values and derived indexes can be
rebuilt deterministically when a policy changes.

Locale fallback is also needed for display/content selection, but fallback must
never manufacture a missing translation.

## Decision

### Language and script identifiers

Language tags use modern BCP 47 syntax and are canonicalized for casing:

```text
fr-fr      -> fr-FR
zh-hant-tw -> zh-Hant-TW
```

LockLearn rejects malformed tags and deliberately does not support legacy
grandfathered spellings in dataset metadata. Dataset/build tooling should use
modern tags so fallback remains deterministic.

Script metadata uses the four-letter ISO 15924 alpha-code form and canonical
title casing:

```text
latn -> Latn
jpan -> Jpan
```

The core validates the structural ISO 15924 representation. Dataset policies
then constrain which script codes are accepted for a given normalization policy.
A full external ISO registry is not embedded in the HA runtime.

If a BCP 47 tag explicitly carries a script, `Term.script` must match it. When
`Term.script` is omitted, the explicit BCP 47 script may populate it.

### Term normalization metadata

`Term` may carry:

```text
normalized_text
normalization_version
```

The pair is atomic: both are present or both are absent. Normalization metadata
is mutable derived content and never participates in `term_id`.

`Term.with_normalization(policy)` creates a new immutable Term value with the
same stable identity and policy-derived normalized text.

### Generic policy engine

Normalization behavior is selected by data through a
`NormalizationPolicy`. The generic engine supports explicit choices for:

```text
Unicode normalization: none | NFC | NFKC
case: preserve | casefold
whitespace: preserve | trim | collapse
punctuation: preserve | remove
allowed_scripts[]
normalization_version
```

No language name or language tag is inspected by `normalize_text()`.
Language-specific behavior is therefore expressed by registered policies, not
hard-coded branches.

The bootstrap registry currently maps Latin showcase languages to
`latin_default_v1` and Japanese to `japanese_v1`. Those policy names and
parameters are data choices. For example, the Japanese policy uses NFKC for
width normalization while preserving case; the core sees only generic policy
fields.

P1.4 does not implement advanced language-specific equivalence such as
hiragana/katakana folding or morphological rules. Those require explicit future
policy/adapters and tests rather than being silently applied to all Japanese
content.

### Versioning and rebuilds

Changing normalization behavior requires a strictly higher
`normalization_version`. Reusing the same version after changing policy
parameters is invalid.

A version or behavior change marks derived normalized values/indexes for rebuild.
The actual `content.db` migration/index rebuild machinery remains P1.6 scope.

### Locale fallback

Fallback is deterministic and ordered:

```text
exact requested tag -> base language -> explicit dataset default -> optional final fallback
```

Duplicates are removed while preserving order. Resolution returns an existing
value or `None`; it never synthesizes or translates content.

Examples:

```text
fr-FR -> fr -> dataset default
en-GB -> en -> dataset default
```

Frontend UI fallback may additionally provide English as its explicit final
fallback according to the frontend contract.

## Alternatives considered

- One global NFKC/casefold rule: rejected because transformations can change
  semantics for some languages/scripts.
- Hard-code Japanese rules in the core: rejected by the content-agnostic
  architecture invariant.
- Store normalized text without a version: rejected because index/grading
  behavior would become ambiguous after algorithm changes.
- Put normalization fields into stable Term identity: rejected because
  algorithm tuning must not replace the semantic Term.
- Automatically translate when fallback misses: rejected because fallback is
  selection, not content generation.
- Bundle a complete ISO 15924 registry in HA runtime: rejected for P1.4; the
  runtime validates standard code shape while data policies constrain accepted
  scripts.

## Consequences

- Normalization can evolve without resetting stable content identity.
- Dataset authors must explicitly select/version normalization policy behavior.
- Script/language metadata is canonicalized before persistence.
- Locale fallback is deterministic and cannot fabricate content.
- Future grading can depend on `normalization_version` without assuming that
  all languages share the same equivalence rules.
- P1.4 does not create the final content schema or rebuild indexes; P1.6 owns
  persistence/activation/migration execution.
