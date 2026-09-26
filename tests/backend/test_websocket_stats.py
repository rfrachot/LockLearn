"""P3.13 WebSocket statistics ACL tests."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN


async def test_stats_get_is_profile_private_and_viewer_readable(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "P3.13 stats",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await owner.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    viewer = await hass_ws_client(hass, hass_read_only_access_token)
    await viewer.send_json_auto_id(
        {
            "type": "locklearn/stats/get",
            "profile_id": profile_id,
        }
    )
    hidden = await viewer.receive_json()
    assert hidden["success"] is False
    assert hidden["error"]["code"] == "locklearn/not_found"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await owner.receive_json())["success"] is True

    await viewer.send_json_auto_id(
        {
            "type": "locklearn/stats/get",
            "profile_id": profile_id,
        }
    )
    visible = await viewer.receive_json()
    assert visible["success"] is True
    assert visible["result"]["profile_id"] == profile_id
    assert visible["result"]["due_today"] == 0
    assert visible["result"]["recent_verified_accuracy"]["total"] == 0
    assert visible["result"]["streak"]["today"]["status"] == "neutral"

    await hass.config_entries.async_unload(entry.entry_id)
