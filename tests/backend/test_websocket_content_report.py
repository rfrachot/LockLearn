"""P3.7 content-report WebSocket ACL and persistence tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


async def test_content_report_requires_answer_permission_and_persists_unrecognized(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    runtime = hass.data[DOMAIN]["runtime"]
    package = create_package(
        tmp_path / "report-package.db",
        "report",
        active_item_ids=(ITEM_A,),
    )
    candidate = runtime.storage.paths.content_staging_dir / "generation-report.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-report",
    )
    await runtime.storage.async_activate_content_generation(candidate)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Reporter",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await owner.receive_json()
    assert profile["success"] is True
    profile_id = profile["result"]["profile_id"]

    card_key = card_identity(ITEM_A)[1]
    await owner.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "Report Track",
            "pack_version_id": "locklearn:pack-version:report",
            "source_language": "en",
            "target_language": "fr",
            "explicit_card_keys": [card_key],
        }
    )
    track = await owner.receive_json()
    assert track["success"] is True
    track_id = track["result"]["track_id"]
    prompt_id, answer_id = facet_ids(ITEM_A)

    payload = {
        "type": "locklearn/content/report",
        "profile_id": profile_id,
        "track_id": track_id,
        "card_key": card_key,
        "learning_item_id": ITEM_A,
        "prompt_facet_id": prompt_id,
        "answer_facet_id": answer_id,
        "submitted_text": "colour",
        "normalized_submission": "colour",
        "grading_policy_kind": "exact",
        "grading_policy_version": 1,
        "normalization_version": 3,
        "dataset_generation": "generation-report",
    }
    await owner.send_json_auto_id(payload)
    response = await owner.receive_json()
    assert response["success"] is True
    assert response["result"]["grading_result"] == "unrecognized"
    assert response["result"]["srs_penalized"] is False

    report = await runtime.storage.repositories.content_reports.async_get(
        response["result"]["report_id"]
    )
    assert report is not None
    assert report["payload"]["card_key"] == card_key
    assert report["payload"]["submitted_text"] == "colour"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await owner.receive_json())["success"] is True

    viewer = await hass_ws_client(hass, hass_read_only_access_token)
    await viewer.send_json_auto_id(payload)
    denied = await viewer.receive_json()
    assert denied["success"] is False
    assert denied["error"]["code"] == "locklearn/forbidden"

    await hass.config_entries.async_unload(entry.entry_id)
