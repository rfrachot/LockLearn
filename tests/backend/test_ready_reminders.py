"""Beta.5 one-shot readiness reminder contract tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, cast

import pytest

from custom_components.locklearn.core.ready_reminders import (
    ReadyReminderError,
    ReadyReminderService,
)


@dataclass
class _Clock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class _Settings:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def async_set(self, key: str, value: Any, *, updated_at_utc: str) -> None:
        del updated_at_utc
        self.values[key] = value

    async def async_get(self, key: str) -> Any | None:
        return self.values.get(key)

    async def async_delete(self, key: str) -> bool:
        return self.values.pop(key, None) is not None

    async def async_list_prefix(self, prefix: str) -> dict[str, Any]:
        return {key: value for key, value in self.values.items() if key.startswith(prefix)}


class _Profiles:
    async def async_get(self, profile_id: str) -> dict[str, Any] | None:
        if profile_id != "profile-1":
            return None
        return {"profile_id": profile_id, "name": "Learner"}


class _Targets:
    target: ClassVar[dict[str, Any]] = {
        "target_id": "target-1",
        "profile_id": "profile-1",
        "enabled": True,
        "shared_device": False,
        "lockscreen_visibility": "private",
    }

    async def async_get(self, target_id: str) -> dict[str, Any] | None:
        return dict(self.target) if target_id == "target-1" else None

    async def async_list_for_profile(
        self, profile_id: str, *, enabled_only: bool = True
    ) -> tuple[dict[str, Any], ...]:
        assert enabled_only is True
        return (dict(self.target),) if profile_id == "profile-1" else ()


class _Availability:
    def __init__(self, states: list[dict[str, Any]]) -> None:
        self.states = states

    async def async_availability(
        self,
        *,
        profile_id: str,
        track_id: str,
        session_type: str,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del settings
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        assert session_type == "learn"
        if len(self.states) > 1:
            return self.states.pop(0)
        return self.states[0]


class _Delivery:
    def __init__(self) -> None:
        self.rendered: list[Any] = []

    async def async_send(self, rendered: Any) -> object:
        self.rendered.append(rendered)
        return object()


def _waiting(when: str) -> dict[str, Any]:
    return {"available_now": 0, "next_available_at_utc": when}


@pytest.mark.asyncio
async def test_reminder_scope_is_idempotent_and_fires_only_after_revalidation() -> None:
    settings = _Settings()
    delivery = _Delivery()
    clock = _Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC))
    availability = _Availability(
        [
            _waiting("2026-09-30T20:10:00+00:00"),
            _waiting("2026-09-30T20:10:00+00:00"),
            {"available_now": 1, "next_available_at_utc": None},
        ]
    )
    service = ReadyReminderService(
        settings,
        _Profiles(),
        _Targets(),
        cast(Any, availability),
        cast(Any, delivery),
        clock=clock,
    )
    try:
        first = await service.async_arm(
            profile_id="profile-1",
            track_id="track-1",
            mode="learn",
        )
        second = await service.async_arm(
            profile_id="profile-1",
            track_id="track-1",
            mode="learn",
        )
        assert first["active"] is True
        assert second["active"] is True
        assert len(settings.values) == 1

        key = next(iter(settings.values.values()))
        reminder_key = f"ready_reminder:{key['reminder_id']}"
        service.close()
        clock.current = datetime(2026, 9, 30, 20, 10, tzinfo=UTC)
        assert await service.async_fire_due(reminder_key) == "sent"
        assert settings.values == {}
        assert len(delivery.rendered) == 1
        assert delivery.rendered[0].pedagogical_signal == "no_result"
    finally:
        service.close()


@pytest.mark.asyncio
async def test_reminder_moves_with_effective_availability_and_can_cancel() -> None:
    settings = _Settings()
    delivery = _Delivery()
    clock = _Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC))
    availability = _Availability(
        [
            _waiting("2026-09-30T20:10:00+00:00"),
            _waiting("2026-09-30T20:30:00+00:00"),
        ]
    )
    service = ReadyReminderService(
        settings,
        _Profiles(),
        _Targets(),
        cast(Any, availability),
        cast(Any, delivery),
        clock=clock,
    )
    try:
        await service.async_arm(
            profile_id="profile-1",
            track_id="track-1",
            mode="learn",
        )
        stored = next(iter(settings.values.values()))
        reminder_key = f"ready_reminder:{stored['reminder_id']}"
        service.close()
        clock.current = datetime(2026, 9, 30, 20, 10, tzinfo=UTC)
        assert await service.async_fire_due(reminder_key) == "rescheduled"
        assert (
            next(iter(settings.values.values()))["scheduled_for_utc"] == "2026-09-30T20:30:00+00:00"
        )
        assert delivery.rendered == []

        result = await service.async_cancel(
            profile_id="profile-1",
            track_id="track-1",
            mode="learn",
        )
        assert result["active"] is False
        assert settings.values == {}
    finally:
        service.close()


@pytest.mark.asyncio
async def test_reminder_refuses_dead_end_without_reliable_time() -> None:
    service = ReadyReminderService(
        _Settings(),
        _Profiles(),
        _Targets(),
        cast(Any, _Availability([{"available_now": 0, "next_available_at_utc": None}])),
        cast(Any, _Delivery()),
        clock=_Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC)),
    )
    try:
        with pytest.raises(ReadyReminderError, match="no reliable"):
            await service.async_arm(
                profile_id="profile-1",
                track_id="track-1",
                mode="learn",
            )
    finally:
        service.close()
