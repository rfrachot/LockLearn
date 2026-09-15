# ADR-0002 — V1 language/resource seed

**Status:** Accepted for bootstrap

## Context

The engine must be language-agnostic, but V1 needs concrete language metadata,
UI localization and a Japanese showcase without hardcoding Japanese into core.

## Decision

Seed machine-readable language metadata for `en`, `fr`, `ja`, `es` and `de`.
Only FR/EN are required UI locales for V1. Japanese language-specific behavior
uses named normalization/rendering adapters selected by metadata rather than
core branches.

Seed source manifests for EDRDG, Wiktionary/Kaikki, Tatoeba and KanjiVG but do
not vendor their corpora in the application repository.

## Alternatives considered

- Japanese-only schema — rejected; violates product invariants.
- Import every available language immediately — rejected; unnecessary scope and
  validation burden.
- No language registry until datasets exist — rejected; BCP47/script/normalizer
  behavior is already a structural requirement.

## Consequences

Adding a new language is primarily data + normalizer/renderer capability work.
FR/EN UI catalogs are independent from the languages being learned.
