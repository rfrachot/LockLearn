"""Home Assistant setup/unload lifecycle tests."""

from pathlib import Path

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn import async_remove_entry
from custom_components.locklearn.const import (
    CONF_UNINSTALL_DATA_POLICY,
    DATA_RUNTIME,
    DOMAIN,
    PANEL_URL_PATH,
)
from custom_components.locklearn.storage import StateMigrationError, StoragePaths
from custom_components.locklearn.storage.lifecycle import UninstallDataPolicy


async def test_setup_unload_and_reload_have_no_duplicate_panel(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Every entry resource is removed or drained before reload."""
    executor_calls: list[str] = []
    async_add_executor_job = hass.async_add_executor_job

    def record_executor_call(function, *args):
        executor_calls.append(getattr(function, "__name__", repr(function)))
        return async_add_executor_job(function, *args)

    monkeypatch.setattr(hass, "async_add_executor_job", record_executor_call)
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert DATA_RUNTIME in hass.data[DOMAIN]
    dispatcher = hass.data[DOMAIN]["notification_dispatcher"]
    assert dispatcher._unsub is not None
    assert {
        "load_runtime_dataset_definitions",
        "load_runtime_trust_store",
        "from_runtime",
        "load_runtime_source_freshness",
        "load_runtime_bundled_datasets",
    } <= set(executor_calls)
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
    assert "notification_dispatcher" not in hass.data[DOMAIN]
    assert PANEL_URL_PATH not in hass.data.get("frontend_panels", {})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert PANEL_URL_PATH in hass.data["frontend_panels"]
    reloaded_dispatcher = hass.data[DOMAIN]["notification_dispatcher"]
    assert reloaded_dispatcher is not dispatcher
    assert reloaded_dispatcher._unsub is not None
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
    assert "notification_dispatcher" not in hass.data[DOMAIN]


async def test_integrity_failure_creates_recovery_issue_without_runtime(
    hass: HomeAssistant,
) -> None:
    """Corrupt state never reaches the writer and is surfaced as a persistent Repair."""
    paths = StoragePaths.from_config_dir(hass.config.config_dir)
    paths.state_db.parent.mkdir(parents=True, exist_ok=True)
    paths.state_db.write_bytes(b"not-a-sqlite-database")

    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id) is False
    await hass.async_block_till_done()

    assert DATA_RUNTIME not in hass.data.get(DOMAIN, {})
    registry = ir.async_get(hass)
    assert any(
        issue.domain == DOMAIN and issue.issue_id == "state_integrity_failure"
        for issue in registry.issues.values()
    )
    assert paths.state_db.read_bytes() == b"not-a-sqlite-database"


async def test_remove_entry_applies_explicit_cache_only_policy(
    hass: HomeAssistant,
) -> None:
    """The HA removal hook preserves state unless its destructive option says otherwise."""
    paths = StoragePaths.from_config_dir(hass.config.config_dir)
    paths.state_db.parent.mkdir(parents=True, exist_ok=True)
    paths.state_db.write_bytes(b"state")
    paths.content_db.parent.mkdir(parents=True, exist_ok=True)
    paths.content_db.write_bytes(b"cache")

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={},
        options={
            CONF_UNINSTALL_DATA_POLICY: UninstallDataPolicy.DELETE_CONTENT_CACHE.value,
        },
    )

    await async_remove_entry(hass, entry)

    assert paths.state_db.is_file()
    assert not paths.content_root.exists()


async def test_migration_failure_creates_repair_without_runtime(
    hass: HomeAssistant,
    monkeypatch,
) -> None:
    """A failed migration is surfaced distinctly from integrity failure."""

    async def fail_create(_hass: HomeAssistant):
        raise StateMigrationError("migration failed")

    monkeypatch.setattr(
        "custom_components.locklearn.LockLearnRuntime.async_create",
        fail_create,
    )
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id) is False
    await hass.async_block_till_done()

    registry = ir.async_get(hass)
    migration_issues = [
        issue
        for issue in registry.issues.values()
        if issue.domain == DOMAIN and issue.issue_id == "state_migration_failure"
    ]
    assert len(migration_issues) == 1
    assert migration_issues[0].translation_key == "state_migration_failure"
    assert DATA_RUNTIME not in hass.data.get(DOMAIN, {})


async def test_backup_cache_anomaly_creates_warning_repair(
    hass: HomeAssistant,
) -> None:
    """Unexpected reconstructible bytes under persistent state are reported."""
    paths = StoragePaths.from_config_dir(hass.config.config_dir)
    anomalous_cache = paths.state_root / "cache"
    anomalous_cache.mkdir(parents=True, exist_ok=True)
    (anomalous_cache / "orphan.bin").write_bytes(b"cache")

    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = ir.async_get(hass)
    issues = [
        issue
        for issue in registry.issues.values()
        if issue.domain == DOMAIN and issue.issue_id == "backup_cache_anomaly"
    ]
    assert len(issues) == 1
    assert issues[0].translation_key == "backup_cache_anomaly"
    assert issues[0].severity is ir.IssueSeverity.WARNING

    await hass.config_entries.async_unload(entry.entry_id)
