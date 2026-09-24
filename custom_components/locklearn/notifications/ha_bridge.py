"""Home Assistant event bridge for Companion notification actions."""

from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from homeassistant.core import Event, HomeAssistant

from ..core.scheduler import SchedulerService, SchedulerValidationError
from .actions import NotificationActionError, NotificationActionProcessor
from .interactions import NotificationInteractionService

_LOGGER = logging.getLogger(__name__)


class NotificationHomeAssistantBridge:
    """Observe Companion events and delegate all authority to persistent state."""

    def __init__(
        self,
        hass: HomeAssistant,
        interactions: NotificationInteractionService,
        actions: NotificationActionProcessor,
        scheduler: SchedulerService,
    ) -> None:
        self._hass = hass
        self._interactions = interactions
        self._actions = actions
        self._scheduler = scheduler
        self._unsubs: list[Any] = []

    async def async_start(self) -> None:
        """Subscribe once to Companion action and clear events."""
        if self._unsubs:
            return
        self._unsubs = [
            self._hass.bus.async_listen(
                "mobile_app_notification_action",
                self._handle_action,
            ),
            self._hass.bus.async_listen(
                "mobile_app_notification_cleared",
                self._handle_cleared,
            ),
        ]

    async def _handle_action(self, event: Event[Any]) -> None:
        action_id = event.data.get("action")
        if not isinstance(action_id, str):
            return
        try:
            await self._actions.async_handle_mobile_action(
                action_id=action_id,
                actor_user_id=event.context.user_id,
            )
        except NotificationActionError as err:
            _LOGGER.warning("Ignored invalid LockLearn notification action: %s", err)
        except Exception:
            _LOGGER.exception("LockLearn notification action processing failed")

    async def _handle_cleared(self, event: Event[Any]) -> None:
        tag = event.data.get("tag")
        if not isinstance(tag, str) or not tag:
            return
        try:
            interaction = await self._interactions.async_clear_tag(tag=tag)
            if interaction is None:
                return
            payload = dict(interaction.get("payload") or {})
            slot_id = payload.get("slot_id")
            if isinstance(slot_id, str) and slot_id:
                with suppress(SchedulerValidationError):
                    await self._scheduler.async_record_receptivity_action(
                        slot_id=slot_id,
                        action="cleared",
                    )
            interaction_id = str(interaction["interaction_id"])
            self._hass.bus.async_fire(
                "locklearn_notification_cleared",
                {
                    "event_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"locklearn:notification-cleared:{interaction_id}",
                        )
                    ),
                    "interaction_id": interaction_id,
                    "profile_id": str(interaction["profile_id"]),
                    "track_id": interaction.get("track_id"),
                    "card_key": interaction.get("card_key"),
                    "target_id": str(interaction["target_id"]),
                },
            )
        except Exception:
            _LOGGER.exception("LockLearn notification clear processing failed")

    def close(self) -> None:
        """Detach all Home Assistant event listeners."""
        while self._unsubs:
            self._unsubs.pop()()
