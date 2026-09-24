"""P4 deterministic materialized scheduler and temporal reconciliation tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN
from custom_components.locklearn.core.scheduler import SchedulerService
from custom_components.locklearn.storage import ProfileRecord, SQLiteStorage, StoragePaths


class FixedClock:
    """Deterministic aware UTC clock for scheduler tests."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


async def _storage(tmp_path: Path, clock: FixedClock) -> SQLiteStorage:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()
    return storage


async def _profile(
    storage: SQLiteStorage,
    *,
    settings: dict[str, Any],
    now: datetime,
) -> None:
    await storage.repositories.profiles.async_insert(
        ProfileRecord(
            profile_id="profile-scheduler",
            name="Scheduler",
            preset="custom",
            timezone="Europe/Paris",
            settings=settings,
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )


async def test_preview_is_deterministic_and_obeys_windows_quiet_gap_and_hour_limit(
    tmp_path: Path,
) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 6,
                "quiet_hours": {"start": "12:00", "end": "13:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "14:00"}],
                    "minimum_gap_seconds": 1800,
                    "maximum_notifications_per_hour": 1,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )

        first = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        second = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )

        assert first == second
        assert first["generated_slots"] == 5
        assert first["capacity_limited"] is True
        assert first["content_selection"] == "send_time"
        assert await storage.repositories.scheduler.async_get_config("profile-scheduler") is None

        local_times = [
            datetime.fromisoformat(slot["scheduled_for_utc"]).astimezone(ZoneInfo("Europe/Paris"))
            for slot in first["slots"]
        ]
        assert all(8 <= value.hour < 14 for value in local_times)
        assert all(value.hour != 12 for value in local_times)
        assert len({(value.date(), value.hour) for value in local_times}) == len(local_times)
        assert all(
            (later - earlier).total_seconds() >= 1800 for earlier, later in pairwise(local_times)
        )
        assert all(slot["track_id"] is None for slot in first["slots"])
        assert all(slot["target_id"] is None for slot in first["slots"])
        assert all("card_key" not in slot for slot in first["slots"])
    finally:
        await storage.async_close()


async def test_materialized_slots_are_authoritative_after_config_change(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 3,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "20:00"}],
                    "minimum_gap_seconds": 3600,
                    "maximum_notifications_per_hour": 1,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            clock=clock,
        )
        day = date(2026, 9, 24)
        generated = await service.async_generate(profile_id="profile-scheduler", local_date=day)
        original_slots = generated["materialized_slots"]
        assert len(original_slots) == 3
        assert {slot["scheduler_config_version"] for slot in original_slots} == {1}

        assert await storage.repositories.scheduler.async_set_slot_status(
            original_slots[0]["slot_id"],
            "consumed",
            updated_at_utc="2026-09-24T09:00:00+00:00",
        )

        profile = await storage.repositories.profiles.async_get("profile-scheduler")
        assert profile is not None
        settings = dict(profile["settings"])
        settings["daily_push_budget"] = 1
        settings["scheduler"] = {
            "active_days": [3],
            "active_windows": [{"start": "18:00", "end": "20:00"}],
            "minimum_gap_seconds": 3600,
            "maximum_notifications_per_hour": 1,
        }
        assert await storage.repositories.profiles.async_update(
            profile_id="profile-scheduler",
            name="Scheduler",
            timezone="Europe/Paris",
            status="active",
            settings=settings,
            updated_at_utc="2026-09-24T10:00:00+00:00",
        )

        preview = await service.async_preview(profile_id="profile-scheduler", local_date=day)
        assert preview["scheduler_config_version"] == 2
        assert preview["generated_slots"] == 1

        regenerated = await service.async_generate(profile_id="profile-scheduler", local_date=day)
        materialized = regenerated["materialized_slots"]
        original_by_id = {slot["slot_id"]: slot for slot in materialized}
        assert original_by_id[original_slots[0]["slot_id"]]["status"] == "consumed"
        for old in original_slots:
            preserved = original_by_id[old["slot_id"]]
            assert preserved["scheduled_for_utc"] == old["scheduled_for_utc"]
            assert preserved["scheduler_config_version"] == 1
        assert any(slot["scheduler_config_version"] == 2 for slot in materialized)
    finally:
        await storage.async_close()


async def test_spring_forward_skips_nonexistent_local_minutes(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 3, 29, 0, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 20,
                "quiet_hours": {"start": "04:00", "end": "05:00"},
                "scheduler": {
                    "active_days": [6],
                    "active_windows": [{"start": "01:30", "end": "03:30"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 20,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 3, 29),
        )
        local_times = [
            datetime.fromisoformat(slot["scheduled_for_utc"]).astimezone(ZoneInfo("Europe/Paris"))
            for slot in preview["slots"]
        ]
        assert local_times
        assert all(value.hour != 2 for value in local_times)
        assert all(value.fold == 0 for value in local_times)
    finally:
        await storage.async_close()


async def test_fall_back_duplicate_hour_respects_one_local_hour_budget(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 10, 25, 0, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 4,
                "quiet_hours": {"start": "04:00", "end": "05:00"},
                "scheduler": {
                    "active_days": [6],
                    "active_windows": [{"start": "02:00", "end": "03:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 1,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 10, 25),
        )
        assert preview["generated_slots"] == 1
        local = datetime.fromisoformat(preview["slots"][0]["scheduled_for_utc"]).astimezone(
            ZoneInfo("Europe/Paris")
        )
        assert local.hour == 2
    finally:
        await storage.async_close()


async def test_cross_midnight_window_uses_start_day_active_rule(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 28, 20, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 10,
                "quiet_hours": {"start": "04:00", "end": "05:00"},
                "scheduler": {
                    "active_days": [0],
                    "active_windows": [{"start": "22:00", "end": "02:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 10,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 29),
        )
        local_times = [
            datetime.fromisoformat(slot["scheduled_for_utc"]).astimezone(ZoneInfo("Europe/Paris"))
            for slot in preview["slots"]
        ]
        assert local_times
        assert all(value.date() == date(2026, 9, 29) for value in local_times)
        assert all(value.hour < 2 for value in local_times)
    finally:
        await storage.async_close()


async def test_backward_clock_jump_uses_persisted_high_watermark(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 10, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 4,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "20:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 4,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        first = await service.async_reconcile(reason="startup")
        assert first.kind == "initial"

        clock.set(datetime(2026, 9, 24, 9, 0, tzinfo=UTC))
        jumped = await service.async_reconcile(reason="timer")
        assert jumped.kind == "clock_backward"
        assert jumped.effective_now_utc == datetime(2026, 9, 24, 10, 0, tzinfo=UTC)

        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        assert all(
            datetime.fromisoformat(slot["scheduled_for_utc"])
            >= datetime(2026, 9, 24, 10, 0, tzinfo=UTC)
            for slot in preview["slots"]
        )
    finally:
        await storage.async_close()


async def test_restart_expires_overdue_unsent_slots_without_touching_consumed(
    tmp_path: Path,
) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 3,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "20:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 3,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        generated = await service.async_generate(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        slots = generated["materialized_slots"]
        assert len(slots) == 3
        assert await storage.repositories.scheduler.async_set_slot_status(
            slots[0]["slot_id"],
            "consumed",
            updated_at_utc=clock.now().isoformat(),
        )

        latest = max(datetime.fromisoformat(slot["scheduled_for_utc"]) for slot in slots)
        clock.set(latest + timedelta(minutes=1))
        reconciled = await service.async_reconcile(reason="startup")
        assert reconciled.kind == "restart"
        assert reconciled.expired_slots == 2

        refreshed = await storage.repositories.scheduler.async_list_slots(
            profile_id="profile-scheduler",
            start_utc="2026-09-23T22:00:00+00:00",
            end_utc="2026-09-24T22:00:00+00:00",
        )
        assert {slot["status"] for slot in refreshed} == {"consumed", "expired"}

        repeated = await service.async_reconcile(reason="startup")
        assert repeated.expired_slots == 0
    finally:
        await storage.async_close()


async def test_timezone_change_cancels_only_old_future_unsent_slots(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 2,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "20:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 2,
                },
            },
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        first = await service.async_generate(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        old_slots = first["materialized_slots"]
        assert await storage.repositories.scheduler.async_set_slot_status(
            old_slots[0]["slot_id"],
            "sent",
            updated_at_utc=clock.now().isoformat(),
        )

        profile = await storage.repositories.profiles.async_get("profile-scheduler")
        assert profile is not None
        assert await storage.repositories.profiles.async_update(
            profile_id="profile-scheduler",
            name=str(profile["name"]),
            timezone="America/New_York",
            status="active",
            settings=dict(profile["settings"]),
            updated_at_utc=clock.now().isoformat(),
        )
        changed = await service.async_generate(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        assert changed["scheduler_config_version"] == 2

        all_slots = await storage.repositories.scheduler.async_list_slots(
            profile_id="profile-scheduler",
            start_utc="2026-09-24T00:00:00+00:00",
            end_utc="2026-09-25T04:00:00+00:00",
        )
        old_by_id = {slot["slot_id"]: slot for slot in all_slots}
        assert old_by_id[old_slots[0]["slot_id"]]["status"] == "sent"
        assert old_by_id[old_slots[1]["slot_id"]]["status"] == "cancelled"
        assert any(int(slot["scheduler_config_version"]) == 2 for slot in all_slots)
    finally:
        await storage.async_close()


async def test_preview_websocket_is_profile_acl_read_only(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "Scheduler owner",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    created = await owner.receive_json()
    assert created["success"] is True
    profile_id = created["result"]["profile_id"]

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
    await viewer.send_json_auto_id(
        {
            "type": "locklearn/scheduler/preview",
            "profile_id": profile_id,
            "local_date": "2026-09-24",
        }
    )
    visible = await viewer.receive_json()
    assert visible["success"] is True
    assert visible["result"]["profile_id"] == profile_id
    assert visible["result"]["content_selection"] == "send_time"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/scheduler/preview",
            "profile_id": profile_id,
            "local_date": "not-a-date",
        }
    )
    invalid = await owner.receive_json()
    assert invalid["success"] is False
    assert invalid["error"]["code"] == "locklearn/invalid_request"

    await hass.config_entries.async_unload(entry.entry_id)
