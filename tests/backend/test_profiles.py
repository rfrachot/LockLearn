"""P2.2 profile presets, ownership mapping, and child/shared profiles."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.locklearn.core.profiles import (
    ProfilePreset,
    ProfileService,
    ProfileValidationError,
    profile_preset_defaults,
)
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 22, 19, 15, tzinfo=UTC)


async def _service(tmp_path: Path, ids: list[str]) -> tuple[SQLiteStorage, ProfileService]:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()

    def next_id() -> str:
        return ids.pop(0)

    return storage, ProfileService(
        storage.repositories.profiles,
        clock=_FixedClock(),
        id_factory=next_id,
    )


async def test_personal_profile_maps_to_ha_user_without_using_ha_id_as_profile_id(
    tmp_path: Path,
) -> None:
    storage, service = await _service(tmp_path, ["profile-personal"])
    try:
        profile = await service.async_ensure_personal_profile(
            ha_user_id="ha-user-1",
            name="Renaud",
            timezone="Europe/Paris",
        )

        assert profile["profile_id"] == "profile-personal"
        assert profile["profile_id"] != "ha-user-1"
        assert profile["preset"] == "standard"
        assert profile["settings"]["max_new_per_day_cards"] == 8
        assert profile["settings"]["daily_push_budget"] == 6

        assert await storage.repositories.profiles.async_list_members(
            "profile-personal"
        ) == (
            {
                "ha_user_id": "ha-user-1",
                "role": "owner",
                "created_at_utc": "2026-09-22T19:15:00+00:00",
            },
        )

        second = await service.async_ensure_personal_profile(
            ha_user_id="ha-user-1",
            name="Renamed HA user",
            timezone="Europe/Paris",
        )
        assert second["profile_id"] == "profile-personal"
    finally:
        await storage.async_close()


async def test_child_profile_needs_no_dedicated_ha_account_and_supports_multiple_owners(
    tmp_path: Path,
) -> None:
    storage, service = await _service(tmp_path, ["profile-child"])
    try:
        profile = await service.async_create_profile(
            name="Lou",
            preset=ProfilePreset.CHILD,
            timezone="Europe/Paris",
            owner_ha_user_ids=("parent-1", "parent-2"),
        )

        assert profile["profile_id"] == "profile-child"
        assert profile["preset"] == "child"
        assert profile["settings"]["session_length_cards"] == 10
        assert profile["settings"]["max_new_per_day_cards"] == 3
        assert profile["settings"]["daily_push_budget"] == 3

        members = await storage.repositories.profiles.async_list_members("profile-child")
        assert {(member["ha_user_id"], member["role"]) for member in members} == {
            ("parent-1", "owner"),
            ("parent-2", "owner"),
        }
        assert await storage.repositories.profiles.async_list_for_ha_user(
            "child-without-ha-account"
        ) == ()
    finally:
        await storage.async_close()


async def test_preset_values_are_initial_defaults_not_restrictions(tmp_path: Path) -> None:
    storage, service = await _service(tmp_path, ["profile-customized"])
    try:
        profile = await service.async_create_profile(
            name="Customized",
            preset="child",
            timezone="Europe/Paris",
            owner_ha_user_ids=("owner",),
            settings_override={
                "session_length_cards": 25,
                "max_new_per_day_cards": 12,
                "daily_push_budget": 7,
            },
        )

        assert profile["preset"] == "child"
        assert profile["settings"]["session_length_cards"] == 25
        assert profile["settings"]["max_new_per_day_cards"] == 12
        assert profile["settings"]["daily_push_budget"] == 7

        defaults = profile_preset_defaults("child")
        assert defaults["session_length_cards"] == 10
        assert defaults["max_new_per_day_cards"] == 3
    finally:
        await storage.async_close()


async def test_profile_creation_rejects_invalid_identity_inputs(tmp_path: Path) -> None:
    storage, service = await _service(tmp_path, ["unused"])
    try:
        with pytest.raises(ProfileValidationError, match="profile name"):
            await service.async_create_profile(
                name=" ",
                preset="standard",
                timezone="Europe/Paris",
                owner_ha_user_ids=("owner",),
            )

        with pytest.raises(ProfileValidationError, match="invalid timezone"):
            await service.async_create_profile(
                name="Learner",
                preset="standard",
                timezone="Mars/Olympus_Mons",
                owner_ha_user_ids=("owner",),
            )

        with pytest.raises(ProfileValidationError, match="at least one owner"):
            await service.async_create_profile(
                name="Learner",
                preset="standard",
                timezone="Europe/Paris",
                owner_ha_user_ids=(),
            )

        with pytest.raises(ProfileValidationError, match="unsupported profile preset"):
            await service.async_create_profile(
                name="Learner",
                preset="turbo",
                timezone="Europe/Paris",
                owner_ha_user_ids=("owner",),
            )
    finally:
        await storage.async_close()
