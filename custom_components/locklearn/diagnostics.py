"""Privacy-redacted Home Assistant diagnostics for LockLearn."""

from __future__ import annotations

import asyncio
from collections import Counter
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONTENT_SCHEMA_VERSION,
    DATA_RUNTIME,
    DB_SCHEMA_VERSION,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .runtime import LockLearnRuntime
from .storage import StoragePaths
from .storage.database import validate_state_database_file
from .storage.lifecycle import StorageLifecycleManager

_REPAIR_CATEGORY_BY_TRANSLATION_KEY = {
    "dataset_sources_stale": "dataset_obsolete",
    "dataset_signature_invalid": "dataset_signature_invalid",
    "dataset_discovery_failed": "dataset_discovery_failed",
    "dataset_install_failed": "dataset_install_failed",
    "notification_target_unavailable": "notification_target_unresolved",
    "state_migration_failure": "migration_failed",
    "state_integrity_failure": "db_integrity_failure",
    "scheduler_configuration_infeasible": "scheduler_infeasible",
    "backup_cache_anomaly": "backup_cache_anomaly",
}


def _active_repair_categories(hass: HomeAssistant) -> dict[str, int]:
    registry = ir.async_get(hass)
    categories: Counter[str] = Counter()
    for issue in registry.issues.values():
        if issue.domain != DOMAIN:
            continue
        translation_key = issue.translation_key
        category = _REPAIR_CATEGORY_BY_TRANSLATION_KEY.get(
            "" if translation_key is None else str(translation_key)
        )
        if category is not None:
            categories[category] += 1
    return dict(sorted(categories.items()))


async def _unloaded_database_status(paths: StoragePaths) -> dict[str, object]:
    observed_state_schema: int | None = None
    if paths.state_db.is_file():
        try:
            observed_state_schema = await asyncio.to_thread(
                validate_state_database_file,
                paths.state_db,
            )
        except RuntimeError:
            observed_state_schema = None
    return {
        "state_schema_version": observed_state_schema,
        "content_schema_version": None,
        "migration_status": (
            "current"
            if observed_state_schema == DB_SCHEMA_VERSION
            else "unavailable"
        ),
        "integrity_status": "unavailable",
        "foreign_key_violation_count": None,
        "journal_mode": None,
        "profile_count": None,
        "dataset_count": None,
        "pack_count": None,
        "writer_initialized": False,
        "backup_active": False,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return only versions, aggregate counts/status, and redacted error categories."""
    domain_data = hass.data.get(DOMAIN, {})
    runtime = domain_data.get(DATA_RUNTIME)
    paths = StoragePaths.from_config_dir(hass.config.config_dir)
    lifecycle = StorageLifecycleManager(paths)

    if isinstance(runtime, LockLearnRuntime):
        database = await runtime.storage.async_redacted_diagnostic_status()
        datasets = await runtime.datasets.async_diagnostic_status()
        scheduler = runtime.scheduler_ha.diagnostic_status()
    else:
        database = await _unloaded_database_status(paths)
        datasets = {
            "official_dataset_count": 0,
            "installed_dataset_count": None,
            "update_available_count": None,
            "stale_dataset_count": None,
            "error_dataset_count": None,
            "error_types": (),
        }
        scheduler = {
            "listener_active": False,
            "configured_entity_count": None,
            "configured_routine_count": None,
        }

    usage = await lifecycle.async_usage()
    repair_categories = _active_repair_categories(hass)

    return {
        "versions": {
            "locklearn": INTEGRATION_VERSION,
            "home_assistant": HA_VERSION,
            "config_entry": entry.version,
            "expected_state_schema": DB_SCHEMA_VERSION,
            "expected_content_schema": CONTENT_SCHEMA_VERSION,
        },
        "database": database,
        "datasets": datasets,
        "scheduler": scheduler,
        "storage": {
            "state_bytes": usage.state_bytes,
            "content_cache_bytes": usage.content_cache_bytes,
            "asset_bytes": usage.asset_bytes,
            "recovery_snapshot_bytes": usage.recovery_snapshot_bytes,
            "backup_policy": usage.backup_policy,
            "backup_cache_anomaly_bytes": await lifecycle.async_backup_cache_anomaly_bytes(),
        },
        "errors": {
            "active_repair_count": sum(repair_categories.values()),
            "active_repair_types": repair_categories,
        },
    }
