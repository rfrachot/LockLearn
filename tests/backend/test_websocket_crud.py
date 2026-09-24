"""P2.6 authenticated WebSocket CRUD, ACL, pagination, and catalog tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN
from tests.backend.content_db_helpers import DATASET_ID, ITEM_A, ITEM_B, create_package


def _directional_package(
    path: Path,
    version: str,
    *,
    active_item_ids: tuple[str, ...],
) -> Path:
    package = create_package(path, version, active_item_ids=active_item_ids)
    with sqlite3.connect(package) as connection:
        connection.execute("UPDATE facets SET language_tag = 'en' WHERE facet_key = 'prompt'")
        connection.execute("UPDATE facets SET language_tag = 'fr' WHERE facet_key = 'answer'")
        connection.commit()
    return package


async def _activate_package(
    hass: HomeAssistant,
    tmp_path: Path,
    *,
    version: str,
    active_item_ids: tuple[str, ...],
) -> None:
    runtime = hass.data[DOMAIN]["runtime"]
    package = _directional_package(
        tmp_path / f"package-{version}.db",
        version,
        active_item_ids=active_item_ids,
    )
    generation_id = f"generation-websocket-crud-{version}"
    candidate = runtime.storage.paths.content_staging_dir / f"{generation_id}.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id=generation_id,
    )
    await runtime.storage.async_activate_content_generation(candidate)


async def test_bootstrap_profile_crud_privacy_share_and_pagination(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={"create_personal_profile": True, "ui_language": "en"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id({"type": "locklearn/bootstrap"})
    bootstrap = await owner.receive_json()
    assert bootstrap["success"] is True
    assert bootstrap["result"]["frontend_protocol"] == 1
    assert bootstrap["result"]["backend_version"] == "0.0.2"
    assert bootstrap["result"]["panel_path"] == "/locklearn"
    personal = bootstrap["result"]["personal_profile"]
    assert personal["role"] == "owner"
    personal_id = personal["profile_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Second",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    created = await owner.receive_json()
    assert created["success"] is True
    second_id = created["result"]["profile_id"]

    await owner.send_json_auto_id({"type": "locklearn/profiles/list", "limit": 1})
    first_page = await owner.receive_json()
    assert first_page["success"] is True
    assert len(first_page["result"]["items"]) == 1
    assert first_page["result"]["cursor"] is not None

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/list",
            "limit": 1,
            "cursor": first_page["result"]["cursor"],
        }
    )
    second_page = await owner.receive_json()
    assert second_page["success"] is True
    assert len(second_page["result"]["items"]) == 1
    assert {
        first_page["result"]["items"][0]["profile_id"],
        second_page["result"]["items"][0]["profile_id"],
    } == {
        personal_id,
        second_id,
    }

    outsider = await hass_ws_client(hass, hass_read_only_access_token)
    await outsider.send_json_auto_id({"type": "locklearn/profiles/list"})
    hidden = await outsider.receive_json()
    assert hidden["success"] is True
    assert hidden["result"]["items"] == []

    await outsider.send_json_auto_id(
        {
            "type": "locklearn/profiles/update",
            "profile_id": second_id,
            "name": "Should not leak",
        }
    )
    not_found = await outsider.receive_json()
    assert not_found["success"] is False
    assert not_found["error"]["code"] == "locklearn/not_found"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": second_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    shared = await owner.receive_json()
    assert shared["success"] is True
    assert shared["result"]["role"] == "viewer"

    await outsider.send_json_auto_id({"type": "locklearn/profiles/list"})
    visible = await outsider.receive_json()
    assert visible["success"] is True
    assert [item["profile_id"] for item in visible["result"]["items"]] == [second_id]

    await outsider.send_json_auto_id(
        {
            "type": "locklearn/profiles/update",
            "profile_id": second_id,
            "name": "Viewer edit",
        }
    )
    forbidden = await outsider.receive_json()
    assert forbidden["success"] is False
    assert forbidden["error"]["code"] == "locklearn/forbidden"

    for command in (
        {"type": "locklearn/profiles/delete", "profile_id": second_id},
        {
            "type": "locklearn/profiles/share",
            "profile_id": second_id,
            "target_user_id": hass_read_only_user.id,
            "role": "editor",
        },
    ):
        await outsider.send_json_auto_id(command)
        denied = await outsider.receive_json()
        assert denied["success"] is False
        assert denied["error"]["code"] == "locklearn/forbidden"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/update",
            "profile_id": second_id,
            "name": "Renamed",
        }
    )
    updated = await owner.receive_json()
    assert updated["success"] is True
    assert updated["result"]["name"] == "Renamed"

    await owner.send_json_auto_id({"type": "locklearn/profiles/list", "cursor": "not-an-offset"})
    invalid_cursor = await owner.receive_json()
    assert invalid_cursor["success"] is False
    assert invalid_cursor["error"]["code"] == "locklearn/invalid_request"

    await owner.send_json_auto_id({"type": "locklearn/profiles/delete", "profile_id": personal_id})
    deleted = await owner.receive_json()
    assert deleted["success"] is True

    await owner.send_json_auto_id({"type": "locklearn/profiles/list"})
    remaining = await owner.receive_json()
    assert remaining["success"] is True
    assert [item["profile_id"] for item in remaining["result"]["items"]] == [second_id]

    await hass.config_entries.async_unload(entry.entry_id)


async def test_track_crud_pack_integration_and_catalog_surfaces(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await _activate_package(hass, tmp_path, version="v1", active_item_ids=(ITEM_A,))

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Track owner",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await client.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    await client.send_json_auto_id({"type": "locklearn/packs/list", "limit": 10})
    packs = await client.receive_json()
    assert packs["success"] is True
    assert any(
        item["pack_version_id"] == "locklearn:pack-version:v1" for item in packs["result"]["items"]
    )

    await client.send_json_auto_id({"type": "locklearn/datasets/list", "limit": 10})
    datasets = await client.receive_json()
    assert datasets["success"] is True
    assert any(item["dataset_id"] == DATASET_ID for item in datasets["result"]["items"])

    await client.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "EN to FR",
            "pack_version_id": "locklearn:pack-version:v1",
            "source_language": "en",
            "target_language": "fr",
            "priority": 2,
            "scheduler_settings": {
                "learning_count": 2,
                "quiz_count": 1,
            },
        }
    )
    created = await client.receive_json()
    assert created["success"] is True
    track_id = created["result"]["track_id"]
    assert created["result"]["pack_version_id"] == "locklearn:pack-version:v1"
    assert created["result"]["settings"]["scheduler"] == {
        "learning_count": 2,
        "quiz_count": 1,
    }

    outsider = await hass_ws_client(hass, hass_read_only_access_token)
    await outsider.send_json_auto_id({"type": "locklearn/tracks/list", "profile_id": profile_id})
    hidden_tracks = await outsider.receive_json()
    assert hidden_tracks["success"] is False
    assert hidden_tracks["error"]["code"] == "locklearn/not_found"

    await client.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await client.receive_json())["success"] is True

    await outsider.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "Viewer cannot create",
            "pack_version_id": "locklearn:pack-version:v1",
            "source_language": "en",
            "target_language": "fr",
        }
    )
    viewer_create = await outsider.receive_json()
    assert viewer_create["success"] is False
    assert viewer_create["error"]["code"] == "locklearn/forbidden"

    for command in (
        {
            "type": "locklearn/tracks/update",
            "track_id": track_id,
            "name": "Viewer cannot update",
        },
        {"type": "locklearn/tracks/delete", "track_id": track_id},
    ):
        await outsider.send_json_auto_id(command)
        denied = await outsider.receive_json()
        assert denied["success"] is False
        assert denied["error"]["code"] == "locklearn/forbidden"

    await client.send_json_auto_id(
        {"type": "locklearn/tracks/list", "profile_id": profile_id, "limit": 10}
    )
    listed = await client.receive_json()
    assert listed["success"] is True
    assert [item["track_id"] for item in listed["result"]["items"]] == [track_id]

    await client.send_json_auto_id(
        {
            "type": "locklearn/tracks/update",
            "track_id": track_id,
            "name": "Updated track",
            "priority": 3,
            "scheduler_settings": {
                "learning_count": 1,
                "quiz_count": 2,
            },
        }
    )
    updated = await client.receive_json()
    assert updated["success"] is True
    assert updated["result"]["name"] == "Updated track"
    assert updated["result"]["priority"] == 3
    assert updated["result"]["settings"]["scheduler"] == {
        "learning_count": 1,
        "quiz_count": 2,
    }

    await _activate_package(
        hass,
        tmp_path,
        version="v2",
        active_item_ids=(ITEM_A, ITEM_B),
    )
    await outsider.send_json_auto_id(
        {
            "type": "locklearn/tracks/integrate_pack_update",
            "track_id": track_id,
            "pack_version_id": "locklearn:pack-version:v2",
        }
    )
    viewer_integrate = await outsider.receive_json()
    assert viewer_integrate["success"] is False
    assert viewer_integrate["error"]["code"] == "locklearn/forbidden"

    await client.send_json_auto_id(
        {
            "type": "locklearn/tracks/integrate_pack_update",
            "track_id": track_id,
            "pack_version_id": "locklearn:pack-version:v2",
        }
    )
    integrated = await client.receive_json()
    assert integrated["success"] is True
    assert integrated["result"]["added_learning_item_ids"] == [ITEM_B]

    await client.send_json_auto_id({"type": "locklearn/tracks/delete", "track_id": track_id})
    deleted = await client.receive_json()
    assert deleted["success"] is True

    await client.send_json_auto_id(
        {"type": "locklearn/tracks/list", "profile_id": profile_id, "limit": 10}
    )
    empty = await client.receive_json()
    assert empty["success"] is True
    assert empty["result"]["items"] == []

    await hass.config_entries.async_unload(entry.entry_id)
