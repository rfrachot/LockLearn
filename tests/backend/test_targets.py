"""Stable device identity and dynamic notify-route tests."""

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.notifications.targets import async_resolve_notify_route


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

    hass.services.async_remove("notify", "mobile_app_old_phone")
    hass.config_entries.async_update_entry(entry, data={"device_name": "Learning Phone"})
    hass.services.async_register("notify", "mobile_app_learning_phone", handle_service)
    second = await async_resolve_notify_route(hass, device.id)

    assert second.device_registry_id == first.device_registry_id
    assert second.service == "notify.mobile_app_learning_phone"
    assert second.service != first.service
