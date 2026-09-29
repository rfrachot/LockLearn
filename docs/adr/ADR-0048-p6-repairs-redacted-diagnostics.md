# ADR-0048 — P6.3 Repairs and redacted diagnostics

## Status

Accepted and qualified for P6.3 on 2026-09-27.

## Context

LockLearn already emitted focused Repairs from dataset discovery/freshness,
notification delivery and scheduler-capacity code. P6.2 added state-integrity
recovery. V1 requires a complete minimum Repair catalogue and Home Assistant
diagnostics that are useful for support without exporting private learning
data.

Profile names, identifiers, learned content, answers, notification contents and
detailed personal statistics are explicitly forbidden from diagnostics.

## Decision

### Repairs

The minimum V1 catalogue is normalized as follows:

- dataset obsolete -> existing `dataset_sources_stale`;
- notification target unresolved -> existing
  `notification_target_unavailable`;
- scheduler configuration infeasible -> existing
  `scheduler_configuration_infeasible`;
- DB integrity failure -> P6.2 `state_integrity_failure`;
- migration failure -> `state_migration_failure`;
- dataset signature invalid -> `dataset_signature_invalid`;
- unexpected reconstructible cache under persistent state ->
  `backup_cache_anomaly`.

Dataset trust failures are distinguished from generic install failures. A
`TrustError` creates the signature-specific Repair while other install
failures retain `dataset_install_failed`. Successful installation clears both
install/signature Repair variants.

A successful runtime startup clears stale migration/integrity Repairs. The
backup/cache anomaly is checked from filesystem layout and byte presence under
the persistent state root; the known Home Assistant 2025.2 policy that includes
the normal external `locklearn-content/` tree is not itself treated as an
anomaly.

### Diagnostics

`diagnostics.py` implements Home Assistant config-entry diagnostics.

The payload contains only:

- LockLearn/Home Assistant/config-entry/schema versions;
- aggregate database health and schema/migration status;
- aggregate counts of Profiles, datasets and packs;
- aggregate dataset status/error categories;
- aggregate scheduler bridge status;
- storage byte counts and backup policy;
- counts of active Repair categories.

Diagnostics never include:

- Profile/Track/target/dataset identifiers;
- Profile or target friendly names;
- studied terms, card keys or content payloads;
- answers, annotations or notification contents;
- detailed personal statistics;
- raw exception text, URLs or Repair placeholders.

Repair placeholders remain available to Home Assistant's local Repair UI when
needed for operator action, but diagnostics reduce them to a stable category
and count.

## Consequences

- Support diagnostics remain useful for version/schema/storage/lifecycle
  triage without becoming a second export surface.
- Raw dataset/network/SQLite error messages are intentionally not included.
- P6.4 remains the only user-data export/import surface.
- P6.5 remains responsible for optional HA entity privacy.
