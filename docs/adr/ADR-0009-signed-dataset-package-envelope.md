# ADR-0009 — Signed dataset package and trust envelope

## Status

Accepted for the P1.2 package contract on 2026-09-22.

## Context

LockLearn installs prebuilt dataset artifacts produced outside Home Assistant.
The runtime must distinguish an authentic publisher declaration from untrusted
ZIP metadata, detect payload corruption, retain durable provenance/license
facts and inspect SQLite safely without prematurely defining the final content
schema. An archive and every byte it contains are hostile until validated.

Putting a SHA-256 of the final ZIP inside its own `manifest.json` would be
self-referential because the ZIP contains that manifest. Re-serializing JSON
before signature verification would also authenticate different bytes from the
ones actually distributed.

## Decision

### Versioned signed envelope

V1 is a ZIP with exactly one `manifest.json`, `dataset.db` and raw 64-byte
`SIGNATURE.ed25519`, plus explicitly declared files below optional `assets/`
and `LICENSES/`. `manifest_version`, `content_schema_version` and
`dataset_version` are independent version domains.

Ed25519 signs the exact UTF-8 bytes of `manifest.json`. Deterministic JSON is a
build/reproducibility property, not a verification transform. The signed
manifest lists every payload path, uncompressed size, SHA-256 and role. This
creates the transitive chain:

```text
trusted public key
  -> exact signed manifest bytes
  -> files[path, size, sha256, role]
  -> dataset.db, licenses and assets
```

`canonical_content_hash` identifies a future canonical logical export. A
checksum and compressed size for the final ZIP may be release metadata outside
the artifact; neither is an internal manifest field.

### Trust and rotation

The runtime trust registry contains public keys only, identified by stable key
IDs. Private production keys remain outside the repository and runtime. A
`revoked` key is always rejected. Historical artifacts signed by an `active` or
`deprecated` key are accepted only when
`valid_from <= manifest.built_at < valid_until`. This prevents wall-clock expiry
from breaking restoration of an artifact that was valid when signed. Producing
or authorizing a new build requires an `active` key valid at `built_at`.

### Hostile archive and policy validation

The validator inspects the central directory before bounded reads. It rejects
absolute, traversing, Windows-separated, NUL-containing and non-normal paths;
non-regular Unix types (including symlinks); duplicate/case-fold-colliding
members; unexpected or undeclared files; and archives over centralized count,
compressed-size, uncompressed-size or expansion-ratio limits. ZIP has no
portable hardlink member type; any non-regular Unix mode is rejected. There is
no `extractall()` call.

Payload hashes are streamed. Official acceptance is derived from LockLearn's
source and license registries, never from a package-authored
`commercial_compatible` assertion. Unknown, NC, ND and otherwise unapproved
official licenses fail closed.

After authentication, `dataset.db` alone is streamed into an isolated
temporary file, opened with SQLite `mode=ro&immutable=1`, and checked with
`PRAGMA integrity_check`. This also proves that validation does not require an
external WAL/SHM file. P1.2 deliberately requires no partial business tables or
`user_version`; P1.6 owns the complete content schema and activation model.

No upstream corpus parser runs on Home Assistant. Build adapters remain an
offline P1.8 concern.

## Alternatives considered

- Sign the final ZIP hash from inside its manifest: rejected as
  self-referential; an external release checksum remains possible.
- Sign `dataset.db` only: rejected because assets, licenses, provenance and
  compatibility metadata would be unauthenticated.
- Verify a canonicalized/re-serialized JSON object: rejected because a parser
  could change the authenticated byte sequence.
- Trust ZIP CRC/central-directory sizes: rejected because they provide neither
  publisher authenticity nor signed payload membership.
- Extract then validate: rejected because traversal, link and resource attacks
  must be stopped before filesystem materialization.
- Define a partial content schema now: rejected because publishing an
  incomplete schema would create avoidable migration debt before P1.6.

## Consequences

- Every accepted payload is transitively authenticated and independently
  checked for accidental corruption.
- Key rotation preserves legitimate historical restore while revocation remains
  an unconditional kill switch.
- Strict V1 parsing intentionally rejects unknown critical fields; format
  expansion requires a new `manifest_version`.
- The absolute archive ceilings are security controls, separate from the
  recommended 150 MiB official-dataset budget.
- P1.2 validates but does not install, download, merge, activate or roll back a
  dataset. Those remain later P1 work packages.
