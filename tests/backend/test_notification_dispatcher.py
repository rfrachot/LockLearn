"""Beta.5 passive notification dispatcher deadline tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from homeassistant.core import HomeAssistant

from custom_components.locklearn.notification_dispatcher import NotificationSchedulerDispatcher


class _Profiles:
    async def async_list_active(self) -> tuple[dict[str, Any], ...]:
        return ({"profile_id": "profile-1"},)


class _SchedulerRepository:
    def __init__(self, slots: tuple[dict[str, Any], ...]) -> None:
        self.slots = slots
        self.calls: list[tuple[str, str, str]] = []

    async def async_list_slots(
        self,
        *,
        profile_id: str,
        start_utc: str,
        end_utc: str,
    ) -> tuple[dict[str, Any], ...]:
        self.calls.append((profile_id, start_utc, end_utc))
        start = datetime.fromisoformat(start_utc)
        end = datetime.fromisoformat(end_utc)
        return tuple(
            slot
            for slot in self.slots
            if start <= datetime.fromisoformat(str(slot["scheduled_for_utc"])) < end
        )


def _runtime(repository: _SchedulerRepository) -> Any:
    return SimpleNamespace(
        storage=SimpleNamespace(
            repositories=SimpleNamespace(
                profiles=_Profiles(),
                scheduler=repository,
            )
        )
    )


def _slot(
    slot_id: str,
    scheduled_for: datetime,
    *,
    status: str = "scheduled",
    deferred_until: datetime | None = None,
) -> dict[str, Any]:
    return {
        "slot_id": slot_id,
        "profile_id": "profile-1",
        "status": status,
        "scheduled_for_utc": scheduled_for.isoformat(),
        "deferred_until_utc": None if deferred_until is None else deferred_until.isoformat(),
    }


@pytest.mark.asyncio
async def test_dispatch_due_includes_normal_and_deferred_deadlines(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    repository = _SchedulerRepository(
        (
            _slot("normal", now - timedelta(seconds=20)),
            _slot(
                "deferred",
                now - timedelta(hours=4),
                status="deferred",
                deferred_until=now - timedelta(seconds=10),
            ),
            _slot("future", now + timedelta(minutes=2)),
            _slot("stale", now - timedelta(minutes=3)),
            _slot("sent", now - timedelta(seconds=5), status="sent"),
        )
    )
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(repository)),
    )
    dispatched: list[str] = []

    async def capture(slot: dict[str, Any]) -> None:
        dispatched.append(str(slot["slot_id"]))

    monkeypatch.setattr(dispatcher, "_async_dispatch_slot", capture)
    await dispatcher._async_dispatch_due(now)

    assert dispatched == ["deferred", "normal"]
    assert repository.calls
    query_start = datetime.fromisoformat(repository.calls[0][1])
    assert query_start <= now - timedelta(hours=4)


def test_effective_due_prefers_deferred_deadline() -> None:
    scheduled = datetime(2026, 10, 4, 8, 0, tzinfo=UTC)
    deferred = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)

    assert NotificationSchedulerDispatcher._effective_due(
        _slot("scheduled", scheduled)
    ) == scheduled
    assert NotificationSchedulerDispatcher._effective_due(
        _slot(
            "deferred",
            scheduled,
            status="deferred",
            deferred_until=deferred,
        )
    ) == deferred


def test_facet_text_uses_first_renderable_text_block() -> None:
    facet = {
        "blocks": [
            {"payload": {"text": "  こんにちは  "}},
            {"payload": {"text": "ignored"}},
        ]
    }

    assert NotificationSchedulerDispatcher._facet_text(facet) == "こんにちは"
    assert NotificationSchedulerDispatcher._facet_text({"blocks": []}) == "LockLearn"
