"""Home Assistant update entities for official LockLearn datasets."""

from __future__ import annotations

import hashlib
from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_RUNTIME, DOMAIN
from .datasets.manager import DatasetDefinition, DatasetManager, DatasetStatus
from .runtime import LockLearnRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create one update entity for each official dataset known to this integration."""
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    if not isinstance(runtime, LockLearnRuntime):
        return
    async_add_entities(
        LockLearnDatasetUpdateEntity(runtime.datasets, definition)
        for definition in runtime.datasets.definitions
    )


class LockLearnDatasetUpdateEntity(UpdateEntity):
    """Expose one independently updatable official dataset."""

    _attr_has_entity_name = True
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES

    def __init__(self, manager: DatasetManager, definition: DatasetDefinition) -> None:
        self._manager = manager
        self._definition = definition
        suffix = hashlib.sha256(definition.dataset_id.encode("utf-8")).hexdigest()[:16]
        self._attr_unique_id = f"dataset_{suffix}"
        self._attr_name = definition.name
        self._attr_title = definition.name
        self._status: DatasetStatus | None = None
        self._apply_status(None)

    async def async_added_to_hass(self) -> None:
        """Load installed state locally without making setup depend on the network."""
        self._apply_status(await self._manager.async_status(self._definition.dataset_id))

    async def async_update(self) -> None:
        """Refresh discovery while preserving installed state if the network fails."""
        await self._manager.async_refresh(self._definition.dataset_id)
        self._apply_status(await self._manager.async_status(self._definition.dataset_id))

    async def async_install(
        self,
        version: str | None,
        backup: bool,
        **kwargs: Any,
    ) -> None:
        """Install a fully verified prebuilt dataset artifact."""
        await self._manager.async_install(self._definition.dataset_id, version=version)
        self._apply_status(await self._manager.async_status(self._definition.dataset_id))

    async def async_release_notes(self) -> str | None:
        """Return full release notes from the discovered release metadata."""
        if self._status is None or self._status.latest is None:
            return None
        return self._status.latest.changelog or None

    def _apply_status(self, status: DatasetStatus | None) -> None:
        self._status = status
        installed = None if status is None else status.installed
        latest = None if status is None else status.latest
        self._attr_installed_version = None if installed is None else installed.version
        self._attr_latest_version = None if latest is None else latest.version
        self._attr_release_summary = None if latest is None else latest.changelog or None
        self._attr_release_url = None if latest is None else latest.release_url
        self._attr_extra_state_attributes = {
            "dataset_id": self._definition.dataset_id,
            "dataset_state": None if status is None else status.state,
            "source_age_days": None if status is None else status.source_age_days,
            "stale_sources": [] if status is None else list(status.stale_sources),
            "cache_bytes": 0 if status is None else status.cache_bytes,
            "licenses": [] if installed is None else list(installed.licenses),
            "sources": []
            if installed is None
            else [
                {
                    "source_id": source["source_id"],
                    "upstream_version": source["upstream_version"],
                    "upstream_date": source["upstream_date"],
                    "retrieved_at": source["retrieved_at"],
                }
                for source in installed.sources
            ],
        }
