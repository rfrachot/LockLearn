"""Resolve stable HA device identities to current notification routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify


class TargetUnavailableError(LookupError):
    """Raised when a stable target has no usable current notify route."""


@dataclass(frozen=True, slots=True)
class NotifyRoute:
    """Ephemeral delivery route resolved from a stable device registry id."""

    device_registry_id: str
    service: str
    target: dict[str, Any] | None
    config_entry_id: str


def legacy_mobile_app_service(device_name: str) -> str:
    """Reproduce HA's dynamic legacy mobile_app target service name."""
    return slugify(f"mobile_app_{device_name}")


async def async_resolve_notify_route(hass: HomeAssistant, device_registry_id: str) -> NotifyRoute:
    """Resolve on every send so renames never become target identity."""
    device = dr.async_get(hass).async_get(device_registry_id)
    if device is None or device.disabled:
        raise TargetUnavailableError(device_registry_id)

    entity_registry = er.async_get(hass)
    notify_entities = sorted(
        (
            entry
            for entry in er.async_entries_for_device(
                entity_registry, device_registry_id, include_disabled_entities=False
            )
            if entry.domain == "notify" and entry.platform == "mobile_app"
        ),
        key=lambda entry: entry.entity_id,
    )
    if notify_entities:
        entry = notify_entities[0]
        config_entry_id = entry.config_entry_id or next(iter(device.config_entries), None)
        if config_entry_id is None:
            raise TargetUnavailableError(device_registry_id)
        return NotifyRoute(
            device_registry_id=device_registry_id,
            service="notify.send_message",
            target={"entity_id": entry.entity_id},
            config_entry_id=config_entry_id,
        )

    for config_entry_id in sorted(device.config_entries):
        config_entry = hass.config_entries.async_get_entry(config_entry_id)
        if config_entry is None or config_entry.domain != "mobile_app":
            continue
        device_name = config_entry.data.get("device_name")
        if not isinstance(device_name, str):
            continue
        service = legacy_mobile_app_service(device_name)
        if hass.services.has_service("notify", service):
            return NotifyRoute(
                device_registry_id=device_registry_id,
                service=f"notify.{service}",
                target=None,
                config_entry_id=config_entry_id,
            )

    raise TargetUnavailableError(device_registry_id)
