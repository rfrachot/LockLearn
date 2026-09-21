# Changelog

All notable changes will be documented here.

## [Unreleased]

### Added
- Reproducible HAOS/Supervisor backup-and-restore qualification harness.
- P0.7 real-instance evidence and platform-specific notification decisions.

### Changed
- Treat lockscreen visibility as an advisory OS rendering preference rather
  than a confidentiality boundary.

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
