# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 remain complete. P1 is in progress on `feat/p1-content-core`.
P1.1, P1.2 and P1.3 are complete. P1.3 was verified on the Ubuntu development
checkout after the final code changes; the final branch-only delta before
closure was Ruff formatting with no semantic behavior change.

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

Next concrete action: start P1.4 multilingual normalization and locale
primitives only. Do not begin P1.5/P1.6 or grading-engine work as part of P1.4.
