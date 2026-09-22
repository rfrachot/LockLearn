"""Profile domain service, presets, and Home Assistant user mapping."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from enum import StrEnum
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..storage.repositories import ProfileMemberRecord, ProfileRecord, ProfilesRepository
from .clock import Clock, SystemClock


class ProfilePreset(StrEnum):
    """Supported onboarding presets."""

    CHILD = "child"
    STANDARD = "standard"
    INTENSIVE = "intensive"
    CUSTOM = "custom"


class ProfileValidationError(ValueError):
    """Raised when profile creation input is invalid."""


_PRESET_DEFAULTS: dict[ProfilePreset, dict[str, Any]] = {
    ProfilePreset.CHILD: {
        "session_length_cards": 10,
        "max_new_per_day_cards": 3,
        "daily_push_budget": 3,
        "quiet_hours": {"start": "20:00", "end": "08:00"},
    },
    ProfilePreset.STANDARD: {
        "session_length_cards": 20,
        "max_new_per_day_cards": 8,
        "daily_push_budget": 6,
        "quiet_hours": {"start": "22:00", "end": "08:00"},
    },
    ProfilePreset.INTENSIVE: {
        "session_length_cards": 30,
        "max_new_per_day_cards": 15,
        "daily_push_budget": 8,
        "quiet_hours": {"start": "23:00", "end": "07:00"},
    },
    ProfilePreset.CUSTOM: {},
}

_PERSONAL_PROFILE_MARKER = "_locklearn_personal_profile"
_PRESET_DEFAULTS_VERSION = "_locklearn_preset_defaults_version"


def profile_preset_defaults(preset: ProfilePreset | str) -> dict[str, Any]:
    """Return a detached copy of the initial settings for a preset."""
    try:
        resolved = ProfilePreset(preset)
    except ValueError as err:
        raise ProfileValidationError(f"unsupported profile preset: {preset}") from err
    defaults = deepcopy(_PRESET_DEFAULTS[resolved])
    defaults[_PRESET_DEFAULTS_VERSION] = 1
    return defaults


class ProfileService:
    """Create learner profiles without conflating them with HA accounts."""

    def __init__(
        self,
        repository: ProfilesRepository,
        *,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._personal_profile_lock = asyncio.Lock()

    async def async_create_profile(
        self,
        *,
        name: str,
        preset: ProfilePreset | str,
        timezone: str,
        owner_ha_user_ids: Iterable[str],
        settings_override: Mapping[str, Any] | None = None,
        personal_profile: bool = False,
    ) -> dict[str, Any]:
        """Create a profile and its initial owners atomically."""
        normalized_name = name.strip()
        if not normalized_name:
            raise ProfileValidationError("profile name must not be empty")

        normalized_timezone = timezone.strip()
        try:
            ZoneInfo(normalized_timezone)
        except (ValueError, ZoneInfoNotFoundError) as err:
            raise ProfileValidationError(f"invalid timezone: {timezone}") from err

        owners = tuple(
            dict.fromkeys(
                user_id.strip() for user_id in owner_ha_user_ids if user_id.strip()
            )
        )
        if not owners:
            raise ProfileValidationError("a profile must start with at least one owner")
        if personal_profile and len(owners) != 1:
            raise ProfileValidationError("a personal profile must have exactly one initial owner")

        try:
            resolved_preset = ProfilePreset(preset)
        except ValueError as err:
            raise ProfileValidationError(f"unsupported profile preset: {preset}") from err

        settings = profile_preset_defaults(resolved_preset)
        if settings_override:
            if any(key.startswith("_locklearn_") for key in settings_override):
                raise ProfileValidationError("settings_override contains a reserved key")
            settings.update(dict(settings_override))
        if personal_profile:
            settings[_PERSONAL_PROFILE_MARKER] = True

        now = self._clock.now().isoformat()
        profile = ProfileRecord(
            profile_id=self._id_factory(),
            name=normalized_name,
            preset=resolved_preset.value,
            timezone=normalized_timezone,
            settings=settings,
            created_at_utc=now,
            updated_at_utc=now,
        )
        members = tuple(
            ProfileMemberRecord(
                profile_id=profile.profile_id,
                ha_user_id=user_id,
                role="owner",
                created_at_utc=now,
            )
            for user_id in owners
        )
        await self._repository.async_insert_with_members(profile, members)
        created = await self._repository.async_get(profile.profile_id)
        if created is None:
            raise RuntimeError("created profile could not be reloaded")
        return created

    async def async_ensure_personal_profile(
        self,
        *,
        ha_user_id: str,
        name: str,
        timezone: str,
        preset: ProfilePreset | str = ProfilePreset.STANDARD,
    ) -> dict[str, Any]:
        """Return or create the onboarding personal profile for one HA user."""
        normalized_user_id = ha_user_id.strip()
        if not normalized_user_id:
            raise ProfileValidationError("ha_user_id must not be empty")

        async with self._personal_profile_lock:
            existing = await self._repository.async_list_for_ha_user(normalized_user_id)
            for profile in existing:
                if (
                    profile["role"] == "owner"
                    and profile["settings"].get(_PERSONAL_PROFILE_MARKER) is True
                ):
                    return profile

            return await self.async_create_profile(
                name=name,
                preset=preset,
                timezone=timezone,
                owner_ha_user_ids=(normalized_user_id,),
                personal_profile=True,
            )
