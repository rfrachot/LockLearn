"""Home Assistant adapters for LockLearn scheduler receptivity and routine hooks."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from .core.scheduler import SchedulerService, SchedulerValidationError
from .storage.repositories import ProfilesRepository

_LOGGER = logging.getLogger(__name__)
_ROUTINE_TYPES = frozenset({"pre_sleep_consolidation", "morning_first_review"})


class SchedulerHomeAssistantBridge:
    """Bind opt-in HA entity state changes to scheduler routine hooks."""

    def __init__(
        self,
        hass: HomeAssistant,
        profiles: ProfilesRepository,
        scheduler: SchedulerService,
    ) -> None:
        self._hass = hass
        self._profiles = profiles
        self._scheduler = scheduler
        self._unsub: Any | None = None
        self._routes: dict[str, tuple[tuple[str, str], ...]] = {}

    async def async_start(self) -> None:
        """Start entity listeners from active Profile configuration."""
        await self.async_refresh()

    async def async_refresh(self) -> None:
        """Rebuild entity listeners after Profile scheduler settings change."""
        self.close()
        routes: dict[str, list[tuple[str, str]]] = {}
        for profile in await self._profiles.async_list_active():
            settings = profile.get("settings")
            if not isinstance(settings, Mapping):
                continue
            scheduler_settings = settings.get("scheduler")
            if not isinstance(scheduler_settings, Mapping):
                continue
            raw_triggers = scheduler_settings.get("routine_triggers")
            if not isinstance(raw_triggers, Mapping):
                continue
            profile_id = str(profile["profile_id"])
            for routine_type, raw_entities in raw_triggers.items():
                if routine_type not in _ROUTINE_TYPES:
                    continue
                if isinstance(raw_entities, str):
                    entities = (raw_entities,)
                elif isinstance(raw_entities, (list, tuple)):
                    entities = tuple(
                        entity_id
                        for entity_id in raw_entities
                        if isinstance(entity_id, str) and entity_id.strip()
                    )
                else:
                    continue
                for entity_id in entities:
                    normalized = entity_id.strip().lower()
                    routes.setdefault(normalized, []).append((profile_id, str(routine_type)))

        self._routes = {
            entity_id: tuple(sorted(items))
            for entity_id, items in routes.items()
        }
        if not self._routes:
            return
        self._unsub = async_track_state_change_event(
            self._hass,
            tuple(self._routes),
            self._handle_state_change,
        )

    def _handle_state_change(self, event: Event[Any]) -> None:
        entity_id = str(event.data.get("entity_id", "")).lower()
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if new_state is None or str(new_state.state).lower() != "on":
            return
        if old_state is not None and str(old_state.state).lower() == "on":
            return
        for profile_id, routine_type in self._routes.get(entity_id, ()):
            self._hass.async_create_task(
                self._async_trigger(profile_id, routine_type),
                f"locklearn routine {routine_type} for {profile_id}",
            )

    async def _async_trigger(self, profile_id: str, routine_type: str) -> None:
        try:
            await self._scheduler.async_trigger_routine(
                profile_id=profile_id,
                routine_type=routine_type,
            )
        except SchedulerValidationError as err:
            _LOGGER.debug(
                "Routine trigger %s for Profile %s was ignored: %s",
                routine_type,
                profile_id,
                err,
            )
        except Exception:
            _LOGGER.exception(
                "Routine trigger %s for Profile %s failed",
                routine_type,
                profile_id,
            )

    def close(self) -> None:
        """Detach every HA state-change listener."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._routes = {}
