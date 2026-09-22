# ADR-0017 — Bundled signed Japanese Starter for first-run content

## Status

Accepted for P1.10 implementation on 2026-09-22; local quality verification is
required before P1.10 is marked PASS.

## Context

LockLearn must not present an empty learning product after a fresh HACS install.
The V1 specification requires a very small signed starter dataset to be bundled
with the release so the first usable content does not depend on downloading or
parsing a large upstream corpus.

P1.8 already provides the offline build/sign pipeline and P1.9 provides trusted
runtime installation. P1.10 therefore needs content and packaging, not another
dataset code path.

## Decision

### Starter content

The first bundled product is:

```text
dataset:      locklearn:dataset:japanese-starter
pack:         locklearn:pack:japanese-starter
pack version: 1.0.0
```

It contains 120 LockLearn-authored LearningItems and 240 CardDefinitions:

- basic hiragana;
- basic katakana;
- a small yōon sample;
- 20 complete Japanese words with contextualized readings.

Kana cards exercise glyph/romaji directions. Word cards exercise complete
written-form/reading directions. The pack does not create isolated ON/KUN
reading cards.

The source is repository-authored `locklearn:original` editorial content under
CC BY-SA 4.0, distinct from the software's MIT license. Per-object provenance is
retained for Concepts, Terms, LearningItems and ContentBlocks, and pack
provenance is retained separately.

### Bundled artifact, not first-run download

The HACS integration contains the exact signed ZIP:

```text
custom_components/locklearn/datasets/bundled/
  japanese-starter-1.0.0.zip
```

The artifact is 178478 bytes, far below the official 10 MiB starter ceiling.
Its external SHA-256 and size are stored in the bundled-dataset registry.

On runtime creation, DatasetManager checks whether the dataset ID is already
installed. If it is absent, the bundled artifact is verified and activated
through the same P1.9 path used by downloaded official datasets:

1. bundled size/SHA-256;
2. exact signed manifest;
3. trusted Ed25519 public key;
4. source/license policy;
5. SQLite/package/schema validation;
6. complete generation build;
7. atomic activation.

No network call is involved. If the starter is already installed, bootstrap is
idempotent and never downgrades a newer version.

### One-purpose signing key

The 1.0.0 artifact was built on an ephemeral GitHub Actions runner with a
fresh Ed25519 private key. Only the public key was committed. The private key
was removed from the runner and the one-shot signing workflow was removed after
the artifact was committed.

The retained public key is immediately marked `deprecated`:

```text
locklearn-starter-2026-01
```

Historical validation therefore remains possible, but this key is not eligible
to authorize a new build. A future starter release must use reviewed current
signing material and a new dataset version; it cannot silently rewrite 1.0.0.

### Source reproducibility versus signature reproducibility

The editorial source JSONL, DatasetRecipe and build configuration remain in the
repository so the semantic dataset can be rebuilt and audited.

The exact 1.0.0 signature is intentionally not reproducible from repository
secrets because the private signing key no longer exists. The distributed
artifact itself remains immutable and verifiable against its bundled public
key, external digest and signed payload hashes.

### Failure and rollback

A corrupt/missing bundled artifact produces the normal P1.9 installation Repair
and does not replace the empty or last-known-good generation.

Tests cover fresh offline activation, installed-content query, idempotent
bootstrap, rollback to the previous generation and clean reinstall.

## Alternatives considered

- Download the starter on first setup: rejected because first usable content
  must not depend on Internet availability.
- Embed raw JSON and trust it specially: rejected because demo content must pass
  the same signature/license/schema rules as official content.
- Reuse large external Japanese corpora: rejected because first-run content
  should remain tiny and deterministic.
- Store a reusable private key in Git or the integration: rejected.
- Keep the one-shot key active after destroying its private half: rejected
  because its lifecycle state should accurately state that no future build may
  use it.

## Consequences

- A fresh HACS setup has signed Japanese learning content immediately.
- The starter exercises the real P1.8/P1.9 supply chain rather than a demo-only
  bypass.
- Future starter updates use normal DatasetManager update semantics.
- P1.11 remains free to add Asset metadata without changing this starter's text
  content path.
