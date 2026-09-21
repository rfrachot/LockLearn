"""P0 Home Assistant WebSocket commands."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import HomeAssistant

from ..const import DATA_RUNTIME, DOMAIN, FRONTEND_PROTOCOL_VERSION
from ..runtime import LockLearnRuntime
from ..storage.database import SessionNotFoundError, StaleSessionError

ERR_FORBIDDEN = "locklearn/forbidden"
ERR_NOT_FOUND = "locklearn/not_found"
ERR_INVALID_REQUEST = "locklearn/invalid_request"
ERR_STALE_SESSION = "locklearn/stale_session"
ERR_OPERATION_IN_PROGRESS = "locklearn/operation_in_progress"


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


def _probe_profile_id(connection: ActiveConnection) -> str:
    """Use an isolated P0 profile namespace until P2 supplies real ACL data."""
    return f"p0-probe:{connection.user.id}"


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
) -> dict[str, Any] | None:
    """Reject cross-user session reads/mutations at the backend boundary."""
    state = await runtime.sessions.async_get(session_id)
    if state is None:
        connection.send_error(message_id, ERR_NOT_FOUND, "Session not found")
        return None
    if state["profile_id"] != _probe_profile_id(connection):
        connection.send_error(message_id, ERR_FORBIDDEN, "Session access denied")
        return None
    return state


@websocket_api.websocket_command({vol.Required("type"): "locklearn/bootstrap"})
@websocket_api.async_response
async def ws_bootstrap(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the minimal protocol handshake without private application data."""
    if _require_runtime(hass, connection, msg["id"]) is None:
        return
    connection.send_result(
        msg["id"],
        {
            "frontend_protocol": FRONTEND_PROTOCOL_VERSION,
            "authenticated_user_id": connection.user.id,
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
        vol.Optional("track_id"): str,
    }
)
@websocket_api.async_response
async def ws_session_start(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Start the P0 persistent session prototype."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await runtime.sessions.async_start(_probe_profile_id(connection), msg.get("track_id"))
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
    """Get a P0 session."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await _authorized_session(runtime, connection, msg["id"], msg["session_id"])
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
    """Apply a session answer using CAS."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if await _authorized_session(runtime, connection, msg["id"], msg["session_id"]) is None:
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
        vol.Required("type"): "locklearn/session/subscribe",
        vol.Required("session_id"): str,
    }
)
@websocket_api.async_response
async def ws_session_subscribe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Subscribe a client to session mutations."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await _authorized_session(runtime, connection, msg["id"], msg["session_id"])
    if state is None:
        return

    def forward(snapshot: dict[str, Any]) -> None:
        connection.send_event(msg["id"], snapshot)

    connection.subscriptions[msg["id"]] = runtime.sessions.subscribe(msg["session_id"], forward)
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
    ws_admin_storage_status,
    ws_session_start,
    ws_session_get,
    ws_session_answer,
    ws_session_subscribe,
    ws_operation_subscribe,
    ws_operation_cancel,
)


def async_register_commands(hass: HomeAssistant) -> None:
    """Register P0 commands once for the HA process lifetime."""
    for command in COMMANDS:
        websocket_api.async_register_command(hass, command)
