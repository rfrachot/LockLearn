"""Public notification-target configuration for beta field validation."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN


async def test_owner_can_discover_create_and_update_companion_target(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    companion = MockConfigEntry(
        domain="mobile_app",
        data={
            "device_name": "Beta Test Phone",
            "os_name": "Android",
        },
    )
    companion.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=companion.entry_id,
        identifiers={("mobile_app", "beta-test-device")},
        name="Beta Test Phone",
    )

    async def handle_service(_call: ServiceCall) -> None:
        return None

    hass.services.async_register("notify", "mobile_app_beta_test_phone", handle_service)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Beta target profile",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await owner.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/targets/discover",
            "profile_id": profile_id,
        }
    )
    discovered = await owner.receive_json()
    assert discovered["success"] is True
    candidate = next(
        item
        for item in discovered["result"]["items"]
        if item["device_registry_id"] == device.id
    )
    assert candidate == {
        "device_registry_id": device.id,
        "friendly_name": "Beta Test Phone",
        "platform": "android",
        "route_available": True,
        "supports_platform_data": True,
        "configured_target_id": None,
    }

    await owner.send_json_auto_id(
        {
            "type": "locklearn/targets/create",
            "profile_id": profile_id,
            "device_registry_id": device.id,
            "capabilities": {
                "action_data": "supported",
                "replace_by_tag": "supported",
                "visible_actions": 3,
            },
            "shared_device": False,
            "lockscreen_visibility": "private",
            "minimum_gap_seconds": 600,
            "maximum_notifications_per_hour": 2,
            "daily_push_budget": 4,
        }
    )
    created = await owner.receive_json()
    assert created["success"] is True
    target = created["result"]
    target_id = target["target_id"]
    assert target["device_registry_id"] == device.id
    assert target["platform"] == "android"
    assert target["capabilities"] == {
        "action_data": "supported",
        "replace_by_tag": "supported",
        "visible_actions": 3,
    }
    assert target["shared_device"] is False
    assert target["daily_push_budget"] == 4

    await owner.send_json_auto_id(
        {
            "type": "locklearn/targets/list",
            "profile_id": profile_id,
        }
    )
    listed = await owner.receive_json()
    assert listed["success"] is True
    assert [item["target_id"] for item in listed["result"]["items"]] == [target_id]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/targets/discover",
            "profile_id": profile_id,
        }
    )
    rediscovered = await owner.receive_json()
    candidate = next(
        item
        for item in rediscovered["result"]["items"]
        if item["device_registry_id"] == device.id
    )
    assert candidate["configured_target_id"] == target_id

    await owner.send_json_auto_id(
        {
            "type": "locklearn/targets/update",
            "profile_id": profile_id,
            "target_id": target_id,
            "friendly_name": "Shared beta phone",
            "shared_device": True,
            "lockscreen_visibility": "secret",
            "daily_push_budget": 2,
        }
    )
    updated = await owner.receive_json()
    assert updated["success"] is True
    assert updated["result"]["target_id"] == target_id
    assert updated["result"]["device_registry_id"] == device.id
    assert updated["result"]["friendly_name"] == "Shared beta phone"
    assert updated["result"]["shared_device"] is True
    assert updated["result"]["lockscreen_visibility"] == "secret"
    assert updated["result"]["daily_push_budget"] == 2
    assert updated["result"]["capabilities"] == target["capabilities"]

    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    persisted = await runtime.storage.repositories.notification_targets.async_get(target_id)
    assert persisted is not None
    assert persisted["device_registry_id"] == device.id
    assert persisted["last_resolved_notify_service"] == "notify.mobile_app_beta_test_phone"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/targets/create",
            "profile_id": profile_id,
            "device_registry_id": device.id,
        }
    )
    duplicate = await owner.receive_json()
    assert duplicate["success"] is False
    assert duplicate["error"]["code"] == "locklearn/invalid_request"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "editor",
        }
    )
    assert (await owner.receive_json())["success"] is True

    editor = await hass_ws_client(hass, hass_read_only_access_token)
    for payload in (
        {"type": "locklearn/targets/discover", "profile_id": profile_id},
        {
            "type": "locklearn/targets/create",
            "profile_id": profile_id,
            "device_registry_id": device.id,
        },
        {
            "type": "locklearn/targets/update",
            "profile_id": profile_id,
            "target_id": target_id,
            "friendly_name": "Denied",
        },
    ):
        await editor.send_json_auto_id(payload)
        denied = await editor.receive_json()
        assert denied["success"] is False
        assert denied["error"]["code"] == "locklearn/forbidden"

    await hass.config_entries.async_unload(entry.entry_id)
