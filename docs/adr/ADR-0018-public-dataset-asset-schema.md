# ADR-0018 — Public dataset Asset schema and media boundary

## Status

Accepted for P1.11 on 2026-09-22.

## Context

LockLearn V1 is text-first but the domain model must already represent image
and audio learning without a conceptual migration later. Public dataset media
must remain signed, attributable and locally verifiable, while large binary
payloads should not be stored as SQLite BLOBs.

Private user media and export/import attachments are a different trust and
privacy boundary from signed public dataset assets.

## Decision

### Asset metadata is normalized content

Content schema v2 adds immutable public dataset Asset metadata:

```text
asset_id
dataset_id
kind
path
sha256
byte_size
mime_type
width
height
license_id
license_scope=asset
attribution
```

Image dimensions are mandatory and positive. Audio does not carry image
dimensions.

Public dataset asset paths are normalized POSIX paths below `assets/`. Paths
with traversal, absolute roots, backslashes or non-normal components are
rejected.

The initial MIME allowlist is intentionally passive:

```text
image/jpeg
image/png
image/webp

audio/mp4
audio/mpeg
audio/ogg
audio/wav
audio/webm
```

Active image formats such as SVG are not accepted before a dedicated renderer
and sanitization policy exist.

### Bytes stay outside SQLite

SQLite stores only Asset metadata and references. Signed package bytes live as
normal ZIP payload members below `assets/`.

The manifest records every media member with:

```text
path
size
sha256
role=asset
```

Package validation requires the signed manifest Asset payload set to match
`assets_metadata(path, byte_size, sha256)` exactly.

At install time, media bytes are extracted into the reconstructible content
cache. Runtime resolution rechecks size and SHA-256 before returning a local
path.

### Facets and ContentBlocks reserve image/audio semantics now

`Facet.kind` supports:

```text
text
image
audio
structured
```

A media facet is linked through `facet_assets` to exactly one Asset of the same
dataset and media kind.

Image/audio ContentBlocks use a closed payload shape:

```json
{"asset_id": "locklearn:asset:..."}
```

The validator requires that reference to resolve to a same-dataset Asset whose
kind matches the ContentBlock kind.

This reserves future cards such as `image → text` and `audio → text` without
requiring a schema redesign. Renderer implementation remains outside P1.11.

### Asset provenance and licensing are mandatory

Every public Asset belongs to the dataset's explicit `asset` license scope and
must have Asset-level provenance. Attribution is stored with Asset metadata and
the source snapshot/license remain available through the normal provenance
tables.

Build tooling derives byte size and SHA-256 from the exact packaged bytes. A
recipe cannot substitute metadata for different bytes.

### Public dataset assets are not private/export assets

The P1.11 runtime resolver is explicitly named
`async_resolve_public_asset()`. It resolves only Asset metadata from the active
signed content generation and only below the reconstructible public Asset cache.

Private user uploads, annotations, export/import attachments and future profile
media must use a separate state/private storage namespace and authenticated
serving path. They must not be inserted into `assets_metadata` or exposed
through the public dataset resolver.

No private/export serving endpoint is introduced by P1.11.

## Backward compatibility

Content schema v1 remains supported for the already-signed asset-free Japanese
Starter 1.0.0. Schema v2 is used for newly built packages and generations.

The validator selects the required table/index contract by schema version.
Legacy v1 packages are not retroactively required to contain Asset tables.

## Alternatives considered

- Store media as SQLite BLOBs: rejected for package/database size and streaming
  behavior.
- Put arbitrary URLs in Facets: rejected because runtime content would no longer
  be self-contained, signed or reliably offline.
- Allow arbitrary image/audio MIME types: rejected until renderer-specific
  security policies exist.
- Reuse the public Asset resolver for private uploads: rejected because public
  signed content and private user state have different ACL, backup and export
  requirements.

## Consequences

- V1 content schema can safely represent image/audio cards before renderers are
  implemented.
- Signed packages authenticate both media bytes and their metadata.
- Dataset updates/rollback naturally version Asset bytes with the content
  generation.
- P7.3 can focus on renderer UX/security instead of redesigning content
  identity.
