# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 and P1.1–P1.6 are complete. P1 remains in progress on
`feat/p1-content-core`. P1.6 received a post-review hardening pass for
cancellation-safe switching, stale-parent rejection and rollback crash recovery.

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
- Post-review P1.6 hardening: the commit containing this handoff.
- Branch is pushed to GitHub; no PR/merge/tag has been created by this handoff.

## Verification

Baseline P1.6 verification before the post-review hardening commit:

- `python3 -m ruff format --check .`: pass, 122 files already formatted.
- `python3 -m ruff check .`: pass.
- `python3 -m mypy custom_components datasets tests`: pass, 57 source files.
- `python3 datasets/tools/validate_resources.py`: pass.
- `python3 -m pytest -q --tb=short`: pass, 151 tests in 2.11 s.
- HA current 2026.9.3 / Python 3.14 backend: included above; 97 backend tests
  also pass when run after the final additions as part of the full 151-test run.
- HA minimum 2025.2.5 / Python 3.13.15 backend: pass, 97 tests in 2.52 s.
- Targeted content/storage suite immediately before final full runs: pass;
  subsequent full runs include the same tests.

No frontend files changed. No frontend command was needed for P1.6.

The post-review hardening commit adds regression tests but was authored through
the GitHub connector rather than the Ubuntu checkout, so the baseline commands
above must be rerun on the updated branch before merge.

## Remaining risks / next action

- P1.7 owns the detailed source/snapshot/provenance/license registry; P1.6 only
  persists the existing minimal Source/Dataset contract.
- P1.9 owns download orchestration, update entities, Repairs and user-facing
  install/rollback policy; P1.6 supplies the storage primitives.
- P1.11 owns full Asset metadata and serving; P1.6 stores only P1.3 stable media
  references in validated payload JSON.
- Applying validated stable-ID mappings transactionally to future user-state
  tables belongs with the released `state.db` schema; P1.6 prevents incomplete
  item/facet mappings from activating.

Next concrete action: review/merge P1.6, then plan P1.7 separately. Do not begin
P1.7 as part of this handoff.
