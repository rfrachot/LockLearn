"""Deliver the second stage of a Companion learning notification."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, TypedDict

from ..core.clock import Clock, SystemClock
from ..core.presentation import CardPresentationService
from ..storage.repositories import NotificationTargetsRepository, ProfilesRepository
from .capabilities import TargetCapabilities
from .delivery import NotificationDeliveryService
from .interactions import NotificationInteractionService, NotificationStage
from .renderers import NotificationRenderer

_TTL = timedelta(minutes=30)


class _LearningRevealArgs(TypedDict):
    profile_id: str
    profile_name: str
    target_id: str
    tag: str
    answer: str
    capabilities: TargetCapabilities
    visibility: str
    slot_type: str


class NotificationRevealService:
    """Replace the prompt, preserving privacy and per-stage replay protection."""

    def __init__(
        self,
        profiles: ProfilesRepository,
        targets: NotificationTargetsRepository,
        presentation: CardPresentationService,
        interactions: NotificationInteractionService,
        delivery: NotificationDeliveryService,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._profiles = profiles
        self._targets = targets
        self._presentation = presentation
        self._interactions = interactions
        self._delivery = delivery
        self._clock = clock or SystemClock()
        self._renderer = NotificationRenderer()

    async def async_reveal(self, interaction: dict[str, Any], *, assessable: bool) -> None:
        """Send the answer; only a retrieval attempt receives self-assessment."""
        if interaction.get("stage") != NotificationStage.PROMPT.value:
            raise ValueError("only prompt-stage interactions can be revealed")
        profile_id = str(interaction["profile_id"])
        target_id = str(interaction["target_id"])
        track_id = interaction.get("track_id")
        card_key = interaction.get("card_key")
        tag = interaction.get("tag")
        if not all(isinstance(value, str) and value for value in (track_id, card_key, tag)):
            raise ValueError("missing revealed-notification identity")
        profile = await self._profiles.async_get(profile_id)
        target = await self._targets.async_get(target_id)
        if (
            profile is None
            or target is None
            or str(target["profile_id"]) != profile_id
            or not bool(target.get("enabled"))
        ):
            raise ValueError("revealed-notification target unavailable")
        capabilities = TargetCapabilities.from_mapping(
            device_registry_id=str(target["device_registry_id"]),
            platform=str(target["platform"]),
            shared_device=bool(target.get("shared_device")),
            values=dict(target.get("capabilities") or {}),
        )
        presentation = await self._presentation.async_for_card(
            track_id=str(track_id), card_key=str(card_key)
        )
        answer = "LockLearn"
        facet = presentation.get("answer")
        if isinstance(facet, dict):
            for block in facet.get("blocks", ()):
                if not isinstance(block, dict):
                    continue
                payload = block.get("payload")
                value = payload.get("text") if isinstance(payload, dict) else None
                if isinstance(value, str) and value.strip():
                    answer = value.strip()
                    break
        selection_reason = (interaction.get("payload") or {}).get("selection_reason")
        common: _LearningRevealArgs = {
            "profile_id": profile_id,
            "profile_name": str(profile.get("name") or "LockLearn"),
            "target_id": target_id,
            "tag": str(tag),
            "answer": answer,
            "capabilities": capabilities,
            "visibility": str(target.get("lockscreen_visibility") or "private"),
            "slot_type": "relearning" if selection_reason == "relearning_due" else "learning",
        }
        if not assessable:
            rendered = self._renderer.render_learning_exposure(**common)
            await self._delivery.async_send(rendered)
            return

        next_stage = await self._interactions.async_create(
            profile_id=profile_id,
            target_id=target_id,
            track_id=str(track_id),
            card_key=str(card_key),
            tag=str(tag),
            stage=NotificationStage.REVEALED,
            expires_at=self._clock.now() + _TTL,
            payload=dict(interaction.get("payload") or {}),
        )
        rendered = self._renderer.render_learning_revealed(**common, token=next_stage.token)
        try:
            await self._delivery.async_send(rendered)
        except Exception:
            await self._interactions.async_clear_tag(tag=str(tag))
            raise
