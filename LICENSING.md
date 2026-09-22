# LockLearn licensing policy

This document separates software, original learning content and third-party
data. That separation is intentional and required by `SPEC_V1.md`.

## Software

LockLearn source code, build tooling and machine-readable schemas authored for
this repository are released under the **MIT License** unless a file explicitly
states otherwise. See `LICENSE`.

MIT permits commercial use, modification, redistribution and private use. It is
compatible with HACS distribution, donations, GitHub Sponsors, Ko-fi and future
commercial services built around the project.

## Original LockLearn learning/editorial content

Recommended license: **CC BY-SA 4.0**.

This includes original explanations, mnemonics, curated learning packs and
pedagogical examples where LockLearn owns the copyright. Content must carry an
explicit content license in its manifest; software's MIT license does not
implicitly relicense learning content.

## Third-party datasets and assets

Third-party material retains its own license. LockLearn must preserve required
attribution, source identity, version/snapshot and modification information.
Official datasets reject:

```text
NonCommercial (NC)
NoDerivatives (ND)
unknown / missing license
commercial-use ambiguity
```

ShareAlike sources are acceptable only when their derived dataset/artifact is
kept in an appropriate licensing boundary. Do not claim MIT over upstream data.

## Initial approved/audit candidates

The machine-readable registry is `datasets/resources/sources.json`.

- EDRDG JMdict: Japanese/English components are covered by EDRDG's CC BY-SA 4.0
  dictionary license; non-English translation components require separate
  source-specific audit before official import.
- KANJIDIC2 / related EDRDG data: CC BY-SA 4.0 baseline, with a strict imported
  field allowlist because some descriptor fields carry additional conditions.
- Wiktionary through Wiktextract/Kaikki: textual Wiktionary content is reusable
  under CC BY-SA 4.0 (and often GFDL); external media can carry different terms
  and is excluded by default.
- Tatoeba: text is CC BY 2.0 FR with attribution; audio licenses vary by
  contributor and audio is excluded by default.
- KanjiVG: CC BY-SA 3.0; keep it as a separately attributed dataset/asset
  boundary rather than pretending it is CC BY-SA 4.0 content.

## Donation / sponsorship compatibility

Receiving donations does not itself make an open-source project incompatible
with MIT or the allowed Creative Commons licenses above. The important
constraint is that official LockLearn distributions must continue to respect
each upstream license, especially attribution and ShareAlike obligations.

Funding channels therefore remain separate from licensing rights.


## Machine-enforced license scopes

P1.7 gives license use an explicit scope:

```text
software
editorial
dataset
asset
```

A license can be valid in more than one content scope, but a source must declare
the scope in which it is actually reused. The official-package policy rejects a
source when its declared scope is not allowed by the registry license.

This prevents the repository's MIT software license from being treated as a
fallback license for LockLearn editorial content or third-party datasets.

Exact source snapshots and per-object provenance retain the source record,
author/language when required, whether LockLearn modified the source material,
and attribution text needed for later Sources & Licences UI.
