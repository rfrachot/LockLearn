"""P4 deterministic materialized scheduler and temporal reconciliation tests."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
from custom_components.locklearn.core.scheduler import SchedulerService
from custom_components.locklearn.storage import (
    NotificationTargetRecord,
    ProfileRecord,
    SQLiteStorage,
    StoragePaths,
    TrackRecord,
)


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


async def _track(
    storage: SQLiteStorage,
    *,
    track_id: str,
    priority: int,
    learning_count: int,
    quiz_count: int = 0,
    target_ids: tuple[str, ...] | None = None,
    now: datetime,
) -> None:
    scheduler: dict[str, Any] = {
        "learning_count": learning_count,
        "quiz_count": quiz_count,
    }
    if target_ids is not None:
        scheduler["target_ids"] = list(target_ids)
    await storage.repositories.tracks.async_insert(
        TrackRecord(
            track_id=track_id,
            profile_id="profile-scheduler",
            name=track_id,
            priority=priority,
            settings={"scheduler": scheduler},
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )


async def _target(
    storage: SQLiteStorage,
    *,
    target_id: str = "target-1",
    profile_id: str = "profile-scheduler",
    device_registry_id: str = "device-1",
    daily_push_budget: int | None = None,
    minimum_gap_seconds: int | None = None,
    maximum_notifications_per_hour: int | None = None,
    now: datetime,
) -> None:
    await storage.repositories.notification_targets.async_insert(
        NotificationTargetRecord(
            target_id=target_id,
            profile_id=profile_id,
            device_registry_id=device_registry_id,
            platform="android",
            friendly_name=target_id,
            daily_push_budget=daily_push_budget,
            minimum_gap_seconds=minimum_gap_seconds,
            maximum_notifications_per_hour=maximum_notifications_per_hour,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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


async def test_forward_clock_jump_expires_overdue_unsent_slots(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 8, 0, tzinfo=UTC))
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )
        generated = await service.async_generate(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        slots = generated["materialized_slots"]
        earliest = min(datetime.fromisoformat(slot["scheduled_for_utc"]) for slot in slots)

        clock.set(earliest + timedelta(hours=6))
        jumped = await service.async_reconcile(reason="timer")
        assert jumped.kind == "clock_forward"
        assert jumped.expired_slots >= 1

        refreshed = await storage.repositories.scheduler.async_list_slots(
            profile_id="profile-scheduler",
            start_utc="2026-09-23T22:00:00+00:00",
            end_utc="2026-09-24T22:00:00+00:00",
        )
        assert any(slot["status"] == "expired" for slot in refreshed)
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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
            storage.repositories.tracks,
            storage.repositories.notification_targets,
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


async def test_weighted_round_robin_prevents_greedy_track_starvation(
    tmp_path: Path,
) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 5,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "18:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 5,
                },
            },
        )
        await _track(
            storage,
            track_id="track-high",
            priority=3,
            learning_count=5,
            now=clock.now(),
        )
        await _track(
            storage,
            track_id="track-low",
            priority=1,
            learning_count=5,
            now=clock.now(),
        )
        await _target(
            storage,
            daily_push_budget=10,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=5,
            now=clock.now(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )

        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        track_ids = [slot["track_id"] for slot in preview["slots"]]
        assert len(track_ids) == 5
        assert "track-high" in track_ids
        assert "track-low" in track_ids
        assert track_ids.count("track-high") > track_ids.count("track-low")
        assert preview["allocation"]["requested_demand"] == 10
        assert preview["allocation"]["allocated_demand"] == 5
        assert preview["allocation"]["unmet_demand"] == 5
    finally:
        await storage.async_close()


async def test_target_daily_budget_limits_track_allocation(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
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
                    "active_windows": [{"start": "08:00", "end": "18:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 4,
                },
            },
        )
        await _track(
            storage,
            track_id="track-1",
            priority=1,
            learning_count=4,
            now=clock.now(),
        )
        await _target(
            storage,
            daily_push_budget=2,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=4,
            now=clock.now(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )

        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        assert preview["generated_slots"] == 2
        assert preview["allocation"]["allocated_demand"] == 2
        assert preview["allocation"]["unmet_demand"] == 2
        assert {slot["target_id"] for slot in preview["slots"]} == {"target-1"}
    finally:
        await storage.async_close()


async def test_shared_device_budget_is_enforced_across_profiles(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 1,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3],
                    "active_windows": [{"start": "08:00", "end": "18:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 4,
                },
            },
        )
        await _track(
            storage,
            track_id="track-1",
            priority=1,
            learning_count=1,
            now=clock.now(),
        )
        await _target(
            storage,
            target_id="target-1",
            device_registry_id="shared-device",
            daily_push_budget=1,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=4,
            now=clock.now(),
        )
        await storage.repositories.profiles.async_insert(
            ProfileRecord(
                profile_id="profile-other",
                name="Other",
                preset="custom",
                timezone="Europe/Paris",
                settings={},
                created_at_utc=clock.now().isoformat(),
                updated_at_utc=clock.now().isoformat(),
            )
        )
        await _target(
            storage,
            target_id="target-other",
            profile_id="profile-other",
            device_registry_id="shared-device",
            daily_push_budget=1,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=4,
            now=clock.now(),
        )
        await storage.repositories.scheduler.async_materialize_day(
            profile_id="profile-other",
            scheduler_config_version=1,
            seed="other",
            start_utc="2026-09-23T22:00:00+00:00",
            end_utc="2026-09-24T22:00:00+00:00",
            now_utc=clock.now().isoformat(),
            slots=(
                {
                    "slot_id": "other-slot",
                    "track_id": None,
                    "target_id": "target-other",
                    "slot_type": "learning",
                    "scheduled_for_utc": "2026-09-24T09:00:00+00:00",
                },
            ),
            updated_at_utc=clock.now().isoformat(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )

        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        assert preview["generated_slots"] == 0
        assert preview["allocation"]["unmet_demand"] == 1
    finally:
        await storage.async_close()


async def test_active_session_suppresses_only_its_track(tmp_path: Path) -> None:
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
                    "active_windows": [{"start": "08:00", "end": "18:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 3,
                },
            },
        )
        await _track(
            storage,
            track_id="track-session",
            priority=10,
            learning_count=3,
            now=clock.now(),
        )
        await _track(
            storage,
            track_id="track-free",
            priority=1,
            learning_count=3,
            now=clock.now(),
        )
        await _target(
            storage,
            daily_push_budget=10,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=3,
            now=clock.now(),
        )
        await storage.async_create_session(
            "active-session",
            "profile-scheduler",
            "track-session",
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )

        preview = await service.async_preview(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 24),
        )
        assert {slot["track_id"] for slot in preview["slots"]} == {"track-free"}
        assert preview["allocation"]["suppressed_active_session_tracks"] == ["track-session"]
    finally:
        await storage.async_close()


async def test_capacity_repair_requires_three_distinct_infeasible_days(
    tmp_path: Path,
) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 5, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    issues: list[tuple[str, str, dict[str, str]]] = []
    cleared: list[str] = []

    async def issue_callback(
        issue_id: str,
        translation_key: str,
        placeholders: Mapping[str, str],
    ) -> None:
        issues.append((issue_id, translation_key, dict(placeholders)))

    async def issue_clear_callback(issue_id: str) -> None:
        cleared.append(issue_id)

    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 3,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "scheduler": {
                    "active_days": [3, 4, 5, 6],
                    "active_windows": [{"start": "08:00", "end": "18:00"}],
                    "minimum_gap_seconds": 0,
                    "maximum_notifications_per_hour": 3,
                },
            },
        )
        await _track(
            storage,
            track_id="track-1",
            priority=1,
            learning_count=3,
            now=clock.now(),
        )
        await _target(
            storage,
            daily_push_budget=1,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=3,
            now=clock.now(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
            issue_callback=issue_callback,
            issue_clear_callback=issue_clear_callback,
        )

        for local_day in (
            date(2026, 9, 24),
            date(2026, 9, 25),
            date(2026, 9, 26),
        ):
            result = await service.async_generate(
                profile_id="profile-scheduler",
                local_date=local_day,
            )
            assert result["allocation"]["unmet_demand"] == 2

        assert len(issues) == 1
        issue_id, translation_key, placeholders = issues[0]
        assert issue_id == "scheduler_configuration_infeasible_profile-scheduler"
        assert translation_key == "scheduler_configuration_infeasible"
        assert placeholders == {
            "profile_id": "profile-scheduler",
            "requested": "3",
            "capacity": "1",
        }
        assert cleared == []

        await _target(
            storage,
            target_id="target-2",
            device_registry_id="device-2",
            daily_push_budget=1,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=3,
            now=clock.now(),
        )
        await _target(
            storage,
            target_id="target-3",
            device_registry_id="device-3",
            daily_push_budget=1,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=3,
            now=clock.now(),
        )
        recovered = await service.async_generate(
            profile_id="profile-scheduler",
            local_date=date(2026, 9, 27),
        )
        assert recovered["allocation"]["unmet_demand"] == 0
        assert cleared == ["scheduler_configuration_infeasible_profile-scheduler"]
    finally:
        await storage.async_close()


async def test_receptive_when_false_defers_without_receptivity_or_srs_signal(
    tmp_path: Path,
) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 8, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)

    async def not_receptive(_expression: str) -> bool:
        return False

    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 1,
                "scheduler": {
                    "receptive_when": "{{ false }}",
                    "defer_window_minutes": 30,
                },
            },
        )
        await storage.repositories.scheduler.async_materialize_day(
            profile_id="profile-scheduler",
            scheduler_config_version=1,
            seed="receptive",
            start_utc="2026-09-24T00:00:00+00:00",
            end_utc="2026-09-25T00:00:00+00:00",
            now_utc=clock.now().isoformat(),
            slots=(
                {
                    "slot_id": "slot-receptive",
                    "track_id": None,
                    "target_id": None,
                    "slot_type": "learning",
                    "scheduled_for_utc": clock.now().isoformat(),
                },
            ),
            updated_at_utc=clock.now().isoformat(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
            receptive_evaluator=not_receptive,
        )

        decision = await service.async_prepare_delivery("slot-receptive")
        assert decision == {
            "slot_id": "slot-receptive",
            "ready": False,
            "status": "deferred",
            "reason": "receptive_when_false",
            "deferred_until_utc": "2026-09-24T08:30:00+00:00",
            "defer_exhausted": False,
        }
        slot = await storage.repositories.scheduler.async_get_slot("slot-receptive")
        assert slot is not None
        assert slot["status"] == "deferred"
        assert slot["defer_reason"] == "receptive_when_false"
        assert (
            await storage.repositories.scheduler.async_get_receptivity_sample(
                "slot-receptive"
            )
            is None
        )
        assert await storage.repositories.review_events.async_list_scope_events(
            profile_id="profile-scheduler",
            track_id=None,
        ) == ()

        clock.set(datetime(2026, 9, 24, 8, 31, tzinfo=UTC))
        exhausted = await service.async_prepare_delivery("slot-receptive")
        assert exhausted["ready"] is False
        assert exhausted["reason"] == "not_receptive_defer_window_exhausted"
        assert exhausted["defer_exhausted"] is True
        assert (
            await storage.repositories.scheduler.async_get_receptivity_sample(
                "slot-receptive"
            )
            is None
        )
    finally:
        await storage.async_close()


async def test_delivery_collects_observational_receptivity_features_only(
    tmp_path: Path,
) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 8, 15, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)

    async def receptive(_expression: str) -> bool:
        return True

    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={
                "daily_push_budget": 1,
                "scheduler": {
                    "receptive_when": "{{ true }}",
                    "defer_window_minutes": 30,
                },
            },
        )
        await storage.repositories.scheduler.async_materialize_day(
            profile_id="profile-scheduler",
            scheduler_config_version=1,
            seed="receptive",
            start_utc="2026-09-24T00:00:00+00:00",
            end_utc="2026-09-25T00:00:00+00:00",
            now_utc=clock.now().isoformat(),
            slots=(
                {
                    "slot_id": "slot-delivered",
                    "track_id": None,
                    "target_id": None,
                    "slot_type": "quiz",
                    "scheduled_for_utc": clock.now().isoformat(),
                },
            ),
            updated_at_utc=clock.now().isoformat(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
            receptive_evaluator=receptive,
        )

        decision = await service.async_prepare_delivery("slot-delivered")
        assert decision["ready"] is True
        assert decision["reason"] == "receptive"

        delivered = await service.async_record_delivery(slot_id="slot-delivered")
        assert delivered["timezone_name"] == "Europe/Paris"
        assert delivered["weekday"] == 3
        assert delivered["local_hour"] == 10
        assert delivered["delivered"] is True
        assert delivered["cleared"] is False
        assert delivered["answered"] is False
        assert delivered["delivery_to_action_ms"] is None

        action = await service.async_record_receptivity_action(
            slot_id="slot-delivered",
            action="answered",
            action_at_utc=clock.now() + timedelta(milliseconds=2500),
        )
        assert action["answered"] is True
        assert action["cleared"] is False
        assert action["delivery_to_action_ms"] == 2500
        assert await storage.repositories.review_events.async_list_scope_events(
            profile_id="profile-scheduler",
            track_id=None,
        ) == ()
    finally:
        await storage.async_close()


async def test_routine_hook_materializes_bounded_content_free_slots(tmp_path: Path) -> None:
    clock = FixedClock(datetime(2026, 9, 24, 19, 0, tzinfo=UTC))
    storage = await _storage(tmp_path, clock)
    try:
        await _profile(
            storage,
            now=clock.now(),
            settings={"daily_push_budget": 2},
        )
        await _track(
            storage,
            track_id="track-routine",
            priority=1,
            learning_count=0,
            now=clock.now(),
        )
        await _target(
            storage,
            target_id="target-routine",
            daily_push_budget=2,
            minimum_gap_seconds=0,
            maximum_notifications_per_hour=2,
            now=clock.now(),
        )
        service = SchedulerService(
            storage.repositories.profiles,
            storage.repositories.tracks,
            storage.repositories.notification_targets,
            storage.repositories.scheduler,
            storage.repositories.settings,
            clock=clock,
        )

        bedtime = await service.async_trigger_routine(
            profile_id="profile-scheduler",
            routine_type="pre_sleep_consolidation",
        )
        assert bedtime["slot_type"] == "pre_sleep_consolidation"
        assert bedtime["track_id"] == "track-routine"
        assert bedtime["target_id"] == "target-routine"
        assert "card_key" not in bedtime

        morning = await service.async_trigger_routine(
            profile_id="profile-scheduler",
            routine_type="morning_first_review",
        )
        assert morning["slot_type"] == "morning_first_review"

        with pytest.raises(
            ValueError,
            match="profile daily push budget is exhausted",
        ):
            await service.async_trigger_routine(
                profile_id="profile-scheduler",
                routine_type="pre_sleep_consolidation",
                track_id="track-routine",
            )
    finally:
        await storage.async_close()


async def test_runtime_receptive_when_uses_home_assistant_template(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    now = await runtime.scheduler.async_effective_now()
    await runtime.storage.repositories.profiles.async_insert(
        ProfileRecord(
            profile_id="profile-receptive-ha",
            name="Receptive",
            preset="custom",
            timezone="Europe/Paris",
            settings={
                "daily_push_budget": 1,
                "scheduler": {
                    "receptive_when": (
                        "{{ is_state('binary_sensor.locklearn_receptive', 'on') }}"
                    ),
                    "defer_window_minutes": 0,
                },
            },
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )
    await runtime.storage.repositories.scheduler.async_materialize_day(
        profile_id="profile-receptive-ha",
        scheduler_config_version=1,
        seed="ha-template",
        start_utc=(now - timedelta(hours=1)).isoformat(),
        end_utc=(now + timedelta(hours=1)).isoformat(),
        now_utc=now.isoformat(),
        slots=(
            {
                "slot_id": "slot-ha-template",
                "track_id": None,
                "target_id": None,
                "slot_type": "learning",
                "scheduled_for_utc": now.isoformat(),
            },
        ),
        updated_at_utc=now.isoformat(),
    )

    hass.states.async_set("binary_sensor.locklearn_receptive", "off")
    blocked = await runtime.scheduler.async_prepare_delivery("slot-ha-template")
    assert blocked["ready"] is False
    assert blocked["reason"] == "not_receptive_defer_window_exhausted"

    hass.states.async_set("binary_sensor.locklearn_receptive", "on")
    ready = await runtime.scheduler.async_prepare_delivery("slot-ha-template")
    assert ready["ready"] is True
    assert ready["reason"] == "receptive"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_ha_entity_routine_bridge_triggers_on_transition_to_on(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    now = await runtime.scheduler.async_effective_now()
    await runtime.storage.repositories.profiles.async_insert(
        ProfileRecord(
            profile_id="profile-routine-ha",
            name="Routine",
            preset="custom",
            timezone="Europe/Paris",
            settings={
                "daily_push_budget": 2,
                "scheduler": {
                    "routine_triggers": {
                        "pre_sleep_consolidation": ["input_boolean.locklearn_bedtime"]
                    }
                },
            },
            created_at_utc=now.isoformat(),
            updated_at_utc=now.isoformat(),
        )
    )
    await runtime.scheduler_ha.async_refresh()

    hass.states.async_set("input_boolean.locklearn_bedtime", "off")
    await hass.async_block_till_done()
    hass.states.async_set("input_boolean.locklearn_bedtime", "on")
    await hass.async_block_till_done()

    slots = await runtime.storage.repositories.scheduler.async_list_slots(
        profile_id="profile-routine-ha",
        start_utc=(now - timedelta(days=1)).isoformat(),
        end_utc=(now + timedelta(days=1)).isoformat(),
    )
    assert [slot["slot_type"] for slot in slots] == ["pre_sleep_consolidation"]

    hass.states.async_set("input_boolean.locklearn_bedtime", "on")
    await hass.async_block_till_done()
    repeated = await runtime.storage.repositories.scheduler.async_list_slots(
        profile_id="profile-routine-ha",
        start_utc=(now - timedelta(days=1)).isoformat(),
        end_utc=(now + timedelta(days=1)).isoformat(),
    )
    assert len(repeated) == 1

    assert await hass.config_entries.async_unload(entry.entry_id)


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
