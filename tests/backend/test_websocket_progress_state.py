"""P3.10 WebSocket user-state and calibration ACL tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package


async def _activate_package(hass: HomeAssistant, tmp_path: Path) -> None:
    runtime = hass.data[DOMAIN]["runtime"]
    package = create_package(
        tmp_path / "p3-10-ws.db",
        "p3-10-ws",
        active_item_ids=(ITEM_A,),
    )
    with sqlite3.connect(package) as connection:
        connection.execute("UPDATE facets SET language_tag = 'en' WHERE facet_key = 'prompt'")
        connection.execute("UPDATE facets SET language_tag = 'fr' WHERE facet_key = 'answer'")
        connection.commit()
    candidate = runtime.storage.paths.content_staging_dir / "generation-p3-10-ws.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p3-10-ws",
    )
    await runtime.storage.async_activate_content_generation(candidate)


async def test_progress_state_and_calibration_enforce_manage_progress_acl(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await _activate_package(hass, tmp_path)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "P3.10 owner",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await owner.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "P3.10 track",
            "pack_version_id": "locklearn:pack-version:p3-10-ws",
            "source_language": "en",
            "target_language": "fr",
            "explicit_card_keys": [card_identity(ITEM_A)[1]],
        }
    )
    track = await owner.receive_json()
    assert track["success"] is True
    track_id = track["result"]["track_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/calibration/sample",
            "profile_id": profile_id,
            "track_id": track_id,
            "sample_size": 20,
        }
    )
    sample = await owner.receive_json()
    assert sample["success"] is True
    assert sample["result"]["available_count"] == 1
    assert sample["result"]["cards"][0]["card_key"] == card_identity(ITEM_A)[1]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/progress/set_user_state",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card_identity(ITEM_A)[1],
            "user_state": "known_already",
        }
    )
    known = await owner.receive_json()
    assert known["success"] is True
    assert known["result"]["user_state"] == "known_already"
    assert known["result"]["seen_count"] == 0

    viewer = await hass_ws_client(hass, hass_read_only_access_token)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await owner.receive_json())["success"] is True

    for command in (
        {
            "type": "locklearn/calibration/sample",
            "profile_id": profile_id,
            "track_id": track_id,
            "sample_size": 20,
        },
        {
            "type": "locklearn/progress/set_user_state",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card_identity(ITEM_A)[1],
            "user_state": "active",
        },
    ):
        await viewer.send_json_auto_id(command)
        denied = await viewer.receive_json()
        assert denied["success"] is False
        assert denied["error"]["code"] == "locklearn/forbidden"

    await hass.config_entries.async_unload(entry.entry_id)
