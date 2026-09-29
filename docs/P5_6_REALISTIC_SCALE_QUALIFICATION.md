# P5.6 realistic content scale qualification

Qualification run: 2026-09-26, Linux development VM, Python 3.14.4, SQLite
through the existing writer/reader executors. The package and raw upstream
download were kept under ignored `datasets/downloads`, `datasets/staging` and
`datasets/dist` paths; no large artifact is committed.

## Reproduction

The qualification corpus uses the existing streaming `jmdict_ng` adapter and
the approved EDRDG JMdict dataset boundary. It imports only Japanese forms,
readings and English glosses; French JMdict glosses are not imported.

```bash
export LOCKLEARN_DATASET_SIGNING_KEY_B64='<ephemeral qualification key>'
.venv/bin/python -m datasets.tools.build_dataset \
  datasets/configs/p5-6-jmdict-scale.json \
  --output datasets/dist/p5-6 \
  --workspace datasets/staging/p5-6-build \
  --repository-root .

.venv/bin/python -m scripts.p5_6_realistic_scale \
  datasets/dist/p5-6/locklearn-dataset-jmdict-scale-2026.09.zip \
  --public-key-b64 '<ephemeral qualification public key>' \
  --repository-root .
```

The build performs normalization, recipe materialization, schema/foreign-key
validation, canonical hashing, signing and ZIP packaging. The qualification
then validates the signed package with its ephemeral public key, extracts only
the validated `dataset.db`, builds two out-of-place content generations,
activates both, and rolls back to the first generated generation.

Source snapshot:

```text
source: edrdg:jmdict
upstream: JMdict_e-2021-05-05 / 2021-05-05
retrieved: 2026-09-26
raw sha256: 824c37b65ae3a731981da5ca3addcfd15e181067bab96d02dee7f27660044d99
adapter: jmdict_ng 1
license: CC-BY-SA-4.0, dataset scope
```

The registered HTTPS download URL uses `www.edrdg.org`; the equivalent FTP
hostname presented a certificate-name error on the qualification VM.

## Result

```text
dataset: 1
concepts: 20,000
terms: 40,000
learning_items: 20,000
facets: 40,000
card_definitions: 40,000
packs: 1
pack_versions: 1
package ZIP: 30,023,845 bytes
dataset.db in package: 243,843,072 bytes
active content.db: 264,339,456 bytes
canonical_content_hash: 03002b1649216bb1ed5f3af6147a9f35f724158a0379eadc183073ffa2c06702
```

`PRAGMA integrity_check` returned `ok` and `PRAGMA foreign_key_check` returned
no rows for the package and generated candidates. Manifest, license policy,
provenance and stable card identity validation passed.

## Generation timings

Measured on the same VM with a fresh temporary state/content root:

```text
package signature/package validation: 1.26 s
generation build 1: 4.91 s
generation activation 1: 1.76 s
generation build 2: 8.17 s
generation activation 2: 1.77 s
rollback: 1.75 s
```

The previous generated file remained available after activation and rollback
restored `p5-6-scale-1`, which was then readable and queryable.

## Hot-path measurements

The timings below use repeated calls on a fresh generated database. p95 is the
95th percentile of 20 calls unless stated otherwise; warm SQLite/page-cache
behavior is representative of the local worker process.

```text
PackVersion lookup: p50 0.74 ms / p95 1.00 ms / max 1.40 ms
pack page, 50 rows at offset 10,000: p50 3.48 ms / p95 3.64 ms / max 3.64 ms
new-card selection, 20 cards: p50 19.31 ms / p95 19.81 ms / max 20.16 ms
due selection, 20 cards: p50 0.78 ms / p95 0.84 ms / max 0.85 ms
one-card presentation: p50 0.97 ms / p95 1.03 ms / max 5.49 ms
bulk direction-card load, 20,000 cards: p50 222.39 ms / p95 225.84 ms / max 230.55 ms
session candidate materialization, 20,000 candidates: p50 198.75 ms / max 204.03 ms
session preparation, 20 requested cards: 0.43 s
```

The `next-card` path is the bounded new-card query and remains below the
150 ms p95 target. Bulk Track integration and candidate materialization are
reported separately because they intentionally load the full selected corpus.
`ORDER BY RANDOM()` is not used. The observed temporary ordering work is on
bulk ordered materialization; the new-card query was forced to use the existing
PackVersion/Item index and dropped from roughly 120 ms p95 to 19 ms p95.

## Issues found and corrections

- The recipe initially treated a JMdict reading as a separate text block. For
  kana entries where writing equals reading this made backend facet resolution
  ambiguous. The reading is now metadata on the Japanese block, and the
  corrected package was rebuilt and requalified.
- Session preparation performed per-card constraint reads even when a pack had
  no prerequisites, confusable groups or sibling concepts. A bounded
  PackVersion probe now skips that N+1 path only when the absence is proven;
  constrained packs retain the existing per-card evaluator. Preparation fell
  from 33.55 s to 0.43 s in this corpus.
- The new-card and PackVersion card-selection joins now force the existing
  `pack_items_version_item` index after `EXPLAIN QUERY PLAN` showed an avoidable
  card-first traversal. No schema version or pedagogical rule changed.

## Home Assistant

`REAL HA: NOT EXECUTED — HARNESS UNAVAILABLE`

The local qualification harness was not available for safely installing this
ephemeral, non-bundled dataset on the development HA instance. No real user
database was touched.
