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


@dataclass(frozen=True)
class _Prepared:
    state: str

    @property
    def payload(self) -> dict[str, Any]:
        return {"selection": {"progress_state": self.state}}


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
    def __init__(
        self,
        states: list[dict[str, Any]],
        *,
        prepared_states: tuple[str, ...] = (),
    ) -> None:
        self.states = states
        self.prepared_states = prepared_states

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
        assert session_type in {"learn", "quiz"}
        if len(self.states) > 1:
            return self.states.pop(0)
        return self.states[0]

    async def async_prepare(
        self,
        *,
        profile_id: str,
        track_id: str,
        session_type: str,
        settings: dict[str, Any],
    ) -> tuple[Any, ...]:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        assert session_type == "learn"
        assert settings == {}
        return tuple(_Prepared(state) for state in self.prepared_states)


class _Delivery:
    def __init__(self) -> None:
        self.rendered: list[Any] = []

    async def async_send(self, rendered: Any) -> object:
        self.rendered.append(rendered)
        return object()


def _learning_wait(when: str, *, available_now: int = 0) -> dict[str, Any]:
    return {
        "available_now": available_now,
        "next_available_at_utc": when,
        "blockers": [
            {
                "code": "scheduled_step",
                "count": 1,
                "until_utc": when,
                "forceable": False,
            }
        ],
    }


def _quiz_wait(when: str | None, *, available_now: int = 0) -> dict[str, Any]:
    return {
        "available_now": available_now,
        "next_available_at_utc": when,
        "blockers": [],
    }


@pytest.mark.asyncio
async def test_learn_reminder_can_arm_while_new_session_is_already_available() -> None:
    settings = _Settings()
    delivery = _Delivery()
    clock = _Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC))
    availability = _Availability(
        [
            _learning_wait("2026-09-30T20:10:00+00:00", available_now=8),
            _learning_wait("2026-09-30T20:10:00+00:00", available_now=8),
            {"available_now": 8, "next_available_at_utc": None, "blockers": []},
        ],
        prepared_states=("learning", "new", "new"),
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

        stored = next(iter(settings.values.values()))
        reminder_key = f"ready_reminder:{stored['reminder_id']}"
        service.close()
        clock.current = datetime(2026, 9, 30, 20, 10, tzinfo=UTC)
        assert await service.async_fire_due(reminder_key) == "sent"
        assert settings.values == {}
        assert len(delivery.rendered) == 1
        assert delivery.rendered[0].pedagogical_signal == "no_result"
        assert delivery.rendered[0].message == "Ton prochain rappel d’apprentissage est dû."
    finally:
        service.close()


@pytest.mark.asyncio
async def test_learn_reminder_moves_with_scheduled_step_and_can_cancel() -> None:
    settings = _Settings()
    delivery = _Delivery()
    clock = _Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC))
    availability = _Availability(
        [
            _learning_wait("2026-09-30T20:10:00+00:00", available_now=8),
            _learning_wait("2026-09-30T20:30:00+00:00", available_now=8),
        ],
        prepared_states=("new", "new"),
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
async def test_learn_reminder_does_not_fire_for_new_cards_only() -> None:
    settings = _Settings()
    delivery = _Delivery()
    clock = _Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC))
    availability = _Availability(
        [
            _learning_wait("2026-09-30T20:10:00+00:00", available_now=8),
            {"available_now": 8, "next_available_at_utc": None, "blockers": []},
        ],
        prepared_states=("new", "new", "new"),
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
        assert await service.async_fire_due(reminder_key) == "cancelled"
        assert delivery.rendered == []
        assert settings.values == {}
    finally:
        service.close()


@pytest.mark.asyncio
async def test_learn_reminder_refuses_dead_end_without_scheduled_step() -> None:
    service = ReadyReminderService(
        _Settings(),
        _Profiles(),
        _Targets(),
        cast(Any, _Availability([_quiz_wait(None)])),
        cast(Any, _Delivery()),
        clock=_Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC)),
    )
    try:
        with pytest.raises(ReadyReminderError, match="no reliable next learning step"):
            await service.async_arm(
                profile_id="profile-1",
                track_id="track-1",
                mode="learn",
            )
    finally:
        service.close()


@pytest.mark.asyncio
async def test_quiz_reminder_keeps_existing_readiness_contract() -> None:
    service = ReadyReminderService(
        _Settings(),
        _Profiles(),
        _Targets(),
        cast(Any, _Availability([_quiz_wait(None, available_now=1)])),
        cast(Any, _Delivery()),
        clock=_Clock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC)),
    )
    try:
        with pytest.raises(ReadyReminderError, match="already ready"):
            await service.async_arm(
                profile_id="profile-1",
                track_id="track-1",
                mode="quiz",
            )
    finally:
        service.close()
