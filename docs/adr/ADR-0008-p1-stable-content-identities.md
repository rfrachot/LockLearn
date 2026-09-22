# ADR-0008 — P1 stable content and card identities

## Status

Accepted for the P1.1 canonical content domain model on 2026-09-22.

## Context

LockLearn keeps user progression in `state.db` while content is independently
updated and eventually rebuilt into generations of `content.db`. Content object
identities must therefore survive display, translation, curation and dataset
release changes. A card is the skill represented by one ordered prompt/answer
facet pair of one LearningItem; it is not a Concept, Term, pack or track.

Independent sources may describe similar meanings without guaranteeing that
they represent the same semantic concept. Gloss similarity is not sufficient
evidence to merge their identities.

## Decision

### Stable content IDs

- Released `concept_id`, `term_id`, `learning_item_id` and `facet_id` values are
  namespaced, transport-safe and immutable.
- Importers reuse a stable upstream record identity when one exists. Otherwise,
  they derive an ID from documented, stable source-owned components.
- Row positions, import order, display labels, translations, normalized text,
  tags and other mutable content never form an identity.
- `Concept` and `Term` remain distinct. A Concept is source-native semantic
  identity; a Term is a linguistic representation. Similar text cannot collapse
  either object into the other.

### Card identity

Both card identifiers use the same canonical ordered tuple:

```text
(learning_item_id, prompt_facet_id, answer_facet_id)
```

Each tuple member is first validated as a stable ID. The canonical byte string
is the UTF-8 encoding of the three IDs joined by U+001F, which cannot occur in a
valid stable ID. Its lowercase SHA-256 hexadecimal digest is then prefixed:

```text
card_key           = locklearn:card:<digest>
card_definition_id = locklearn:carddef:<digest>
```

Tuple ordering is significant, so reversing prompt and answer produces a
different card. The two facets must belong to the LearningItem and must be
distinct.

No pack ID, pack version, track ID, dataset build/version, source snapshot,
ordering, tag, display text, facet label, language metadata, grading policy or
context hint participates in this derivation. Packs and tracks select or carry
progress for an existing CardDefinition; they do not define its identity.
Future P1.3 metadata may change without resetting progression as long as the
tested LearningItem and facet pair is unchanged.

### Cross-source alignment

Concepts remain native to their source or to a corpus with guaranteed internal
alignment. Any cross-source relation is a separate `ConceptAlignment` carrying
the source and target concept IDs, confidence, method and review status. It is
never inferred from equal or similar text. Only a reviewed alignment may later
be treated as pedagogical truth by a consumer.

### Identity changes and migrations

Changing a released ID is a data migration, not an ordinary content edit. The
dataset must ship an explicit old-to-new mapping with object type, dataset,
introduced version and reason. If a LearningItem or facet ID changes, the
mapping must also cover every transitively changed `card_definition_id` and
`card_key` before activation, so existing state can be migrated without losing
or silently reassigning progression.

Changing the separator, encoding, digest algorithm, prefixes or tuple members
also changes published identities and therefore requires the same explicit
migration treatment. P1.6 must validate these mappings during generation build
and activation; this ADR does not introduce the `content.db` schema.

## Consequences

- Dataset updates may freely revise mutable presentation content without
  changing card progression identity.
- The same LearningItem and facet pair has one deterministic identity across
  packs, tracks and dataset builds.
- Accidental source merges cannot silently broaden accepted answers.
- Correcting a bad published source identity has an explicit operational cost:
  complete migration mappings and validation are mandatory.
- The P1.1 model defines identities and mappings only. Persistence, activation
  and tombstone behavior remain P1.6 scope.
