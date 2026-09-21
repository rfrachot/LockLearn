"""Bundled custom-panel registration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    INTEGRATION_VERSION,
    PANEL_COMPONENT_NAME,
    PANEL_URL_PATH,
    STATIC_URL_PATH,
)


async def async_register_static_path(hass: HomeAssistant) -> None:
    """Serve the immutable bundled frontend artifact once per HA process."""
    asset = Path(__file__).parent / "frontend" / "locklearn-panel.js"
    if not await hass.async_add_executor_job(asset.is_file):
        raise FileNotFoundError(f"Bundled LockLearn panel is missing: {asset}")
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL_PATH, str(asset.parent), True)]
    )


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the sidebar panel with a version cache-buster."""
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_COMPONENT_NAME,
        sidebar_title="LockLearn",
        sidebar_icon="mdi:school",
        module_url=f"{STATIC_URL_PATH}/locklearn-panel.js?v={INTEGRATION_VERSION}",
        require_admin=False,
    )


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the mutable panel registration on unload."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
