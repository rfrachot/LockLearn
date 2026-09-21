"""Evidence-driven Companion notification capabilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class Capability(StrEnum):
    """Tri-state result; unknown is never treated as supported."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class LearningNotificationMode(StrEnum):
    """Safe rendering modes for passive learning."""

    TWO_STEP_REVEAL = "two_step_reveal"
    EXPOSURE_ONLY = "exposure_only"


@dataclass(frozen=True, slots=True)
class TargetCapabilities:
    """Capabilities measured for one stable device-registry target."""

    device_registry_id: str
    platform: str
    tag_replace: Capability = Capability.UNKNOWN
    silent_replace: Capability = Capability.UNKNOWN
    clear_notification: Capability = Capability.UNKNOWN
    cleared_signal: Capability = Capability.UNKNOWN
    expiration: Capability = Capability.UNKNOWN
    channel_importance: Capability = Capability.UNKNOWN
    text_input: Capability = Capability.UNKNOWN
    lockscreen_visibility: Capability = Capability.UNKNOWN
    media: Capability = Capability.UNKNOWN
    visible_action_count: int = 0
    shared_device: bool = False
    tested_app_version: str | None = None
    tested_at_utc: str | None = None

    def learning_mode(self) -> LearningNotificationMode:
        """Select two-step reveal only when both replacement gates are proven."""
        if (
            self.tag_replace is Capability.SUPPORTED
            and self.silent_replace is Capability.SUPPORTED
            and self.visible_action_count >= 2
        ):
            return LearningNotificationMode.TWO_STEP_REVEAL
        return LearningNotificationMode.EXPOSURE_ONLY

    def as_dict(self) -> dict[str, Any]:
        """Serialize the evidence without guessing unknown features."""
        return asdict(self)
