# ADR-0057 — Beta.5 natural-language Latin quiz case normalization

## Context

ADR-0028 originally described `exact` and `any_of` free-text grading as raw byte-for-byte comparisons. Beta.5 real-user testing exposed a false failure for Latin-script natural-language answers: a phone keyboard can turn romaji `ko` into `Ko`, although case has no pedagogical value for that answer.

The existing normalization model is explicitly script-aware and already supports Unicode casefold. The Japanese Starter romaji facet is correctly tagged `Latn`; no Japanese-specific branch is required.

## Decision

For the runtime natural-language panel policy `quiz_free_text`:

- `Latn` answers use Unicode `casefold()` in addition to the existing Unicode/whitespace/punctuation normalization;
- `exact` means equality **after** that declared normalization, with no edit-distance tolerance;
- `any_of` means membership after the same normalization, also with no edit-distance tolerance;
- non-Latin scripts keep their declared case behavior;
- `fuzzy_normalized` remains a separate policy and is the only policy that may use the conservative single-edit rule.

This decision supersedes only ADR-0028's raw byte-for-byte wording for `exact`/`any_of`. It is a pre-1.0 contract correction discovered during Beta.5 testing, not a generic rule that every future Latin-script content type must be case-insensitive. A future case-sensitive domain must use an explicit policy rather than relying on the natural-language `quiz_free_text` policy.

## Alternatives considered

- Calling `.lower()` on every answer: rejected because it is not Unicode-complete and is not script/policy aware.
- Casefolding every script globally: rejected because normalization must remain explicit and script-aware.
- Switching romaji to `fuzzy_normalized`: rejected because case-insensitivity must not implicitly enable typo tolerance.
- Fixing only the mobile keyboard: rejected because backend grading remains authoritative and must accept semantically equivalent input from every client.

## Consequences

`ko`, `Ko`, and `KO` grade identically for romaji while `ka` remains wrong for expected `ko`. The backend remains authoritative; mobile `autocapitalize="none"` and autocorrection disabling are complementary UX protections, not correctness requirements.

**Status:** Accepted — 2026-10-04.
