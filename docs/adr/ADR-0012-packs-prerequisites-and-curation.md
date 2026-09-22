# ADR-0012 — Versioned packs, prerequisites and data-driven curation

## Status

Accepted for the P1.5 content-selection contract on 2026-09-22.

## Context

LockLearn needs reusable LearningItems that can appear in several pedagogical
packs without duplication. Tracks must pin an immutable pack version so pack
updates can be previewed and deliberately integrated instead of silently
changing a learner's curriculum.

The spec also requires declarative prerequisites, unlock thresholds, confusable
introduction spacing and Japanese curation defaults. Those Japanese choices must
not become language-specific branches in the generic core.

## Decision

### Tags

Tags are stable queryable identifiers attached to LearningItems. They are
metadata and do not participate in LearningItem identity.

Persistence/indexes that make tags queryable at scale remain P1.6 scope.

### Pack identity and versioning

A `Pack` is a stable pedagogical-selection identity. A `PackVersion` is an
immutable released curation version and has a deterministic
`pack_version_id = pack_id + version`.

A Track pins exactly one `pack_version_id`. P1.5 defines the
`TrackPackPin` contract; full Track/Profile persistence and CRUD remain P2.

The same `learning_item_id` may be referenced by several PackVersions. Packs
never copy or redefine the LearningItem itself.

### Pack items and prerequisites

A `PackItem` references one LearningItem and carries pack-owned ordering and
optional prerequisite metadata:

```text
prerequisite_card_keys[]
unlock_when[]
card_defaults[]
```

Prerequisites use stable `card_key` identities. Unlock conditions are typed
thresholds over generic progress metrics. Evaluation of those thresholds belongs
to P3; P1.5 only defines and validates the declarative contract.

### Confusable groups

A `ConfusableGroup` contains at least two LearningItems and a positive
`min_intro_gap_days`. It is pack-version owned. Scheduling/enforcement belongs
to P3/P4.

### Pack version diffs

`PackVersionDiff` represents added, removed and changed LearningItem IDs so a
future Track update can show a deterministic integration preview. Diff buckets
must be disjoint.

### Curation policies

Curation behavior is represented by versioned generic `CurationPolicy` and
`CurationRule` values. The core understands rule kinds but never branches on a
language tag.

The official Japanese defaults are stored in
`datasets/resources/curation_policies.json`. They explicitly declare:

- isolated `glyph -> reading_on` disabled by default;
- isolated `glyph -> reading_kun` disabled by default;
- preference for contextualized readings;
- production anchored on complete terms/okurigana rather than bare glyphs;
- strong grading required before inverse production is enabled by default;
- isolated kanji meaning treated as mnemonic-keyword material;
- ambiguous prompts require context hints;
- examples should prefer already-covered vocabulary;
- furigana may support indispensable uncovered vocabulary.

LearningItem-level `register` and `required_item_ids`, plus P1.3 structured
reading/furigana and context-hint metadata, supply the generic data fields these
rules need.

A third-party pack may choose different curation defaults, but it must declare
them explicitly.

## Alternatives considered

- Copy LearningItems into each Pack: rejected because content identity and
  progression would fragment.
- Let Tracks point only to a mutable Pack: rejected because curriculum changes
  would silently alter active Tracks.
- Encode Japanese defaults in `if language == "ja"` branches: rejected by the
  core/content-agnostic architecture invariant.
- Evaluate prerequisites in P1.5: rejected because progress/SRS state belongs
  to P3.
- Store confusable timing directly in the scheduler: rejected because the group
  is content/curation metadata while enforcement is scheduling behavior.

## Consequences

- Pack updates are explicit and previewable.
- One LearningItem can participate in many packs with one stable identity.
- Prerequisites and confusable spacing can later be enforced without schema
  reinterpretation.
- Japanese official pedagogical choices are testable data, not core behavior.
- P1.6 still owns the final `content.db` schema/indexes.
- P2 owns full Track persistence/CRUD.
- P3/P4 own prerequisite evaluation, introduction selection and spacing.
