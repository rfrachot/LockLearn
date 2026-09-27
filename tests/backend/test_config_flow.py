"""Config-flow contract tests."""

from types import SimpleNamespace
from typing import cast

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.locklearn import async_migrate_entry
from custom_components.locklearn.config_flow import LockLearnConfigFlow
from custom_components.locklearn.const import CONFIG_ENTRY_VERSION, DOMAIN


async def test_user_flow_creates_single_entry(hass: HomeAssistant) -> None:
    """The UI flow creates one entry without YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"create_personal_profile": True, "ui_language": "fr"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"create_personal_profile": True, "ui_language": "fr"}

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "single_instance_allowed"


async def test_config_entry_version_boundary_accepts_current_version(
    hass: HomeAssistant,
) -> None:
    """Config Entry versioning is explicit even before the first real migration."""
    assert LockLearnConfigFlow.VERSION == CONFIG_ENTRY_VERSION
    entry = cast(ConfigEntry, SimpleNamespace(version=CONFIG_ENTRY_VERSION))

    assert await async_migrate_entry(hass, entry) is True


async def test_config_entry_version_boundary_rejects_unknown_legacy_and_future_versions(
    hass: HomeAssistant,
) -> None:
    """No fake Config Entry migration path is invented for unsupported versions."""
    legacy = cast(ConfigEntry, SimpleNamespace(version=0))
    future = cast(ConfigEntry, SimpleNamespace(version=CONFIG_ENTRY_VERSION + 1))

    assert await async_migrate_entry(hass, legacy) is False
    assert await async_migrate_entry(hass, future) is False
