# ADR-0016 — Local DatasetManager, trusted updates and rollback

## Status

Accepted for P1.9 implementation on 2026-09-22; local quality verification is
required before P1.9 is marked PASS.

## Context

P1.2–P1.8 establish the signed artifact format, immutable content generations,
source/license provenance and the offline build pipeline. Home Assistant still
needs a local component that discovers released artifacts, installs them without
parsing upstream corpora, exposes update status and preserves last-known-good
content on every failure.

The remote release catalog is useful for discovery, but it is network-controlled
metadata and cannot be a root of trust.

## Decision

### Discovery is untrusted; signed artifacts are authoritative

Each official dataset is defined by bundled runtime policy:

- stable dataset ID and display name;
- HTTPS discovery catalog URL;
- explicit artifact-host allowlist;
- maximum artifact size.

The remote catalog may advertise versions, changelog, release URL, artifact URL,
size and external SHA-256. Before download, the artifact URL must be HTTPS and
its hostname must be allowlisted by the bundled definition.

A successful installation still requires all of:

1. bounded download;
2. exact external SHA-256 and size match;
3. hostile-ZIP validation;
4. detached Ed25519 signature against bundled public keys;
5. manifest compatibility with the installed LockLearn/content schema;
6. source/license policy validation;
7. read-only SQLite/package validation;
8. signed manifest ↔ package dataset/version/canonical-hash agreement;
9. validated generation build;
10. atomic generation activation.

A compromised discovery catalog cannot authorize unsigned content.

### Runtime policy is bundled

The HACS custom component includes copies of the public source/license policy,
official dataset definitions and public signing-key registry. Tests require the
runtime source/license copies to be byte-identical to the build-time registries.

The initial P1.9 official dataset and key registries are intentionally empty.
P1.10 owns the first reviewed Japanese Starter dataset definition and production
public signing key. No private key is ever bundled.

### Package cache and full-generation rebuild

Verified normalized `dataset.db` payloads are cached below the reconstructible
content cache, keyed by hashes of dataset ID and version.

Updating one dataset rebuilds the next generation from:

- the newly verified target package; and
- one validated cached package for every other active dataset.

The manager fails closed when a required cache entry is missing, has the wrong
dataset/version, or no longer matches the active canonical content hash.

A dataset version is immutable. Reinstalling the currently active version is
rejected; the same version with different canonical content is treated as an
integrity violation.

### Pack versions and removal

Dataset updates do not delete old PackVersion rows. Tracks therefore remain
pinned until a future explicit integration decision.

Removal is an explicit operation. It requires confirmation and refuses removal
when any PackVersion in the dataset is referenced by persistent
`track_pack_versions` state. Before P2 creates that table, the same guard can be
supplied explicitly by the caller. User state is never cascade-deleted.

### UpdateEntity and Repairs

One Home Assistant UpdateEntity is created per bundled official dataset
definition. Installed state is loaded locally on entity addition so Home
Assistant startup does not depend on Internet access. Polling may refresh remote
availability later.

The entity exposes privacy-safe metadata:

- installed/latest version;
- changelog/release URL;
- source age and stale source IDs;
- cache size;
- source snapshot versions/dates;
- licenses.

Repairs are created for discovery failures, installation/verification failures
and stale source snapshots. Discovery failure never makes installed content
unavailable.

### Rollback and cancellation

P1.9 delegates the atomic reader drain/switch to P1.6. The immediately previous
validated generation remains available for rollback.

Long generation builds are shielded from task cancellation until their executor
work finishes, preventing cleanup from racing an in-flight SQLite build.

## Alternatives considered

- Trust the remote catalog checksum alone: rejected; the catalog is not trusted.
- Download and parse raw JMdict/etc. in Home Assistant: rejected by the offline
  build boundary.
- Replace only the target dataset in-place: rejected; runtime uses one immutable
  generation and update must remain atomic.
- Delete old PackVersions during dataset update: rejected because Tracks pin
  exact versions.
- Infer signing keys from manifests/releases: rejected because trust material
  must be local and reviewed.

## Consequences

- P1.10 can activate the first official dataset by populating reviewed runtime
  dataset/key registries without changing DatasetManager architecture.
- P2 can populate `track_pack_versions`; the P1.9 removal guard will begin using
  it automatically.
- P5 can render dataset update/source/license details from the UpdateEntity and
  manager status rather than reimplementing supply-chain logic.
- Installed content remains usable when release discovery is offline.
