# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 remain complete. P1 is in progress on `feat/p1-content-core`.
P1.1, P1.2 and P1.3 are complete. P1.4 implementation is complete and awaits
repository verification on the Ubuntu development checkout.

P1.3 adds the generic content presentation/grading contract without changing
progression identity. `CardDefinition` now carries mutable
`answer_semantics`, versioned grading metadata and context-hint facet IDs,
while `card_key` and `card_definition_id` still derive only from LearningItem
+ ordered prompt/answer facet IDs.

Content blocks model semantic role, explicit answer revelation, masking strategy
and typed text/rich-text/media references. Text supports structured
reading/furigana/ruby segments without Unicode offsets. Rich text is a closed,
bounded AST; arbitrary HTML, links, remote media, event attributes and unknown
nodes/fields fail closed. `unrecognized` grading remains distinct from
`wrong` and is explicitly non-definitive for downstream SRS handling.

ADR-0010 records the safe AST, reveal/mask, ruby and grading-identity decisions.
P1.3 does not implement the frontend renderer, normalization engine, grading
engine, SRS behavior, full Asset schema, `content.db` schema or cloze
generator.

## Branch / commits

- Branch: `feat/p1-content-core`
- P1.1 closure: `e931bb52e569e9a6f57536623b9d95602589b396`
- P1.2 closure: `8ee51f17bdb5e61d2d4c50b9327b33d990a90c9c`
- P1.3 implementation commits begin at `d62a317540297486028e295dc63be131d7661666`
  and continue through the current branch head.
- ADR-0010: `docs/adr/ADR-0010-safe-content-blocks-and-grading.md`

## Verification

P1.3 PASS on the Ubuntu development checkout:

- Ruff format: pass (111 files already formatted on final head).
- Ruff check: pass.
- mypy (`custom_components datasets tests`): pass (49 source files).
- dataset resource registries: pass.
- pytest full suite: 102 passed in 1.19 s.

The mypy/registry/pytest run was performed immediately before the final
format-only commit; that last commit changed only Ruff line wrapping. Ruff
format was then re-run on the resulting head and passed. No frontend files
changed in P1.3.

## P1.4 implementation

P1.4 adds `core/localization.py` with modern BCP 47 parsing/canonicalization,
structural ISO 15924 script validation, deterministic locale fallback and
versioned generic normalization policies. The normalization engine has no
language-specific branches.

`Term` now canonicalizes language/script metadata and may carry the atomic
`normalized_text` + `normalization_version` pair. Applying a policy preserves
`term_id`. A changed policy behavior without a higher normalization version is
rejected so later persisted indexes can be rebuilt safely.

The bootstrap language registry now references a validated
`normalization_policies.json`; `latin_default_v1` and `japanese_v1` are
data-driven policies rather than core conditionals. ADR-0011 records these
boundaries and the exact -> base -> explicit default/final fallback contract.

## P1.4 verification pending

Required before changing P1.4 to PASS:

```text
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy custom_components datasets tests
python3 datasets/tools/validate_resources.py
python3 -m pytest -q --tb=short
```

## Remaining risks / next action

- P1.4 owns BCP 47/ISO 15924 validation, `normalized_text`,
  `normalization_version`, script-aware policies and locale fallback.
- P3.7 owns actual exact/any_of/fuzzy grading execution and the
  “Ma réponse devrait être acceptée” quality workflow.
- P1.6 owns the complete `content.db` schema, persistence/generation activation
  and stable-ID migration execution.
- P1.11 owns full Asset metadata and serving; P1.3 only carries stable media
  references.
- The future Lit renderer must map the rich-text AST node-by-node and must never
  route dataset strings through `unsafeHTML`.

Next concrete action: verify and close P1.4 PASS. Only after that, start P1.5
tags/packs/prerequisites and Japanese curation primitives. Do not begin P1.6 or
grading-engine work as part of P1.4.
