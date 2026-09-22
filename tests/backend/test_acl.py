"""P2.3 backend ACL and privacy filtering tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.locklearn.core.acl import (
    LastOwnerError,
    ProfileACLService,
    ProfileAccessDenied,
    ProfilePermission,
    ProfileRole,
)
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 22, 20, 0, tzinfo=UTC)


async def _services(
    tmp_path: Path,
) -> tuple[SQLiteStorage, ProfileService, ProfileACLService]:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    ids = iter(("profile-private", "profile-second"))
    profiles = ProfileService(
        storage.repositories.profiles,
        clock=_FixedClock(),
        id_factory=lambda: next(ids),
    )
    acl = ProfileACLService(storage.repositories.profiles, clock=_FixedClock())
    return storage, profiles, acl


async def test_permission_matrix_matches_v1_roles(tmp_path: Path) -> None:
    storage, profiles, acl = await _services(tmp_path)
    try:
        profile = await profiles.async_create_profile(
            name="Private",
            preset="standard",
            timezone="Europe/Paris",
            owner_ha_user_ids=("owner",),
        )
        profile_id = str(profile["profile_id"])
        await acl.async_set_member_role(
            actor_ha_user_id="owner",
            profile_id=profile_id,
            target_ha_user_id="editor",
            role=ProfileRole.EDITOR,
        )
        await acl.async_set_member_role(
            actor_ha_user_id="owner",
            profile_id=profile_id,
            target_ha_user_id="viewer",
            role=ProfileRole.VIEWER,
        )

        expected = {
            "owner": {
                ProfilePermission.READ,
                ProfilePermission.EDIT_TRACK,
                ProfilePermission.ANSWER,
                ProfilePermission.SHARE,
                ProfilePermission.DELETE,
                ProfilePermission.MANAGE_ACL,
                ProfilePermission.MANAGE_PROGRESS,
            },
            "editor": {
                ProfilePermission.READ,
                ProfilePermission.EDIT_TRACK,
                ProfilePermission.ANSWER,
                ProfilePermission.MANAGE_PROGRESS,
            },
            "viewer": {ProfilePermission.READ},
            "outsider": set(),
        }
        for user_id, allowed in expected.items():
            for permission in ProfilePermission:
                assert (
                    await acl.async_can(
                        profile_id=profile_id,
                        ha_user_id=user_id,
                        permission=permission,
                    )
                    is (permission in allowed)
                )
    finally:
        await storage.async_close()


async def test_private_profile_listing_and_direct_visibility_do_not_leak_to_outsider(
    tmp_path: Path,
) -> None:
    storage, profiles, acl = await _services(tmp_path)
    try:
        profile = await profiles.async_create_profile(
            name="Tiffanie private",
            preset="standard",
            timezone="Europe/Paris",
            owner_ha_user_ids=("tiffanie",),
        )
        profile_id = str(profile["profile_id"])

        assert await acl.async_list_visible_profiles("outsider") == ()
        assert (
            await acl.async_get_visible_profile(
                profile_id=profile_id,
                ha_user_id="outsider",
            )
            is None
        )
        assert (
            await acl.async_get_visible_profile(
                profile_id="profile-does-not-exist",
                ha_user_id="outsider",
            )
            is None
        )
    finally:
        await storage.async_close()


async def test_ha_admin_identity_does_not_bypass_profile_membership(tmp_path: Path) -> None:
    storage, profiles, acl = await _services(tmp_path)
    try:
        profile = await profiles.async_create_profile(
            name="Private",
            preset="standard",
            timezone="Europe/Paris",
            owner_ha_user_ids=("owner",),
        )
        profile_id = str(profile["profile_id"])

        assert await acl.async_authorize(profile_id=profile_id, ha_user_id="ha-admin") is None
        with pytest.raises(ProfileAccessDenied):
            await acl.async_require(
                profile_id=profile_id,
                ha_user_id="ha-admin",
                permission=ProfilePermission.READ,
            )
    finally:
        await storage.async_close()


async def test_only_owner_can_modify_acl_and_last_owner_is_preserved(tmp_path: Path) -> None:
    storage, profiles, acl = await _services(tmp_path)
    try:
        profile = await profiles.async_create_profile(
            name="Shared child",
            preset="child",
            timezone="Europe/Paris",
            owner_ha_user_ids=("owner-1", "owner-2"),
        )
        profile_id = str(profile["profile_id"])
        await acl.async_set_member_role(
            actor_ha_user_id="owner-1",
            profile_id=profile_id,
            target_ha_user_id="editor",
            role="editor",
        )

        with pytest.raises(ProfileAccessDenied):
            await acl.async_set_member_role(
                actor_ha_user_id="editor",
                profile_id=profile_id,
                target_ha_user_id="viewer",
                role="viewer",
            )

        assert await acl.async_remove_member(
            actor_ha_user_id="owner-1",
            profile_id=profile_id,
            target_ha_user_id="owner-2",
        )
        with pytest.raises(LastOwnerError):
            await acl.async_remove_member(
                actor_ha_user_id="owner-1",
                profile_id=profile_id,
                target_ha_user_id="owner-1",
            )

        with pytest.raises(LastOwnerError):
            await acl.async_set_member_role(
                actor_ha_user_id="owner-1",
                profile_id=profile_id,
                target_ha_user_id="owner-1",
                role="editor",
            )
    finally:
        await storage.async_close()
