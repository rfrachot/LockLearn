"""Backend profile ACL authority for LockLearn."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..storage.repositories import ProfileMemberRecord, ProfilesRepository
from .clock import Clock, SystemClock


class ProfileRole(StrEnum):
    """Profile membership roles defined by the V1 specification."""

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class ProfilePermission(StrEnum):
    """Backend permissions derived from profile membership."""

    READ = "read"
    EDIT_TRACK = "edit_track"
    ANSWER = "answer"
    SHARE = "share"
    DELETE = "delete"
    MANAGE_ACL = "manage_acl"
    MANAGE_PROGRESS = "manage_progress"


_ROLE_PERMISSIONS: dict[ProfileRole, frozenset[ProfilePermission]] = {
    ProfileRole.OWNER: frozenset(ProfilePermission),
    ProfileRole.EDITOR: frozenset(
        {
            ProfilePermission.READ,
            ProfilePermission.EDIT_TRACK,
            ProfilePermission.ANSWER,
            ProfilePermission.MANAGE_PROGRESS,
        }
    ),
    ProfileRole.VIEWER: frozenset({ProfilePermission.READ}),
}


class ProfileAccessDenied(PermissionError):
    """Raised when a HA user lacks the requested profile permission."""


class LastOwnerError(RuntimeError):
    """Raised when an ACL mutation would orphan a profile."""


@dataclass(frozen=True, slots=True)
class ProfileAuthorization:
    """Resolved profile membership and permission set."""

    profile_id: str
    ha_user_id: str
    role: ProfileRole
    permissions: frozenset[ProfilePermission]


class ProfileACLService:
    """Single backend authority for profile membership and permissions."""

    def __init__(
        self,
        repository: ProfilesRepository,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or SystemClock()

    async def async_authorize(
        self,
        *,
        profile_id: str,
        ha_user_id: str,
    ) -> ProfileAuthorization | None:
        """Resolve membership without granting implicit admin bypass."""
        role_value = await self._repository.async_get_role(profile_id, ha_user_id)
        if role_value is None:
            return None
        role = ProfileRole(role_value)
        return ProfileAuthorization(
            profile_id=profile_id,
            ha_user_id=ha_user_id,
            role=role,
            permissions=_ROLE_PERMISSIONS[role],
        )

    async def async_can(
        self,
        *,
        profile_id: str,
        ha_user_id: str,
        permission: ProfilePermission,
    ) -> bool:
        """Return whether a HA user may perform a profile-scoped action."""
        authorization = await self.async_authorize(
            profile_id=profile_id,
            ha_user_id=ha_user_id,
        )
        return authorization is not None and permission in authorization.permissions

    async def async_require(
        self,
        *,
        profile_id: str,
        ha_user_id: str,
        permission: ProfilePermission,
    ) -> ProfileAuthorization:
        """Require a permission at the backend boundary."""
        authorization = await self.async_authorize(
            profile_id=profile_id,
            ha_user_id=ha_user_id,
        )
        if authorization is None or permission not in authorization.permissions:
            raise ProfileAccessDenied(profile_id)
        return authorization

    async def async_list_visible_profiles(self, ha_user_id: str) -> tuple[dict[str, object], ...]:
        """Return only profiles the HA user is allowed to know exist."""
        return await self._repository.async_list_for_ha_user(ha_user_id)

    async def async_get_visible_profile(
        self,
        *,
        profile_id: str,
        ha_user_id: str,
    ) -> dict[str, object] | None:
        """Return None for both nonexistent and unauthorized profiles."""
        return await self._repository.async_get_visible(profile_id, ha_user_id)

    async def async_set_member_role(
        self,
        *,
        actor_ha_user_id: str,
        profile_id: str,
        target_ha_user_id: str,
        role: ProfileRole | str,
    ) -> None:
        """Add or update membership after owner-only ACL authorization."""
        await self.async_require(
            profile_id=profile_id,
            ha_user_id=actor_ha_user_id,
            permission=ProfilePermission.MANAGE_ACL,
        )
        resolved_role = ProfileRole(role)
        now = self._clock.now().isoformat()
        await self._repository.async_upsert_member(
            ProfileMemberRecord(
                profile_id=profile_id,
                ha_user_id=target_ha_user_id,
                role=resolved_role.value,
                created_at_utc=now,
            )
        )

    async def async_remove_member(
        self,
        *,
        actor_ha_user_id: str,
        profile_id: str,
        target_ha_user_id: str,
    ) -> bool:
        """Remove membership while guaranteeing at least one remaining owner."""
        await self.async_require(
            profile_id=profile_id,
            ha_user_id=actor_ha_user_id,
            permission=ProfilePermission.MANAGE_ACL,
        )
        target_role = await self._repository.async_get_role(profile_id, target_ha_user_id)
        if target_role == ProfileRole.OWNER.value:
            if await self._repository.async_count_owners(profile_id) <= 1:
                raise LastOwnerError(profile_id)
        return await self._repository.async_delete_member(profile_id, target_ha_user_id)
