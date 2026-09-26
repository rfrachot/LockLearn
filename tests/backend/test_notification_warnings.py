"""P4.7 dashboard warning surface tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
from custom_components.locklearn.storage import NotificationTargetRecord


async def test_unrecorded_mobile_response_warning_is_private_and_expiry_based(
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
            "name": "P4.7 warnings",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    created = await owner.receive_json()
    assert created["success"] is True
    profile_id = created["result"]["profile_id"]

    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    now = datetime.now(UTC)
    await runtime.storage.repositories.notification_targets.async_insert(
        NotificationTargetRecord(
            target_id="target-warning",
            profile_id=profile_id,
            device_registry_id="device-warning",
            platform="android",
            friendly_name="Warning phone",
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )
    interaction = await runtime.notification_interactions.async_create(
        profile_id=profile_id,
        target_id="target-warning",
        stage="prompt",
        expires_at=now + timedelta(minutes=5),
    )
    expired_at = now + timedelta(minutes=6)
    consumed = await runtime.storage.repositories.notification_interactions.async_consume(
        token=interaction.token,
        action_id="late-action",
        actor_user_id=None,
        action_at_utc=expired_at.isoformat(),
    )
    assert consumed.disposition == "expired"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/notifications/unrecorded_responses",
            "profile_id": profile_id,
        }
    )
    visible = await owner.receive_json()
    assert visible["success"] is True
    assert visible["result"]["warning"] is True
    assert visible["result"]["message_key"] == "recent_unrecorded_mobile_responses"
    assert visible["result"]["count"] == 1
    assert visible["result"]["items"][0]["target_id"] == "target-warning"

    viewer = await hass_ws_client(hass, hass_read_only_access_token)
    await viewer.send_json_auto_id(
        {
            "type": "locklearn/notifications/unrecorded_responses",
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
            "type": "locklearn/notifications/unrecorded_responses",
            "profile_id": profile_id,
        }
    )
    shared = await viewer.receive_json()
    assert shared["success"] is True
    assert shared["result"]["count"] == 1

    await hass.config_entries.async_unload(entry.entry_id)
