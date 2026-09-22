"""P1.5 pack, prerequisite and curation contract tests."""

from dataclasses import replace

import pytest

from custom_components.locklearn.core import content as m
from custom_components.locklearn.core import packs as p


def _item(item_id: str = "locklearn:item:rest") -> m.LearningItem:
    return m.LearningItem(
        item_id,
        "locklearn:dataset:starter",
        m.ContentType.VOCABULARY,
        ("edrdg:concept:1",),
    )


def test_same_learning_item_can_belong_to_multiple_pack_versions() -> None:
    item = _item()
    n5 = p.PackVersion.create("locklearn:pack:japanese-n5", "1.0.0")
    food = p.PackVersion.create("locklearn:pack:japanese-food", "1.0.0")

    n5_item = p.PackItem(n5.pack_version_id, item.learning_item_id, 10)
    food_item = p.PackItem(food.pack_version_id, item.learning_item_id, 3)

    assert n5_item.learning_item_id == food_item.learning_item_id == item.learning_item_id
    assert n5_item.pack_version_id != food_item.pack_version_id


def test_pack_version_is_an_explicit_immutable_track_pin_target() -> None:
    v1 = p.PackVersion.create("locklearn:pack:japanese-n5", "1.0.0")
    v2 = p.PackVersion.create("locklearn:pack:japanese-n5", "1.1.0")
    pin = p.TrackPackPin("locklearn:track:renaud-japanese", v1.pack_version_id)

    assert pin.pack_version_id == v1.pack_version_id
    assert pin.pack_version_id != v2.pack_version_id


def test_pack_version_id_is_derived_from_pack_identity_and_version() -> None:
    version = p.PackVersion.create(
        "locklearn:pack:japanese-n5",
        "2026.09",
        curation_policy_id="locklearn:curation:japanese-default",
    )
    assert version.pack_version_id == "locklearn:pack:japanese-n5:version:2026.09"

    with pytest.raises(p.PackModelError, match="does not match"):
        p.PackVersion(
            "locklearn:pack:japanese-n5:version:wrong",
            "locklearn:pack:japanese-n5",
            "2026.09",
        )


def test_pack_item_prerequisites_and_unlock_conditions_are_declarative() -> None:
    prerequisite = "locklearn:card:recognition"
    item = p.PackItem(
        "locklearn:pack:japanese-n5:version:1.0.0",
        "locklearn:item:production",
        2,
        prerequisite_card_keys=(prerequisite,),
        unlock_when=(
            p.UnlockCondition(p.UnlockMetric.VERIFIED_CORRECT_COUNT, 2),
            p.UnlockCondition(p.UnlockMetric.MASTERY, 0.7),
        ),
    )

    assert item.prerequisite_card_keys == (prerequisite,)
    assert item.unlock_when[1].minimum == 0.7

    with pytest.raises(p.PackModelError, match="requires at least one prerequisite"):
        p.PackItem(
            "locklearn:pack:japanese-n5:version:1.0.0",
            "locklearn:item:production",
            2,
            unlock_when=(p.UnlockCondition(p.UnlockMetric.BOX, 2),),
        )


def test_mastery_unlock_threshold_is_bounded() -> None:
    with pytest.raises(p.PackModelError, match=r"within \[0, 1\]"):
        p.UnlockCondition(p.UnlockMetric.MASTERY, 1.1)


def test_confusable_groups_require_distinct_items_and_positive_gap() -> None:
    group = p.ConfusableGroup(
        "locklearn:confusable:wait-hold",
        "locklearn:pack:japanese-n5:version:1.0.0",
        ("locklearn:item:wait", "locklearn:item:hold"),
        2,
    )
    assert group.min_intro_gap_days == 2

    with pytest.raises(p.PackModelError, match="at least two"):
        p.ConfusableGroup(
            "locklearn:confusable:bad",
            "locklearn:pack:japanese-n5:version:1.0.0",
            ("locklearn:item:wait",),
            1,
        )


def test_pack_card_defaults_can_disable_specific_card_keys() -> None:
    isolated_reading = p.PackCardDefault(
        "locklearn:card:glyph-reading-on",
        enabled_by_default=False,
    )
    item = p.PackItem(
        "locklearn:pack:japanese-n5:version:1.0.0",
        "locklearn:item:kanji-rest",
        0,
        card_defaults=(isolated_reading,),
    )

    assert item.default_card_enabled(isolated_reading.card_key) is False
    assert item.default_card_enabled("locklearn:card:other") is None


def test_pack_version_diff_buckets_are_disjoint() -> None:
    diff = p.PackVersionDiff(
        "locklearn:pack:japanese-n5:version:1.0.0",
        "locklearn:pack:japanese-n5:version:1.1.0",
        added_learning_item_ids=("locklearn:item:new",),
        removed_learning_item_ids=("locklearn:item:old",),
        changed_learning_item_ids=("locklearn:item:changed",),
    )
    assert diff.added_learning_item_ids == ("locklearn:item:new",)

    with pytest.raises(p.PackModelError, match="disjoint"):
        p.PackVersionDiff(
            "locklearn:pack:japanese-n5:version:1.0.0",
            "locklearn:pack:japanese-n5:version:1.1.0",
            added_learning_item_ids=("locklearn:item:same",),
            changed_learning_item_ids=("locklearn:item:same",),
        )


def test_learning_item_curation_metadata_does_not_change_identity() -> None:
    item = _item()
    curated = replace(
        item,
        tag_ids=("locklearn:tag:theme-food", "locklearn:tag:difficulty-beginner"),
        register="plain",
        required_item_ids=("locklearn:item:known-word",),
    )

    assert curated.learning_item_id == item.learning_item_id
    assert curated.concept_ids == item.concept_ids


def test_learning_item_cannot_require_itself() -> None:
    with pytest.raises(m.ContentModelError, match="cannot require itself"):
        m.LearningItem(
            "locklearn:item:self",
            "locklearn:dataset:starter",
            m.ContentType.SENTENCE,
            ("locklearn:concept:self",),
            required_item_ids=("locklearn:item:self",),
        )


def test_curation_policy_is_generic_and_versioned() -> None:
    policy = p.CurationPolicy(
        "locklearn:curation:japanese-default",
        1,
        (
            p.CurationRule(
                "locklearn:curation-rule:disable-reading",
                p.CurationRuleKind.CARD_DIRECTION_DEFAULT,
                prompt_facet_key="glyph",
                answer_facet_key="reading_on",
                enabled_by_default=False,
            ),
            p.CurationRule(
                "locklearn:curation-rule:complete-term",
                p.CurationRuleKind.PRODUCTION_COMPLETE_TERM,
            ),
        ),
    )

    assert policy.version == 1
    assert policy.rules[0].enabled_by_default is False


def test_direction_fields_are_restricted_to_direction_rules() -> None:
    with pytest.raises(p.PackModelError, match="only valid"):
        p.CurationRule(
            "locklearn:curation-rule:bad",
            p.CurationRuleKind.PRODUCTION_COMPLETE_TERM,
            prompt_facet_key="meaning_fr",
        )
