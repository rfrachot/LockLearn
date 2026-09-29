"""Capability-aware, privacy-minimal Companion notification renderers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .capabilities import Capability, LearningNotificationMode, TargetCapabilities

ACTION_PREFIX = "LOCKLEARN"
PANEL_URI = "/locklearn"

CHANNEL_LEARNING = "LockLearn Learning"
CHANNEL_QUIZ = "LockLearn Quiz"
CHANNEL_RELEARNING = "LockLearn Relearning"


class NotificationRenderMode(StrEnum):
    """Renderer path selected from measured target capabilities."""

    TWO_STEP_REVEAL = "two_step_reveal"
    DIRECT_EXPOSURE = "direct_exposure"
    QUIZ_ACTIONS = "quiz_actions"
    PANEL_HANDOFF = "panel_handoff"


@dataclass(frozen=True, slots=True)
class QuizOption:
    """One opaque quiz option; text is rendered, identity stays protocol data."""

    option_id: str
    title: str


@dataclass(frozen=True, slots=True)
class RenderedNotification:
    """Companion-ready payload plus pedagogical/rendering metadata."""

    profile_id: str
    target_id: str
    tag: str
    stage: str
    mode: NotificationRenderMode
    title: str
    message: str
    data: dict[str, Any]
    pedagogical_signal: str
    panel_required: bool = False
    action_semantics: dict[str, str] | None = None

    def service_data(self) -> dict[str, Any]:
        """Return the payload accepted by a data-capable mobile_app notify action."""
        return {
            "title": self.title,
            "message": self.message,
            "data": dict(self.data),
        }


def encode_action_id(token: str, semantic: str) -> str:
    """Encode one content-free action identifier carrying the P4.6 token."""
    if not token or "|" in token:
        raise ValueError("invalid interaction token")
    if not semantic or "|" in semantic:
        raise ValueError("invalid action semantic")
    return f"{ACTION_PREFIX}|{token}|{semantic}"


def decode_action_id(action_id: str) -> tuple[str, str] | None:
    """Decode a LockLearn mobile action without treating it as authentication."""
    parts = action_id.split("|", 2)
    if len(parts) != 3 or parts[0] != ACTION_PREFIX or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def effective_lockscreen_visibility(
    requested: str | None,
    *,
    profile_preset: str,
    shared_device: bool,
) -> str:
    """Resolve conservative V1 defaults without treating OS visibility as security."""
    if requested is not None and requested not in {"public", "private", "secret"}:
        raise ValueError("invalid lockscreen visibility")
    if requested is not None:
        return requested
    if shared_device or profile_preset == "child":
        return "private"
    return "private"


class NotificationRenderer:
    """Build conservative Companion payloads from per-target capability evidence."""

    @staticmethod
    def _title(base: str, *, profile_name: str, shared_device: bool) -> str:
        return f"{base} · {profile_name}" if shared_device else base

    @staticmethod
    def _channel(slot_type: str) -> str:
        if slot_type == "relearning":
            return CHANNEL_RELEARNING
        if slot_type == "quiz":
            return CHANNEL_QUIZ
        return CHANNEL_LEARNING

    @classmethod
    def _base_data(
        cls,
        *,
        tag: str,
        slot_type: str,
        visibility: str,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        if visibility not in {"public", "private", "secret"}:
            raise ValueError("invalid lockscreen visibility")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        return {
            "tag": tag,
            "ttl": ttl_seconds,
            "channel": cls._channel(slot_type),
            "visibility": visibility,
        }

    def render_learning_prompt(
        self,
        *,
        profile_id: str,
        profile_name: str,
        target_id: str,
        tag: str,
        prompt: str,
        answer: str,
        token: str,
        capabilities: TargetCapabilities,
        visibility: str = "private",
        slot_type: str = "learning",
        ttl_seconds: int = 1800,
    ) -> RenderedNotification:
        """Render prompt-first learning or conservative direct-exposure fallback."""
        data = self._base_data(
            tag=tag,
            slot_type=slot_type,
            visibility=visibility,
            ttl_seconds=ttl_seconds,
        )
        title = self._title(
            "LockLearn",
            profile_name=profile_name,
            shared_device=capabilities.shared_device,
        )
        if capabilities.learning_mode() is LearningNotificationMode.TWO_STEP_REVEAL:
            reveal = encode_action_id(token, "reveal")
            unknown = encode_action_id(token, "idk")
            data["actions"] = [
                {"action": reveal, "title": "Reveal"},
                {"action": unknown, "title": "I don't know"},
            ]
            return RenderedNotification(
                profile_id=profile_id,
                target_id=target_id,
                tag=tag,
                stage="prompt",
                mode=NotificationRenderMode.TWO_STEP_REVEAL,
                title=title,
                message=prompt,
                data=data,
                pedagogical_signal="retrieval_pending",
                action_semantics={reveal: "reveal", unknown: "idk"},
            )

        return RenderedNotification(
            profile_id=profile_id,
            target_id=target_id,
            tag=tag,
            stage="revealed",
            mode=NotificationRenderMode.DIRECT_EXPOSURE,
            title=title,
            message=f"{prompt}\n\n{answer}",
            data=data,
            pedagogical_signal="exposure_only",
        )

    def render_learning_revealed(
        self,
        *,
        profile_id: str,
        profile_name: str,
        target_id: str,
        tag: str,
        answer: str,
        token: str,
        capabilities: TargetCapabilities,
        visibility: str = "private",
        slot_type: str = "learning",
        explanation: str | None = None,
        ttl_seconds: int = 1800,
    ) -> RenderedNotification:
        """Render post-retrieval answer using the same tag and silent preference."""
        data = self._base_data(
            tag=tag,
            slot_type=slot_type,
            visibility=visibility,
            ttl_seconds=ttl_seconds,
        )
        data["alert_once"] = True
        known = encode_action_id(token, "known")
        review = encode_action_id(token, "review")
        data["actions"] = [
            {"action": known, "title": "I knew it"},
            {"action": review, "title": "Review again"},
        ]
        message = answer if not explanation else f"{answer}\n\n{explanation}"
        return RenderedNotification(
            profile_id=profile_id,
            target_id=target_id,
            tag=tag,
            stage="revealed",
            mode=NotificationRenderMode.TWO_STEP_REVEAL,
            title=self._title(
                "LockLearn",
                profile_name=profile_name,
                shared_device=capabilities.shared_device,
            ),
            message=message,
            data=data,
            pedagogical_signal="self_assessment_after_retrieval",
            action_semantics={known: "known", review: "review"},
        )

    def render_quiz_prompt(
        self,
        *,
        profile_id: str,
        profile_name: str,
        target_id: str,
        tag: str,
        prompt: str,
        token: str,
        options: tuple[QuizOption, ...],
        capabilities: TargetCapabilities,
        visibility: str = "private",
        ttl_seconds: int = 1800,
    ) -> RenderedNotification:
        """Render a binary mobile quiz or direct a larger/unsafe MCQ to the panel."""
        data = self._base_data(
            tag=tag,
            slot_type="quiz",
            visibility=visibility,
            ttl_seconds=ttl_seconds,
        )
        title = self._title(
            "LockLearn Quiz",
            profile_name=profile_name,
            shared_device=capabilities.shared_device,
        )
        mobile_quiz = (
            len(options) == 2
            and capabilities.action_data is Capability.SUPPORTED
            and capabilities.visible_actions >= 3
        )
        if not mobile_quiz:
            data["actions"] = [
                {
                    "action": "URI",
                    "title": "Open LockLearn",
                    "uri": PANEL_URI,
                }
            ]
            return RenderedNotification(
                profile_id=profile_id,
                target_id=target_id,
                tag=tag,
                stage="prompt",
                mode=NotificationRenderMode.PANEL_HANDOFF,
                title=title,
                message=prompt,
                data=data,
                pedagogical_signal="no_result",
                panel_required=True,
            )

        actions: list[dict[str, str]] = []
        semantics: dict[str, str] = {}
        for index, option in enumerate(options):
            action_id = encode_action_id(token, f"choice_{index}")
            actions.append({"action": action_id, "title": option.title})
            semantics[action_id] = f"choice:{option.option_id}"
        unknown = encode_action_id(token, "idk")
        actions.append({"action": unknown, "title": "I don't know"})
        semantics[unknown] = "idk"
        data["actions"] = actions
        return RenderedNotification(
            profile_id=profile_id,
            target_id=target_id,
            tag=tag,
            stage="prompt",
            mode=NotificationRenderMode.QUIZ_ACTIONS,
            title=title,
            message=prompt,
            data=data,
            pedagogical_signal="verified_mcq_pending",
            action_semantics=semantics,
        )
