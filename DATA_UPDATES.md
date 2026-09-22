# Data update model

Official content follows the V1 pipeline:

```text
upstream source
→ CI adapter
→ normalized intermediate data
→ semantic + license validation
→ prebuilt SQLite dataset package
→ manifest + canonical content hash + Ed25519 signature
→ release artifact
→ LockLearn DatasetManager staging
→ local validation
→ merged content.next.db
→ atomic generation switch
```

Home Assistant does **not** parse the large raw upstream corpora during normal
updates. Runtime uses a single active generated `content.db` plus `state.db`.

A future `locklearn-data` repository should host adapters, scheduled builds and
official dataset release artifacts. Until that repository exists, this repo
contains only schemas, registries, tiny fixtures and validation tooling.


## P1.8 implementation

The repository now contains the build engine and source adapters, but **not**
the real upstream corpora.

Build-time layout:

```text
datasets/resources/sources.json
  legal/provenance/freshness policy

datasets/resources/source_builds.json
  discovery/fetch metadata and download ceilings

datasets/adapters/
  streaming source-native parsers

datasets/pipeline.py
  normalize → recipe → validate → sign → package

datasets/tools/build_dataset.py
  explicit build CLI

.github/workflows/datasets.yml
  weekly source check + manual signed build/release
```

Raw source files belong only in ignored `datasets/downloads/`,
`datasets/staging/` or temporary workspaces. Generated ZIPs live under ignored
`datasets/dist/`. GitHub Releases may contain only the signed LockLearn
artifact and its external SHA-256 file.

The source adapters deliberately do not decide which cards should exist.
A DatasetRecipe materializes normalized source records into the LockLearn
content model. The first reviewed production recipe/build config is P1.10.

### Release decision

A source refresh may change checksums or provenance without changing the
semantic learning content. Publication is therefore based on
`canonical_content_hash`, a deterministic ordered export of semantic tables.

```text
same canonical_content_hash → no release
different canonical_content_hash → release eligible
```

The signed manifest still records the exact new SourceSnapshots even when a
local/test rebuild is not published.

### Signing key

Production signing uses the CI secret:

```text
LOCKLEARN_DATASET_SIGNING_KEY_B64
```

It contains exactly 32 raw Ed25519 private-key bytes encoded as base64. The
private key is never stored in repository files or the Home Assistant
integration.


## P1.9 runtime update path

Home Assistant consumes only prebuilt LockLearn artifacts:

```text
bundled official dataset definition
        ↓
untrusted release catalog
        ↓
bounded ZIP download
        ↓
external SHA-256 + size
        ↓
Ed25519 manifest trust
        ↓
source/license/schema/package validation
        ↓
cached normalized dataset.db
        ↓
full content.next.db generation
        ↓
reader drain + atomic switch
        ↓
one-generation rollback
```

The release catalog is discovery metadata, not trust material. Artifact URLs are
restricted to HTTPS hosts bundled with the integration. Public verification keys
are bundled; private signing keys are never runtime data.

The package cache is reconstructible and validated against the active dataset
identity before every full-generation rebuild.

Dataset updates retain historical PackVersions. A Track remains pinned until an
explicit later integration action. Destructive dataset removal requires
confirmation and is rejected when persistent track state references one of its
PackVersions.

An UpdateEntity exists for each official dataset definition and exposes
installed/latest version, source freshness, disk cache size, sources, licenses
and release notes. Installed content remains usable when discovery is offline.
