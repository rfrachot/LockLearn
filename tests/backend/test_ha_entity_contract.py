"""P6.5 Home Assistant entity privacy contract tests."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import Platform

from custom_components.locklearn import _PLATFORMS
from custom_components.locklearn.ha_entity_contract import (
    OPTIONAL_SENSOR_CONTRACTS,
    OPTIONAL_SENSOR_DEBOUNCE,
    RecorderGuidance,
    optional_sensor_contract,
    optional_sensor_unique_id,
    profile_device_identifier,
    resolve_optional_sensor_metrics,
)

_PROFILE_ID = "11111111-1111-4111-8111-111111111111"
_TRACK_ID = "a2222222-2222-4222-8222-222222222222"


def test_v1_ships_without_optional_private_sensor_platform() -> None:
    """Optional learning sensors cannot accidentally become a 1.0 requirement."""
    assert _PLATFORMS == (Platform.UPDATE,)
    assert Platform.SENSOR not in _PLATFORMS


def test_every_optional_sensor_is_explicitly_opt_in_aggregate_only_and_debounced() -> None:
    """Future sensor implementations inherit a fail-closed privacy contract."""
    assert timedelta(minutes=5) <= OPTIONAL_SENSOR_DEBOUNCE
    assert OPTIONAL_SENSOR_CONTRACTS

    keys: set[str] = set()
    for contract in OPTIONAL_SENSOR_CONTRACTS:
        assert contract.key not in keys
        keys.add(contract.key)
        assert contract.enabled_by_default is False
        assert contract.aggregate_only is True
        assert contract.extra_state_attribute_keys == ()
        assert contract.minimum_publish_interval >= OPTIONAL_SENSOR_DEBOUNCE
        assert contract.recorder in {
            RecorderGuidance.OPTIONAL_HISTORY,
            RecorderGuidance.EXCLUDE_RECOMMENDED,
        }


def test_state_class_is_only_used_for_real_measurements() -> None:
    """Counts/snapshots must not masquerade as HA long-term statistics."""
    measurement_keys = {
        contract.key
        for contract in OPTIONAL_SENSOR_CONTRACTS
        if contract.state_class is SensorStateClass.MEASUREMENT
    }
    assert measurement_keys == {"mastery", "quiz_accuracy", "last_exam_score"}

    for key in {
        "due_count",
        "streak",
        "consecutive_correct",
        "consecutive_wrong",
        "session_accuracy",
        "daily_goal_progress",
    }:
        assert optional_sensor_contract(key).state_class is None


def test_entity_identity_is_uuid_based_and_independent_of_names() -> None:
    """HA display/entity names never participate in LockLearn sensor identity."""
    assert optional_sensor_unique_id(_TRACK_ID, "mastery") == f"{_TRACK_ID}:mastery"
    assert profile_device_identifier(_PROFILE_ID) == (
        "locklearn",
        f"profile:{_PROFILE_ID}",
    )

    with pytest.raises(ValueError, match="track_id must be a UUID"):
        optional_sensor_unique_id("Japanese with Zoé", "mastery")
    with pytest.raises(ValueError, match="canonical UUID"):
        optional_sensor_unique_id(_TRACK_ID.upper(), "mastery")
    with pytest.raises(ValueError, match="unsupported optional sensor metric"):
        optional_sensor_unique_id(_TRACK_ID, "last_learned_word")


def test_contract_contains_no_content_bearing_attribute_surface() -> None:
    """No future default entity attributes can carry vocabulary/answers/IDs."""
    forbidden_fragments = {
        "card",
        "content",
        "word",
        "answer",
        "response",
        "annotation",
        "learning_item",
        "facet",
        "target",
        "profile_name",
        "track_name",
    }
    for contract in OPTIONAL_SENSOR_CONTRACTS:
        serialized = " ".join(contract.extra_state_attribute_keys).lower()
        assert all(fragment not in serialized for fragment in forbidden_fragments)
        assert contract.extra_state_attribute_keys == ()


def test_sensor_exposure_requires_profile_and_track_double_opt_in() -> None:
    """ACL membership/admin status can never implicitly expose private sensors."""
    profile_settings = {"ha_sensors": {"enabled": True}}
    track_settings = {
        "ha_sensors": {
            "enabled": True,
            "metrics": ["mastery", "due_count"],
        }
    }

    assert resolve_optional_sensor_metrics({}, track_settings) == frozenset()
    assert resolve_optional_sensor_metrics(profile_settings, {}) == frozenset()
    assert (
        resolve_optional_sensor_metrics(
            {"ha_sensors": {"enabled": False}},
            track_settings,
        )
        == frozenset()
    )
    assert (
        resolve_optional_sensor_metrics(
            profile_settings,
            {"ha_sensors": {"enabled": False, "metrics": ["mastery"]}},
        )
        == frozenset()
    )
    assert resolve_optional_sensor_metrics(
        profile_settings,
        track_settings,
    ) == frozenset({"mastery", "due_count"})

    with pytest.raises(ValueError, match="unsupported optional sensor metrics"):
        resolve_optional_sensor_metrics(
            profile_settings,
            {
                "ha_sensors": {
                    "enabled": True,
                    "metrics": ["mastery", "last_learned_word"],
                }
            },
        )

    with pytest.raises(ValueError, match="only strings"):
        resolve_optional_sensor_metrics(
            profile_settings,
            {"ha_sensors": {"enabled": True, "metrics": ["mastery", 1]}},
        )
