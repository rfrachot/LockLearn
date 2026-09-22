# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 remain complete. P1 is in progress on `feat/p1-content-core`, with
P1.1 complete and no P1.2/P1.3/P1.5 or starter-dataset implementation started.

P1.1 now provides typed Source, Dataset, Concept, Term, LearningItem, Facet and
CardDefinition domain objects. Card identity is deterministic from only the
LearningItem ID and ordered prompt/answer facet IDs. Concepts remain
source-native, cross-source alignment is explicit and confidence-bearing, and
released identity changes require typed old-to-new migration mappings.

## Branch / commits

- Branch: `feat/p1-content-core`
- P0 base: `5bdcc06d6d92816d126fcfc67a3d1e0462069da5`
- P1.1 implementation: `89d1656b0ecf7633638d5363b54b26ccc5ad2b0e`
- P1.1 invariant tests: `29d26e58f920cc31ee893f2cfa4e62ef6bbae3bc`
- P1.1 closure: ADR/docs/test hardening committed with this handoff after final
  verification
- ADR-0008 freezes content/card identities, cross-source alignment and future
  migration consequences.

## Verification

- Ruff format: pass (101 files).
- Ruff check: pass.
- mypy (`custom_components datasets tests scripts`): pass (46 source files).
- pytest full suite on Python 3.14.4 / HA 2026.9.3: 41 passed.
- dataset resource validation: pass.
- frontend: typecheck pass; 2 Vitest files / 3 tests pass; production build
  pass, 21.96 kB / 7.13 kB gzip.
- backend compatibility: 35 passed on HA 2025.2.5 / Python 3.13.15 and 35
  passed on HA 2026.9.3 / Python 3.14.4.

## Remaining risks / next action

- Stable IDs depend on importers choosing durable upstream/source-owned inputs;
  P1.5 must validate complete transitive mappings before content activation.
- P1.2 must add content blocks, reveal semantics, grading metadata and safe rich
  text without adding those mutable fields to card identity.
- P1.5 still owns the complete `content.db` schema, generations, activation,
  tombstones and migration execution.

Next concrete action: start P1.2 only. Do not begin P1.3, P1.5 or the starter
dataset as part of the P1.1 closure.
