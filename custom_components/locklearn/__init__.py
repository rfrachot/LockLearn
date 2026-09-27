"""LockLearn Home Assistant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.typing import ConfigType

from .api.websocket import async_register_commands
from .const import (
    CONF_UNINSTALL_DATA_POLICY,
    CONFIG_ENTRY_VERSION,
    DATA_RUNTIME,
    DATA_STATIC_REGISTERED,
    DEFAULT_UNINSTALL_DATA_POLICY,
    DOMAIN,
)
from .ha_services import async_register_services, async_unregister_services
from .panel import async_register_panel, async_register_static_path, async_unregister_panel
from .runtime import LockLearnRuntime
from .storage import StateIntegrityError, StoragePaths
from .storage.lifecycle import StorageLifecycleManager, UninstallDataPolicy

type LockLearnConfigEntry = ConfigEntry

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_PLATFORMS = (Platform.UPDATE,)
_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: LockLearnConfigEntry) -> bool:
    """Validate or migrate the LockLearn Config Entry schema."""
    if entry.version == CONFIG_ENTRY_VERSION:
        return True
    if entry.version > CONFIG_ENTRY_VERSION:
        _LOGGER.error(
            "LockLearn Config Entry version %s is newer than supported version %s",
            entry.version,
            CONFIG_ENTRY_VERSION,
        )
        return False
    _LOGGER.error(
        "No LockLearn Config Entry migration path from version %s to %s",
        entry.version,
        CONFIG_ENTRY_VERSION,
    )
    return False


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
    try:
        runtime = await LockLearnRuntime.async_create(hass)
    except StateIntegrityError:
        manager = StorageLifecycleManager(StoragePaths.from_config_dir(hass.config.config_dir))
        snapshots = await manager.async_valid_recovery_snapshots()
        ir.async_create_issue(
            hass,
            DOMAIN,
            "state_integrity_failure",
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="state_integrity_failure",
            translation_placeholders={"snapshot_count": str(len(snapshots))},
        )
        return False
    ir.async_delete_issue(hass, DOMAIN, "state_integrity_failure")
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


async def async_remove_entry(
    hass: HomeAssistant,
    entry: LockLearnConfigEntry,
) -> None:
    """Apply the user's explicit retention policy after Config Entry removal."""
    raw_policy = str(
        entry.options.get(
            CONF_UNINSTALL_DATA_POLICY,
            DEFAULT_UNINSTALL_DATA_POLICY,
        )
    )
    try:
        policy = UninstallDataPolicy(raw_policy)
    except ValueError:
        _LOGGER.error(
            "Unknown LockLearn uninstall policy %s; preserving all user data",
            raw_policy,
        )
        policy = UninstallDataPolicy.KEEP_USER_DATA
    manager = StorageLifecycleManager(StoragePaths.from_config_dir(hass.config.config_dir))
    await manager.async_apply_uninstall_policy(policy)
