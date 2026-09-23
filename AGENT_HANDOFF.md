# AGENT_HANDOFF.md

## Current state

P4.1 implementation is now on `feat/p4-scheduler` from the final P3 HEAD
`146b48a3bf0f8331feecff20d4784029d290b7bb`. It adds deterministic
profile-level scheduler generation, a persistent SchedulerRepository,
`locklearn/scheduler/preview`, backend tests, `docs/SCHEDULER.md` and
ADR-0036. Materialized `scheduled_slots` are append/idempotent authority after
creation; config version changes never rewrite an existing row. P4.1 slots are
generic time opportunities only: Track, target and CardDefinition selection are
left to P4.3/P4.5 send-time policy. Cross-midnight active windows and temporal
reconciliation remain explicitly P4.2.

Repository quality gates for this P4.1 implementation still need to be run in a
development checkout. Do not mark ADR-0036 accepted or P4.1 PASS until Ruff
format/lint, mypy, resource validation and pytest are green.

P0.1–P0.7, P1.1–P1.11, P2.1–P2.6 and P3.1–P3.14 are complete. P1, P2 and P3
are closed PASS. The completed P3 work remains on `feat/p3-sessions` pending
the normal branch/merge workflow.
P3.8 and P3.9 are PASS. P3.8's targeted real-HA qualification ran on 2026-09-23
at `417ff41df90cf137e2751320d72e3166bdc0793b` after HACS explicitly
redownloaded `feat/p3-sessions` and HA restarted. It exercised public P3.9
selection into a real question, simultaneous two-client answer CAS (one primary
winner, one `locklearn/stale_session` loser, one immutable answer), navigation
undo, reconnect, Config Entry reload/subscription cleanup, storage diagnostics
and public cleanup. The baseline three sessions/three answers was restored.

P3.10 adds user-owned card state without a DB migration: `active`,
`known_already`, indefinite `suspended`, and timed `buried`. State changes
are audited as `progress_user_state` rather than ReviewEvents, preserve SRS
counters/due state and remain independent from content_status. P3.9 now filters
user state itself so an expired buried card becomes logically active without a
hidden write. The initial calibration sampler is deterministic/read-only,
accepts requested sizes 20–40 and creates no Progress rows. ADR-0031 records
that P3.12 owns preservation/replay of these non-pedagogical overlays during
rebuild/recompute. Backend and WebSocket ACL tests are present. Final P3.10 gate on 2026-09-23:
Ruff format PASS (197 files), Ruff lint PASS, mypy PASS (109 sources), resource
registries PASS and pytest PASS (292 tests in 7.12 s).

P3.11 implements the normative `leech` scheduling state with state schema
v3 and an explicit v2→v3 Progress-table migration. LeechPolicy V1 evaluates
trusted verified ReviewEvents using the 6 failures / last 10 attempts / 60 days
or 8 verified relapses / 60 days thresholds. Detection is written into the
triggering ReviewEvent post-state, not as a projection-only mutation. Ordinary
session selection treats leeches as fallback and supports explicit
`leeches_only=true` targeted sessions. Confusion matrices are derived from
expected/chosen answer IDs already stored in ReviewEvents. Private
LearningItem/CardDefinition annotations reuse `user_annotations`, prioritize
personal mnemonic remediation, and follow Profile READ/MANAGE_PROGRESS ACL.
Manual reactivation uses a canonical non-retrieval ReviewEvent. ADR-0032 records
the design. Migration, policy, integration, session and WebSocket privacy
tests are present. Final P3.11 gate on 2026-09-23: Ruff format PASS (202 files),
Ruff lint PASS, mypy PASS (113 sources), resource registries PASS and pytest
PASS (300 tests in 7.48 s).

P3.12 separates three integrity operations. Progress undo is append-only:
the latest admissible ReviewEvent is compensated using its pre_state_snapshot,
with the target relation stored in a private `progress_undo` audit record and a
transactional current-state recheck to reject races. Historical progress rebuild
uses stored post-state snapshots exactly as applied while preserving P3.10
user/content overlays, including overlay-only Progress rows. Explicit admin
recompute currently supports target policy V1, replays supported interaction
modes at historical timestamps, excludes explicitly undone evidence, recalculates
leech state and produces card-level changed-field divergences. Any unsupported
historical replay mode makes the operation fail closed with `applied=false` and
no Progress replacement. `stats_daily` rebuild is independent and excludes
undone events. Admin rebuild/recompute use OperationRegistry and expose terminal
result payloads. ADR-0033 records the design. Integrity, operation and WebSocket ACL tests are present. Final
P3.12 gate on 2026-09-23: Ruff format PASS (206 files), Ruff lint PASS, mypy
PASS (116 sources), resource registries PASS and pytest PASS (309 tests in
8.20 s).

P3.13 makes `stats_daily` a live rebuildable projection: every committed
ReviewEvent refreshes its historical local-date row atomically, while undo
refreshes both the source and compensation days. `locklearn/stats/get` is
profile-private READ-only and reports due-through-local-midnight, new/learning/
review/relearning/leech counts, latest trusted verified retention, recent
verified accuracy, secondary time-decayed mastery, metacognitive calibration,
frequent confusions, daily aggregates and streak status. Calibration counts
distinct cards declared known through P3.10 `known_already` audit or positive
post-retrieval self-assessment and compares the first later trusted verified
retrieval. Streak uses an 80% due-queue goal by default, configurable absolute
minimum and one grace day; no-due days are neutral. Historical local dates and
timezone names remain immutable when a profile timezone changes. ADR-0034
records the design. Stats/domain/timezone/WebSocket ACL tests are present. Final
P3.13 gate on 2026-09-23: Ruff format PASS (210 files), Ruff lint PASS, mypy
PASS (119 sources), resource registries PASS and pytest PASS (313 tests in
8.71 s).

P3.14 adds a deterministic 180-day quality simulator using the actual
LearningStateMachine, ReviewPolicyV1 and LeechPolicyV1. Production preset
new-card quotas are reused (child 3, standard 8, intensive 15 cards/day).
Declared positive-bench review capacities are 30/80/150 cards/day respectively
and are simulation assumptions only; no runtime default has changed. The
simulator treats max_new_per_day as a ceiling and throttles introductions when
the opening due queue consumes capacity, matching P3.9 due-first session
selection; throttled cards/days are reported explicitly. The matrix
covers typical, mixed and bursty learners plus an explicit negative-control
stress case. Detectors cover sustained due backlog, >7-day starvation,
systemic short-step cap exhaustion/relearning oscillation (repeat on a card or
>=1% of introduced cards), box promotion beyond accumulated verified-success
evidence, and excessive p95 daily interactions
after accounting for expected short-step work.
`tests/backend/test_srs_simulation.py` checks reproducibility, preset coverage,
required-scenario sustainability and negative-control sensitivity.
`scripts/p3_14_srs_simulation.py` prints JSON and exits non-zero if a required
scenario fails or the negative control unexpectedly passes. ADR-0035 records
the methodology. Do not tune SRS/preset defaults or mark P3.14 PASS until the
simulation output and normal repository gate are both green.

P3.14 measured qualification on 2026-09-23 is functionally green:
child_typical, standard_typical, standard_mixed, standard_bursty and
intensive_typical are sustainable under due-first new-card throttling.
standard_mixed remained bounded at backlog 77 final / 96 max with 208 deferred
new cards and max overdue age one day at 0.818412 verified accuracy.
standard_bursty remained bounded at 48 / 97 with 112 deferred new cards and max
overdue one day. The explicit stress negative control remained unsustainable
and triggered due_queue_explosion, relearning_oscillation and
unrealistic_daily_workload, proving detector sensitivity. The qualification run had Ruff lint PASS, mypy PASS (121 sources), resource
registries PASS and pytest PASS (318 tests). The final repository gate after the
format-only fix passed on 2026-09-23: Ruff format PASS (214 files), Ruff lint
PASS, mypy PASS (121 sources), resource registries PASS and pytest PASS
(318 tests in 15.14 s). P3.14 and the full P3 phase are therefore closed PASS
without changing SRS/preset defaults.

The only unavailable supplemental proof is real viewer/outsider ACL: one HA
development-user token is configured, and no second usable token exists in the
declared repository environment. This is documented as
`viewer/outsider real-HA ACL remains BLOCKED — second HA development-user token unavailable`,
but is not a P3.8 formal exit blocker. `scripts/p3_8_real_ha_qualification.py`
is the secret-safe public-API harness; it adds no runtime endpoint, fixture or
development-mode behavior. Next concrete action: start the separately scoped P4.1 work package
(materialized scheduler slots and deterministic generation) when requested.

Final post-qualification gate in `.venv`: Ruff format PASS (193 files), Ruff
lint PASS, mypy PASS (106 sources), resource registries PASS and pytest PASS
(287 tests in 6.85 s). The P3.8 closure is committed locally on
`feat/p3-sessions`; no frontend, schema or ADR change was required.

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


## P2.3 closure

Renaud's local P2.3 gate reported:
- Ruff format: only mechanical formatting diffs in the ACL repository/test.
- Ruff lint: one import-order issue in test_acl.py.
- mypy: PASS, 81 source files.
- resource registries: PASS.
- pytest: PASS, 214 tests in 4.21 s.

The exact Ruff formatting/import corrections were applied. No semantic ACL code
changed after the passing type/resource/test gate. P2.3 is closed PASS.

## P2.4 implementation pending verification

P2.4 adds TrackService over the P2.1 state repositories and the immutable P1
content catalog. Track identity remains user state and is distinct from Pack
identity.

Track creation now:
- pins one explicit active PackVersion;
- stores source/target language preferences and priority;
- resolves direction preferences to exact active CardDefinitions;
- supports explicit card-key selection;
- respects pack-owned disabled-by-default card rules for broad direction
  resolution;
- persists exact prompt/answer facet card rules;
- persists non-negative relative content weights;
- writes Track + PackVersion pin + card rules + weights atomically.

Pack updates are previewable and deliberate. Activating a newer content
generation does not alter an existing Track pin. The service computes
added/removed/changed LearningItem buckets and only changes the pin through an
explicit integrate call. Direction-mode rules are regenerated against the new
PackVersion; explicit-card mode refuses integration if a selected card
disappeared instead of silently dropping the learner's choice.

ADR-0020 records the Track/Pack/card-rule boundary.

New tests in tests/backend/test_tracks.py cover direction resolution, explicit
selection validation, content weights, stable pinning across content updates,
preview diffs and explicit integration.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P2.4 and begin P2.5 learning quotas, goals and load forecast.


## P2.4 closure

Renaud's local P2.4 gate reported:
- Ruff format: only two mechanical formatting diffs in repositories.py and
  test_tracks.py.
- Ruff lint: PASS.
- mypy: PASS, 83 source files.
- resource registries: PASS.
- pytest: PASS, 218 tests in 4.46 s.

The exact Ruff-recommended formatting changes were applied. No semantic Track
code changed after the passing type/resource/test gate. P2.4 is closed PASS.

## P2.5 implementation pending verification

P2.5 adds LearningPlanService. Track planning now persists card-based new/review
quotas plus optional target_date, target_coverage and target_retention. The
standard profile preset's max_new_per_day_cards value is consumed directly;
child/standard/intensive therefore keep the spec-defined 3/8/15 new-card
defaults.

The spec does not define numeric preset defaults for max_reviews_per_day_cards.
P2.5 deliberately requires an explicit review ceiling instead of inventing one.

Forecasting counts selected CardDefinitions rather than LearningItems and
reports:
- selected/introduced/remaining target cards;
- required and planned new cards/day;
- review load/day around 3 weeks and 3 months;
- current due backlog;
- notification-deliverable versus active-session card load;
- goal/review-capacity feasibility and machine-readable warnings.

The review forecast is deterministic and explainable: it uses the V1 base
long-review intervals 1/3/7/14/30/60 days, accumulated in sequence, and reports
a seven-day average ending at each horizon. It assumes successful reviews and
does not pretend to predict future lapses, leeches, difficulty changes or
jitter. target_retention is persisted as goal metadata; actual retention policy
belongs to P3.

ADR-0021 records this boundary. New tests in tests/backend/test_planning.py
cover CardDefinition counting, profile-preset new quotas, target infeasibility,
review forecast horizons, notification capacity splitting and warnings.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P2.5 and begin P2.6 Profiles/tracks WebSocket CRUD and errors.


## P2.5 closure

Renaud's local P2.5 gate reported:
- Ruff format: one mechanical wrapping diff in test_planning.py.
- Ruff lint: PASS.
- mypy: PASS, 85 source files.
- resource registries: PASS.
- pytest: PASS, 222 tests in 4.61 s.

The exact Ruff-recommended formatting change was applied. No semantic planning
code changed after the passing type/resource/test gate. P2.5 is closed PASS.

## P2.6 implementation pending verification

P2.6 replaces the profile/track management gap with authenticated Home Assistant
WebSocket surfaces.

Bootstrap now consumes the config-entry personal-profile preference only after
an authenticated HA user exists. Personal-profile creation is idempotent and
keeps Profile identity independent from HA user identity.

Implemented P2 WebSocket surfaces:
- profiles list/create/update/delete/share;
- tracks list/create/update/delete/integrate_pack_update;
- packs/list and datasets/list;
- existing bootstrap/session/operation/admin commands remain registered.

All P2 collection endpoints use a server-bounded limit (max 100) plus cursor.
Profile listing is ACL-filtered before pagination. Private profile/track access
returns not_found when the caller cannot see the owning profile; a visible
viewer receives forbidden for mutations. This avoids using normal API errors as
a private-profile existence oracle.

Profile update/delete/share and Track list/create/update/delete/integration
recheck backend ACL on every request. HA admin status is not a profile ACL
bypass. Track reconfiguration preserves explicit-card mode unless the caller
explicitly replaces the card selection; direction-mode updates resolve exact
CardDefinitions again.

Profile/Track deletion explicitly cleans non-FK private state in addition to the
state.db cascade-owned rows. Track configuration updates replace metadata, card
rules and content weights atomically.

Pack and dataset list surfaces expose only public installed-content metadata from
the active immutable content generation.

New tests in tests/backend/test_websocket_crud.py cover:
- authenticated personal-profile bootstrap;
- Profile CRUD visibility and bounded pagination;
- private-profile not_found semantics;
- viewer forbidden semantics for Profile mutations;
- Track CRUD, PackVersion integration and catalog list surfaces;
- negative ACL checks for Track list/create/update/delete/integrate.

The existing ACL matrix gained an explicit owner-only EDIT_PROFILE permission.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P2.6 and the P2 exit gate, then begin P3.1 ReviewEvent audit log
and progress projection.


## P2.6 / P2 closure

Renaud's final local P2 gate reported:
- Ruff format: only mechanical formatting diffs in websocket.py, tracks.py and
  test_websocket_crud.py.
- Ruff lint: PASS.
- mypy: PASS, 86 source files.
- resource registries: PASS.
- pytest: PASS, 224 tests in 5.41 s.

The exact Ruff-recommended formatting changes were applied. No semantic P2 code
changed after the passing lint/type/resource/test gate. P2.6 and the complete P2
exit gate are closed PASS.

## P3.1 implementation pending verification

P3.1 establishes ReviewEvent as the canonical append-only learning audit source
without pulling P3.2/P3.3 state-transition policy into scope.

New ReviewEvent persistence records:
- exact profile/track/LearningItem/prompt facet/answer facet/card_key identity;
- mode, question type, result, hint/retrieval flags and signal quality;
- policy_version, dataset_generation and normalization_version;
- complete pre_state_snapshot and post_state_snapshot;
- independent presentation_to_answer_ms and delivery_to_action_ms;
- optional session/notification linkage;
- created_at_utc plus historical local_date/timezone_name/utc_offset_minutes.

ReviewEvent append and progress post-state materialization share one SQLite
writer transaction. Snapshot identity must match the event before persistence.
Progress remains keyed by Profile + Track + CardDefinition.

Integrity rebuild can clear a selected progress scope and restore the latest
historical post-state snapshot per card in stable created_at_utc/id order. This
is a historical integrity rebuild, not an algorithmic recompute under a newer
ReviewPolicy; that distinction remains P3.12 scope.

The ReviewEvent service derives historical local date/offset from the Profile
timezone at event time. Notification delivery latency is stored independently
and never substituted for cognitive answer latency.

ADR-0022 records the audit/projection boundary. New tests in
tests/backend/test_review_events.py cover atomic materialization, latency
separation, version metadata, historical timezone fields and progress rebuild.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.1 and begin P3.2 introduction and learning-step state machine.


## P3.1 closure

Renaud's local P3.1 gate is fully green:
- Ruff format: PASS, 165 files already formatted.
- Ruff lint: PASS.
- mypy: PASS, 88 source files.
- resource registries: PASS.
- pytest: PASS, 226 tests in 5.53 s.

P3.1 is closed PASS.

## P3.2 implementation pending verification

P3.2 adds a pure LearningStateMachine with the V1 short-step timing contract:
- new cards first enter an explicit introduction/exposure transition;
- introduction sets mode=introduction and retrieval_occurred=false;
- first exposure cannot increment a verified failure;
- learning uses 1/10/60 minute short steps;
- relearning uses 10/60 minute short steps;
- any short-step failure resets the current short sequence and always schedules
  a strictly positive delay, so immediate working-memory retest is impossible.

Short-step completion emits ready_for_long_review=true but deliberately leaves
the state in learning/relearning with no short next_due. P3.3 owns the actual
long-review state/box/interval transition. P3.4 owns mapping UI/quiz signals to
success/failure strength, and P3.9 owns actual interleaving/session selection.

ADR-0023 records these boundaries. New tests in
tests/backend/test_learning_state_machine.py cover introduction semantics,
1/10/60 learning, 10/60 relearning, failure reset/no-immediate-retest,
graduation handoff and invalid state/configuration.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.2 and begin P3.3 ReviewPolicy V1 core.


## P3.2 closure

Renaud's local P3.2 gate reported:
- Ruff format: only two mechanical formatting diffs in core/learning.py and
  test_learning_state_machine.py.
- Ruff lint: PASS.
- mypy: PASS, 90 source files.
- resource registries: PASS.
- pytest: PASS, 231 tests in 5.48 s.

The exact Ruff-recommended formatting changes were applied. No semantic P3.2
behavior changed after the passing lint/type/resource/test gate. P3.2 is closed
PASS.

## P3.3 implementation pending verification

P3.3 adds ReviewPolicyV1 as the deterministic long-review policy boundary.

The policy uses V1 boxes and nominal intervals:
- box 1: 8 h;
- box 2: 1 day;
- box 3: 3 days;
- box 4: 7 days;
- box 5: 14 days;
- box 6: 30 days;
- box 7: 60 days.

Successful long reviews advance by at most one box. The next interval combines
the target-box base interval, bounded difficulty_factor and deterministic
SHA-256-derived jitter. The jitter seed uses card_key + policy_version +
target_box + historical verified-attempt ordinal, so identical state/history
produces the same due date.

Elapsed review time is computed from the real last_verified_at_utc timestamp.
For remembered overdue cards, the effective next interval has a hard floor at
the demonstrated elapsed retention; deterministic jitter cannot shorten that
floor.

difficulty_factor is bounded to [0.6, 2.0] and follows the V1 factors:
- verified failure: x0.85;
- verified success without hint: x1.05;
- success with hint: no increase.

Long-review failure applies relapse_penalty=2 boxes, increments verified-wrong
state, resets the long correct streak and enters the P3.2 relearning sequence
rather than resetting every card to box zero.

Completing P3.2 short steps is consumed through an explicit graduation method.
Learning enters long review at box 1; relearning preserves its demoted box floor.
The short-step streak is reset on graduation so it cannot leak into the long
review streak.

Mastery is a derived non-terminal label based on box, verified accuracy and time
since last verified retrieval. It decays with time and never changes scheduling
state by itself.

All policy time comes from an injected Clock. ReviewPolicy contains no direct
datetime.now() call. ReviewPolicyV1 is exposed from the runtime for later
session/signal integration.

ADR-0024 records this long-review policy boundary. New tests in
tests/backend/test_review_policy.py cover deterministic scheduling, hint
behavior, bounded difficulty, relapse/relearning, overdue-retention floors,
mastery decay, short-step graduation and invalid policy/state input.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.3 and begin P3.4 verified-retrieval gate and signal weighting.


## P3.3 closure

Renaud's local P3.3 gate is fully green after the typing/style remediation:
- Ruff format: PASS, 171 files already formatted.
- Ruff lint: PASS.
- mypy: PASS, 92 source files.
- resource registries: PASS.
- pytest: PASS, 239 tests in 5.50 s.

P3.3 is closed PASS.

## P3.4 implementation pending verification

P3.4 adds SignalPolicy as the normalization boundary between UI/channel
interactions and ReviewPolicy.

Signals now distinguish:
- exposure: neutral, no retrieval;
- post-retrieval self-assessment: weak, non-verified evidence;
- verified MCQ: medium verified evidence;
- verified free-text/cloze/exam retrieval: strong verified evidence;
- hinted correct retrieval: verified but weak and no difficulty reward;
- IDK: explicit retrieval failure;
- unrecognized free-text: neutral, never automatic SRS failure.

A positive self-assessment after the answer was already visible is forced to a
neutral signal and cannot mutate long-box promotion.

The default verified_gate_box is 2. A promotion targeting a box above that gate
requires either gate-eligible verified evidence in the current interaction or a
verified success already accumulated in the current box. Promotion consumes
that evidence by resetting verified_success_since_box, forcing periodic verified
retrieval above the gate instead of allowing indefinite weak self-assessment
promotion.

ReviewPolicy success/failure APIs now accept signal confidence explicitly.
Non-verified success can support weak scheduling without incrementing verified
counters. Non-verified negative self-assessment may enter relearning but does
not apply verified relapse demotion, difficulty penalty or verified-wrong
counters.

Untrusted shared-device responses are signal_quality=reduced, are not considered
verified/gate-eligible, and cannot cross the gate alone. Explicitly trusted
shared-device responses may count as verified evidence.

SignalPolicy has no delivery_to_action_ms input. Notification responsiveness
therefore cannot influence SRS strength by construction. presentation latency
also remains outside automatic V1 SRS weighting.

ADR-0025 records this boundary. New tests in tests/backend/test_signal_policy.py
cover visible-answer blocking, weak progression up to the gate, periodic
verified refresh, shared-device trust, hint reduction, IDK, unrecognized
answers and the notification-latency boundary.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.4 and begin P3.5 sibling burial, prerequisites and confusable
introduction spacing.


## P3.4 closure

Renaud's local P3.4 gate reported:
- Ruff format: only two mechanical formatting diffs in review_policy.py and
  signals.py.
- Ruff lint: PASS.
- mypy: PASS, 94 source files.
- resource registries: PASS.
- pytest: PASS, 250 tests in 5.40 s.

The exact Ruff-recommended formatting changes were applied. No semantic P3.4
behavior changed after the passing lint/type/resource/test gate. P3.4 is closed
PASS.

## P3.5 implementation pending verification

P3.5 introduces SelectionConstraintService as an eligibility layer before the
later P3.9/P4 ranking schedulers.

For new-card candidates, the service evaluates the Track-pinned PackVersion's
prerequisite_card_keys and unlock_when thresholds against same-Profile/same-Track
progress. Supported generic metrics are verified_correct_count, mastery and box.
If a prerequisite is declared without unlock_when, the conservative default is
one prior exposure (seen_count >= 1).

Sibling CardDefinitions are identified by shared LearningItem identity. The
latest sibling ReviewEvent controls configurable burial windows:
- new sibling gap: 1440 minutes by default;
- review sibling gap: 240 minutes by default.

Learning/relearning short-step cards are deliberately exempt from sibling burial
so P3.5 cannot starve P3.2 same-day obligations.

ConfusableGroup metadata remains PackVersion-owned. A new LearningItem is blocked
until min_intro_gap_days has elapsed since the latest first introduction of any
other item in the same group. Confusable distractors are exposed as eligible only
for review-state cards; P3.6 still owns actual distractor generation.

The repository also verifies that the candidate card is enabled in the Track's
card rules before evaluating constraints, preventing arbitrary Pack cards from
being treated as selectable.

Selection decisions expose deterministic machine-readable reasons and the latest
blocked_until_utc timestamp. All time comparisons use the injected Clock.

ADR-0026 records the eligibility/ranking boundary and the bare-prerequisite
semantics. New tests in tests/backend/test_selection_constraints.py cover
thresholds, bare prerequisites, sibling gaps, learning/relearning exemptions,
Track overrides, confusable spacing, distractor stability, selected-card
validation and content-backed repository reads.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.5 and begin P3.6 quiz engine, distractors and corrective
feedback.


## P3.5 closure

Renaud's final local P3.5 gate reported:
- Ruff format: one remaining blank-line formatting diff in
  test_selection_constraints.py.
- Ruff lint: PASS.
- mypy: PASS, 96 source files.
- resource registries: PASS.
- pytest: PASS, 259 tests in 5.57 s.

The final Ruff-only blank-line fix was applied. No semantic P3.5 behavior changed
after the passing lint/type/resource/test gate. P3.5 is closed PASS.


## P3.6 implementation pending verification

P3.6 adds a deterministic QuizEngine for panel MCQ and grammar cloze-MCQ.

Question construction now:
- enforces 4–6 answer options;
- keeps Je ne sais pas as a separate explicit action rather than a guessed option;
- preserves CardDefinition-provided context hints;
- marks every question reportable for the later dataset-quality workflow;
- rotates examples deterministically from example_rotation_index;
- balances correct-answer position from answer_position_balance;
- re-samples distractors reproducibly using card_key + presentation_index +
  answer_id.

Distractor filtering excludes:
- the correct answer;
- current LearningItem/sibling answers;
- same normalized accepted answers;
- same native-concept answers;
- explicit synonym relations supplied by candidate metadata;
- duplicate answer IDs/normalized answers;
- confusable candidates unless the card is already in review.

Candidate pools are deliberately caller-owned/indexed. QuizEngine never performs
corpus-wide SQL randomization and contains no ORDER BY RANDOM(). This keeps the
domain engine independent from storage lookup while still requiring callers to
narrow large corpora before construction.

Grammar cloze-MCQ is accepted only for grammar cards with an explicit cloze
prompt, and its distractors are restricted to grammar candidates so the task
cannot accidentally become vocabulary-reading difficulty.

Outside exam mode, wrong and IDK answers reveal the correct answer immediately.
Known confusable distractors may attach contrastive feedback. Exam mode records
the result but suppresses immediate feedback/reveal.

ADR-0027 records these boundaries. New tests in tests/backend/test_quiz_engine.py
cover option bounds, IDK, safety exclusions, confusable stability,
presentation resampling, answer-position balance, example rotation, grammar
cloze filtering, contrastive feedback, exam suppression and invalid
construction.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.6 and begin P3.7 panel free-text grading and content-quality
feedback.


## P3.6 closure

Renaud's local P3.6 gate is fully green:
- Ruff format: PASS, 180 files already formatted.
- Ruff lint: PASS.
- mypy: PASS, 98 source files.
- resource registries: PASS.
- pytest: PASS, 269 tests in 6.00 s.

P3.6 is closed PASS.

## P3.7 implementation pending verification

P3.7 adds FreeTextGrader with explicit versioned exact, any_of and
fuzzy_normalized policies.

exact accepts one exact value. any_of accepts exact membership in an explicit
accepted-answer set. fuzzy_normalized first runs the existing versioned
NormalizationPolicy and is available only when the policy declares supported
scripts. V1 fuzzy matching is deliberately conservative: normalized strings of
length >= 4 may differ by one insertion/deletion/substitution. Diacritic-only
differences are excluded from this typo tolerance so a normalization policy that
preserves semantic accents cannot be silently weakened by fuzzy matching.

Every FreeTextGradingResult carries grading_policy_version and
normalization_version. P3.1 ReviewEvent already persists normalization_version;
the ReviewEvent test now asserts that field survives round-trip persistence.

A normal unmatched answer is wrong until the user explicitly chooses the
"Ma réponse devrait être acceptée" recovery action. That conversion produces an
unrecognized, reportable result whose is_definitive_failure is false.
SignalPolicy already treats unrecognized as neutral, so no automatic SRS
failure/demotion is implied.

ContentReportService plus locklearn/content/report implement the feedback path.
The WebSocket endpoint rechecks Profile ANSWER permission, validates Track
ownership and the exact active CardDefinition, verifies the card is enabled in
the Track, and persists a private audit_events content_report payload with the
raw/normalized answer and grading/normalization versions. The response explicitly
reports srs_penalized=false.

The content generation stored on the report is backend-owned from the active
ContentGenerationManager; clients cannot forge it. P3.8 will later persist
generation identity per presented session question across concurrent content
switches.

No state schema migration was introduced: V1 requires append-only content
feedback, not a moderator/status queue. A future moderation workflow can add a
dedicated table through an explicit migration if needed.

ADR-0028 records these boundaries. New tests cover exact/any_of,
script-aware fuzzy normalization, semantic diacritics, recoverable unrecognized
grading, no progress mutation from reports, report persistence, WebSocket ACL
and normalization-version persistence.

Next required local gate:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short

If PASS, close P3.7 and begin P3.8 persistent sessions, CAS concurrency and
cross-client resume.


## P3.7 closure

Renaud's local P3.7 gate is fully green after the final typing/style remediation:
- Ruff format: PASS, 185 files already formatted.
- Ruff lint: PASS.
- mypy: PASS, 102 source files.
- resource registries: PASS.
- pytest: PASS, 274 tests in 6.13 s.

P3.7 is closed PASS. The long-lived feat/p1-content-core branch is ready to
merge into main before P3.8 starts on a dedicated sessions branch.


## Branch cut after P3.7

The long-lived feat/p1-content-core branch was merged into main through PR #1
with a merge commit, preserving full history. P3.8 starts from that merged main
on dedicated branch feat/p3-sessions.

## P3.8 implementation pending verification

P3.8 upgrades the P0 session prototype into real persistent application state.

Session snapshots now persist and return:
- Profile/Track ownership;
- type, strategy, status and version;
- settings_json;
- question_count/current_position;
- full session_items with exact CardDefinition identity and renderer payload;
- immutable session_answers history;
- derived current_question.

Backend-prepared SessionQuestion rows are validated against enabled Track card
rules and the exact active CardDefinition. The persisted payload is pinned to the
backend's active content generation rather than trusting a client-supplied
generation.

session/answer now CAS-checks session status/version and the exact question at
current_position in one writer transaction. It marks the current item answered,
presents the next item, advances the cursor/version and appends the immutable
answer. Two same-version answers cannot both commit.

pause/resume/complete are versioned CAS transitions. Completed sessions cannot
resume. session/pause uses paused=true/false because the indicative V1 API names
only that lifecycle command.

session/subscribe returns current persistent state and publishes only successful
winning mutations. Disconnect removes listeners but leaves state.db untouched,
so another client can recover through session/get.

All public session commands now use real Profile ACL instead of the old P0
user-derived probe profile. READ gates get/subscribe; ANSWER gates mutations.
Invisible private profiles preserve not_found semantics while visible viewers
cannot mutate.

session/undo in P3.8 is deliberately navigation-only: it reopens the last
answered session item through CAS, preserves historical session_answers and
appends a session_undo_navigation audit event. It never edits ReviewEvent or
progress; pedagogical undo remains P3.12.

ADR-0029 records these boundaries. Tests cover persistent settings/questions,
storage close/reopen resume, simultaneous answer CAS, wrong-question rejection,
pause/resume/complete, navigation undo, winner-only subscriptions, real ACL and
cross-WebSocket-client resume.

Next required local gate on feat/p3-sessions:
- python3 -m ruff format --check .
- python3 -m ruff check .
- python3 -m mypy custom_components datasets tests
- python3 datasets/tools/validate_resources.py
- python3 -m pytest -q --tb=short


## P3.8 local gate closure

Renaud's local P3.8 gate is green after the final Ruff-only storage formatting fix:
- Ruff format: one mechanical diff in storage/database.py, applied without semantic change.
- Ruff lint: PASS.
- mypy: PASS, 104 source files.
- resource registries: PASS.
- pytest: PASS, 280 tests in 7.24 s.

P3.8 is considered LOCAL GATE PASS. Before beginning P3.9, run one targeted
real-Home-Assistant qualification covering WebSocket reconnect/resume,
same-version concurrent answer CAS, pause/resume/complete, subscription cleanup
on disconnect and state persistence across integration reload.


## P3.8 real Home Assistant qualification blocked

On 2026-09-23, `feat/p3-sessions` at
`7857143376c317f955bfd783196aeb5effea0982` was installed on the development
instance through HACS and loaded after a Core restart. The real state database
migrated from schema 1 to schema 2 with the pre-existing three sessions and
three answer rows preserved.

The full local gate remained green: Ruff format/lint PASS, mypy PASS (104 source
files), resource registries PASS and pytest PASS (280 tests in 6.77 s).

Real HA PASS evidence covers Profile/Track bootstrap, persistent session
metadata/settings, independent WebSocket clients, one-winner lifecycle CAS,
winner-only subscription events, pause/resume/stale rejection, disconnect and
cross-client reconstruction, real Config Entry reload, removal of pre-reload
subscriptions, completion and incompatible-mutation rejection. Storage remained
healthy (`integrity_check=ok`, zero FK violations, WAL, reader off event loop),
one panel/entry remained, and HA `system_log` contained no LockLearn error.
Temporary qualification data was deleted and the original session/answer counts
were restored.

The qualification is **BLOCKED**, not PASS: public P3.8 `session/start`
correctly accepts no client-prepared questions and P3.9 selection does not yet
exist, so the mandatory real-HA concurrent `session/answer` race and immutable
answer-row proof could not be executed. Viewer/outsider real ACL was also not
run because only one HA token is configured; it remains harness-only evidence.
See `docs/P3_8_REAL_HA_QUALIFICATION.md` for the exact matrix.

Next action for P3.8: after the P3.9 repository gate is green, install the
qualified P3.9 branch on real HA and rerun the mandatory concurrent
`session/answer` race plus navigation undo using the public backend-selected
question. Add a second development-user token for real viewer/outsider ACL when
available. Do not change P3.8 from `LOCAL GATE PASS — real HA qualification
pending` until those checks succeed.


## P3.9 closure

P3.9 now owns backend session candidate ranking while P3.5 remains the reusable
eligibility layer.

Implemented behavior:
- `locklearn/session/start` with a Track asks `SessionSelectionService` for
  backend-owned CardDefinitions and persists them through the unchanged P3.8
  SessionQuestion/CAS boundary;
- absent Progress is treated as `new`; learning/relearning/review are candidates
  only when due;
- relearning/learning short steps take priority, while remaining candidates are
  interleaved by Track content weights with stable deterministic tie-breakers;
- profile-local actual introduction events consume the new-card daily quota;
- new cards are never queued in the final 25% of a bounded requested session;
- prospective planning avoids pre-queuing new/review siblings and multiple new
  members of the same confusable group;
- prepared question payloads retain explainable selection state/reason/weight and
  Pack position;
- fatigue advice reads the ten most recent trusted verified ReviewEvents for the
  session, defaults to a 0.60 accuracy threshold and offers
  finish/recognition_only/continue without mutating Progress or ReviewEvents.

The existing two-WebSocket CAS test now starts its question through the public
P3.9 path instead of injecting a prepared SessionQuestion directly. Focused
P3.9 tests cover short-step priority, final-quarter behavior, card-based daily
quota, prospective confusable protection, not-yet-due rejection and fatigue
advice. ADR-0030 records the policy/boundaries.

No state/content schema migration was added. No frontend, scheduler/P4,
P3.10 known/suspend/bury/calibration, P3.11 leech/annotations or P3.12
pedagogical undo work is included.

Final development-checkout gate on 2026-09-23:
- `python3 -m ruff format --check .`: PASS, 192 files already formatted.
- `python3 -m ruff check .`: PASS.
- `python3 -m mypy custom_components datasets tests`: PASS, 106 source files.
- `python3 datasets/tools/validate_resources.py`: PASS.
- `python3 -m pytest -q --tb=short`: PASS, 287 tests in 6.88 s.

P3.9 is closed PASS. Next action is to return to the remaining P3.8 real-HA
qualification now that public `session/start` can provide a real backend-owned
question.
