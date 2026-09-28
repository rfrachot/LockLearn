"""P6.11 public-API V1 acceptance smoke on the bundled starter."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN

STARTER_DATASET_ID = "locklearn:dataset:japanese-starter"
STARTER_PACK_VERSION_ID = "locklearn:pack-version:japanese-starter-1.0.0"


async def test_fresh_starter_public_api_acceptance(
    hass: HomeAssistant,
    hass_ws_client: Any,
) -> None:
    """Exercise first-run starter -> Profile -> Track -> 20-card resumable session."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    owner = await hass_ws_client(hass)

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Adrien",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    created_profile = await owner.receive_json()
    assert created_profile["success"] is True
    profile_id = created_profile["result"]["profile_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/update",
            "profile_id": profile_id,
            "settings_patch": {
                "max_new_per_day_cards": 20,
                "session_length_cards": 20,
                "scheduler": {
                    "active_windows": [
                        {"start": "08:00", "end": "20:00"},
                    ]
                },
            },
        }
    )
    configured_profile = await owner.receive_json()
    assert configured_profile["success"] is True
    assert configured_profile["result"]["settings"]["session_length_cards"] == 20
    assert configured_profile["result"]["settings"]["max_new_per_day_cards"] == 20

    await owner.send_json_auto_id({"type": "locklearn/packs/list", "limit": 20})
    packs = await owner.receive_json()
    assert packs["success"] is True
    starter_pack = next(
        item
        for item in packs["result"]["items"]
        if item["pack_version_id"] == STARTER_PACK_VERSION_ID
    )
    assert starter_pack["pack_version_id"] == STARTER_PACK_VERSION_ID

    await owner.send_json_auto_id({"type": "locklearn/datasets/list", "limit": 20})
    datasets = await owner.receive_json()
    assert datasets["success"] is True
    starter_dataset = next(
        item
        for item in datasets["result"]["items"]
        if item["dataset_id"] == STARTER_DATASET_ID
    )
    assert starter_dataset["installed_version"] == "1.0.0"
    assert starter_dataset["state"] == "installed"
    assert starter_dataset["sources"]
    assert starter_dataset["licenses"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "Japanese Starter",
            "pack_version_id": STARTER_PACK_VERSION_ID,
            "source_language": "ja",
            "target_language": "ja-Latn",
            "scheduler_settings": {
                "learning_count": 1,
                "quiz_count": 1,
            },
        }
    )
    created_track = await owner.receive_json()
    assert created_track["success"] is True
    track_id = created_track["result"]["track_id"]
    assert created_track["result"]["pack_version_id"] == STARTER_PACK_VERSION_ID
    assert created_track["result"]["settings"]["scheduler"] == {
        "learning_count": 1,
        "quiz_count": 1,
    }

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "track_id": track_id,
            "session_type": "learn",
            "settings": {"requested_cards": 20},
        }
    )
    started = await owner.receive_json()
    assert started["success"] is True
    session = started["result"]
    assert session["profile_id"] == profile_id
    assert session["track_id"] == track_id
    assert session["type"] == "learn"
    assert session["question_count"] == 20
    assert len(session["items"]) == 20
    assert session["current_question"] is not None

    other_client = await hass_ws_client(hass)
    await other_client.send_json_auto_id(
        {
            "type": "locklearn/session/get",
            "session_id": session["id"],
        }
    )
    resumed = await other_client.receive_json()
    assert resumed["success"] is True
    assert resumed["result"]["id"] == session["id"]
    assert resumed["result"]["version"] == session["version"]
    assert resumed["result"]["question_count"] == 20
    assert resumed["result"]["current_question"] == session["current_question"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/dashboard/get",
            "profile_id": profile_id,
        }
    )
    dashboard = await owner.receive_json()
    assert dashboard["success"] is True
    assert dashboard["result"]["profile"]["profile_id"] == profile_id
    assert any(item["track_id"] == track_id for item in dashboard["result"]["tracks"])

    await owner.send_json_auto_id(
        {
            "type": "locklearn/stats/get",
            "profile_id": profile_id,
            "track_id": track_id,
        }
    )
    stats = await owner.receive_json()
    assert stats["success"] is True
    assert stats["result"]["profile_id"] == profile_id
    assert stats["result"]["track_id"] == track_id

    await hass.config_entries.async_unload(entry.entry_id)
