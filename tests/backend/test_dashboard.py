"""P5.2 Home dashboard aggregation and ACL tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN


async def test_dashboard_is_private_and_aggregates_track_home_state(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Dashboard owner",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile_response = await owner.receive_json()
    assert profile_response["success"] is True
    profile_id = profile_response["result"]["profile_id"]

    track = await runtime.tracks.async_create_track(
        profile_id=profile_id,
        name="Japanese N5",
        pack_version_id="locklearn:pack-version:japanese-starter-1.0.0",
        source_language="ja",
        target_language="ja-Latn",
    )
    track_id = str(track["track_id"])

    now = datetime.now(UTC)
    await runtime.storage.async_create_session(
        "session-dashboard",
        profile_id,
        track_id,
        session_type="learn",
        items=(
            {
                "question_id": "q1",
                "card_key": "card-1",
                "learning_item_id": "item-1",
                "prompt_facet_id": "prompt-1",
                "answer_facet_id": "answer-1",
                "payload": {},
            },
            {
                "question_id": "q2",
                "card_key": "card-2",
                "learning_item_id": "item-2",
                "prompt_facet_id": "prompt-2",
                "answer_facet_id": "answer-2",
                "payload": {},
            },
        ),
    )
    await runtime.storage.async_answer_session(
        "session-dashboard",
        1,
        "q1",
        {"result": "known"},
    )
    await runtime.storage.repositories.scheduler.async_materialize_day(
        profile_id=profile_id,
        scheduler_config_version=1,
        seed="dashboard",
        start_utc=now.isoformat(),
        end_utc=(now + timedelta(hours=4)).isoformat(),
        now_utc=now.isoformat(),
        updated_at_utc=now.isoformat(),
        slots=(
            {
                "slot_id": "slot-dashboard",
                "track_id": track_id,
                "slot_type": "learning",
                "scheduled_for_utc": (now + timedelta(hours=2)).isoformat(),
            },
        ),
    )

    viewer = await hass_ws_client(hass, hass_read_only_access_token)
    await viewer.send_json_auto_id(
        {
            "type": "locklearn/dashboard/get",
            "profile_id": profile_id,
        }
    )
    hidden = await viewer.receive_json()
    assert hidden["success"] is False
    assert hidden["error"]["code"] == "locklearn/not_found"

    await viewer.send_json_auto_id({"type": "locklearn/profiles/list"})
    invisible_profiles = await viewer.receive_json()
    assert invisible_profiles["success"] is True
    assert all(
        item["profile_id"] != profile_id
        for item in invisible_profiles["result"]["items"]
    )

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await owner.receive_json())["success"] is True

    await viewer.send_json_auto_id(
        {
            "type": "locklearn/dashboard/get",
            "profile_id": profile_id,
        }
    )
    visible = await viewer.receive_json()
    assert visible["success"] is True
    result = visible["result"]
    assert result["profile"] == {
        "profile_id": profile_id,
        "name": "Dashboard owner",
        "preset": "standard",
        "timezone": "Europe/Paris",
    }
    assert len(result["tracks"]) == 1
    card = result["tracks"][0]
    assert card["track_id"] == track_id
    assert card["name"] == "Japanese N5"
    assert card["due_today"] == 0
    assert card["recent_verified_accuracy"]["total"] == 0
    assert card["recent_verified_retention"] is None
    assert card["last_session"]["session_id"] == "session-dashboard"
    assert card["last_session"]["question_count"] == 2
    assert card["last_session"]["answered_count"] == 1
    assert card["next_notification"]["slot_type"] == "learning"
    assert card["next_notification"]["effective_for_utc"] == (
        now + timedelta(hours=2)
    ).isoformat()

    await hass.config_entries.async_unload(entry.entry_id)
