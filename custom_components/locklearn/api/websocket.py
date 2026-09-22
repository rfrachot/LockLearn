"""Authenticated LockLearn Home Assistant WebSocket commands."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import HomeAssistant

from ..const import CONF_CREATE_PERSONAL_PROFILE, DATA_RUNTIME, DOMAIN, FRONTEND_PROTOCOL_VERSION
from ..core.acl import LastOwnerError, ProfilePermission, ProfileRole
from ..core.content import GradingOutcome, GradingPolicyKind
from ..core.content_reports import ContentReportError
from ..core.grading import FreeTextGradingResult
from ..core.profiles import ProfileValidationError
from ..core.sessions import SessionValidationError
from ..core.tracks import TrackValidationError
from ..runtime import LockLearnRuntime
from ..storage.database import SessionNotFoundError, StaleSessionError
from ..storage.repositories import CardReference, ContentReferenceError

ERR_FORBIDDEN = "locklearn/forbidden"
ERR_NOT_FOUND = "locklearn/not_found"
ERR_INVALID_REQUEST = "locklearn/invalid_request"
ERR_STALE_SESSION = "locklearn/stale_session"
ERR_OPERATION_IN_PROGRESS = "locklearn/operation_in_progress"
ERR_DATASET_UNAVAILABLE = "locklearn/dataset_unavailable"
ERR_PACK_VERSION_MISMATCH = "locklearn/pack_version_mismatch"

_DEFAULT_PAGE_LIMIT = 50
_MAX_PAGE_LIMIT = 100


def _runtime(hass: HomeAssistant) -> LockLearnRuntime | None:
    domain_data = hass.data.get(DOMAIN, {})
    runtime = domain_data.get(DATA_RUNTIME)
    return runtime if isinstance(runtime, LockLearnRuntime) else None


def _require_runtime(
    hass: HomeAssistant, connection: ActiveConnection, message_id: int
) -> LockLearnRuntime | None:
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(message_id, ERR_NOT_FOUND, "LockLearn is not loaded")
    return runtime


def _paginate(
    items: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    *,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    """Return one bounded collection page with an offset cursor."""
    try:
        offset = 0 if cursor is None else int(cursor)
    except ValueError as err:
        raise ValueError("invalid cursor") from err
    if offset < 0:
        raise ValueError("invalid cursor")
    page = list(items[offset : offset + limit])
    next_offset = offset + len(page)
    return {
        "items": page,
        "cursor": str(next_offset) if next_offset < len(items) else None,
    }


async def _require_profile_permission(
    runtime: LockLearnRuntime,
    connection: ActiveConnection,
    message_id: int,
    profile_id: str,
    permission: ProfilePermission,
) -> bool:
    visible = await runtime.acl.async_get_visible_profile(
        profile_id=profile_id,
        ha_user_id=connection.user.id,
    )
    if visible is None:
        connection.send_error(message_id, ERR_NOT_FOUND, "Profile not found")
        return False
    if not await runtime.acl.async_can(
        profile_id=profile_id,
        ha_user_id=connection.user.id,
        permission=permission,
    ):
        connection.send_error(message_id, ERR_FORBIDDEN, "Profile access denied")
        return False
    return True


async def _require_track_permission(
    runtime: LockLearnRuntime,
    connection: ActiveConnection,
    message_id: int,
    track_id: str,
    permission: ProfilePermission,
) -> dict[str, Any] | None:
    track = await runtime.storage.repositories.tracks.async_get(track_id)
    if track is None:
        connection.send_error(message_id, ERR_NOT_FOUND, "Track not found")
        return None
    if not await _require_profile_permission(
        runtime,
        connection,
        message_id,
        str(track["profile_id"]),
        permission,
    ):
        return None
    return track


def _can_access_operation(connection: ActiveConnection, owner_user_id: str | None) -> bool:
    """Keep user operations private; system operations are admin-only."""
    if owner_user_id is None:
        return connection.user.is_admin
    return owner_user_id == connection.user.id


async def _authorized_session(
    runtime: LockLearnRuntime,
    connection: ActiveConnection,
    message_id: int,
    session_id: str,
    permission: ProfilePermission,
) -> dict[str, Any] | None:
    """Recheck Profile ACL for every persistent-session read or mutation."""
    state = await runtime.sessions.async_get(session_id)
    if state is None:
        connection.send_error(message_id, ERR_NOT_FOUND, "Session not found")
        return None
    if not await _require_profile_permission(
        runtime,
        connection,
        message_id,
        str(state["profile_id"]),
        permission,
    ):
        return None
    return state


@websocket_api.websocket_command({vol.Required("type"): "locklearn/bootstrap"})
@websocket_api.async_response
async def ws_bootstrap(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the minimal protocol handshake without private application data."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    personal_profile: dict[str, Any] | None = None
    entries = hass.config_entries.async_entries(DOMAIN)
    create_personal = bool(entries and entries[0].data.get(CONF_CREATE_PERSONAL_PROFILE, False))
    if create_personal:
        try:
            personal_profile = await runtime.profiles.async_ensure_personal_profile(
                ha_user_id=connection.user.id,
                name=connection.user.name or "Personal",
                timezone=hass.config.time_zone,
            )
        except ProfileValidationError as err:
            connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
            return
    connection.send_result(
        msg["id"],
        {
            "frontend_protocol": FRONTEND_PROTOCOL_VERSION,
            "authenticated_user_id": connection.user.id,
            "personal_profile": personal_profile,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/profiles/list",
        vol.Optional("limit", default=_DEFAULT_PAGE_LIMIT): vol.All(
            int, vol.Range(min=1, max=_MAX_PAGE_LIMIT)
        ),
        vol.Optional("cursor"): str,
    }
)
@websocket_api.async_response
async def ws_profiles_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profiles = await runtime.acl.async_list_visible_profiles(connection.user.id)
    try:
        result = _paginate(profiles, limit=msg["limit"], cursor=msg.get("cursor"))
    except ValueError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/profiles/create",
        vol.Required("name"): str,
        vol.Optional("preset", default="standard"): vol.In(
            ("child", "standard", "intensive", "custom")
        ),
        vol.Optional("timezone"): str,
    }
)
@websocket_api.async_response
async def ws_profiles_create(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    try:
        profile = await runtime.profiles.async_create_profile(
            name=msg["name"],
            preset=msg["preset"],
            timezone=msg.get("timezone", hass.config.time_zone),
            owner_ha_user_ids=(connection.user.id,),
        )
    except ProfileValidationError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    profile["role"] = ProfileRole.OWNER.value
    connection.send_result(msg["id"], profile)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/profiles/update",
        vol.Required("profile_id"): str,
        vol.Optional("name"): str,
        vol.Optional("timezone"): str,
        vol.Optional("status"): vol.In(("active", "archived")),
        vol.Optional("settings_patch"): dict,
    }
)
@websocket_api.async_response
async def ws_profiles_update(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.EDIT_PROFILE,
    ):
        return
    try:
        profile = await runtime.profiles.async_update_profile(
            profile_id=profile_id,
            name=msg.get("name"),
            timezone=msg.get("timezone"),
            status=msg.get("status"),
            settings_patch=msg.get("settings_patch"),
        )
    except ProfileValidationError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    profile["role"] = await runtime.storage.repositories.profiles.async_get_role(
        profile_id, connection.user.id
    )
    connection.send_result(msg["id"], profile)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/profiles/delete",
        vol.Required("profile_id"): str,
    }
)
@websocket_api.async_response
async def ws_profiles_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.DELETE,
    ):
        return
    if not await runtime.profiles.async_delete_profile(profile_id):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Profile not found")
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/profiles/share",
        vol.Required("profile_id"): str,
        vol.Required("target_user_id"): str,
        vol.Optional("role", default="viewer"): vol.In(("owner", "editor", "viewer")),
        vol.Optional("remove", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_profiles_share(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.MANAGE_ACL,
    ):
        return
    target_user = await hass.auth.async_get_user(msg["target_user_id"])
    if target_user is None:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, "Home Assistant user not found")
        return
    try:
        if msg["remove"]:
            removed = await runtime.acl.async_remove_member(
                actor_ha_user_id=connection.user.id,
                profile_id=profile_id,
                target_ha_user_id=target_user.id,
            )
            connection.send_result(msg["id"], {"removed": removed})
        else:
            await runtime.acl.async_set_member_role(
                actor_ha_user_id=connection.user.id,
                profile_id=profile_id,
                target_ha_user_id=target_user.id,
                role=msg["role"],
            )
            connection.send_result(
                msg["id"],
                {"ha_user_id": target_user.id, "role": msg["role"]},
            )
    except LastOwnerError:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, "Profile must keep an owner")


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/tracks/list",
        vol.Required("profile_id"): str,
        vol.Optional("limit", default=_DEFAULT_PAGE_LIMIT): vol.All(
            int, vol.Range(min=1, max=_MAX_PAGE_LIMIT)
        ),
        vol.Optional("cursor"): str,
    }
)
@websocket_api.async_response
async def ws_tracks_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.READ,
    ):
        return
    tracks = await runtime.storage.repositories.tracks.async_list_for_profile(profile_id)
    try:
        result = _paginate(tracks, limit=msg["limit"], cursor=msg.get("cursor"))
    except ValueError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/tracks/create",
        vol.Required("profile_id"): str,
        vol.Required("name"): str,
        vol.Required("pack_version_id"): str,
        vol.Required("source_language"): str,
        vol.Required("target_language"): str,
        vol.Optional("priority", default=1): vol.All(int, vol.Range(min=1)),
        vol.Optional("content_weights"): dict,
        vol.Optional("explicit_card_keys"): [str],
    }
)
@websocket_api.async_response
async def ws_tracks_create(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.EDIT_TRACK,
    ):
        return
    try:
        track = await runtime.tracks.async_create_track(
            profile_id=profile_id,
            name=msg["name"],
            pack_version_id=msg["pack_version_id"],
            source_language=msg["source_language"],
            target_language=msg["target_language"],
            priority=msg["priority"],
            content_weights=msg.get("content_weights"),
            explicit_card_keys=(
                None if "explicit_card_keys" not in msg else tuple(msg["explicit_card_keys"])
            ),
        )
    except ContentReferenceError as err:
        connection.send_error(msg["id"], ERR_DATASET_UNAVAILABLE, str(err))
        return
    except TrackValidationError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], track)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/tracks/update",
        vol.Required("track_id"): str,
        vol.Optional("name"): str,
        vol.Optional("source_language"): str,
        vol.Optional("target_language"): str,
        vol.Optional("status"): vol.In(("active", "paused", "archived")),
        vol.Optional("priority"): vol.All(int, vol.Range(min=1)),
        vol.Optional("content_weights"): dict,
        vol.Optional("explicit_card_keys"): [str],
    }
)
@websocket_api.async_response
async def ws_tracks_update(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _require_track_permission(
            runtime,
            connection,
            msg["id"],
            msg["track_id"],
            ProfilePermission.EDIT_TRACK,
        )
        is None
    ):
        return
    try:
        track = await runtime.tracks.async_update_track(
            track_id=msg["track_id"],
            name=msg.get("name"),
            source_language=msg.get("source_language"),
            target_language=msg.get("target_language"),
            status=msg.get("status"),
            priority=msg.get("priority"),
            content_weights=msg.get("content_weights"),
            explicit_card_keys=(
                None if "explicit_card_keys" not in msg else tuple(msg["explicit_card_keys"])
            ),
        )
    except TrackValidationError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], track)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/tracks/delete",
        vol.Required("track_id"): str,
    }
)
@websocket_api.async_response
async def ws_tracks_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _require_track_permission(
            runtime,
            connection,
            msg["id"],
            msg["track_id"],
            ProfilePermission.EDIT_TRACK,
        )
        is None
    ):
        return
    if not await runtime.tracks.async_delete_track(msg["track_id"]):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Track not found")
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/tracks/integrate_pack_update",
        vol.Required("track_id"): str,
        vol.Required("pack_version_id"): str,
    }
)
@websocket_api.async_response
async def ws_tracks_integrate_pack_update(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _require_track_permission(
            runtime,
            connection,
            msg["id"],
            msg["track_id"],
            ProfilePermission.EDIT_TRACK,
        )
        is None
    ):
        return
    try:
        diff = await runtime.tracks.async_integrate_pack_update(
            track_id=msg["track_id"],
            target_pack_version_id=msg["pack_version_id"],
        )
    except ContentReferenceError as err:
        connection.send_error(msg["id"], ERR_DATASET_UNAVAILABLE, str(err))
        return
    except TrackValidationError as err:
        code = (
            ERR_PACK_VERSION_MISMATCH
            if "same Pack" in str(err) or "already integrated" in str(err)
            else ERR_INVALID_REQUEST
        )
        connection.send_error(msg["id"], code, str(err))
        return
    connection.send_result(
        msg["id"],
        {
            "from_pack_version_id": diff.from_pack_version_id,
            "to_pack_version_id": diff.to_pack_version_id,
            "added_learning_item_ids": list(diff.added_learning_item_ids),
            "removed_learning_item_ids": list(diff.removed_learning_item_ids),
            "changed_learning_item_ids": list(diff.changed_learning_item_ids),
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/packs/list",
        vol.Optional("limit", default=_DEFAULT_PAGE_LIMIT): vol.All(
            int, vol.Range(min=1, max=_MAX_PAGE_LIMIT)
        ),
        vol.Optional("cursor"): str,
    }
)
@websocket_api.async_response
async def ws_packs_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    items = await runtime.storage.async_pack_inventory()
    try:
        result = _paginate(items, limit=msg["limit"], cursor=msg.get("cursor"))
    except ValueError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/datasets/list",
        vol.Optional("limit", default=_DEFAULT_PAGE_LIMIT): vol.All(
            int, vol.Range(min=1, max=_MAX_PAGE_LIMIT)
        ),
        vol.Optional("cursor"): str,
    }
)
@websocket_api.async_response
async def ws_datasets_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    items = await runtime.storage.async_dataset_inventory()
    try:
        result = _paginate(items, limit=msg["limit"], cursor=msg.get("cursor"))
    except ValueError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/content/report",
        vol.Required("profile_id"): str,
        vol.Required("track_id"): str,
        vol.Required("card_key"): str,
        vol.Required("learning_item_id"): str,
        vol.Required("prompt_facet_id"): str,
        vol.Required("answer_facet_id"): str,
        vol.Required("submitted_text"): str,
        vol.Optional("normalized_submission"): vol.Any(str, None),
        vol.Required("grading_policy_kind"): vol.In(("exact", "any_of", "fuzzy_normalized")),
        vol.Required("grading_policy_version"): vol.All(int, vol.Range(min=1)),
        vol.Required("normalization_version"): vol.All(int, vol.Range(min=1)),
    }
)
@websocket_api.async_response
async def ws_content_report(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Report a plausible free-text answer that should be accepted."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.ANSWER,
    ):
        return

    track = await runtime.storage.repositories.tracks.async_get(msg["track_id"])
    if track is None or str(track["profile_id"]) != profile_id:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Track not found")
        return

    grade = FreeTextGradingResult(
        outcome=GradingOutcome.UNRECOGNIZED,
        submitted_text=msg["submitted_text"],
        normalized_submission=msg.get("normalized_submission"),
        matched_answer=None,
        grading_policy_kind=GradingPolicyKind(msg["grading_policy_kind"]),
        grading_policy_version=msg["grading_policy_version"],
        normalization_version=msg["normalization_version"],
        reportable=True,
        reason="user_claimed_should_be_accepted",
    )
    try:
        receipt = await runtime.content_reports.async_report_should_be_accepted(
            actor_user_id=connection.user.id,
            profile_id=profile_id,
            track_id=msg["track_id"],
            card=CardReference(
                card_key=msg["card_key"],
                learning_item_id=msg["learning_item_id"],
                prompt_facet_id=msg["prompt_facet_id"],
                answer_facet_id=msg["answer_facet_id"],
            ),
            grade=grade,
            dataset_generation=runtime.storage.content_generations.active_metadata.generation_id,
        )
    except (ContentReportError, ContentReferenceError) as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(
        msg["id"],
        {
            "report_id": receipt.report_id,
            "grading_result": receipt.grading_result,
            "srs_penalized": receipt.srs_penalized,
        },
    )


@websocket_api.websocket_command({vol.Required("type"): "locklearn/admin/storage/status"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_admin_storage_status(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return privacy-safe storage health metadata to administrators."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    connection.send_result(msg["id"], await runtime.storage.async_diagnostic_status())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/start",
        vol.Required("profile_id"): str,
        vol.Optional("track_id"): str,
        vol.Optional("session_type", default="learn"): str,
        vol.Optional("strategy", default="default"): str,
        vol.Optional("settings", default={}): dict,
    }
)
@websocket_api.async_response
async def ws_session_start(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Start a persistent session owned by a real LockLearn Profile."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime,
        connection,
        msg["id"],
        profile_id,
        ProfilePermission.ANSWER,
    ):
        return
    track_id = msg.get("track_id")
    if track_id is not None:
        track = await runtime.storage.repositories.tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            connection.send_error(msg["id"], ERR_NOT_FOUND, "Track not found")
            return
    try:
        state = await runtime.sessions.async_start(
            profile_id,
            track_id,
            session_type=msg["session_type"],
            strategy=msg["strategy"],
            settings=msg["settings"],
        )
    except SessionValidationError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/get",
        vol.Required("session_id"): str,
    }
)
@websocket_api.async_response
async def ws_session_get(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Get a complete resumable persistent-session snapshot."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await _authorized_session(
        runtime,
        connection,
        msg["id"],
        msg["session_id"],
        ProfilePermission.READ,
    )
    if state is None:
        return
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/answer",
        vol.Required("session_id"): str,
        vol.Required("expected_version"): vol.All(int, vol.Range(min=1)),
        vol.Required("question_id"): str,
        vol.Required("answer"): object,
    }
)
@websocket_api.async_response
async def ws_session_answer(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Apply one current-question answer using session/version CAS."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _authorized_session(
            runtime,
            connection,
            msg["id"],
            msg["session_id"],
            ProfilePermission.ANSWER,
        )
        is None
    ):
        return
    try:
        state = await runtime.sessions.async_answer(
            msg["session_id"],
            msg["expected_version"],
            msg["question_id"],
            msg["answer"],
        )
    except SessionNotFoundError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Session not found")
        return
    except StaleSessionError:
        connection.send_error(msg["id"], ERR_STALE_SESSION, "The session changed on another client")
        return
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/pause",
        vol.Required("session_id"): str,
        vol.Required("expected_version"): vol.All(int, vol.Range(min=1)),
        vol.Optional("paused", default=True): bool,
    }
)
@websocket_api.async_response
async def ws_session_pause(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Pause or resume a session through one CAS lifecycle command."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _authorized_session(
            runtime,
            connection,
            msg["id"],
            msg["session_id"],
            ProfilePermission.ANSWER,
        )
        is None
    ):
        return
    try:
        if msg["paused"]:
            state = await runtime.sessions.async_pause(
                msg["session_id"], msg["expected_version"]
            )
        else:
            state = await runtime.sessions.async_resume(
                msg["session_id"], msg["expected_version"]
            )
    except SessionNotFoundError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Session not found")
        return
    except StaleSessionError:
        connection.send_error(msg["id"], ERR_STALE_SESSION, "The session changed on another client")
        return
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/complete",
        vol.Required("session_id"): str,
        vol.Required("expected_version"): vol.All(int, vol.Range(min=1)),
    }
)
@websocket_api.async_response
async def ws_session_complete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Complete a persistent session with CAS."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _authorized_session(
            runtime,
            connection,
            msg["id"],
            msg["session_id"],
            ProfilePermission.ANSWER,
        )
        is None
    ):
        return
    try:
        state = await runtime.sessions.async_complete(
            msg["session_id"], msg["expected_version"]
        )
    except SessionNotFoundError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Session not found")
        return
    except StaleSessionError:
        connection.send_error(msg["id"], ERR_STALE_SESSION, "The session changed on another client")
        return
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/undo",
        vol.Required("session_id"): str,
        vol.Required("expected_version"): vol.All(int, vol.Range(min=1)),
    }
)
@websocket_api.async_response
async def ws_session_undo(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Undo session navigation only; P3.12 owns ReviewEvent/progress undo."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if (
        await _authorized_session(
            runtime,
            connection,
            msg["id"],
            msg["session_id"],
            ProfilePermission.ANSWER,
        )
        is None
    ):
        return
    try:
        state = await runtime.sessions.async_undo(
            msg["session_id"],
            msg["expected_version"],
            actor_user_id=connection.user.id,
        )
    except SessionNotFoundError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Session not found")
        return
    except StaleSessionError:
        connection.send_error(msg["id"], ERR_STALE_SESSION, "No admissible session answer to undo")
        return
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/subscribe",
        vol.Required("session_id"): str,
    }
)
@websocket_api.async_response
async def ws_session_subscribe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Subscribe a client to persistent session mutations."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await _authorized_session(
        runtime,
        connection,
        msg["id"],
        msg["session_id"],
        ProfilePermission.READ,
    )
    if state is None:
        return

    def forward(snapshot: dict[str, Any]) -> None:
        connection.send_event(msg["id"], snapshot)

    connection.subscriptions[msg["id"]] = runtime.sessions.subscribe(
        msg["session_id"],
        forward,
    )
    connection.send_result(msg["id"], state)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/operations/subscribe",
        vol.Required("operation_id"): str,
    }
)
@websocket_api.async_response
async def ws_operation_subscribe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Subscribe to a long-operation stream."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return

    def forward(snapshot: dict[str, Any]) -> None:
        connection.send_event(msg["id"], snapshot)

    state = runtime.operations.get(msg["operation_id"])
    if state is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Operation not found")
        return
    if not _can_access_operation(connection, state.owner_user_id):
        connection.send_error(msg["id"], ERR_FORBIDDEN, "Operation access denied")
        return
    try:
        unsubscribe = runtime.operations.subscribe(msg["operation_id"], forward)
    except KeyError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Operation not found")
        return
    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"], state.as_dict())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/operations/cancel",
        vol.Required("operation_id"): str,
    }
)
@websocket_api.async_response
async def ws_operation_cancel(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Cancel a cancellable long operation."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = runtime.operations.get(msg["operation_id"])
    if state is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Operation not found")
        return
    if not _can_access_operation(connection, state.owner_user_id):
        connection.send_error(msg["id"], ERR_FORBIDDEN, "Operation access denied")
        return
    if not runtime.operations.cancel(msg["operation_id"]):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Cancellable operation not found")
        return
    connection.send_result(msg["id"])


COMMANDS = (
    ws_bootstrap,
    ws_profiles_list,
    ws_profiles_create,
    ws_profiles_update,
    ws_profiles_delete,
    ws_profiles_share,
    ws_tracks_list,
    ws_tracks_create,
    ws_tracks_update,
    ws_tracks_delete,
    ws_tracks_integrate_pack_update,
    ws_packs_list,
    ws_datasets_list,
    ws_content_report,
    ws_admin_storage_status,
    ws_session_start,
    ws_session_get,
    ws_session_answer,
    ws_session_pause,
    ws_session_complete,
    ws_session_undo,
    ws_session_subscribe,
    ws_operation_subscribe,
    ws_operation_cancel,
)


def async_register_commands(hass: HomeAssistant) -> None:
    """Register LockLearn WebSocket commands once for the HA process lifetime."""
    for command in COMMANDS:
        websocket_api.async_register_command(hass, command)
