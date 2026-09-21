"""Per-config-entry LockLearn runtime."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant

from .core.operations import OperationRegistry
from .core.sessions import SessionService
from .storage import SQLiteStorage, StoragePaths


@dataclass(slots=True)
class LockLearnRuntime:
    """Own all resources that must be drained on reload/unload."""

    storage: SQLiteStorage
    sessions: SessionService
    operations: OperationRegistry

    @classmethod
    async def async_create(cls, hass: HomeAssistant) -> LockLearnRuntime:
        """Create and open a runtime from HA's persistent config directory."""
        storage = SQLiteStorage(StoragePaths.from_config_dir(hass.config.config_dir))
        await storage.async_open()
        return cls(
            storage=storage,
            sessions=SessionService(storage),
            operations=OperationRegistry(),
        )

    async def async_close(self) -> None:
        """Cancel callbacks/operations, then drain and close SQLite."""
        self.sessions.close()
        await self.operations.async_close()
        await self.storage.async_close()
