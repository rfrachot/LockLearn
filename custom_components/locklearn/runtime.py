"""Per-config-entry LockLearn runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .core.operations import OperationRegistry
from .core.sessions import SessionService
from .datasets.manager import (
    DatasetManager,
    load_runtime_dataset_definitions,
    load_runtime_source_freshness,
    load_runtime_trust_store,
)
from .datasets.policy import OfficialRegistryPolicy
from .datasets.transport import HomeAssistantDatasetTransport
from .storage import SQLiteStorage, StoragePaths


@dataclass(slots=True)
class LockLearnRuntime:
    """Own all resources that must be drained on reload/unload."""

    storage: SQLiteStorage
    sessions: SessionService
    operations: OperationRegistry
    datasets: DatasetManager

    @classmethod
    async def async_create(cls, hass: HomeAssistant) -> LockLearnRuntime:
        """Create and open a runtime from HA's persistent config directory."""
        storage = SQLiteStorage(StoragePaths.from_config_dir(hass.config.config_dir))
        await storage.async_open()

        async def report_issue(
            issue_id: str,
            translation_key: str,
            placeholders: Mapping[str, str],
        ) -> None:
            severity = (
                ir.IssueSeverity.WARNING
                if translation_key in {"dataset_discovery_failed", "dataset_sources_stale"}
                else ir.IssueSeverity.ERROR
            )
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                is_persistent=True,
                severity=severity,
                translation_key=translation_key,
                translation_placeholders=dict(placeholders),
            )

        async def clear_issue(issue_id: str) -> None:
            ir.async_delete_issue(hass, DOMAIN, issue_id)

        try:
            datasets = DatasetManager(
                storage=storage,
                transport=HomeAssistantDatasetTransport(hass),
                definitions=load_runtime_dataset_definitions(),
                trust_store=load_runtime_trust_store(),
                policy=OfficialRegistryPolicy.from_runtime(),
                freshness_targets=load_runtime_source_freshness(),
                issue_callback=report_issue,
                issue_clear_callback=clear_issue,
            )
            return cls(
                storage=storage,
                sessions=SessionService(storage),
                operations=OperationRegistry(),
                datasets=datasets,
            )
        except Exception:
            await storage.async_close()
            raise

    async def async_close(self) -> None:
        """Cancel callbacks/operations, then drain and close SQLite."""
        self.sessions.close()
        await self.operations.async_close()
        await self.storage.async_close()
