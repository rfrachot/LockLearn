"""Canonical content-domain model tests."""

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


def test_mutable_display_text_is_not_part_of_card_identity() -> None:
    item, prompt, answer = _item_and_facets()
    before = m.CardDefinition.from_facets(item, prompt, answer)
    renamed_item = m.LearningItem(
        item.learning_item_id,
        item.dataset_id,
        item.content_type,
        item.concept_ids,
    )
    after = m.CardDefinition.from_facets(renamed_item, prompt, answer)
    assert before.card_key == after.card_key


def test_source_accepts_existing_license_registry_ids() -> None:
    source = m.Source("edrdg:jmdict", "JMdict", "EDRDG", "CC-BY-SA-4.0")
    assert source.license_id == "CC-BY-SA-4.0"
