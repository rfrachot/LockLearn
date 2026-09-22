"""Canonical content-domain model tests."""

from dataclasses import replace
from inspect import signature

import pytest

from custom_components.locklearn.core import content as m


def _item_and_facets() -> tuple[m.LearningItem, m.Facet, m.Facet]:
    item = m.LearningItem(
        "locklearn:item:rest",
        "locklearn:dataset:starter",
        m.ContentType.VOCABULARY,
        ("edrdg:concept:1",),
    )
    prompt = m.Facet(
        "locklearn:facet:rest-prompt",
        item.learning_item_id,
        m.FacetKind.TEXT,
        "prompt",
        "ja",
        "Jpan",
    )
    answer = m.Facet(
        "locklearn:facet:rest-answer",
        item.learning_item_id,
        m.FacetKind.TEXT,
        "answer",
        "fr",
        "Latn",
    )
    return item, prompt, answer


def test_card_identity_is_deterministic_and_facet_specific() -> None:
    item, prompt, answer = _item_and_facets()
    card = m.CardDefinition.from_facets(item, prompt, answer)
    same = m.CardDefinition.from_facets(item, prompt, answer)
    reverse = m.CardDefinition.from_facets(item, answer, prompt)

    assert card == same
    assert card.card_key != reverse.card_key
    assert card.card_definition_id != reverse.card_definition_id


def test_card_identity_derivation_accepts_only_item_and_facet_ids() -> None:
    expected_parameters = [
        "learning_item_id",
        "prompt_facet_id",
        "answer_facet_id",
    ]
    assert list(signature(m.derive_card_key).parameters) == expected_parameters
    assert list(signature(m.derive_card_definition_id).parameters) == expected_parameters


def test_card_rejects_foreign_facet() -> None:
    item, prompt, _ = _item_and_facets()
    foreign = m.Facet(
        "locklearn:facet:foreign",
        "locklearn:item:other",
        m.FacetKind.TEXT,
        "answer",
    )
    with pytest.raises(m.ContentModelError, match="different LearningItem"):
        m.CardDefinition.from_facets(item, prompt, foreign)


def test_concept_alignment_is_explicit_and_bounded() -> None:
    alignment = m.ConceptAlignment(
        "edrdg:concept:1",
        "wiktionary:concept:42",
        0.9,
        "manual-curation-v1",
    )
    assert alignment.review_status is m.AlignmentReviewStatus.PROPOSED

    with pytest.raises(m.ContentModelError, match=r"within \[0, 1\]"):
        m.ConceptAlignment(
            "edrdg:concept:1",
            "wiktionary:concept:42",
            1.1,
            "manual-curation-v1",
        )


def test_stable_id_builder_escapes_structural_separators() -> None:
    assert m.make_stable_id("edrdg", "jmdict", "123:abc") == "edrdg:jmdict:123%3Aabc"


def test_released_id_migration_is_explicit() -> None:
    migration = m.StableIdMigration(
        m.StableObjectType.FACET,
        "locklearn:dataset:starter",
        "locklearn:facet:old",
        "locklearn:facet:new",
        "1.1.0",
        "upstream stable identifier correction",
    )
    assert migration.old_id != migration.new_id

    card_key_migration = m.StableIdMigration(
        m.StableObjectType.CARD_KEY,
        "locklearn:dataset:starter",
        "locklearn:card:old",
        "locklearn:card:new",
        "1.1.0",
        "facet identity correction changed the derived progression key",
    )
    assert card_key_migration.object_type is m.StableObjectType.CARD_KEY


def test_mutable_display_text_is_not_part_of_card_identity() -> None:
    item, prompt, answer = _item_and_facets()
    before = m.CardDefinition.from_facets(item, prompt, answer)
    relabelled_prompt = replace(
        prompt,
        key="renamed-prompt",
        language_tag="en",
        script="Latn",
    )
    relabelled_answer = replace(answer, key="renamed-answer")
    after = m.CardDefinition.from_facets(item, relabelled_prompt, relabelled_answer)
    assert before.card_key == after.card_key
    assert before.card_definition_id == after.card_definition_id


def test_concept_and_term_are_distinct_source_domain_objects() -> None:
    concept = m.Concept(
        "edrdg:concept:1",
        "locklearn:dataset:starter",
        "edrdg:jmdict",
        "1234567",
        "1",
        m.ConceptType.LEXICAL,
    )
    term = m.Term(
        "edrdg:term:1234567-rest",
        "locklearn:dataset:starter",
        "en",
        "rest",
        "Latn",
    )

    assert concept.concept_id != term.term_id
    assert concept.source_record_id == "1234567"
    assert term.text == "rest"


def test_source_accepts_existing_license_registry_ids() -> None:
    source = m.Source("edrdg:jmdict", "JMdict", "EDRDG", "CC-BY-SA-4.0")
    assert source.license_id == "CC-BY-SA-4.0"
