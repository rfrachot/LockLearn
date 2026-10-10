"""Complete the prompt -> revealed Companion notification transition.

The second-stage token is persisted before sending the replacement; no raw
learning content or bearer token is emitted in Home Assistant events.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from ..core.clock import Clock, SystemClock
from ..core.presentation import CardPresentationService
from ..storage.repositories import NotificationTargetsRepository, ProfilesRepository
from .capabilities import TargetCapabilities
from .delivery import NotificationDeliveryService
from .interactions import NotificationInteractionService, NotificationStage
from .renderers import NotificationRenderer

_REVEALED_TTL = timedelta(minutes=30)


class NotificationRevealService:
    """Send same-tag answer feedback, optionally with a fresh assessment token."""

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

    @staticmethod
    def _answer_text(presentation: dict[str, Any]) -> str:
        facet = presentation.get("answer")
        if isinstance(facet, dict):
            for block in facet.get("blocks", ()):
                if not isinstance(block, dict):
                    continue
                payload = block.get("payload")
                text = payload.get("text") if isinstance(payload, dict) else None
                if isinstance(text, str) and text.strip():
                    return text.strip()
        return "LockLearn"

    async def async_show_answer(
        self,
        interaction: dict[str, Any],
        *,
        allow_self_assessment: bool,
    ) -> None:
        """Replace the original prompt without generating an unearned result."""
        if interaction.get("stage") != NotificationStage.PROMPT.value:
            raise ValueError("only prompt notifications may reveal their answer")
        profile_id = str(interaction["profile_id"])
        target_id = str(interaction["target_id"])
        track_id = interaction.get("track_id")
        card_key = interaction.get("card_key")
        tag = interaction.get("tag")
        if not all(isinstance(value, str) and value for value in (track_id, card_key, tag)):
            raise ValueError("prompt interaction is missing a card or replacement tag")

        profile = await self._profiles.async_get(profile_id)
        target = await self._targets.async_get(target_id)
        if (
            profile is None
            or target is None
            or str(target["profile_id"]) != profile_id
            or not bool(target.get("enabled"))
        ):
            raise ValueError("notification profile or target is unavailable")

        capabilities = TargetCapabilities.from_mapping(
            device_registry_id=str(target["device_registry_id"]),
            platform=str(target["platform"]),
            shared_device=bool(target.get("shared_device")),
            values=dict(target.get("capabilities") or {}),
        )
        card = await self._presentation.async_for_card(
            track_id=str(track_id),
            card_key=str(card_key),
        )
        answer = self._answer_text(card)
        payload = dict(interaction.get("payload") or {})
        slot_type = (
            "relearning" if payload.get("selection_reason") == "relearning_due" else "learning"
        )
        common = {
            "profile_id": profile_id,
            "profile_name": str(profile.get("name") or "LockLearn"),
            "target_id": target_id,
            "tag": str(tag),
            "answer": answer,
            "capabilities": capabilities,
            "visibility": str(target.get("lockscreen_visibility") or "private"),
            "slot_type": slot_type,
        }
        if allow_self_assessment:
            revealed = await self._interactions.async_create(
                profile_id=profile_id,
                target_id=target_id,
                track_id=str(track_id),
                card_key=str(card_key),
                tag=str(tag),
                stage=NotificationStage.REVEALED,
                expires_at=self._clock.now() + _REVEALED_TTL,
                payload=payload,
            )
            rendered = self._renderer.render_learning_revealed(
                **common,
                token=revealed.token,
            )
        else:
            rendered = self._renderer.render_learning_exposure(**common)

        try:
            await self._delivery.async_send(rendered)
        except Exception:
            if allow_self_assessment:
                await self._interactions.async_clear_tag(tag=str(tag))
            raise
