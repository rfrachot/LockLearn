"""P0 identity and unattended-action security boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..storage.database import SQLiteStorage


class ActionKind(StrEnum):
    """HA-facing actions considered by the P0 authorization spike."""

    START_SESSION = "start_session"
    SEND_NOW = "send_now"
    SNOOZE = "snooze"
    PAUSE_TRACK = "pause_track"
    READ_PRIVATE = "read_private"
    EXPORT = "export"
    DELETE = "delete"


class ActorKind(StrEnum):
    """Source identity of an authorized action."""

    HA_USER = "ha_user"
    UNATTENDED_AUTOMATION = "unattended_automation"


UNATTENDED_ALLOWLIST = frozenset(
    {
        ActionKind.SEND_NOW,
        ActionKind.SNOOZE,
        ActionKind.PAUSE_TRACK,
    }
)


class ActionForbiddenError(PermissionError):
    """Raised when an action crosses the unattended boundary."""


@dataclass(frozen=True, slots=True)
class AuthorizedActor:
    """Authorization result suitable for privacy-minimal audit records."""

    kind: ActorKind
    user_id: str | None


def authorize_action(
    *, user_id: str | None, allow_unattended_actions: bool, action: ActionKind
) -> AuthorizedActor:
    """Validate HA user context or the narrow unattended allowlist.

    Profile ACL remains mandatory for user-context actions in P2. HA admin
    status is deliberately absent: it never implies profile membership.
    """
    if user_id is not None:
        return AuthorizedActor(ActorKind.HA_USER, user_id)
    if allow_unattended_actions and action in UNATTENDED_ALLOWLIST:
        return AuthorizedActor(ActorKind.UNATTENDED_AUTOMATION, None)
    raise ActionForbiddenError(action)


def effective_signal_quality(*, shared_device: bool, explicit_trust: bool) -> str:
    """Prevent a shared target alone from satisfying verified retrieval."""
    if shared_device and not explicit_trust:
        return "reduced"
    return "normal"


async def async_authorize_and_audit(
    storage: SQLiteStorage,
    *,
    user_id: str | None,
    profile_id: str,
    allow_unattended_actions: bool,
    action: ActionKind,
) -> AuthorizedActor:
    """Authorize an action and durably audit every unattended invocation."""
    actor = authorize_action(
        user_id=user_id,
        allow_unattended_actions=allow_unattended_actions,
        action=action,
    )
    if actor.kind is ActorKind.UNATTENDED_AUTOMATION:
        await storage.async_append_audit(
            "unattended_action",
            actor_user_id=None,
            profile_id=profile_id,
            payload={"action": action.value, "actor_kind": actor.kind.value},
        )
    return actor
