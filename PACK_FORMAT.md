# Pack and dataset format

This document describes the V1 community/official artifact boundary. Machine
validation is authoritative.

## Package envelope

A dataset package is a bounded ZIP containing at minimum:

```text
manifest.json
SIGNATURE.ed25519
dataset.db
```

Optional signed payloads may exist under:

```text
assets/
LICENSES/
```

The validator rejects path traversal, duplicate/case-colliding members, encrypted
or unsupported compression, unsafe file types, excessive entry/size/expansion
limits and unlisted payloads.

## Manifest and signature

`manifest.json` describes dataset identity/version, content schema compatibility,
source snapshots, files/checksums, signing key and activation requirements.
The exact manifest bytes are verified using Ed25519.

External release discovery metadata is not trusted: runtime separately checks
artifact size and SHA-256 before validating the signed package.

## Stable IDs

Released IDs are namespaced and transport-safe. Concept, Term, LearningItem,
Facet and CardDefinition identities do not depend on mutable display text.

CardDefinition identity is derived from:

```text
learning_item_id + prompt_facet_id + answer_facet_id
```

Released-ID changes require explicit migration mappings.

## Languages and normalization

Language tags use canonical BCP 47 forms; script codes follow ISO 15924.
Term normalization is versioned. A behavior change that alters normalized output
requires a normalization version change/rebuild.

## Content types and tags

Core content types are generic (vocabulary, grammar, expression, sentence,
culture, conjugation, kanji, custom). `kanji` is data classification, not a
Japanese-specific core behavior.

Tags, register, required-item relationships and PackVersion curation are data.

## Answer/grading contract

CardDefinitions declare:

- `answer_semantics`;
- `grading_policy_kind`;
- `grading_policy_version`;
- optional context-hint Facets.

The runtime supports exact/any-of/conservative normalized fuzzy grading contracts;
`unrecognized` is distinct from `wrong` and must not fabricate an SRS failure.

## PackVersion

PackVersions are immutable and may define:

- ordered LearningItems;
- prerequisites;
- unlock thresholds;
- enabled-by-default cards;
- confusable groups and minimum introduction gap;
- curation policy ID.

Tracks explicitly pin a PackVersion. Updates are previewed/integrated deliberately.

## Sources, provenance and licenses

Every official object must remain attributable to exact SourceSnapshots and
declared licenses. Source/asset license scope is explicit. Official policy rejects
NC, ND, missing/unknown and commercially ambiguous licenses.

See `DATA_SOURCES.md`, `DATA_UPDATES.md`, `LICENSING.md`.

## Assets

Signed public assets are metadata rows plus payload files; binary media is not
stored as SQLite BLOBs. Runtime extraction rechecks size and SHA-256. Private
exports/uploads are a separate storage/security boundary.

## Compatibility and update policy

Software version and dataset version are independent. Runtime accepts only the
supported content schema versions declared by the integration. Installation builds
a complete candidate generation, validates it, drains readers and atomically
switches active content; last-known-good content remains usable on failure.

## Machine-readable schemas

Schemas live in `datasets/schemas/` and are validated by
`datasets/tools/validate_schemas.py`. Package/manifest semantic validation lives
in the dataset package/pipeline modules and tests.
