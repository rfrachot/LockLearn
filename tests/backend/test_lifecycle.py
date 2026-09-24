"""Home Assistant setup/unload lifecycle tests."""

from pathlib import Path

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN, PANEL_URL_PATH


async def test_setup_unload_and_reload_have_no_duplicate_panel(hass: HomeAssistant) -> None:
    """Every entry resource is removed or drained before reload."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert DATA_RUNTIME in hass.data[DOMAIN]
    assert PANEL_URL_PATH in hass.data["frontend_panels"]

    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    inventory = await runtime.storage.async_dataset_inventory()
    assert len(inventory) == 1
    assert inventory[0]["dataset_id"] == "locklearn:dataset:japanese-starter"
    assert inventory[0]["version"] == "1.0.0"
    assert inventory[0]["pack_version_ids"] == ("locklearn:pack-version:japanese-starter-1.0.0",)

    state_path = Path(runtime.storage.paths.state_db)
    assert state_path.is_file()
    assert "custom_components" not in state_path.parts
    initial_scheduler_time = await runtime.storage.repositories.settings.async_get(
        "scheduler_time_state_v1"
    )
    assert isinstance(initial_scheduler_time, dict)
    assert initial_scheduler_time["kind"] == "initial"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert DATA_RUNTIME not in hass.data[DOMAIN]
    assert PANEL_URL_PATH not in hass.data.get("frontend_panels", {})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert PANEL_URL_PATH in hass.data["frontend_panels"]
    reloaded_runtime = hass.data[DOMAIN][DATA_RUNTIME]
    reloaded_scheduler_time = await reloaded_runtime.storage.repositories.settings.async_get(
        "scheduler_time_state_v1"
    )
    assert isinstance(reloaded_scheduler_time, dict)
    assert reloaded_scheduler_time["kind"] == "restart"
    assert (
        reloaded_scheduler_time["high_watermark_utc"]
        >= initial_scheduler_time["high_watermark_utc"]
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
