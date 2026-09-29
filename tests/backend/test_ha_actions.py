"""P4.8 Home Assistant event/service boundary tests."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from homeassistant.core import Context, Event, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
from custom_components.locklearn.storage import NotificationTargetRecord


async def test_companion_clear_closes_state_without_review_event(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    now = datetime.now(UTC)
    profile = await runtime.profiles.async_create_profile(
        name="P4.8 clear",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner-clear",),
    )
    profile_id = str(profile["profile_id"])
    await runtime.storage.repositories.notification_targets.async_insert(
        NotificationTargetRecord(
            target_id="target-clear",
            profile_id=profile_id,
            device_registry_id="device-clear",
            platform="android",
            friendly_name="Clear phone",
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )
    await runtime.storage.repositories.scheduler.async_materialize_day(
        profile_id=profile_id,
        scheduler_config_version=1,
        seed="clear",
        start_utc=(now - timedelta(minutes=1)).isoformat(),
        end_utc=(now + timedelta(hours=1)).isoformat(),
        now_utc=now.isoformat(),
        updated_at_utc=now.isoformat(),
        slots=(
            {
                "slot_id": "slot-clear",
                "target_id": "target-clear",
                "slot_type": "learning",
                "scheduled_for_utc": now.isoformat(),
            },
        ),
    )
    assert await runtime.storage.repositories.scheduler.async_mark_slot_sent(
        slot_id="slot-clear",
        delivered_at_utc=now.isoformat(),
        timezone_name="Europe/Paris",
        weekday=now.weekday(),
        local_hour=now.hour,
    )
    interaction = await runtime.notification_interactions.async_create(
        profile_id=profile_id,
        target_id="target-clear",
        stage="prompt",
        tag="locklearn:clear",
        expires_at=now + timedelta(minutes=30),
        payload={"slot_id": "slot-clear"},
    )

    observed: list[dict[str, Any]] = []

    async def capture(event: Event[Any]) -> None:
        observed.append(dict(event.data))

    unsub = hass.bus.async_listen("locklearn_notification_cleared", capture)
    hass.bus.async_fire(
        "mobile_app_notification_cleared",
        {"tag": "locklearn:clear"},
    )
    await hass.async_block_till_done()
    unsub()

    stored = await runtime.storage.repositories.notification_interactions.async_get_by_token(
        interaction.token
    )
    assert stored is not None
    assert stored["status"] == "cleared"

    slot = await runtime.storage.repositories.scheduler.async_get_slot("slot-clear")
    assert slot is not None
    assert slot["status"] == "expired"
    assert slot["expired_reason"] == "cleared"

    sample = await runtime.storage.repositories.scheduler.async_get_receptivity_sample("slot-clear")
    assert sample is not None
    assert sample["cleared"] is True

    assert (
        await runtime.storage.repositories.review_events.async_list_scope_events(
            profile_id=profile_id
        )
        == ()
    )
    assert len(observed) == 1
    assert observed[0]["interaction_id"] == interaction.interaction_id
    assert observed[0]["profile_id"] == profile_id
    assert "token" not in observed[0]
    assert "tag" not in observed[0]

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_services_lifecycle_and_unattended_snooze_audit(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    for service in ("start_session", "send_now", "snooze", "pause_track", "resume_track"):
        assert hass.services.has_service(DOMAIN, service)

    now = datetime.now(UTC)
    profile = await runtime.profiles.async_create_profile(
        name="P4.8 unattended",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner-unattended",),
        settings_override={"allow_unattended_actions": True},
    )
    profile_id = str(profile["profile_id"])
    await runtime.storage.repositories.scheduler.async_materialize_day(
        profile_id=profile_id,
        scheduler_config_version=1,
        seed="snooze",
        start_utc=(now - timedelta(minutes=1)).isoformat(),
        end_utc=(now + timedelta(hours=1)).isoformat(),
        now_utc=now.isoformat(),
        updated_at_utc=now.isoformat(),
        slots=(
            {
                "slot_id": "slot-snooze",
                "slot_type": "learning",
                "scheduled_for_utc": now.isoformat(),
            },
        ),
    )

    await hass.services.async_call(
        DOMAIN,
        "snooze",
        {
            "profile_id": profile_id,
            "slot_id": "slot-snooze",
            "minutes": 20,
        },
        blocking=True,
    )
    slot = await runtime.storage.repositories.scheduler.async_get_slot("slot-snooze")
    assert slot is not None
    assert slot["status"] == "deferred"
    assert slot["defer_reason"] == "manual_snooze"

    with pytest.raises(HomeAssistantError, match="not authorized unattended"):
        await hass.services.async_call(
            DOMAIN,
            "start_session",
            {"profile_id": profile_id},
            blocking=True,
        )

    connection = sqlite3.connect(runtime.storage.paths.state_db)
    try:
        rows = connection.execute(
            """SELECT event_type, profile_id, payload_json
               FROM audit_events
               WHERE event_type = 'unattended_action'
               ORDER BY id"""
        ).fetchall()
    finally:
        connection.close()
    assert len(rows) == 1
    assert rows[0][0] == "unattended_action"
    assert rows[0][1] == profile_id
    payload = json.loads(str(rows[0][2]))
    assert payload == {
        "action": "snooze",
        "actor_kind": "unattended_automation",
    }

    assert await hass.config_entries.async_unload(entry.entry_id)
    for service in ("start_session", "send_now", "snooze", "pause_track", "resume_track"):
        assert not hass.services.has_service(DOMAIN, service)


async def test_user_services_delegate_to_scheduler_track_and_session_primitives(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    now = datetime.now(UTC)
    profile = await runtime.profiles.async_create_profile(
        name="P4.8 owner actions",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner-service",),
    )
    profile_id = str(profile["profile_id"])
    track = await runtime.tracks.async_create_track(
        profile_id=profile_id,
        name="Japanese",
        pack_version_id="locklearn:pack-version:japanese-starter-1.0.0",
        source_language="ja",
        target_language="ja-Latn",
    )
    track_id = str(track["track_id"])
    await runtime.storage.repositories.notification_targets.async_insert(
        NotificationTargetRecord(
            target_id="target-service",
            profile_id=profile_id,
            device_registry_id="device-service",
            platform="android",
            friendly_name="Service phone",
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )
    context = Context(user_id="owner-service")

    await hass.services.async_call(
        DOMAIN,
        "send_now",
        {
            "profile_id": profile_id,
            "track_id": track_id,
            "target_id": "target-service",
        },
        blocking=True,
        context=context,
    )
    slots = await runtime.storage.repositories.scheduler.async_list_slots(
        profile_id=profile_id,
        start_utc=(now - timedelta(minutes=5)).isoformat(),
        end_utc=(now + timedelta(hours=1)).isoformat(),
    )
    manual = [slot for slot in slots if slot["slot_type"] == "manual_send_now"]
    assert len(manual) == 1
    assert manual[0]["track_id"] == track_id
    assert manual[0]["target_id"] == "target-service"
    assert manual[0]["card_key"] is not None
    assert manual[0]["selection_reason"] == "teaser_new"

    await hass.services.async_call(
        DOMAIN,
        "pause_track",
        {"profile_id": profile_id, "track_id": track_id},
        blocking=True,
        context=context,
    )
    paused = await runtime.storage.repositories.tracks.async_get(track_id)
    assert paused is not None
    assert paused["status"] == "paused"

    await hass.services.async_call(
        DOMAIN,
        "resume_track",
        {"profile_id": profile_id, "track_id": track_id},
        blocking=True,
        context=context,
    )
    resumed = await runtime.storage.repositories.tracks.async_get(track_id)
    assert resumed is not None
    assert resumed["status"] == "active"

    await hass.services.async_call(
        DOMAIN,
        "start_session",
        {
            "profile_id": profile_id,
            "track_id": track_id,
            "settings": {"requested_cards": 2},
        },
        blocking=True,
        context=context,
    )
    connection = sqlite3.connect(runtime.storage.paths.state_db)
    try:
        session_rows = connection.execute(
            "SELECT profile_id, track_id, status, question_count FROM sessions"
        ).fetchall()
    finally:
        connection.close()
    assert session_rows == [(profile_id, track_id, "active", 2)]

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_locklearn_output_events_are_observation_only(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    profile = await runtime.profiles.async_create_profile(
        name="P4.8 observational bus",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner-observation",),
    )
    profile_id = str(profile["profile_id"])

    hass.bus.async_fire(
        "locklearn_answered",
        {
            "event_id": "attacker-controlled",
            "interaction_id": "fake-interaction",
            "profile_id": profile_id,
            "track_id": "fake-track",
            "card_key": "fake-card",
            "result": "correct",
        },
    )
    hass.bus.async_fire(
        "locklearn_quiz_correct",
        {
            "event_id": "attacker-controlled-2",
            "profile_id": profile_id,
        },
    )
    await hass.async_block_till_done()

    assert (
        await runtime.storage.repositories.review_events.async_list_scope_events(
            profile_id=profile_id
        )
        == ()
    )
    assert await runtime.storage.repositories.progress.async_list_scope(profile_id=profile_id) == ()

    assert await hass.config_entries.async_unload(entry.entry_id)
