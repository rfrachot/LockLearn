"""Home Assistant WebSocket session protocol tests."""

import asyncio
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package


async def test_storage_status_is_admin_only_and_privacy_safe(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
) -> None:
    """Only admins can retrieve aggregate SQLite health metadata."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    admin = await hass_ws_client(hass)
    await admin.send_json_auto_id({"type": "locklearn/admin/storage/status"})
    result = await admin.receive_json()
    assert result["success"] is True
    assert result["result"]["integrity_check"] == ["ok"]
    assert result["result"]["foreign_key_violation_count"] == 0
    assert result["result"]["reader_off_event_loop"] is True
    assert result["result"]["writer_initialized"] is True

    non_admin = await hass_ws_client(hass, hass_read_only_access_token)
    await non_admin.send_json_auto_id({"type": "locklearn/admin/storage/status"})
    forbidden = await non_admin.receive_json()
    assert forbidden["success"] is False
    assert forbidden["error"]["code"] == "unauthorized"

    await hass.config_entries.async_unload(entry.entry_id)


async def test_two_websocket_clients_get_cas_and_subscription(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
    tmp_path: Path,
) -> None:
    """Only one same-version answer wins and subscribers receive the mutation."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN]["runtime"]

    package = create_package(
        tmp_path / "session-websocket-package.db",
        "session-websocket",
        active_item_ids=(ITEM_A,),
    )
    candidate = runtime.storage.paths.content_staging_dir / "generation-session-websocket.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-session-websocket",
    )
    await runtime.storage.async_activate_content_generation(candidate)

    client_one = await hass_ws_client(hass)
    await client_one.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Session owner",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile_response = await client_one.receive_json()
    assert profile_response["success"] is True
    profile_id = profile_response["result"]["profile_id"]

    card_key = card_identity(ITEM_A)[1]
    await client_one.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "Session Track",
            "pack_version_id": "locklearn:pack-version:session-websocket",
            "source_language": "en",
            "target_language": "fr",
            "explicit_card_keys": [card_key],
        }
    )
    track_response = await client_one.receive_json()
    assert track_response["success"] is True
    track_id = track_response["result"]["track_id"]
    await client_one.send_json_auto_id(
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "track_id": track_id,
            "session_type": "bounded",
            "strategy": "default",
            "settings": {"requested_cards": 1},
        }
    )
    started_response = await client_one.receive_json()
    assert started_response["success"] is True
    started = started_response["result"]
    assert started["question_count"] == 1
    assert started["current_question"] is not None
    assert started["fatigue_advice"]["detected"] is False
    session_id = started["id"]
    question_id = started["current_question"]["question_id"]

    client_two = await hass_ws_client(hass)
    await client_two.send_json_auto_id(
        {"type": "locklearn/session/subscribe", "session_id": session_id}
    )
    subscribed = await client_two.receive_json()
    assert subscribed["success"] is True
    assert subscribed["result"]["current_question"]["question_id"] == question_id

    answer = {
        "type": "locklearn/session/answer",
        "session_id": session_id,
        "expected_version": 1,
        "question_id": question_id,
        "answer": {"choice": "a"},
    }
    await client_one.send_json_auto_id(answer)
    winner = await client_one.receive_json()
    assert winner["success"] is True
    assert winner["result"]["version"] == 2
    assert winner["result"]["current_position"] == 1

    event = await client_two.receive_json()
    assert event["type"] == "event"
    assert event["event"]["version"] == 2

    await client_two.send_json_auto_id(answer)
    stale = await client_two.receive_json()
    assert stale["success"] is False
    assert stale["error"]["code"] == "locklearn/stale_session"

    await client_one.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await client_one.receive_json())["success"] is True

    outsider = await hass_ws_client(hass, hass_read_only_access_token)
    await outsider.send_json_auto_id({"type": "locklearn/session/get", "session_id": session_id})
    visible = await outsider.receive_json()
    assert visible["success"] is True

    await outsider.send_json_auto_id(
        {
            "type": "locklearn/session/answer",
            "session_id": session_id,
            "expected_version": 2,
            "question_id": question_id,
            "answer": {"choice": "b"},
        }
    )
    forbidden = await outsider.receive_json()
    assert forbidden["success"] is False
    assert forbidden["error"]["code"] == "locklearn/forbidden"

    assert runtime.sessions.subscriber_count == 1
    await client_two.close()
    await hass.async_block_till_done()
    assert runtime.sessions.subscriber_count == 0

    await hass.config_entries.async_unload(entry.entry_id)


async def test_websocket_operation_stream_can_be_cancelled(
    hass: HomeAssistant, hass_ws_client: Any
) -> None:
    """The operation subscription returns current state then streams cancellation."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN]["runtime"]
    started = asyncio.Event()

    async def worker(context: Any) -> None:
        await context.async_update("merge", 0.25)
        started.set()
        await asyncio.Event().wait()

    operation_id = runtime.operations.start("queued", worker)
    await started.wait()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "locklearn/operations/subscribe", "operation_id": operation_id}
    )
    subscribed = await client.receive_json()
    assert subscribed["success"] is True
    assert subscribed["result"]["phase"] == "merge"
    assert subscribed["result"]["progress"] == 0.25

    await client.send_json_auto_id(
        {"type": "locklearn/operations/cancel", "operation_id": operation_id}
    )
    messages = [await client.receive_json(), await client.receive_json()]
    assert any(message.get("success") is True for message in messages)
    assert any(
        message.get("type") == "event" and message["event"]["status"] == "cancelled"
        for message in messages
    )
    await hass.config_entries.async_unload(entry.entry_id)
