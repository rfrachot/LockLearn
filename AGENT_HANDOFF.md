# AGENT_HANDOFF.md

## Current state

P0.1–P0.7, P1.1–P1.11 and P2.1–P2.2 are complete. P1 is closed PASS and P2
is in progress on `feat/p1-content-core`. P2.3 — Backend ACL and privacy
filtering — is implemented and awaiting the combined local quality gate.

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

- P1.11 owns full Asset metadata and serving; P1.6 stores only P1.3 stable media
  references in validated payload JSON.
- Applying validated stable-ID mappings transactionally to future user-state
  tables belongs with the released `state.db` schema; P1.6 prevents incomplete
  item/facet mappings from activating.

P1.6–P1.11 are closed PASS. The signed-starter P1 exit gate is satisfied and
the full P1 content/data-supply-chain phase is complete. Next concrete action:
begin P2.1 state.db foundation and application repositories.


## P1.9 closure

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

Final Ubuntu verification after the P1.9 fixture/style remediation:

- `python3 -m ruff format --check .`: pass, 138 files already formatted.
- `python3 -m ruff check .`: pass.
- `python3 -m mypy custom_components datasets tests`: pass, 69 source files.
- `python3 datasets/tools/validate_resources.py`: pass.
- `python3 -m pytest -q --tb=short`: pass, 188 tests in 3.10 s.

ADR-0016 records the runtime trust/update boundary.


## P1.10 closure

P1.10 adds the actual bundled `Japanese Starter 1.0.0` product required by
the first-run spec. It contains 120 LockLearn-authored LearningItems and 240
CardDefinitions covering basic hiragana, basic katakana, a small yōon sample
and 20 complete Japanese words with contextualized readings. It deliberately
contains no isolated ON/KUN cards.

The source is `locklearn:original` first-party editorial content under
CC BY-SA 4.0. Source JSONL, DatasetRecipe and build config remain in the
repository. The signed ZIP is bundled under
`custom_components/locklearn/datasets/bundled/` and is 178478 bytes.

Fresh runtime setup installs the bundle without any network request. It goes
through the same P1.9 checksum, Ed25519, manifest, source/license, SQLite,
generation-build and atomic-activation path as downloaded official content.
Existing installations are not downgraded. Corrupt bundle validation produces
the normal persistent install Repair and preserves last-known-good content.

The immutable 1.0.0 package was signed on an ephemeral GitHub Actions runner.
Only public key `locklearn-starter-2026-01` remains and is marked deprecated;
the private key and one-shot signing workflow were destroyed/removed after the
artifact was committed. Future builds therefore require a new reviewed key and
dataset version.

Tests cover semantic recipe output, real bundled signature validation, first-run
offline activation, query, idempotent bootstrap, rollback/reinstall, real HA
setup bootstrap and corrupt-bundle Repair behavior.

ADR-0017 records the bundled starter and signing lifecycle.

Final P1.10 verification:
- local Ubuntu: mypy PASS (72 source files), resource registries PASS,
  pytest PASS (192 tests in 3.54 s); Ruff reported only formatting/lint issues.
- follow-up GitHub closure gate after the exact Ruff fixes: Ruff format PASS,
  Ruff lint PASS, mypy PASS, resource registries PASS and full pytest PASS.

P1.10 is closed PASS and the signed-starter P1 exit gate is satisfied. Next
concrete action: implement P1.11 Asset schema.


## P1.11 closure

P1.11 completes the media-ready Asset contract without pulling renderer work
into the V1 critical path.

Content schema v2 now represents signed public dataset media through
`assets_metadata` and `facet_assets`. Asset metadata includes stable
`asset_id`, dataset ownership, image/audio kind, normalized package-relative
path, exact SHA-256 and byte size, MIME type, image dimensions where required,
asset-scope license and attribution.

The build pipeline accepts explicit BuildAssetInput records, derives hashes and
sizes from the exact bytes, adds media members under `assets/`, records Asset
provenance/license metadata in SQLite and includes every asset in the signed
manifest. Package validation binds manifest Asset payloads back to
`assets_metadata` exactly.

Facet kinds and ContentBlock kinds reserve `image` and `audio` semantics now.
Media ContentBlocks use the closed payload shape `{"asset_id": ...}`; validators
require same-dataset, matching-kind Asset references. No renderer was added.

Runtime DatasetManager extracts public media into a reconstructible content
cache and `async_resolve_public_asset()` rechecks size and SHA-256 before
returning a local path. This resolver only exposes assets present in the active
signed public content generation. Private user uploads, annotations and
export/import attachments remain a separate future state/private-storage and
authenticated-serving boundary.

Content schema v1 compatibility is retained for the already-signed asset-free
Japanese Starter 1.0.0; new content builds use schema v2.

Final P1.11 GitHub technical gate on head
`4511d40d5c2318a9a177c5aa366316cca8c80da6`:

- `python -m ruff format --check .`: pass, 145 files already formatted.
- `python -m ruff check .`: pass.
- `python -m mypy custom_components datasets tests`: pass, 75 source files.
- `python datasets/tools/validate_resources.py`: pass.
- `python -m pytest -q --tb=short`: pass, 202 tests in 10.24 s.

ADR-0018 records the public dataset Asset/private-export media boundary.

P1 is now complete. Next concrete action: P2.1.


## P2.1 closure

P2.1 upgrades persistent user state from the P0 spike schema to state schema v2.
The schema now reserves the complete V1 state surface for profiles/members,
tracks and PackVersion pins, card/content rules, notification targets, lazy
progress, review events, annotations, sessions/items/answers, exam attempts,
scheduler config/materialized slots, notification interactions, stats and
settings.

No SQL FK crosses into content.db. New PackVersion and card references are
validated against the active content generation in repository code, and
`async_cross_domain_integrity_issues()` audits PackVersion/card references
already stored in state. Progress remains lazy: Profile/Track creation never
pre-populates card rows.

The v1→v2 migration checkpoints WAL, creates a coherent
`state.db.pre-migration-v1.bak`, builds a complete v2 candidate out-of-place,
copies the existing P0 session/session-answer/progress/audit rows inside one
transaction, validates integrity/FKs, checkpoints the candidate and atomically
switches state.db. A migration failure preserves the original DB and backup.

Application repositories now expose persistence primitives for Profile, Track
and explicit PackVersion pinning, lazy Progress creation and deterministic JSON
settings. P2.2/P2.3 retain ownership of onboarding and ACL policy; P2.4 owns the
full Track configuration behavior.

P0 WebSocket session probes remain compatible with their temporary
`p0-probe:*` identity until P2.2 replaces that boundary with real Profile/HA
user mapping.

Final P2.1 GitHub verification:

- `python -m ruff format --check .`: pass, 148 files already formatted.
- `python -m ruff check .`: pass.
- `python -m mypy custom_components datasets tests`: pass, 77 source files.
- `python datasets/tools/validate_resources.py`: pass.
- `python -m pytest -q --tb=short`: pass, 206 tests in 13.70 s.

ADR-0019 records the state.db v2 and migration boundary.

P2.1 is closed PASS. Next concrete action: P2.2 Profiles, presets and HA-user
mapping.


## P2.2 closure

P2.2 adds a ProfileService over the P2.1 repositories. Profile identity is a
LockLearn UUID/string generated independently from Home Assistant user IDs.
Initial ownership is stored in profile_members and profile + initial owners are
inserted in one writer transaction.

Presets child/standard/intensive/custom now provide mutable initial settings.
The V1 card-introduction defaults remain 3/8/15 for child/standard/intensive;
session length, daily push budget and quiet hours are initial values only and
can be overridden. Reserved _locklearn_* keys cannot be injected through user
settings.

Personal-profile onboarding is idempotent for one HA user and never reuses the
HA user ID as profile_id. Child/shared profiles can have multiple HA owners and
need no dedicated HA account.

Home Assistant ConfigFlowContext has no authenticated user identity. Therefore
the existing "create personal profile" config-flow value remains a preference;
P2.6 authenticated bootstrap will call the idempotent ProfileService rather than
guessing an owner during config-entry setup.

New tests in tests/backend/test_profiles.py cover personal mapping/idempotence,
child profiles with two owners, mutable preset defaults, invalid identity input,
and protection of internal settings markers.

Renaud's local gate after pulling `80825c9` reported:
- `python3 -m ruff format --check .`: only two formatting diffs, in
  `core/profiles.py` and `test_profiles.py`.
- `python3 -m ruff check .`: PASS.
- `python3 -m mypy custom_components datasets tests`: PASS, 79 source files.
- `python3 datasets/tools/validate_resources.py`: PASS.
- `python3 -m pytest -q --tb=short`: PASS, 210 tests in 4.12 s.

The exact Ruff-recommended formatting changes were then applied. P2.2 is closed
PASS; the next combined gate will revalidate those formatting-only edits together
with P2.3.

No PR, merge or tag has been created.


## P2.3 implementation pending verification

P2.3 adds `ProfileACLService` as the single backend profile authorization
authority. The V1 role matrix is encoded as owner/editor/viewer permissions:
owners have full profile rights; editors can read, edit tracks/planning, answer
and manage progress; viewers are read-only; outsiders have no profile access.

Normal profile listings and direct profile visibility are membership-filtered.
Direct visibility returns the same absence result for nonexistent and
unauthorized profiles. Home Assistant admin state is deliberately not accepted
as an ACL bypass input.

ACL membership mutations are owner-only. Repository writes protect the final
owner transactionally inside the single SQLite writer, preventing concurrent
remove/demote races from orphaning a profile.

`PERMISSIONS.md`, `PRIVACY.md`, and `SECURITY.md` now document the role
matrix, backend-authority rule, HA-admin separation, HA entity/event privacy
caveat, shared-child profiles, Companion boundary and backup/export privacy.

New tests in `tests/backend/test_acl.py` cover the complete role matrix,
negative outsider access, non-bypass by an HA-admin identity, owner-only ACL
mutation, and final-owner preservation. Profile CRUD/WebSocket endpoint-specific
negative authorization tests remain P2.6 scope because those endpoints do not
exist yet.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P2.3 and begin P2.4 Track configuration, pack pinning and card
rules.
