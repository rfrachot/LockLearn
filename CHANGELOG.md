# Changelog

All notable changes will be documented here.

## [Unreleased]

### Added
- P3.7 versioned panel free-text grading for exact, any_of and conservative
  script-gated fuzzy_normalized policies, with explicit correct/wrong/unrecognized
  outcomes and normalization-version propagation.
- Recoverable "answer should be accepted" content reports persisted as private
  state audit feedback through the authenticated locklearn/content/report API.
- ADR-0028 documenting the grading/report boundary, semantic-diacritic protection
  and the no-false-SRS-failure contract for unrecognized answers.
- P3.6 deterministic panel quiz engine with 4–6 option MCQ, grammar cloze-MCQ,
  explicit IDK, answer-position balancing and deterministic example rotation.
- Safe distractor filtering for same native concept, accepted normalized answers,
  explicit synonyms, sibling answers and unstable confusables, with
  presentation-index resampling instead of corpus-wide random SQL.
- Immediate corrective/contrastive feedback outside exams plus reportable
  question metadata.
- ADR-0027 documenting the quiz/distractor boundary and indexed-pool contract.
- P3.5 deterministic selection constraints for prerequisite unlocks, new/review
  sibling burial and PackVersion-owned confusable introduction spacing (PASS).
- Track-scoped candidate validation plus machine-readable eligibility reasons and
  blocked-until timestamps for later session/scheduler ranking.
- ADR-0026 documenting the eligibility/ranking boundary, bare-prerequisite
  exposure semantics and confusable-distractor stability rule.
- P3.4 normalized signal policy separating exposure, weak post-retrieval
  self-assessment, verified MCQ/free-text/cloze/exam retrieval, IDK and
  unrecognized outcomes.
- Configurable verified-gate enforcement with periodic verified evidence,
  conservative shared-device handling and hint-reduced confidence.
- ADR-0025 documenting the signal/gate boundary and the rule that notification
  response latency never affects SRS strength.
- P3.3 deterministic ReviewPolicy V1 with explicit boxes/intervals, elapsed-time
  adjustment, deterministic jitter, bounded difficulty_factor and relapse demotion.
- Non-terminal time-decaying mastery plus explicit P3.2 short-step graduation
  into the long review queue.
- ADR-0024 documenting reproducibility, overdue-retention floors and the boundary
  between long-review policy and later signal weighting.
- P3.2 explicit introduction state for new cards plus deterministic V1 short
  learning/relearning steps (1/10/60 and 10/60 minutes).
- Positive failure delays that prevent immediate working-memory retests, with
  an explicit graduation handoff to the future long-review policy.
- ADR-0023 documenting the boundary between short-step learning, P3.3 long
  review policy, P3.4 signal weighting and P3.9 interleaving.
- P3.1 canonical ReviewEvent audit service with exact CardDefinition identity,
  policy/dataset/normalization versioning, complete pre/post progress snapshots,
  historical local timezone fields and separate cognitive/delivery latency.
- Atomic ReviewEvent append plus progress materialization, and integrity rebuild
  of progress from historical post-state snapshots.
- ADR-0022 documenting the append-only audit source, rebuild semantics and the
  rule that notification latency never influences cognitive/SRS strength.
- P2.6 authenticated WebSocket bootstrap plus Profile CRUD/share, Track CRUD,
  explicit PackVersion integration and paginated Pack/Dataset catalog surfaces.
- Server-side ACL rechecks for every profile-scoped P2 command, bounded
  limit/cursor pagination and privacy-preserving not-found/forbidden semantics.
- P2.5 learning-plan service with card-based new/review quotas, profile-preset
  new-card defaults, target date/coverage/retention goals and deterministic
  3-week/3-month workload forecasts.
- Machine-readable structural planning warnings plus notification-versus-active
  session capacity estimates bounded by the profile push budget.
- ADR-0021 documenting the explainable success-only forecast model and the
  decision not to invent unspecified review-preset defaults.
- P2.4 Track configuration service with explicit immutable PackVersion pinning,
  direction-to-CardDefinition resolution, explicit card selection, relative
  content weights, deterministic update previews and deliberate pack integration.
- ADR-0020 documenting Track/Pack separation, materialized card rules and the
  no-silent-pack-update contract.
- P2.3 centralized backend profile ACL authority with owner/editor/viewer roles,
  privacy-filtered profile visibility, explicit non-bypass for HA admins, and
  transactional protection against removing or demoting the final owner.
- P2.3 permission/privacy documentation covering backend ACL, HA entity/event
  caveats, shared profiles and local private learning state.
- P2.2 profile service with independent LockLearn profile identity, persistent
  Home Assistant user membership, idempotent personal-profile onboarding and
  child/shared profiles without dedicated HA accounts.
- Mutable child/standard/intensive/custom profile presets with protected internal
  settings markers.
- P2.1 state.db schema v2 covering the V1 profile/track/ACL-ready persistence
  skeleton, progress/review events, sessions, scheduler, notifications,
  annotations, stats and settings with required hot-query indexes.
- Recoverable v1→v2 state migration using a coherent SQLite backup, out-of-place
  candidate build, integrity checks and atomic replacement.
- Application repositories for Profile, Track/PackVersion pinning, lazy Progress
  materialization and settings, with explicit active-content reference validation.
- Cross-domain integrity audit for state references that cannot use SQL foreign
  keys into the independently replaceable content.db.
- ADR-0019 defining the P2.1 state persistence and migration boundary.
- P1.11 media-ready public Asset schema v2 with signed external image/audio
  payloads, strict path/MIME/dimension checks, asset-scope licensing/provenance
  and same-dataset Facet/ContentBlock references.
- Runtime public-asset cache extraction and checksum revalidation without adding
  an image/audio renderer or mixing private/export media into signed content.
- Backward-compatible validation for the already-signed asset-free content
  schema v1 starter package.
- ADR-0018 defining the public-dataset Asset and private/export media boundary.
- P1.10 bundled signed Japanese Starter dataset with 120 LearningItems and 240
  cards, original CC BY-SA 4.0 provenance and a 178478-byte offline artifact.
- First-run offline starter bootstrap through the normal DatasetManager trust,
  validation, immutable-generation activation and rollback path.
- One-purpose deprecated Ed25519 public key for immutable starter 1.0.0
  verification; the ephemeral private key and signing workflow are not retained.
- ADR-0017 defining bundled first-run content and its signing lifecycle.
- P1.9 local DatasetManager for signed prebuilt artifacts, with bounded staging,
  checksum/signature/schema/license/package validation, full-generation activation and rollback.
- Home Assistant UpdateEntity support per official dataset plus privacy-safe
  source age, provenance, license and cache metadata.
- Dataset Repairs for discovery/install failures and stale upstream snapshots.
- Bundled runtime source/license/trust policy and artifact-host allowlists for
  HACS installs, with explicit pack-version removal guards.
- ADR-0016 defining the runtime dataset trust and update boundary.
- P1.8 build-time dataset pipeline separating upstream adapters from pedagogical
  recipes, with bounded fetching, canonical JSONL normalization, semantic
  validation, Ed25519 signing, deterministic package layout and external checksums.
- Streaming adapters for JMdict, KANJIDIC2, Tatoeba text, Wiktextract/Kaikki,
  KanjiVG and repository-authored LockLearn editorial input using synthetic tests only.
- Scheduled/manual dataset GitHub Actions, source freshness/fetch registries and
  a canonical-content publication gate that never commits or releases raw corpora.
- Manifest v2 signed SourceSnapshot metadata including upstream date and adapter version.
- ADR-0015 defining the offline build/release boundary.
- P1.7 normalized source snapshots and per-object provenance retained inside merged content generations, including author/language/modification attribution fields.
- Version-2 source/license registries with explicit software/editorial/dataset/asset license scopes, source field allowlists and required provenance contracts.
- ADR-0014 defining snapshot identity, provenance granularity and license boundaries.
- P1.6 normalized `content.db` schema with stable content/card relationships,
  lifecycle tombstones and PackVersion pre-aggregates.
- Validated immutable content generations built from one attached package at a
  time, atomically activated after reader drain and retained for rollback.
- Stable merge lifecycle history preserving exact IDs and card keys across
  active → removed → active transitions.
- ADR-0013 defining content generation versioning, activation, leases,
  rollback, crash boundaries and the no-ATTACH-fan-out contract.
- P1.5 pack/tag primitives with immutable pack-version pinning, prerequisites,
  unlock thresholds, confusable intro gaps and pack-version diff metadata.
- Data-driven Japanese curation policy keeping isolated ON/KUN cards disabled by
  default and requiring contextualized readings, complete-term production and strong grading defaults.
- LearningItem curation metadata for queryable tags, register and required-item dependencies.
- ADR-0012 defining versioned packs, prerequisite boundaries and data-owned curation.
- P1.4 multilingual locale primitives with BCP 47 canonicalization, ISO 15924
  script metadata, deterministic locale fallback and versioned normalization policies.
- Generic script-aware normalization policy registry with explicit Unicode,
  case, whitespace and punctuation behavior; language-specific choices remain data-driven.
- Versioned `Term.normalized_text` metadata and rebuild guards that reject
  behavior changes without a normalization-version bump.
- ADR-0011 defining multilingual normalization, stable Term identity and fallback rules.
- P1.3 content-block contract with semantic roles, explicit reveal/mask metadata,
  structured reading/furigana/ruby segments and media references.
- Strict bounded rich-text AST that rejects arbitrary HTML, links, remote media
  and unknown attributes/nodes.
- Versioned CardDefinition grading metadata with explicit `unrecognized`
  outcome that is distinct from a definitive wrong answer.
- ADR-0010 defining safe rich text, reveal/mask semantics, structured readings
  and the non-identifying grading contract.
- Strict P1.2 signed dataset package contract with exact-byte Ed25519
  verification, public-key lifecycle policy, transitively hashed payloads,
  registry-backed official licensing, hostile-ZIP defenses and read-only SQLite
  integrity validation.
- ADR-0009 defining the dataset trust envelope, external ZIP checksum boundary
  and historical key semantics.
- Canonical P1.1 content-domain types with deterministic card identities,
  explicit cross-source alignments and released-ID migration mappings.
- ADR-0008 defining stable content/card identity and future migration rules.
- Reproducible HAOS/Supervisor backup-and-restore qualification harness.
- P0.7 real-instance evidence and platform-specific notification decisions.

### Fixed
- Harden content-generation activation against asyncio cancellation and HA unload
  so the reader gate cannot reopen before an executor-side pointer switch has
  finished and in-memory generation state has been reconciled.
- Reject stale generation candidates whose declared parent is no longer active,
  preventing an older build from overwriting a newer activated catalog.
- Add a fsynced switch-intent journal so restart can recover the exact previous
  generation after a crash during forward activation or rollback.
- Validate package-wide dataset ownership and require stable-ID card migrations
  to target the identity derived from the migrated item/facet tuple.

### Changed
- Treat lockscreen visibility as an advisory OS rendering preference rather
  than a confidentiality boundary.
- Separate per-target notification capabilities from pedagogical signal:
  second vibration or stacked post-action reveal no longer implies
  `exposure_only`.

## [0.0.2] - 2026-09-21

### Added
- Secret-safe real-instance qualification harness for Companion notifications.
- Administrator-only, privacy-safe SQLite health diagnostics for restore qualification.

### Fixed
- Resolve actionable Companion notifications through the data-capable
  `notify.mobile_app_*` action instead of the generic notify entity action.
- Parse both current and legacy Home Assistant WebSocket event envelopes in P0 probes.

## [0.0.1] - 2026-09-21

### Added
- Initial LockLearn repository bootstrap.
- Home Assistant integration and frontend skeletons.
- Data source, language and license registries.
- Project licensing and funding foundations.
- P0 HA lifecycle with bundled/versioned panel, clean unload and single-entry tests.
- Thread-confined SQLite state/content foundation, coherent backup hooks and benchmark.
- Persistent session CAS, WebSocket subscriptions and cancellable operation streams.
- Stable notification-target resolution, capability gates and unattended-action boundary.
- HA 2025.2/current compatibility matrix plus HACS and hassfest CI validation.
