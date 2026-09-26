"""P3.12 WebSocket ACL and long-operation tests."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN


async def test_integrity_websockets_enforce_progress_and_admin_permissions(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    admin = await hass_ws_client(hass)
    await admin.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "P3.12 ACL",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await admin.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    viewer = await hass_ws_client(hass, hass_read_only_access_token)
    await admin.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await admin.receive_json())["success"] is True

    await viewer.send_json_auto_id(
        {
            "type": "locklearn/progress/undo_last",
            "profile_id": profile_id,
        }
    )
    denied = await viewer.receive_json()
    assert denied["success"] is False
    assert denied["error"]["code"] == "locklearn/forbidden"

    await admin.send_json_auto_id(
        {
            "type": "locklearn/progress/undo_last",
            "profile_id": profile_id,
        }
    )
    empty = await admin.receive_json()
    assert empty["success"] is False
    assert empty["error"]["code"] == "locklearn/invalid_request"

    await viewer.send_json_auto_id({"type": "locklearn/admin/rebuild_progress"})
    forbidden = await viewer.receive_json()
    assert forbidden["success"] is False
    assert forbidden["error"]["code"] == "unauthorized"

    await admin.send_json_auto_id({"type": "locklearn/admin/rebuild_progress"})
    started = await admin.receive_json()
    assert started["success"] is True
    operation_id = started["result"]["operation_id"]

    runtime = hass.data[DOMAIN]["runtime"]
    task = runtime.operations.task(operation_id)
    if task is not None:
        await task
    state = runtime.operations.get(operation_id)
    assert state is not None
    assert state.status == "completed"
    assert state.result == {"rebuilt_cards": 0}

    await admin.send_json_auto_id({"type": "locklearn/admin/rebuild_stats"})
    stats_started = await admin.receive_json()
    assert stats_started["success"] is True
    stats_operation_id = stats_started["result"]["operation_id"]
    stats_task = runtime.operations.task(stats_operation_id)
    if stats_task is not None:
        await stats_task
    stats_state = runtime.operations.get(stats_operation_id)
    assert stats_state is not None
    assert stats_state.status == "completed"
    assert stats_state.result == {"rebuilt_days": 0}

    await hass.config_entries.async_unload(entry.entry_id)
