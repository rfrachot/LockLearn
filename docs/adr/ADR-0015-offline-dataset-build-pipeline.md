# ADR-0015 — Offline dataset build pipeline and source adapters

## Status

Accepted for P1.8 implementation on 2026-09-22; local quality verification is
required before P1.8 is marked PASS.

## Context

LockLearn must consume large, independently licensed upstream corpora without
turning Home Assistant into an ETL worker or making installed learning depend on
source availability. The signed package contract, immutable content generations,
source/license registry and provenance model already exist from P1.2–P1.7.

The remaining supply-chain boundary is the build pipeline itself: fetching exact
upstream snapshots, source-native parsing, deterministic normalization,
pedagogical materialization, validation, signing and release.

Raw JMdict/KANJIDIC2/Tatoeba/Kaikki/KanjiVG downloads are large and mutable.
They are build inputs, not repository content.

## Decision

### Build-time only

All upstream adapters live under `datasets/`, outside the Home Assistant custom
component package. Runtime code never imports them and never queries upstream
sources for a session, notification or ordinary dataset read.

Raw files are downloaded only into ignored or temporary workspaces
(`datasets/downloads/`, `datasets/staging/` or temporary directories).
They are never committed and are never attached to GitHub Releases.

### Adapter and recipe are separate concerns

A source adapter answers:

> What facts does this upstream snapshot contain?

It produces canonical JSONL `NormalizedRecord` values with source-native
identity and attribution fields.

A dataset recipe answers:

> Which LockLearn Concepts, Terms, LearningItems, Facets, Cards and Packs should
> this product contain?

Recipes consume normalized records and materialize the LockLearn schema. This
keeps Japanese pedagogy and pack curation out of generic source parsers and
allows one source adapter to feed multiple dataset products.

P1.8 defines the recipe protocol but does not commit the first production
Japanese Starter recipe; that is P1.10 scope.

### Exact snapshots and bounded fetches

Each build pins exact source metadata and raw SHA-256. Single-file sources use
the source file SHA-256 directly. Multi-file source snapshots require an
explicit snapshot URL and use a deterministic composite digest over named file
digests.

Fetches are streamed into an atomic temporary file with a configured maximum
byte count. The operational source-build registry records discovery URLs,
stable direct/template URLs when appropriate and build ceilings. Sources whose
latest artifact requires discovery use an exact URL supplied by the reviewed
build configuration rather than scraping a floating "latest" link.

### Deterministic normalization and logical reproducibility

Canonical JSONL uses sorted JSON object keys and stable source identities.
Row numbers are never stable identity. When an upstream source lacks a stable
record ID, an adapter derives one from documented stable semantic fields.

V1 requires reproducible **content**, not byte-identical SQLite files.
`canonical_content_hash` is calculated from a deterministic ordered export of
semantic content tables and deliberately excludes build timestamps, dataset
version labels and source-snapshot bookkeeping. Therefore a refresh that changes
only upstream packaging/provenance does not force a new published learning
artifact.

### Signed package and publication

The build pipeline creates:

```text
dataset.db
LICENSES/*
manifest.json
SIGNATURE.ed25519
<artifact>.zip.sha256
```

Manifest version 2 contains complete SourceSnapshot identity including
`upstream_date` and `adapter_version`.

Production Ed25519 private keys never live in the repository or runtime. The CLI
accepts only `LOCKLEARN_DATASET_SIGNING_KEY_B64` from the build environment.
Tests use deterministic test-only keys.

The GitHub Actions workflow supports schedule and manual dispatch. Source
availability checks are lightweight. A signed ZIP may be published as a GitHub
Release only when a requested release tag is present and
`canonical_content_hash` differs from the previous supplied artifact. Raw
upstream downloads are never release assets.

### Freshness without runtime dependency

The source registry carries `check_interval_days` and
`target_refresh_days`. CI can report or rebuild stale sources, while an
installed dataset remains fully usable offline. Network failure never invalidates
an already installed generation.

## Alternatives considered

- Parse upstream corpora inside Home Assistant: rejected for latency, resource,
  reliability and offline-operation reasons.
- Commit raw upstream snapshots to the code repository: rejected because of
  size, churn and license-boundary confusion.
- Put pedagogy directly in JMdict/KANJIDIC adapters: rejected because source
  normalization and learning-product curation are separate responsibilities.
- Publish whenever an upstream checksum changes: rejected because source
  repackaging can change without changing LockLearn semantic content.
- Store a production private signing key in the repository: rejected
  categorically.

## Consequences

- P1.9 can consume prebuilt signed artifacts without owning upstream ETL.
- P1.10 can add the reviewed Japanese Starter recipe/configuration on top of
  this pipeline.
- Updating an adapter changes `adapter_version` in signed provenance.
- Official releases can be rebuilt and audited without retaining CI logs.
- CI/source availability can fail while installed LockLearn content continues
  to function.
