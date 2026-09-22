# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 remain complete. P1 is in progress on `feat/p1-content-core`; P1.1
and P1.2 are complete. The supplied P1.2 mission intentionally moved the signed
dataset package contract ahead of content blocks, so the plan/traceability now
place content blocks in P1.3 and the complete `content.db` schema in P1.6.

P1.2 provides a strict immutable manifest V1, exact-byte Ed25519 verification,
public-key validity/deprecation/revocation semantics, streamed payload hashes,
registry-backed official license/source policy, hostile-ZIP validation and
read-only standalone SQLite `integrity_check`. It validates packages without
installing/extracting them and does not define the future business schema.

## Branch / commits

- Branch: `feat/p1-content-core`
- P0 base: `5bdcc06d6d92816d126fcfc67a3d1e0462069da5`
- P1.1 implementation: `89d1656b0ecf7633638d5363b54b26ccc5ad2b0e`
- P1.1 invariant tests: `29d26e58f920cc31ee893f2cfa4e62ef6bbae3bc`
- P1.1 closure: `e931bb52e569e9a6f57536623b9d95602589b396`
- P1.2 closure: implementation, tests, ADR/docs and this handoff are committed
  together after final verification.
- ADR-0009 freezes the signed envelope, external ZIP-checksum boundary,
  historical key semantics and hostile-archive order.

## Verification

- Ruff format: pass (108 files).
- Ruff check: pass.
- mypy (`custom_components datasets tests scripts`): pass (52 source files).
- pytest full suite on Python 3.14.4 / HA 2026.9.3: 86 passed.
- dataset resource validation: pass.
- frontend: typecheck pass; 2 Vitest files / 3 tests pass; production build
  pass, 21.96 kB / 7.13 kB gzip.
- backend+dataset compatibility: 81 passed on HA 2025.2.5 / Python 3.13 and 81
  passed on HA 2026.9.3 / Python 3.14.4.

## Remaining risks / next action

- Stable IDs depend on importers choosing durable upstream/source-owned inputs;
  P1.6 must validate complete transitive mappings before content activation.
- P1.3 must add content blocks, reveal semantics, grading metadata and safe rich
  text without adding those mutable fields to card identity.
- P1.6 still owns the complete `content.db` schema, generations, activation,
  tombstones and migration execution.
- P1.8 still owns production signing/build tooling; no private production key
  or upstream parser exists in runtime/repository code.

Next concrete action: start P1.3 content blocks, grading metadata and safe rich
text. Do not begin the full content schema, upstream adapters, activation or the
starter dataset as part of P1.3.
