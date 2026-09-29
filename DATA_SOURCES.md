# Official data sources

The canonical machine-readable policy is in
`datasets/resources/sources.json` and fetch/build metadata is in
`datasets/resources/source_builds.json`. This document explains the reviewed
human-facing contract required by SPEC §108.1.

No large upstream corpus is vendored in this repository or parsed on the Home
Assistant runtime.

## Source inventory

| Source | Provider | Upstream format / fetch | Adapter | License | Intended use | Refresh |
|---|---|---|---|---|---|---|
| JMdict | EDRDG | compressed dictionary XML/direct download | `jmdict_ng` | CC BY-SA 4.0 | Japanese lexicon, readings, English glosses | weekly check, 30-day target age |
| KANJIDIC2 | EDRDG | compressed XML/direct download | `kanjidic2` | CC BY-SA 4.0 | readings, stroke count, selected metadata | weekly check, 30-day target age |
| Wiktionary via Wiktextract/Kaikki | Wikimedia contributors / Kaikki | pinned JSONL release URL | `wiktextract_kaikki` | CC BY-SA 4.0 | multilingual glosses/forms/POS | weekly check, 30-day target age |
| Tatoeba text | Tatoeba contributors | per-language TSV/BZ2 template | `tatoeba_text` | CC BY 2.0 FR | example sentences/translations | weekly check, 30-day target age |
| KanjiVG | KanjiVG contributors | pinned release asset | `kanjivg_svg` | CC BY-SA 3.0 | stroke-order SVG/components | 30-day check, 90-day target age |
| LockLearn original | LockLearn contributors | repository-authored JSONL | `locklearn_editorial` | CC BY-SA 4.0 | grammar, mnemonics, curation, starter pack | release-driven |

RADKFILE/KRADFILE remain candidates, not an approved active registry entry; they
require a separate field/license audit before official use.

## JMdict

**Provider:** EDRDG.

**Usage:** Japanese lexical forms/readings, English glosses, parts of speech,
restrictions and sense metadata.

**Attribution:** “JMdict/EDRDG contributors — CC BY-SA 4.0”.

**Imported fields:** Japanese forms, readings, English glosses, POS,
restrictions and sense metadata.

**Excluded by default:** non-English glosses.

**Known risk:** non-English translation equivalents may have source-specific
rights/provenance and are therefore excluded until separately audited.

**Refresh:** weekly source check; official freshness target 30 days.

## KANJIDIC2

**Provider:** EDRDG.

**Usage:** kanji literal, readings, meanings, stroke count and selected educational
metadata.

**Attribution:** “KANJIDIC2/EDRDG contributors — CC BY-SA 4.0”.

**Imported fields:** literal, readings, meanings, stroke count, grade, frequency
and legacy JLPT metadata.

**Excluded by default:** third-party descriptor fields and search codes.

**Known risk:** some descriptor/search fields may have additional conditions;
official builds therefore use a strict allowlist.

**Refresh:** weekly source check; official freshness target 30 days.

## Wiktionary via Wiktextract / Kaikki

**Provider:** Wikimedia contributors; extracted through Wiktextract/Kaikki.

**Usage:** multilingual words, POS, senses, forms, translations and textual
examples.

**Attribution:** “Wiktionary contributors via Wiktextract/Kaikki — CC BY-SA 4.0”.

**Imported fields:** word, language, POS, senses, forms, translations and
examples text.

**Excluded by default:** media and externally licensed fragments.

**Known risk:** Wiktionary entries can embed material under different terms;
official ingestion is text-only unless a separate asset/license audit says
otherwise.

**Refresh:** weekly source check; recipe pins an exact JSONL URL rather than a
floating latest link; official freshness target 30 days.

## Tatoeba text

**Provider:** Tatoeba contributors.

**Usage:** example sentences and translation links.

**Attribution:** sentence-level source ID, author, license and language are
required. Template:
“Tatoeba sentence {source_record_id} by {author} — {license_id}”.

**Imported fields:** sentence ID, text, language, author, license and translation
links.

**Excluded by default:** audio and records with license problems.

**Known risk:** audio licenses vary by contributor; V1 official ingestion is
text-only.

**Refresh:** weekly check; official freshness target 30 days.

## KanjiVG

**Provider:** KanjiVG contributors.

**Usage:** stroke-order SVGs and visual component metadata.

**Attribution:** “KanjiVG contributors — CC BY-SA 3.0”.

**Imported fields:** character, SVG, stroke paths and components.

**Excluded by default:** none inside the reviewed asset boundary.

**Known risk:** it is a separate ShareAlike asset boundary, not LockLearn
editorial content. SVG is sanitized before signing/packaging.

**Refresh:** 30-day check; official freshness target 90 days; recipes pin an
exact release asset.

## LockLearn original

**Provider:** LockLearn contributors.

**Usage:** original grammar, mnemonics, curation and bundled starter material.

**Attribution:** “LockLearn contributors — CC BY-SA 4.0”.

**Imported fields:** recipe/editorial fields defined by the first-party adapter.

**Excluded by default:** none.

**Known risk:** editorial content must remain under its explicit content license
and must not inherit the repository MIT software license.

**Refresh:** release-driven; no network fetch.

## Provenance contract

Every accepted build records exact SourceSnapshots including source identity,
upstream version/date when available, retrieval timestamp, source URL, SHA-256
and adapter version. Per-object provenance retains source record identity and,
where required, author/language/modification/attribution fields.

The runtime and Sources & Licences UI read this provenance from the active signed
content generation rather than reconstructing legal truth from frontend
constants.

## Source audit

Material licensing decisions are recorded in
`docs/data/SOURCE_AUDIT_2026-09-15.md` and relevant ADRs. Any new source or
scope expansion must update:

1. the machine registry;
2. source/build schema validation;
3. this document;
4. the dated audit/ADR when licensing interpretation changes.

See `LICENSING.md` and `DATA_UPDATES.md`.
