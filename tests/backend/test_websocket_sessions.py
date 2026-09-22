"""P3.8 WebSocket session lifecycle and cross-client resume tests."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN


async def test_session_start_pause_resume_complete_and_cross_client_get(
    hass: HomeAssistant,
    hass_ws_client: Any,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Session profile",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await owner.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "session_type": "bounded",
            "strategy": "manual",
            "settings": {
                "requested_cards": 12,
                "content_types": ["vocabulary", "grammar"],
            },
        }
    )
    started = await owner.receive_json()
    assert started["success"] is True
    session_id = started["result"]["id"]
    assert started["result"]["profile_id"] == profile_id
    assert started["result"]["type"] == "bounded"
    assert started["result"]["strategy"] == "manual"
    assert started["result"]["settings"]["requested_cards"] == 12
    assert started["result"]["version"] == 1

    other_client = await hass_ws_client(hass)
    await other_client.send_json_auto_id(
        {"type": "locklearn/session/get", "session_id": session_id}
    )
    resumed = await other_client.receive_json()
    assert resumed["success"] is True
    assert resumed["result"]["id"] == session_id
    assert resumed["result"]["version"] == 1
    assert resumed["result"]["settings"]["content_types"] == ["vocabulary", "grammar"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/pause",
            "session_id": session_id,
            "expected_version": 1,
        }
    )
    paused = await owner.receive_json()
    assert paused["success"] is True
    assert paused["result"]["status"] == "paused"
    assert paused["result"]["version"] == 2

    await other_client.send_json_auto_id(
        {
            "type": "locklearn/session/pause",
            "session_id": session_id,
            "expected_version": 2,
            "paused": False,
        }
    )
    active = await other_client.receive_json()
    assert active["success"] is True
    assert active["result"]["status"] == "active"
    assert active["result"]["version"] == 3

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/complete",
            "session_id": session_id,
            "expected_version": 3,
        }
    )
    completed = await owner.receive_json()
    assert completed["success"] is True
    assert completed["result"]["status"] == "completed"
    assert completed["result"]["version"] == 4
    assert completed["result"]["completed_at_utc"] is not None

    await other_client.send_json_auto_id(
        {
            "type": "locklearn/session/pause",
            "session_id": session_id,
            "expected_version": 4,
            "paused": False,
        }
    )
    stale = await other_client.receive_json()
    assert stale["success"] is False
    assert stale["error"]["code"] == "locklearn/stale_session"

    await hass.config_entries.async_unload(entry.entry_id)
