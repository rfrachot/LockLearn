"""Beta.5 passive notification dispatcher deadline tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from homeassistant.core import HomeAssistant

from custom_components.locklearn.notification_dispatcher import NotificationSchedulerDispatcher
from custom_components.locklearn.notifications.delivery import NotificationDeliveryError


class _Profiles:
    async def async_list_active(self) -> tuple[dict[str, Any], ...]:
        return ({"profile_id": "profile-1"},)


class _SchedulerRepository:
    def __init__(self, slots: tuple[dict[str, Any], ...]) -> None:
        self.slots = slots
        self.calls: list[tuple[str, str, str]] = []
        self.expire_calls: list[tuple[str, str]] = []

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

    async def async_list_pending_slots(
        self,
        *,
        profile_id: str,
        start_utc: str,
        end_utc: str,
    ) -> tuple[dict[str, Any], ...]:
        self.calls.append((profile_id, start_utc, end_utc))
        start = datetime.fromisoformat(start_utc)
        end = datetime.fromisoformat(end_utc)
        result = []
        for slot in self.slots:
            if str(slot.get("status")) not in {"scheduled", "deferred"}:
                continue
            raw = (
                slot.get("deferred_until_utc")
                if str(slot.get("status")) == "deferred"
                else slot.get("scheduled_for_utc")
            )
            if isinstance(raw, str) and start <= datetime.fromisoformat(raw) < end:
                result.append(slot)
        return tuple(result)

    async def async_expire_before(self, *, before_utc: str, updated_at_utc: str) -> int:
        self.expire_calls.append((before_utc, updated_at_utc))
        return 0


def _runtime(repository: _SchedulerRepository, scheduler: Any | None = None) -> Any:
    return SimpleNamespace(
        scheduler=scheduler,
        storage=SimpleNamespace(
            repositories=SimpleNamespace(
                profiles=_Profiles(),
                scheduler=repository,
            )
        ),
    )


class _PipelineScheduler:
    def __init__(self, slot: dict[str, Any], events: list[str]) -> None:
        self.slot = slot
        self.events = events
        self.recorded: list[dict[str, Any]] = []

    async def async_prepare_delivery(self, slot_id: str) -> dict[str, Any]:
        assert slot_id == self.slot["slot_id"]
        return {
            "slot_id": slot_id,
            "ready": self.slot["status"] in {"scheduled", "deferred"},
        }

    async def async_record_delivery(self, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["prepared"] is True
        assert self.slot["status"] in {"scheduled", "deferred"}
        self.events.append("record_delivery")
        self.recorded.append(kwargs)
        self.slot["status"] = "sent"
        return {}


class _PipelineSchedulerRepository:
    def __init__(self, slot: dict[str, Any], events: list[str]) -> None:
        self.slot = slot
        self.events = events

    async def async_get_slot(self, slot_id: str) -> dict[str, Any] | None:
        return dict(self.slot) if slot_id == self.slot["slot_id"] else None

    async def async_set_slot_status(
        self, slot_id: str, status: str, *, updated_at_utc: str
    ) -> bool:
        del updated_at_utc
        assert slot_id == self.slot["slot_id"]
        self.events.append(f"status:{status}")
        self.slot["status"] = status
        return True


class _PipelineInteractions:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.cleared: list[str] = []

    async def async_create(self, **kwargs: Any) -> Any:
        self.events.append("create_interaction")
        return SimpleNamespace(
            interaction_id="interaction-1",
            token="token-1",
        )

    async def async_clear_tag(self, *, tag: str) -> None:
        self.events.append("clear_interaction")
        self.cleared.append(tag)


class _PipelineDelivery:
    def __init__(self, events: list[str], *, fail: bool = False) -> None:
        self.events = events
        self.fail = fail
        self.rendered: list[Any] = []

    async def async_send(self, rendered: Any) -> object:
        self.events.append("notify")
        self.rendered.append(rendered)
        if self.fail:
            raise NotificationDeliveryError("test delivery failure")
        return object()


class _PipelineReviews:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.recorded: list[dict[str, Any]] = []

    async def async_record(self, **kwargs: Any) -> None:
        self.events.append("review")
        self.recorded.append(kwargs)


def _pipeline_runtime(
    *,
    slot: dict[str, Any],
    events: list[str],
    fail_delivery: bool = False,
    action_capable: bool = False,
) -> tuple[Any, _PipelineScheduler, _PipelineDelivery, _PipelineReviews]:
    scheduler = _PipelineScheduler(slot, events)
    repository = _PipelineSchedulerRepository(slot, events)
    delivery = _PipelineDelivery(events, fail=fail_delivery)
    reviews = _PipelineReviews(events)
    target = {
        "target_id": "target-1",
        "profile_id": "profile-1",
        "device_registry_id": "device-1",
        "platform": "android",
        "enabled": True,
        "capabilities": (
            {"action_data": "supported", "visible_actions": 2} if action_capable else {}
        ),
        "lockscreen_visibility": "private",
    }
    runtime = SimpleNamespace(
        scheduler=scheduler,
        storage=SimpleNamespace(
            repositories=SimpleNamespace(
                scheduler=repository,
                profiles=SimpleNamespace(
                    async_get=lambda profile_id: _async_value(
                        {"profile_id": profile_id, "name": "Learner"}
                    ),
                ),
                notification_targets=SimpleNamespace(
                    async_get=lambda target_id: _async_value(
                        target if target_id == "target-1" else None
                    ),
                ),
                progress=SimpleNamespace(
                    async_get=lambda **kwargs: _async_value(None),
                ),
                tracks=SimpleNamespace(
                    async_card_reference=lambda **kwargs: _async_value(
                        SimpleNamespace(
                            card_key="card-1",
                            learning_item_id="item-1",
                            prompt_facet_id="prompt-1",
                            answer_facet_id="answer-1",
                        )
                    ),
                ),
            ),
            content_generations=SimpleNamespace(
                active_metadata=SimpleNamespace(generation_id="generation-1")
            ),
        ),
        presentation=SimpleNamespace(
            async_for_card=lambda **kwargs: _async_value(
                {
                    "prompt": {"blocks": [{"payload": {"text": "Prompt"}}]},
                    "answer": {"blocks": [{"payload": {"text": "Answer"}}]},
                }
            ),
        ),
        notification_delivery=delivery,
        notification_interactions=_PipelineInteractions(events),
        review_policy=SimpleNamespace(policy_version="policy-1"),
        reviews=reviews,
    )
    return runtime, scheduler, delivery, reviews


async def _async_value(value: Any) -> Any:
    return value


def _pipeline_slot(*, slot_type: str = "learning") -> dict[str, Any]:
    return {
        "slot_id": "slot-1",
        "profile_id": "profile-1",
        "track_id": "track-1",
        "target_id": "target-1",
        "card_key": "card-1",
        "slot_type": slot_type,
        "selection_reason": "teaser_new",
        "status": "scheduled",
    }


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
async def test_dispatch_due_includes_normal_and_deferred_deadlines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    repository = _SchedulerRepository(
        (
            _slot("normal", now - timedelta(seconds=20)),
            _slot(
                "deferred",
                now - timedelta(days=3),
                status="deferred",
                deferred_until=now - timedelta(seconds=10),
            ),
            _slot("future", now + timedelta(minutes=2)),
            _slot("stale", now - timedelta(minutes=7)),
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

    assert dispatched == ["normal", "deferred"]
    assert repository.calls
    query_start = datetime.fromisoformat(repository.calls[0][1])
    assert query_start == now - timedelta(minutes=6)


@pytest.mark.asyncio
async def test_callback_slightly_early_defers_once_then_dispatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    due = datetime(2026, 10, 4, 12, 0, 0, 500000, tzinfo=UTC)
    slot = _slot("early", due)
    repository = _SchedulerRepository((slot,))
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(repository)),
    )
    dispatched: list[str] = []

    async def capture(current: dict[str, Any]) -> None:
        dispatched.append(str(current["slot_id"]))
        current["status"] = "sent"

    monkeypatch.setattr(dispatcher, "_async_dispatch_slot", capture)

    await dispatcher._async_dispatch_due(due - timedelta(milliseconds=250))
    assert dispatched == []
    assert slot["status"] == "scheduled"

    await dispatcher._async_dispatch_due(due + timedelta(milliseconds=250))
    assert dispatched == ["early"]


@pytest.mark.asyncio
async def test_delayed_wake_inside_grace_dispatches_without_expiration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 10, 4, 12, 3, tzinfo=UTC)
    slot = _slot("delayed", now - timedelta(minutes=3))
    repository = _SchedulerRepository((slot,))
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(repository)),
    )
    dispatched: list[str] = []

    async def capture(current: dict[str, Any]) -> None:
        dispatched.append(str(current["slot_id"]))

    monkeypatch.setattr(dispatcher, "_async_dispatch_slot", capture)

    await dispatcher._async_dispatch_due(now)

    assert dispatched == ["delayed"]
    assert repository.expire_calls == []


@pytest.mark.asyncio
async def test_near_due_slot_is_guarded_from_materialization_reconciliation() -> None:
    now = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    repository = _SchedulerRepository((_slot("near", now + timedelta(milliseconds=250)),))
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(repository)),
    )

    assert await dispatcher._async_has_guarded_pending(now) is True


@pytest.mark.asyncio
async def test_stale_expiration_starts_only_after_dispatch_grace() -> None:
    now = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    repository = _SchedulerRepository(())
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(repository)),
    )

    await dispatcher._async_expire_stale(now)

    assert repository.expire_calls == [((now - timedelta(minutes=6)).isoformat(), now.isoformat())]


@pytest.mark.asyncio
async def test_startup_reconciles_only_after_dispatch_and_preserves_recovery_grace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, Any]] = []

    class _CycleScheduler:
        async def async_reconcile(self, **kwargs: Any) -> None:
            events.append(("reconcile", kwargs))

        async def async_generate(self, **kwargs: Any) -> None:
            events.append(("generate", kwargs))

    repository = _SchedulerRepository(())
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(repository, _CycleScheduler())),
    )

    async def capture_dispatch(_now: datetime) -> None:
        events.append(("dispatch", None))

    monkeypatch.setattr(dispatcher, "_async_dispatch_due", capture_dispatch)
    monkeypatch.setattr(dispatcher, "_async_schedule_next", _async_noop)

    await dispatcher._async_cycle(startup=True)

    assert [name for name, _value in events] == ["dispatch", "reconcile", "generate"]
    assert events[1][1]["reason"] == "startup"
    assert events[1][1]["recovery_grace"] == timedelta(minutes=6)
    assert events[2][1]["recovery_grace"] == timedelta(minutes=6)


@pytest.mark.asyncio
async def test_timer_rearms_and_close_cancels_previous_wake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armed: list[datetime] = []
    cancelled: list[bool] = []

    def track(_hass: HomeAssistant, _callback: Any, point: datetime) -> Any:
        armed.append(point)

        def cancel() -> None:
            cancelled.append(True)

        return cancel

    monkeypatch.setattr(
        "custom_components.locklearn.notification_dispatcher.async_track_point_in_utc_time",
        track,
    )
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, _runtime(_SchedulerRepository(()))),
    )

    await dispatcher._async_schedule_next()
    first = armed[-1]
    await dispatcher._async_schedule_next()
    second = armed[-1]

    assert len(armed) == 2
    assert first.tzinfo is not None
    assert second.tzinfo is not None
    assert cancelled == [True]

    dispatcher.close()
    assert cancelled == [True, True]


async def _async_noop() -> None:
    return None


def test_effective_due_prefers_deferred_deadline() -> None:
    scheduled = datetime(2026, 10, 4, 8, 0, tzinfo=UTC)
    deferred = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)

    assert (
        NotificationSchedulerDispatcher._effective_due(_slot("scheduled", scheduled)) == scheduled
    )
    assert (
        NotificationSchedulerDispatcher._effective_due(
            _slot(
                "deferred",
                scheduled,
                status="deferred",
                deferred_until=deferred,
            )
        )
        == deferred
    )


def test_facet_text_uses_first_renderable_text_block() -> None:
    facet = {
        "blocks": [
            {"payload": {"text": "  こんにちは  "}},
            {"payload": {"text": "ignored"}},
        ]
    }

    assert NotificationSchedulerDispatcher._facet_text(facet) == "こんにちは"
    assert NotificationSchedulerDispatcher._facet_text({"blocks": []}) == "LockLearn"


@pytest.mark.asyncio
async def test_direct_teaser_records_exposure_only_after_success_and_is_idempotent() -> None:
    events: list[str] = []
    slot = _pipeline_slot()
    runtime, scheduler, delivery, reviews = _pipeline_runtime(
        slot=slot,
        events=events,
    )
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, runtime),
    )

    await dispatcher._async_dispatch_slot(slot)
    await dispatcher._async_dispatch_slot(slot)

    assert events.index("notify") < events.index("record_delivery") < events.index("review")
    assert delivery.rendered[0].pedagogical_signal == "exposure_only"
    assert reviews.recorded[0]["retrieval_occurred"] is False
    assert len(reviews.recorded) == 1
    assert scheduler.slot["status"] == "consumed"


@pytest.mark.asyncio
async def test_failed_direct_teaser_delivery_does_not_create_introduction() -> None:
    events: list[str] = []
    slot = _pipeline_slot()
    runtime, scheduler, _delivery, reviews = _pipeline_runtime(
        slot=slot,
        events=events,
        fail_delivery=True,
    )
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, runtime),
    )

    with pytest.raises(NotificationDeliveryError):
        await dispatcher._async_dispatch_slot(slot)

    assert "notify" in events
    assert "record_delivery" not in events
    assert "review" not in events
    assert reviews.recorded == []
    assert scheduler.slot["status"] == "scheduled"


@pytest.mark.asyncio
async def test_actionable_delivery_keeps_interaction_after_success() -> None:
    events: list[str] = []
    slot = _pipeline_slot()
    runtime, scheduler, delivery, _reviews = _pipeline_runtime(
        slot=slot,
        events=events,
        action_capable=True,
    )
    dispatcher = NotificationSchedulerDispatcher(
        cast(HomeAssistant, object()),
        cast(Any, runtime),
    )

    await dispatcher._async_dispatch_slot(slot)

    assert delivery.rendered[0].mode.value == "two_step_reveal"
    assert events.index("create_interaction") < events.index("notify")
    assert "clear_interaction" not in events
    assert scheduler.slot["status"] == "sent"
