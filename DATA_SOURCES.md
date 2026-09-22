# Official data source candidates

The canonical machine-readable registry is `datasets/resources/sources.json`.
No large upstream corpus is vendored in this repository.

## Priority V1 candidates

| Source | Intended use | Initial status |
|---|---|---|
| EDRDG JMdict | Japanese lexicon, readings, English senses | recommended; non-English glosses separately audited |
| KANJIDIC2 | kanji readings/strokes/selected metadata | recommended with imported-field allowlist |
| RADKFILE / KRADFILE | kanji components | recommended after field/license audit |
| Wiktionary via Wiktextract/Kaikki | multilingual lexicon/glosses | recommended textual data; media excluded by default |
| Tatoeba | example sentences/translations | recommended text; author attribution retained |
| KanjiVG | stroke/component vector assets | optional V1 data model, stronger V1.1/V2 renderer value |
| LockLearn original | grammar, curation, mnemonics, starter pack | required for a coherent first-party showcase |

## Design consequence

The Japanese showcase should not rely on the French JMdict glosses until their
specific rights/provenance are audited. A pragmatic V1 path is JMdict for
Japanese/English lexical structure plus French-language Wiktionary extraction
or original curated French content where license/provenance is explicit.

See `docs/data/SOURCE_AUDIT_2026-09-15.md` and `LICENSING.md`.


## P1.7 registry contract

The machine-readable registry is policy, not descriptive metadata. Each source
now declares:

```text
license_scope
attribution_template
adapter_id
required_provenance[]
field_allowlist (when a mixed source needs one)
excluded_by_default[]
notes
```

Future P1.8 adapters must call the centralized registry policy before emitting
official fields. Exact upstream material is represented by SourceSnapshot
records and merged content retains provenance records rather than relying on CI
logs or release-manifest availability.

Tatoeba text is the reference case for sentence-level attribution. KANJIDIC2 is
the reference case for a source that is acceptable only through an explicit
field allowlist. KanjiVG is the reference case for an asset license boundary.
