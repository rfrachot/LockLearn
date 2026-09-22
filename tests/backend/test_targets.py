"""Stable device identity and dynamic notify-route tests."""

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.notifications.targets import (
    TargetUnavailableError,
    async_resolve_notify_route,
)


async def test_device_registry_id_survives_mobile_app_rename(hass: HomeAssistant) -> None:
    """A rename changes the ephemeral service, never the persisted identity."""
    entry = MockConfigEntry(domain="mobile_app", data={"device_name": "Old Phone"})
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("mobile_app", "native-device-id")},
        name="Old Phone",
    )

    async def handle_service(call: ServiceCall) -> None:
        return None

    hass.services.async_register("notify", "mobile_app_old_phone", handle_service)
    first = await async_resolve_notify_route(hass, device.id)
    assert first.device_registry_id == device.id
    assert first.service == "notify.mobile_app_old_phone"
    assert first.supports_platform_data

    hass.services.async_remove("notify", "mobile_app_old_phone")
    hass.config_entries.async_update_entry(entry, data={"device_name": "Learning Phone"})
    hass.services.async_register("notify", "mobile_app_learning_phone", handle_service)
    second = await async_resolve_notify_route(hass, device.id)

    assert second.device_registry_id == first.device_registry_id
    assert second.service == "notify.mobile_app_learning_phone"
    assert second.service != first.service


async def test_actionable_route_prefers_mobile_app_service_over_notify_entity(
    hass: HomeAssistant,
) -> None:
    """Companion data cannot be sent through generic notify.send_message."""
    entry = MockConfigEntry(domain="mobile_app", data={"device_name": "Learning Phone"})
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("mobile_app", "native-device-id")},
        name="Learning Phone",
    )
    er.async_get(hass).async_get_or_create(
        "notify",
        "mobile_app",
        "native-device-id",
        config_entry=entry,
        device_id=device.id,
        suggested_object_id="learning_phone",
    )

    async def handle_service(call: ServiceCall) -> None:
        return None

    hass.services.async_register("notify", "mobile_app_learning_phone", handle_service)
    route = await async_resolve_notify_route(hass, device.id)

    assert route.service == "notify.mobile_app_learning_phone"
    assert route.target is None
    assert route.supports_platform_data


async def test_notify_entity_is_plain_message_fallback_only(hass: HomeAssistant) -> None:
    """Fail closed when an actionable target has no data-capable route."""
    entry = MockConfigEntry(domain="mobile_app", data={"device_name": "Missing Service"})
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("mobile_app", "native-device-id")},
        name="Missing Service",
    )
    entity = er.async_get(hass).async_get_or_create(
        "notify",
        "mobile_app",
        "native-device-id",
        config_entry=entry,
        device_id=device.id,
        suggested_object_id="missing_service",
    )

    with pytest.raises(TargetUnavailableError):
        await async_resolve_notify_route(hass, device.id)

    route = await async_resolve_notify_route(hass, device.id, require_platform_data=False)
    assert route.service == "notify.send_message"
    assert route.target == {"entity_id": entity.entity_id}
    assert not route.supports_platform_data
