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
    """Technical rendering modes for passive learning."""

    TWO_STEP_REVEAL = "two_step_reveal"
    DIRECT_EXPOSURE = "direct_exposure"


class LearningSignal(StrEnum):
    """Pedagogical result derived from what the learner actually experienced."""

    NO_RESULT = "no_result"
    EXPOSURE_ONLY = "exposure_only"
    SELF_ASSESSMENT_AFTER_RETRIEVAL = "self_assessment_after_retrieval"


def classify_learning_signal(
    *, answer_exposed_before_retrieval: bool, retrieval_was_usable: bool
) -> LearningSignal:
    """Classify actual presentation/retrieval facts, never device capabilities."""
    if answer_exposed_before_retrieval:
        return LearningSignal.EXPOSURE_ONLY
    if retrieval_was_usable:
        return LearningSignal.SELF_ASSESSMENT_AFTER_RETRIEVAL
    return LearningSignal.NO_RESULT


@dataclass(frozen=True, slots=True)
class TargetCapabilities:
    """Capabilities measured for one stable device-registry target."""

    device_registry_id: str
    platform: str
    replace_by_tag: Capability = Capability.UNKNOWN
    silent_replace: Capability = Capability.UNKNOWN
    action_data: Capability = Capability.UNKNOWN
    text_input: Capability = Capability.UNKNOWN
    clear_event: Capability = Capability.UNKNOWN
    device_attribution: Capability = Capability.UNKNOWN
    lockscreen_privacy: Capability = Capability.UNKNOWN
    visible_actions: int = 0
    expiration: Capability = Capability.UNKNOWN
    channel_importance: Capability = Capability.UNKNOWN
    media: Capability = Capability.UNKNOWN
    shared_device: bool = False
    tested_app_version: str | None = None
    tested_at_utc: str | None = None

    @classmethod
    def from_mapping(
        cls,
        *,
        device_registry_id: str,
        platform: str,
        shared_device: bool,
        values: dict[str, Any] | None,
    ) -> TargetCapabilities:
        """Parse persisted tri-state capability JSON without optimistic defaults."""
        raw = dict(values or {})

        def capability(name: str) -> Capability:
            value = raw.get(name, Capability.UNKNOWN.value)
            try:
                return Capability(str(value))
            except ValueError:
                return Capability.UNKNOWN

        visible_actions_raw = raw.get("visible_actions", 0)
        visible_actions = (
            int(visible_actions_raw)
            if isinstance(visible_actions_raw, (int, float, str))
            and str(visible_actions_raw).isdigit()
            else 0
        )
        return cls(
            device_registry_id=device_registry_id,
            platform=platform,
            replace_by_tag=capability("replace_by_tag"),
            silent_replace=capability("silent_replace"),
            action_data=capability("action_data"),
            text_input=capability("text_input"),
            clear_event=capability("clear_event"),
            device_attribution=capability("device_attribution"),
            lockscreen_privacy=capability("lockscreen_privacy"),
            visible_actions=max(0, visible_actions),
            expiration=capability("expiration"),
            channel_importance=capability("channel_importance"),
            media=capability("media"),
            shared_device=shared_device,
            tested_app_version=(
                str(raw["tested_app_version"])
                if raw.get("tested_app_version") is not None
                else None
            ),
            tested_at_utc=(str(raw["tested_at_utc"]) if raw.get("tested_at_utc") is not None else None),
        )

    def learning_mode(self) -> LearningNotificationMode:
        """Select a prompt-first flow when actionable delivery is proven.

        Replacement, sound, attribution and privacy capabilities affect UX,
        routing and security choices. They do not retroactively determine
        whether a learner had a usable retrieval attempt.
        """
        if self.action_data is Capability.SUPPORTED and self.visible_actions >= 2:
            return LearningNotificationMode.TWO_STEP_REVEAL
        return LearningNotificationMode.DIRECT_EXPOSURE

    def as_dict(self) -> dict[str, Any]:
        """Serialize the evidence without guessing unknown features."""
        return asdict(self)
