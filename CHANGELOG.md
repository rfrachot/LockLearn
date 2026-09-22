# Changelog

All notable changes will be documented here.

## [Unreleased]

### Added
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
