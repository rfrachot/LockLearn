"""LockLearn Home Assistant integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api.websocket import async_register_commands
from .const import DATA_RUNTIME, DATA_STATIC_REGISTERED, DOMAIN
from .ha_services import async_register_services, async_unregister_services
from .panel import async_register_panel, async_register_static_path, async_unregister_panel
from .runtime import LockLearnRuntime

type LockLearnConfigEntry = ConfigEntry

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_PLATFORMS = (Platform.UPDATE,)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register process-lifetime HTTP and WebSocket resources."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get(DATA_STATIC_REGISTERED):
        await async_register_static_path(hass)
        async_register_commands(hass)
        domain_data[DATA_STATIC_REGISTERED] = True
    return True


async def async_setup_entry(hass: HomeAssistant, entry: LockLearnConfigEntry) -> bool:
    """Set up LockLearn from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if DATA_RUNTIME in domain_data:
        return False
    runtime = await LockLearnRuntime.async_create(hass)
    domain_data[DATA_RUNTIME] = runtime
    async_register_services(hass)
    try:
        await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
        await async_register_panel(hass)
    except Exception:
        domain_data.pop(DATA_RUNTIME, None)
        async_unregister_services(hass)
        await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
        await runtime.async_close()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LockLearnConfigEntry) -> bool:
    """Unload a LockLearn config entry."""
    domain_data = hass.data.get(DOMAIN, {})
    runtime = domain_data.get(DATA_RUNTIME)
    if not await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        return False
    domain_data.pop(DATA_RUNTIME, None)
    async_unregister_services(hass)
    async_unregister_panel(hass)
    if isinstance(runtime, LockLearnRuntime):
        await runtime.async_close()
    return True
