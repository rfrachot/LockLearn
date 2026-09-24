"""P5.1 bundled panel registration and cache-buster tests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.locklearn.const import INTEGRATION_VERSION, STATIC_URL_PATH
from custom_components.locklearn import panel


async def test_panel_module_url_uses_release_and_bundle_hash(
    hass: HomeAssistant,
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}

    async def register_panel(_hass: HomeAssistant, **kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(panel.panel_custom, "async_register_panel", register_panel)

    await panel.async_register_panel(hass)

    asset = Path(panel.__file__).parent / "frontend" / "locklearn-panel.js"
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
    assert captured["module_url"] == (
        f"{STATIC_URL_PATH}/locklearn-panel.js?v={INTEGRATION_VERSION}-{digest}"
    )
    assert captured["webcomponent_name"] == "locklearn-panel"
    assert captured["frontend_url_path"] == "locklearn"
    assert captured["require_admin"] is False
