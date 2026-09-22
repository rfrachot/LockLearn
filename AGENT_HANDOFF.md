# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 and P1.1–P1.8 are complete. P1 remains in progress on
`feat/p1-content-core`. P1.9 DatasetManager/update-entity implementation is
on the branch and awaits local Ruff/mypy/registry/pytest verification before PASS.

P1.6 replaces the provisional P0 content table with normalized content schema
v1 for the P1.1–P1.5 domain: datasets/versions, Concepts, Terms,
LearningItems, Facets, CardDefinitions, safe ContentBlocks, Tags, Packs,
PackVersions, prerequisites, confusable groups, explicit ID migrations,
lifecycle tombstones/history and PackVersion pre-aggregates.

`ContentGenerationBuilder` copies the previous immutable generation, merges
validated packages one at a time (`main` + one attached package maximum),
preserves stable rows, rebuilds tombstones/aggregates, and exposes a candidate
only after schema, integrity, FK, stable-ID, P1.3 payload, migration-coverage and
aggregate validation.

`ContentGenerationManager` blocks new readers, drains real SQLite reader
leases, rejects candidates built from a stale parent generation, atomically
replaces the `current.db` hard link, and keeps a fsynced switch-intent journal
across the crash boundary. Cancellation and HA unload wait for the executor-side
switch to finish before reopening/closing the gate. Activated generation files
are read-only. Failed builds/activations preserve the last-known-good
generation. The exact unreleased P0 cache schema is rebuilt out-of-place without
touching `state.db`.

Removed/superseded LearningItems, Facets and CardDefinitions retain their rows
and current tombstones. Lifecycle history proves that
`active → removed → active` restores the exact LearningItem ID, Facet IDs,
`card_definition_id` and `card_key`; user progress remains exclusively in
`state.db`.

ADR-0013 records schema/version boundaries, bounded merge, activation,
lease/drain, rollback, tombstones, crash behavior and the no-fan-out decision.

## Branch / commits

- Branch: `feat/p1-content-core`
- Remote P1.5 closure pulled at start: `9881cfd36b98d245e810b3ad69ceba04124dbaff`
- P1.6 implementation/tests: `a5e2d11` (`feat(storage): add immutable content generations`).
- P1.6 ADR/tracking/handoff: `adde1c9` (`docs(storage): close P1.6 generation design`).
- P1.6 post-review hardening: `f5c2fe7` and verification fix `9ba254d`.
- P1.6 final verification/handoff closure: the commit containing this handoff.
- Branch is pushed to GitHub; no PR/merge/tag has been created by this handoff.

## Verification

Final P1.6 verification after post-review hardening on the Ubuntu development checkout:

- `python3 -m ruff format --check .`: pass, 122 files already formatted.
- `python3 -m ruff check .`: pass.
- `python3 -m mypy custom_components datasets tests`: pass, 57 source files.
- `python3 datasets/tools/validate_resources.py`: pass.
- `python3 -m pytest -q --tb=short`: pass, 157 tests in 2.38 s.
- Post-review cancellation, stale-parent, rollback-recovery, dataset-ownership
  and semantic migration regression tests are included in that 157-test run.
- Earlier HA minimum 2025.2.5 / Python 3.13.15 backend qualification remains
  recorded from the P1.6 baseline and must be rerun when the compatibility
  matrix is next exercised.

No frontend files changed. No frontend command was needed for P1.6.

## P1.7 closure

P1.7 upgrades the repository source/license registries to policy schema v2,
adds centralized field-allowlist/provenance gates, persists exact SourceSnapshot
and per-object provenance rows in content.db, and reserves an Asset provenance
boundary without implementing the P1.11 Asset schema.

Final Ubuntu verification after the compatibility remediation:
- `python3 -m ruff check .`: pass.
- `python3 -m mypy custom_components datasets tests`: pass, 57 source files.
- `python3 datasets/tools/validate_resources.py`: pass.
- `python3 -m pytest -q --tb=short`: pass, 165 tests in 2.54 s.
- The only remaining issue in that run was one Ruff-format-only wrapping change,
  applied by the subsequent style commit without semantic changes.

ADR-0014 records the source/snapshot/provenance/license-scope decision.

## P1.8 closure

P1.8 adds build-time-only streaming adapters for the recommended source set,
canonical normalized JSONL, a DatasetRecipe boundary, bounded fetches, exact
SourceSnapshot hashing, complete signed manifest v2 provenance, deterministic
semantic content hashing, Ed25519 package signing and external ZIP checksums.

`.github/workflows/datasets.yml` performs weekly lightweight source checks and
manual builds. Raw upstream downloads remain under ignored/temporary paths and
are never committed or uploaded as release assets. GitHub Release creation is
gated by a changed `canonical_content_hash`.

No production source corpus, signing private key, Japanese Starter recipe or
production build config is committed. The latter recipe/config belongs to P1.10.

Final Ubuntu verification after the P1.8 style/type remediation:

- `python3 -m ruff format --check .`: pass, 133 files already formatted.
- `python3 -m ruff check .`: pass.
- `python3 -m mypy custom_components datasets tests`: pass, 65 source files.
- `python3 datasets/tools/validate_resources.py`: pass.
- `python3 -m pytest -q --tb=short`: pass, 181 tests in 2.79 s.

ADR-0015 records the offline ETL/release boundary.

## Remaining risks / next action

- P1.9 owns download orchestration, update entities, Repairs and user-facing
  install/rollback policy; P1.6 supplies the storage primitives.
- P1.11 owns full Asset metadata and serving; P1.6 stores only P1.3 stable media
  references in validated payload JSON.
- Applying validated stable-ID mappings transactionally to future user-state
  tables belongs with the released `state.db` schema; P1.6 prevents incomplete
  item/facet mappings from activating.

P1.6, P1.7 and P1.8 are closed PASS. Next concrete action: plan/implement
P1.9 DatasetManager, update entity, staging and rollback without pulling P1.10
starter-content curation into the same work package.


## P1.9 implementation awaiting verification

P1.9 adds a local DatasetManager for official prebuilt artifacts. Remote release
catalogs are discovery-only and cannot authorize content: installation requires
bounded download, external SHA/size match, bundled-host allowlist, Ed25519
signature, compatibility, source/license policy, SQLite/package validation and
a validated full-generation build before P1.6 atomic activation.

The HACS integration bundles runtime copies of source/license policy plus empty
official dataset/public-key registries. P1.10 owns the first production dataset
definition and public signing key; no private key or raw corpus is bundled.

One UpdateEntity is supported per official dataset. Installed state loads
without network access. Repairs cover catalog failure, install/verification
failure and stale sources. PackVersions are retained across updates; explicit
dataset removal refuses PackVersions referenced by persistent track state.

Synthetic P1.9 tests cover signed install, v1→v2 update, pack-version retention,
rollback, checksum failure, failure after a valid install, explicit removal
guards, repair recovery and artifact-host allowlisting.

ADR-0016 records the runtime trust/update boundary.

Next concrete action: run the full local quality suite. If green, close P1.9
PASS. Do not begin P1.10 starter content before that gate.
