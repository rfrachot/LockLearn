# ADR-0014 — Source snapshots, provenance and license boundaries

## Status

Accepted for P1.7 implementation on 2026-09-22; local quality verification is
required before the work package is marked PASS.

## Context

P1.2 already authenticates signed dataset manifests and rejects unknown,
NonCommercial and NoDerivatives licenses through the repository registries.
P1.6 stores a normalized content generation, but its Source/License rows were
deliberately minimal.

The V1 specification requires a dataset to answer, without consulting CI logs,
which exact upstream snapshots produced it. Provenance may be dataset-, entry-,
sentence- or asset-granular, and source-specific obligations such as Tatoeba
author attribution or KANJIDIC field exclusions must survive normalization.
Software licensing must not silently become the license of editorial content,
datasets or assets.

## Decision

### Registry is the policy authority

`datasets/resources/licenses.json` and `sources.json` are versioned registry
contracts. Licenses declare normalized identity, commercial/derivative/
ShareAlike/attribution facts and the scopes in which they may be used:

```text
software
editorial
dataset
asset
```

A source declares its default license and actual content scope, attribution
template, adapter ID, refresh policy, required provenance fields, audited field
allowlist and fields excluded by default.

The runtime/build policy does not infer compatibility from an SPDX-looking
string. Official artifacts fail closed when a license/source is unknown,
non-commercial, non-derivative, not approved for official data, or used in an
incompatible scope.

### Exact source snapshots

`SourceSnapshot` is distinct from Source and DatasetVersion. It records:

```text
snapshot_id
source_id
upstream_version
upstream_date
retrieved_at
source_url
sha256
adapter_version
```

The SHA-256 is canonical lowercase hexadecimal. A source listed by a dataset
must have at least one provenance record backed by an exact snapshot.

### Provenance records

`provenance_records` link a dataset/content object to:

```text
source snapshot
license + license scope
source record ID
author
language
modified_from_source
renderable attribution text
```

Supported V1 object boundaries are dataset, Concept, Term, LearningItem,
ContentBlock, Pack and reserved Asset identity. Asset metadata itself remains
P1.11 scope.

Dataset-level provenance is legal when that source's audit permits dataset
granularity. Source-specific policies can require finer fields. Tatoeba text,
for example, requires source record ID, author, license and language before an
adapter may emit official data.

### Mixed and third-party fields

Field-level legal/audit decisions live in the source registry, not in language-
specific core branches. `OfficialRegistryPolicy.validate_import_fields()`
provides the P1.8 adapters a fail-closed gate for field allowlists and explicit
exclusions.

## Alternatives considered

- Keep provenance only in the signed manifest: rejected because item/sentence/
  asset attribution would be lost after packages are merged into one generation.
- Put all attribution text directly on LearningItems: rejected because it
  duplicates source/snapshot/license facts and does not cover Terms, Packs or
  assets cleanly.
- Treat repository MIT as the default content license: rejected because software
  and data/editorial rights are separate.
- Implement source-specific checks in each adapter only: rejected because policy
  would become duplicated and easier to bypass.

## Consequences

- P1.8 adapters have a typed, centralized policy/provenance target.
- P1.9/P5 can expose installed source/version/license information without
  reparsing release manifests.
- P1.11 can attach Asset metadata to the already-reserved provenance boundary.
- Existing unpublished content schema v1 is completed in place; there is no
  released content database requiring a schema migration yet.
