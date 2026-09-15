# Initial source/license audit — 2026-09-15

This is the bootstrap audit used to shape the V1 source registry. Re-check it
before publishing any official dataset artifact.

## EDRDG JMdict / KANJIDIC

EDRDG's general dictionary license places the covered dictionary files under CC
BY-SA 4.0 and explicitly states that commercial use is not restricted when the
license conditions are met. For JMdict, the statement covers Japanese and
English components; translation equivalents in other languages are called out
as potentially subject to copyrights held by their compilers.

Decision: JMdict Japanese/English is a strong V1 source. Do not ingest French or
other non-English glosses into an official LockLearn dataset until their
specific rights are audited.

KANJIDIC uses the same CC BY-SA 4.0 baseline, but its documentation notes that
some third-party descriptor/search code fields have their own conditions.
Decision: maintain an explicit allowlist of imported fields.

## Wiktionary via Wiktextract / Kaikki

Wiktionary text is generally reusable under CC BY-SA 4.0 (and GFDL on relevant
editions), while individual media/externally sourced material can differ.
Kaikki provides regularly refreshed machine-readable Wiktextract outputs.

Decision: strong multilingual text source; exclude media by default and retain
edition/snapshot provenance.

## Tatoeba

Tatoeba documents its textual data as CC BY 2.0 France and requires attribution.
Audio uses contributor-specific licenses and can include NonCommercial terms.

Decision: use text with sentence ID/author/license provenance; exclude audio by
default.

## KanjiVG

KanjiVG is published under CC BY-SA 3.0.

Decision: acceptable as a separately attributed asset/dataset boundary; do not
silently treat it as CC BY-SA 4.0 original LockLearn content.
