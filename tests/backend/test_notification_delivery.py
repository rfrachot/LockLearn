"""P4.7 Home Assistant notification delivery tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.notifications.capabilities import Capability, TargetCapabilities
from custom_components.locklearn.notifications.delivery import (
    NotificationDeliveryError,
    NotificationDeliveryService,
)
from custom_components.locklearn.notifications.renderers import NotificationRenderer
from custom_components.locklearn.storage import (
    NotificationTargetRecord,
    ProfileRecord,
    SQLiteStorage,
    StoragePaths,
)


async def _storage(tmp_path: Path) -> SQLiteStorage:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC).isoformat()
    await storage.repositories.profiles.async_insert(
        ProfileRecord(
            profile_id="profile-1",
            name="Renaud",
            preset="standard",
            timezone="Europe/Paris",
            created_at_utc=now,
            updated_at_utc=now,
        )
    )
    return storage


async def test_actionable_delivery_resolves_dynamic_mobile_app_service(
    hass: HomeAssistant,
    tmp_path: Path,
) -> None:
    storage = await _storage(tmp_path)
    try:
        entry = MockConfigEntry(domain="mobile_app", data={"device_name": "Learning Phone"})
        entry.add_to_hass(hass)
        device = dr.async_get(hass).async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("mobile_app", "device-1")},
            name="Learning Phone",
        )
        now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC).isoformat()
        await storage.repositories.notification_targets.async_insert(
            NotificationTargetRecord(
                target_id="target-1",
                profile_id="profile-1",
                device_registry_id=device.id,
                platform="android",
                friendly_name="Learning Phone",
                capabilities={
                    "action_data": "supported",
                    "visible_actions": 3,
                },
                created_at_utc=now,
                updated_at_utc=now,
            )
        )

        calls: list[ServiceCall] = []

        async def handle_service(call: ServiceCall) -> None:
            calls.append(call)

        hass.services.async_register("notify", "mobile_app_learning_phone", handle_service)

        renderer = NotificationRenderer()
        rendered = renderer.render_learning_prompt(
            profile_id="profile-1",
            profile_name="Renaud",
            target_id="target-1",
            tag="locklearn:slot-1",
            prompt="休",
            answer="repos",
            token="token-1",
            capabilities=TargetCapabilities(
                device_registry_id=device.id,
                platform="android",
                action_data=Capability.SUPPORTED,
                visible_actions=3,
            ),
        )
        delivery = NotificationDeliveryService(
            hass,
            storage.repositories.notification_targets,
        )
        route = await delivery.async_send(rendered)

        assert route.service == "notify.mobile_app_learning_phone"
        assert len(calls) == 1
        assert calls[0].data["message"] == "休"
        assert len(calls[0].data["data"]["actions"]) == 2

        target = await storage.repositories.notification_targets.async_get("target-1")
        assert target is not None
        assert target["last_resolved_notify_service"] == "notify.mobile_app_learning_phone"
    finally:
        await storage.async_close()


async def test_direct_exposure_can_use_plain_notify_entity_fallback(
    hass: HomeAssistant,
    tmp_path: Path,
) -> None:
    storage = await _storage(tmp_path)
    try:
        entry = MockConfigEntry(domain="mobile_app", data={"device_name": "No Dynamic Service"})
        entry.add_to_hass(hass)
        device = dr.async_get(hass).async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("mobile_app", "device-plain")},
            name="No Dynamic Service",
        )
        entity = er.async_get(hass).async_get_or_create(
            "notify",
            "mobile_app",
            "device-plain",
            config_entry=entry,
            device_id=device.id,
            suggested_object_id="plain_phone",
        )
        now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC).isoformat()
        await storage.repositories.notification_targets.async_insert(
            NotificationTargetRecord(
                target_id="target-plain",
                profile_id="profile-1",
                device_registry_id=device.id,
                platform="android",
                friendly_name="Plain Phone",
                created_at_utc=now,
                updated_at_utc=now,
            )
        )

        calls: list[ServiceCall] = []

        async def handle_service(call: ServiceCall) -> None:
            calls.append(call)

        hass.services.async_register("notify", "send_message", handle_service)

        rendered = NotificationRenderer().render_learning_prompt(
            profile_id="profile-1",
            profile_name="Renaud",
            target_id="target-plain",
            tag="locklearn:plain",
            prompt="休",
            answer="repos",
            token="unused",
            capabilities=TargetCapabilities(
                device_registry_id=device.id,
                platform="android",
            ),
        )
        route = await NotificationDeliveryService(
            hass,
            storage.repositories.notification_targets,
        ).async_send(rendered)

        assert route.service == "notify.send_message"
        assert route.target == {"entity_id": entity.entity_id}
        assert len(calls) == 1
        assert calls[0].data == {
            "title": "LockLearn",
            "message": "休\n\nrepos",
        }
    finally:
        await storage.async_close()


async def test_unavailable_target_reports_repair_and_does_not_deliver(
    hass: HomeAssistant,
    tmp_path: Path,
) -> None:
    storage = await _storage(tmp_path)
    issues: list[tuple[str, str, dict[str, str]]] = []
    cleared: list[str] = []

    async def issue(
        issue_id: str,
        key: str,
        placeholders: Any,
    ) -> None:
        issues.append((issue_id, key, dict(placeholders)))

    async def clear(issue_id: str) -> None:
        cleared.append(issue_id)

    try:
        now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC).isoformat()
        await storage.repositories.notification_targets.async_insert(
            NotificationTargetRecord(
                target_id="target-missing",
                profile_id="profile-1",
                device_registry_id="missing-device",
                platform="android",
                friendly_name="Missing Phone",
                created_at_utc=now,
                updated_at_utc=now,
            )
        )
        rendered = NotificationRenderer().render_learning_prompt(
            profile_id="profile-1",
            profile_name="Renaud",
            target_id="target-missing",
            tag="locklearn:missing",
            prompt="休",
            answer="repos",
            token="unused",
            capabilities=TargetCapabilities(
                device_registry_id="missing-device",
                platform="android",
            ),
        )
        delivery = NotificationDeliveryService(
            hass,
            storage.repositories.notification_targets,
            issue_callback=issue,
            issue_clear_callback=clear,
        )

        with pytest.raises(NotificationDeliveryError, match="route is unavailable"):
            await delivery.async_send(rendered)

        assert issues == [
            (
                "notification_target_unavailable_target-missing",
                "notification_target_unavailable",
                {
                    "target_id": "target-missing",
                    "friendly_name": "Missing Phone",
                },
            )
        ]
        assert cleared == []
        target = await storage.repositories.notification_targets.async_get("target-missing")
        assert target is not None
        assert target["last_resolved_notify_service"] is None
    finally:
        await storage.async_close()
