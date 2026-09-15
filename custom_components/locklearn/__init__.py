"""LockLearn Home Assistant integration bootstrap."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


type LockLearnConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: LockLearnConfigEntry) -> bool:
    """Set up LockLearn from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LockLearnConfigEntry) -> bool:
    """Unload a LockLearn config entry."""
    domain_data = hass.data.get(DOMAIN)
    if domain_data is not None:
        domain_data.pop(entry.entry_id, None)
        if not domain_data:
            hass.data.pop(DOMAIN, None)
    return True
