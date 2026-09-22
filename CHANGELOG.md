# Changelog

All notable changes will be documented here.

## [Unreleased]

### Added
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
