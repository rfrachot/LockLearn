"""Home Assistant backup lifecycle hooks."""

from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant

from .const import DATA_RUNTIME, DOMAIN
from .runtime import LockLearnRuntime

BACKUP_HOOK_TIMEOUT_SECONDS = 10


def _runtime(hass: HomeAssistant) -> LockLearnRuntime | None:
    runtime = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    return runtime if isinstance(runtime, LockLearnRuntime) else None


async def async_pre_backup(hass: HomeAssistant) -> None:
    """Pause user writes and checkpoint state.db before HA archives config."""
    runtime = _runtime(hass)
    if runtime is None:
        return
    async with asyncio.timeout(BACKUP_HOOK_TIMEOUT_SECONDS):
        await runtime.storage.async_prepare_ha_backup()


async def async_post_backup(hass: HomeAssistant) -> None:
    """Always resume writes after HA backup completion/failure."""
    runtime = _runtime(hass)
    if runtime is not None:
        await runtime.storage.async_finish_ha_backup()
