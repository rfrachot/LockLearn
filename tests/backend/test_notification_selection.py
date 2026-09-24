"""P4.5 send-time notification selection policy tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from custom_components.locklearn.core.notification_selection import NotificationSelectionService
from custom_components.locklearn.core.selection import SelectionDecision


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakeTracks:
    def __init__(self, candidates: tuple[dict[str, Any], ...]) -> None:
        self._candidates = candidates

    async def async_get(self, track_id: str) -> dict[str, Any] | None:
        return {
            "track_id": track_id,
            "profile_id": "profile-1",
            "status": "active",
        }

    async def async_session_candidates(
        self,
        *,
        profile_id: str,
        track_id: str,
    ) -> tuple[dict[str, Any], ...]:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        return self._candidates


class FakeProfiles:
    async def async_get(self, profile_id: str) -> dict[str, Any] | None:
        assert profile_id == "profile-1"
        return {
            "profile_id": profile_id,
            "status": "active",
            "timezone": "Europe/Paris",
        }


class FakeReviews:
    def __init__(self, introduced: frozenset[str] = frozenset()) -> None:
        self._introduced = introduced
        self.requested_dates: list[str] = []

    async def async_introduced_card_keys(
        self,
        *,
        profile_id: str,
        track_id: str,
        local_date: str,
    ) -> frozenset[str]:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        self.requested_dates.append(local_date)
        return self._introduced


class FakeConstraints:
    async def async_evaluate(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        learning_item_id: str,
        state: str,
    ) -> SelectionDecision:
        return SelectionDecision(eligible=True, reasons=())


class FakeScheduler:
    def __init__(
        self,
        *,
        slot_type: str = "learning",
        teaser_count: int = 0,
    ) -> None:
        self.slot = {
            "slot_id": "slot-1",
            "profile_id": "profile-1",
            "track_id": "track-1",
            "target_id": "target-1",
            "slot_type": slot_type,
            "card_key": None,
            "learning_item_id": None,
            "prompt_facet_id": None,
            "answer_facet_id": None,
            "selection_reason": None,
        }
        self.teaser_count = teaser_count
        self.bind_count = 0

    async def async_get_slot(self, slot_id: str) -> dict[str, Any] | None:
        assert slot_id == "slot-1"
        return dict(self.slot)

    async def async_bind_content_selection(
        self,
        *,
        slot_id: str,
        card: Any,
        selection_reason: str,
        updated_at_utc: str,
    ) -> bool:
        assert slot_id == "slot-1"
        assert updated_at_utc
        if self.slot["card_key"] is not None:
            return False
        self.bind_count += 1
        self.slot.update(
            {
                "card_key": card.card_key,
                "learning_item_id": card.learning_item_id,
                "prompt_facet_id": card.prompt_facet_id,
                "answer_facet_id": card.answer_facet_id,
                "selection_reason": selection_reason,
            }
        )
        return True

    async def async_count_selected_teasers(
        self,
        *,
        profile_id: str,
        start_utc: str,
        end_utc: str,
    ) -> int:
        assert profile_id == "profile-1"
        assert start_utc < end_utc
        return self.teaser_count


def candidate(
    card_key: str,
    *,
    state: str,
    due: str | None = None,
    difficulty: float = 1.0,
    self_known_count: int = 0,
    last_seen: str | None = None,
    last_verified: str | None = None,
    position: int = 0,
) -> dict[str, Any]:
    return {
        "card_key": card_key,
        "learning_item_id": f"item-{card_key}",
        "prompt_facet_id": f"prompt-{card_key}",
        "answer_facet_id": f"answer-{card_key}",
        "content_type": "vocabulary",
        "state": state,
        "next_due_at_utc": due,
        "pack_position": position,
        "user_state": "active",
        "suspend_until_utc": None,
        "difficulty_factor": difficulty,
        "last_verified_at_utc": last_verified,
        "last_seen_at_utc": last_seen,
        "self_known_count": self_known_count,
        "verified_correct_count": 0,
        "verified_wrong_count": 0,
        "confusable_group_ids": (),
    }


def service(
    candidates: tuple[dict[str, Any], ...],
    *,
    slot_type: str = "learning",
    teaser_count: int = 0,
    introduced: frozenset[str] = frozenset(),
) -> tuple[NotificationSelectionService, FakeScheduler, FakeReviews]:
    scheduler = FakeScheduler(slot_type=slot_type, teaser_count=teaser_count)
    reviews = FakeReviews(introduced)
    selector = NotificationSelectionService(
        FakeTracks(candidates),
        FakeProfiles(),
        reviews,
        scheduler,
        FakeConstraints(),
        clock=FixedClock(datetime(2026, 9, 24, 10, 0, tzinfo=UTC)),
    )
    return selector, scheduler, reviews


async def test_relearning_due_beats_review_leech_calibration_and_teaser() -> None:
    candidates = (
        candidate("new", state="new", position=5),
        candidate(
            "calibration",
            state="review",
            due="2026-09-30T10:00:00+00:00",
            self_known_count=2,
            last_seen="2026-09-24T09:00:00+00:00",
            last_verified="2026-09-20T09:00:00+00:00",
            position=4,
        ),
        candidate(
            "leech",
            state="leech",
            due="2026-09-24T09:00:00+00:00",
            difficulty=0.7,
            position=3,
        ),
        candidate(
            "review",
            state="review",
            due="2026-09-24T08:00:00+00:00",
            position=2,
        ),
        candidate(
            "relearning",
            state="relearning",
            due="2026-09-24T09:30:00+00:00",
            position=1,
        ),
    )
    selector, scheduler, _reviews = service(candidates)

    selected = await selector.async_select_for_slot("slot-1")

    assert selected is not None
    assert selected.card.card_key == "relearning"
    assert selected.reason == "relearning_due"
    assert scheduler.bind_count == 1


async def test_future_review_is_not_used_unless_calibration_is_needed() -> None:
    candidates = (
        candidate(
            "future",
            state="review",
            due="2026-10-10T10:00:00+00:00",
            position=1,
        ),
        candidate(
            "calibration",
            state="review",
            due="2026-10-10T10:00:00+00:00",
            self_known_count=1,
            last_seen="2026-09-24T09:00:00+00:00",
            last_verified=None,
            position=2,
        ),
    )
    selector, _scheduler, _reviews = service(candidates)

    selected = await selector.async_select_for_slot("slot-1")

    assert selected is not None
    assert selected.card.card_key == "calibration"
    assert selected.reason == "calibration_needed"


async def test_new_teaser_is_learning_only_and_bounded_to_two_per_day() -> None:
    candidates = (candidate("new", state="new"),)

    selector, _scheduler, _reviews = service(candidates, slot_type="quiz")
    assert await selector.async_select_for_slot("slot-1") is None

    selector, _scheduler, _reviews = service(candidates, teaser_count=2)
    assert await selector.async_select_for_slot("slot-1") is None

    selector, _scheduler, _reviews = service(candidates, teaser_count=1)
    selected = await selector.async_select_for_slot("slot-1")
    assert selected is not None
    assert selected.reason == "teaser_new"


async def test_routine_slots_filter_to_same_day_or_previous_day_introductions() -> None:
    candidates = (
        candidate("today-card", state="learning"),
        candidate("other-card", state="learning"),
    )
    selector, scheduler, reviews = service(
        candidates,
        slot_type="pre_sleep_consolidation",
        introduced=frozenset({"today-card"}),
    )

    selected = await selector.async_select_for_slot("slot-1")

    assert selected is not None
    assert selected.card.card_key == "today-card"
    assert selected.reason == "routine_pre_sleep"
    assert reviews.requested_dates == ["2026-09-24"]

    scheduler.slot.update(
        {
            "card_key": None,
            "learning_item_id": None,
            "prompt_facet_id": None,
            "answer_facet_id": None,
            "selection_reason": None,
            "slot_type": "morning_first_review",
        }
    )
    scheduler.bind_count = 0
    selected = await selector.async_select_for_slot("slot-1")
    assert selected is not None
    assert reviews.requested_dates[-1] == "2026-09-23"


async def test_persisted_selection_is_idempotent_across_retry() -> None:
    candidates = (
        candidate(
            "review",
            state="review",
            due="2026-09-24T09:00:00+00:00",
        ),
    )
    selector, scheduler, _reviews = service(candidates)

    first = await selector.async_select_for_slot("slot-1")
    second = await selector.async_select_for_slot("slot-1")

    assert first == second
    assert scheduler.bind_count == 1
