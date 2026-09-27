"""Executable privacy contract for optional LockLearn Home Assistant sensors.

P6.5 deliberately ships no SensorEntity platform. This module defines the
identity, privacy, Recorder and state_class rules that any future optional
sensor implementation must obey.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from uuid import UUID

from homeassistant.components.sensor import SensorStateClass

from .const import DOMAIN

OPTIONAL_SENSOR_DEBOUNCE = timedelta(minutes=5)
OPTIONAL_SENSOR_SETTINGS_KEY = "ha_sensors"


class SensorScope(StrEnum):
    """Supported aggregate sensor scopes."""

    TRACK = "track"


class RecorderGuidance(StrEnum):
    """Whether generic HA history is useful for the metric."""

    OPTIONAL_HISTORY = "optional_history"
    EXCLUDE_RECOMMENDED = "exclude_recommended"


@dataclass(frozen=True, slots=True)
class OptionalSensorContract:
    """One future aggregate-only sensor contract."""

    key: str
    scope: SensorScope
    native_unit: str | None
    state_class: SensorStateClass | None
    recorder: RecorderGuidance
    enabled_by_default: bool = False
    aggregate_only: bool = True
    extra_state_attribute_keys: tuple[str, ...] = ()
    minimum_publish_interval: timedelta = OPTIONAL_SENSOR_DEBOUNCE


OPTIONAL_SENSOR_CONTRACTS: tuple[OptionalSensorContract, ...] = (
    OptionalSensorContract(
        key="mastery",
        scope=SensorScope.TRACK,
        native_unit="%",
        state_class=SensorStateClass.MEASUREMENT,
        recorder=RecorderGuidance.OPTIONAL_HISTORY,
    ),
    OptionalSensorContract(
        key="quiz_accuracy",
        scope=SensorScope.TRACK,
        native_unit="%",
        state_class=SensorStateClass.MEASUREMENT,
        recorder=RecorderGuidance.OPTIONAL_HISTORY,
    ),
    OptionalSensorContract(
        key="due_count",
        scope=SensorScope.TRACK,
        native_unit=None,
        state_class=None,
        recorder=RecorderGuidance.EXCLUDE_RECOMMENDED,
    ),
    OptionalSensorContract(
        key="streak",
        scope=SensorScope.TRACK,
        native_unit=None,
        state_class=None,
        recorder=RecorderGuidance.EXCLUDE_RECOMMENDED,
    ),
    OptionalSensorContract(
        key="last_exam_score",
        scope=SensorScope.TRACK,
        native_unit="%",
        state_class=SensorStateClass.MEASUREMENT,
        recorder=RecorderGuidance.OPTIONAL_HISTORY,
    ),
    OptionalSensorContract(
        key="consecutive_correct",
        scope=SensorScope.TRACK,
        native_unit=None,
        state_class=None,
        recorder=RecorderGuidance.EXCLUDE_RECOMMENDED,
    ),
    OptionalSensorContract(
        key="consecutive_wrong",
        scope=SensorScope.TRACK,
        native_unit=None,
        state_class=None,
        recorder=RecorderGuidance.EXCLUDE_RECOMMENDED,
    ),
    OptionalSensorContract(
        key="session_accuracy",
        scope=SensorScope.TRACK,
        native_unit="%",
        state_class=None,
        recorder=RecorderGuidance.EXCLUDE_RECOMMENDED,
    ),
    OptionalSensorContract(
        key="daily_goal_progress",
        scope=SensorScope.TRACK,
        native_unit="%",
        state_class=None,
        recorder=RecorderGuidance.EXCLUDE_RECOMMENDED,
    ),
)

_CONTRACT_BY_KEY = {contract.key: contract for contract in OPTIONAL_SENSOR_CONTRACTS}


def _canonical_uuid(value: str, *, field: str) -> str:
    """Require a canonical stable UUID before it can become HA entity identity."""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a UUID")
    try:
        parsed = UUID(value)
    except (AttributeError, TypeError, ValueError) as err:
        raise ValueError(f"{field} must be a UUID") from err
    canonical = str(parsed)
    if value != canonical:
        raise ValueError(f"{field} must use canonical UUID form")
    return canonical


def optional_sensor_unique_id(track_id: str, metric_key: str) -> str:
    """Return stable entity unique_id independent of HA entity_id or display name."""
    track_uuid = _canonical_uuid(track_id, field="track_id")
    if metric_key not in _CONTRACT_BY_KEY:
        raise ValueError(f"unsupported optional sensor metric: {metric_key}")
    return f"{track_uuid}:{metric_key}"


def profile_device_identifier(profile_id: str) -> tuple[str, str]:
    """Return the stable logical Device identifier for one private Profile."""
    profile_uuid = _canonical_uuid(profile_id, field="profile_id")
    return DOMAIN, f"profile:{profile_uuid}"


def optional_sensor_contract(metric_key: str) -> OptionalSensorContract:
    """Return one validated future sensor contract."""
    try:
        return _CONTRACT_BY_KEY[metric_key]
    except KeyError as err:
        raise ValueError(f"unsupported optional sensor metric: {metric_key}") from err


def resolve_optional_sensor_metrics(
    profile_settings: Mapping[str, object],
    track_settings: Mapping[str, object],
) -> frozenset[str]:
    """Resolve explicit double opt-in without inferring consent from ACL or HA admin status."""
    profile_raw = profile_settings.get(OPTIONAL_SENSOR_SETTINGS_KEY)
    track_raw = track_settings.get(OPTIONAL_SENSOR_SETTINGS_KEY)
    if not isinstance(profile_raw, Mapping) or profile_raw.get("enabled") is not True:
        return frozenset()
    if not isinstance(track_raw, Mapping) or track_raw.get("enabled") is not True:
        return frozenset()

    metrics = track_raw.get("metrics")
    if not isinstance(metrics, (list, tuple, set, frozenset)):
        raise ValueError("ha_sensors.metrics must be a collection")
    if not all(isinstance(metric, str) for metric in metrics):
        raise ValueError("ha_sensors.metrics must contain only strings")
    normalized = frozenset(metrics)
    unknown = normalized - _CONTRACT_BY_KEY.keys()
    if unknown:
        raise ValueError(f"unsupported optional sensor metrics: {sorted(unknown)!r}")
    return normalized
