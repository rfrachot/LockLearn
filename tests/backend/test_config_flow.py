"""Config-flow contract tests."""

from types import SimpleNamespace
from typing import cast

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn import async_migrate_entry
from custom_components.locklearn.config_flow import LockLearnConfigFlow
from custom_components.locklearn.const import (
    CONFIG_ENTRY_VERSION,
    CONF_PURGE_CONTENT_CACHE,
    CONF_UNINSTALL_DATA_POLICY,
    DEFAULT_UNINSTALL_DATA_POLICY,
    DOMAIN,
)
from custom_components.locklearn.storage import StoragePaths
from custom_components.locklearn.storage.lifecycle import UninstallDataPolicy


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
    assert result["options"] == {
        CONF_UNINSTALL_DATA_POLICY: DEFAULT_UNINSTALL_DATA_POLICY
    }

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


async def test_options_flow_persists_explicit_uninstall_policy(
    hass: HomeAssistant,
) -> None:
    """Storage retention is chosen explicitly before Config Entry removal."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={CONF_UNINSTALL_DATA_POLICY: DEFAULT_UNINSTALL_DATA_POLICY},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_UNINSTALL_DATA_POLICY: UninstallDataPolicy.DELETE_CONTENT_CACHE.value,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_UNINSTALL_DATA_POLICY] == (
        UninstallDataPolicy.DELETE_CONTENT_CACHE.value
    )


async def test_options_flow_purges_cache_offline_before_rebuild(
    hass: HomeAssistant,
    monkeypatch,
) -> None:
    """The explicit cache purge runs while no LockLearn runtime is open."""
    paths = StoragePaths.from_config_dir(hass.config.config_dir)
    paths.content_db.parent.mkdir(parents=True, exist_ok=True)
    paths.content_db.write_bytes(b"reconstructible-cache")

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={CONF_UNINSTALL_DATA_POLICY: DEFAULT_UNINSTALL_DATA_POLICY},
    )
    entry.add_to_hass(hass)

    setup_calls: list[str] = []

    async def fake_setup(entry_id: str) -> bool:
        setup_calls.append(entry_id)
        return True

    monkeypatch.setattr(hass.config_entries, "async_setup", fake_setup)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_UNINSTALL_DATA_POLICY: DEFAULT_UNINSTALL_DATA_POLICY,
            CONF_PURGE_CONTENT_CACHE: True,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert not paths.content_root.exists()
    assert setup_calls == [entry.entry_id]
