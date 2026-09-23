"""P3.9 fatigue-aware session selection tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from custom_components.locklearn.core.selection import SelectionDecision
from custom_components.locklearn.core.session_selection import (
    SessionSelectionError,
    SessionSelectionService,
)


@dataclass
class _FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class _Tracks:
    def __init__(
        self,
        candidates: tuple[dict[str, Any], ...],
        *,
        weights: dict[str, float] | None = None,
        track_settings: dict[str, Any] | None = None,
    ) -> None:
        self.candidates = candidates
        self.weights = weights or {
            "vocabulary": 0.5,
            "grammar": 0.3,
            "kanji": 0.2,
        }
        self.track_settings = track_settings or {}

    async def async_get(self, track_id: str) -> dict[str, Any] | None:
        if track_id != "track-1":
            return None
        return {
            "track_id": track_id,
            "profile_id": "profile-1",
            "settings": dict(self.track_settings),
        }

    async def async_get_content_weights(self, track_id: str) -> dict[str, float]:
        assert track_id == "track-1"
        return dict(self.weights)

    async def async_session_candidates(
        self,
        *,
        profile_id: str,
        track_id: str,
    ) -> tuple[dict[str, Any], ...]:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        return self.candidates


class _Profiles:
    def __init__(self, *, max_new: int = 8, session_length: int = 20) -> None:
        self.max_new = max_new
        self.session_length = session_length

    async def async_get(self, profile_id: str) -> dict[str, Any] | None:
        if profile_id != "profile-1":
            return None
        return {
            "profile_id": profile_id,
            "timezone": "Europe/Paris",
            "settings": {
                "max_new_per_day_cards": self.max_new,
                "session_length_cards": self.session_length,
            },
        }


class _Reviews:
    def __init__(
        self,
        *,
        introductions: int = 0,
        verified_results: tuple[str, ...] = (),
    ) -> None:
        self.introductions = introductions
        self.verified_results = verified_results

    async def async_count_introductions(
        self,
        *,
        profile_id: str,
        track_id: str,
        local_date: str,
    ) -> int:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        assert local_date == "2026-09-23"
        return self.introductions

    async def async_recent_session_verified_results(
        self,
        session_id: str,
        *,
        limit: int,
    ) -> tuple[str, ...]:
        assert session_id == "session-1"
        return self.verified_results[:limit]


class _Constraints:
    async def async_evaluate(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        learning_item_id: str,
        state: str,
    ) -> SelectionDecision:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        assert card_key
        assert learning_item_id
        assert state in {"new", "learning", "review", "relearning", "leech"}
        return SelectionDecision(eligible=True, reasons=())


def _candidate(
    index: int,
    *,
    state: str,
    content_type: str,
    due: str | None = None,
    group: str | None = None,
    user_state: str = "active",
    suspend_until_utc: str | None = None,
) -> dict[str, Any]:
    return {
        "card_key": f"card-{index}",
        "learning_item_id": f"item-{index}",
        "prompt_facet_id": f"prompt-{index}",
        "answer_facet_id": f"answer-{index}",
        "content_type": content_type,
        "state": state,
        "next_due_at_utc": due,
        "pack_position": index,
        "user_state": user_state,
        "suspend_until_utc": suspend_until_utc,
        "confusable_group_ids": () if group is None else (group,),
    }


def _service(
    candidates: tuple[dict[str, Any], ...],
    *,
    reviews: _Reviews | None = None,
    profiles: _Profiles | None = None,
    track_settings: dict[str, Any] | None = None,
) -> SessionSelectionService:
    return SessionSelectionService(
        _Tracks(candidates, track_settings=track_settings),
        profiles or _Profiles(),
        reviews or _Reviews(),
        _Constraints(),
        clock=_FixedClock(datetime(2026, 9, 23, 12, 0, tzinfo=UTC)),
    )


@pytest.mark.asyncio
async def test_selection_prioritizes_short_steps_and_reserves_final_quarter() -> None:
    due = "2026-09-23T10:00:00+00:00"
    candidates = (
        _candidate(1, state="relearning", content_type="vocabulary", due=due),
        _candidate(2, state="learning", content_type="grammar", due=due),
        _candidate(3, state="review", content_type="kanji", due=due),
        _candidate(4, state="review", content_type="vocabulary", due=due),
        _candidate(5, state="new", content_type="vocabulary"),
        _candidate(6, state="new", content_type="grammar"),
        _candidate(7, state="new", content_type="kanji"),
        _candidate(8, state="new", content_type="vocabulary"),
        _candidate(9, state="new", content_type="grammar"),
        _candidate(10, state="new", content_type="kanji"),
    )
    service = _service(candidates)

    selected = await service.async_prepare(
        profile_id="profile-1",
        track_id="track-1",
        session_type="bounded",
        settings={"requested_cards": 8},
    )

    assert len(selected) == 8
    states = tuple(item.payload["selection"]["progress_state"] for item in selected)
    assert states[:2] == ("relearning", "learning")
    assert states[6:] == ("review", "review")
    assert all(state != "new" for state in states[6:])
    assert states.count("new") == 4
    assert all("reason" in item.payload["selection"] for item in selected)


@pytest.mark.asyncio
async def test_new_card_quota_is_counted_in_cards_for_profile_local_date() -> None:
    candidates = tuple(
        _candidate(index, state="new", content_type="vocabulary") for index in range(1, 6)
    )
    service = _service(candidates, reviews=_Reviews(introductions=7))

    selected = await service.async_prepare(
        profile_id="profile-1",
        track_id="track-1",
        session_type="bounded",
        settings={"requested_cards": 4},
    )

    assert len(selected) == 1
    assert selected[0].payload["selection"]["progress_state"] == "new"


@pytest.mark.asyncio
async def test_session_plan_does_not_prequeue_confusable_new_cards_together() -> None:
    candidates = (
        _candidate(1, state="new", content_type="vocabulary", group="group-a"),
        _candidate(2, state="new", content_type="grammar", group="group-a"),
        _candidate(3, state="new", content_type="kanji"),
        _candidate(4, state="new", content_type="vocabulary"),
    )
    service = _service(candidates)

    selected = await service.async_prepare(
        profile_id="profile-1",
        track_id="track-1",
        session_type="bounded",
        settings={"requested_cards": 4},
    )

    selected_keys = {item.card_key for item in selected}
    assert not {"card-1", "card-2"} <= selected_keys
    assert all(item.payload["selection"]["progress_state"] != "new" for item in selected[3:])


@pytest.mark.asyncio
async def test_not_yet_due_review_is_not_selected() -> None:
    service = _service(
        (
            _candidate(
                1,
                state="review",
                content_type="vocabulary",
                due="2026-09-23T13:00:00+00:00",
            ),
        )
    )

    selected = await service.async_prepare(
        profile_id="profile-1",
        track_id="track-1",
        session_type="bounded",
        settings={"requested_cards": 4},
    )

    assert selected == ()


@pytest.mark.asyncio
async def test_fatigue_advice_uses_ten_recent_verified_results_only() -> None:
    service = _service(
        (),
        reviews=_Reviews(
            verified_results=(
                "wrong",
                "idk",
                "correct",
                "wrong",
                "correct",
                "wrong",
                "wrong",
                "correct",
                "correct",
                "wrong",
            )
        ),
    )

    advice = await service.async_fatigue_advice(
        "session-1",
        settings={},
    )

    assert advice.detected is True
    assert advice.sample_size == 10
    assert advice.verified_accuracy == 0.4
    assert advice.actions == ("finish", "recognition_only", "continue")
    assert advice.reason == "verified_accuracy_drop"


@pytest.mark.asyncio
async def test_fatigue_never_fires_on_incomplete_sample_or_paused_session() -> None:
    incomplete = _service(
        (),
        reviews=_Reviews(verified_results=("wrong",) * 9),
    )
    incomplete_advice = await incomplete.async_fatigue_advice(
        "session-1",
        settings={},
    )
    assert incomplete_advice.detected is False
    assert incomplete_advice.reason == "insufficient_verified_sample"

    paused = _service(
        (),
        reviews=_Reviews(verified_results=("wrong",) * 10),
    )
    paused_advice = await paused.async_fatigue_advice(
        "session-1",
        settings={},
        active=False,
    )
    assert paused_advice.detected is False
    assert paused_advice.actions == ()


def test_invalid_fatigue_threshold_is_rejected() -> None:
    service = _service(())

    with pytest.raises(SessionSelectionError, match="within"):
        service.validate_session_settings({"fatigue_accuracy_threshold": 1.1})


@pytest.mark.asyncio
async def test_user_owned_state_filters_sessions_and_expired_burial_reactivates() -> None:
    due = "2026-09-23T10:00:00+00:00"
    candidates = (
        _candidate(1, state="review", content_type="vocabulary", due=due),
        _candidate(
            2,
            state="review",
            content_type="vocabulary",
            due=due,
            user_state="known_already",
        ),
        _candidate(
            3,
            state="review",
            content_type="vocabulary",
            due=due,
            user_state="suspended",
        ),
        _candidate(
            4,
            state="review",
            content_type="vocabulary",
            due=due,
            user_state="buried",
            suspend_until_utc="2026-09-23T13:00:00+00:00",
        ),
        _candidate(
            5,
            state="review",
            content_type="vocabulary",
            due=due,
            user_state="buried",
            suspend_until_utc="2026-09-23T11:00:00+00:00",
        ),
    )
    service = _service(candidates)

    selected = await service.async_prepare(
        profile_id="profile-1",
        track_id="track-1",
        session_type="bounded",
        settings={"requested_cards": 5},
    )

    assert [item.card_key for item in selected] == ["card-1", "card-5"]


@pytest.mark.asyncio
async def test_leeches_are_fallback_after_normal_due_and_new_cards() -> None:
    due = "2026-09-23T10:00:00+00:00"
    candidates = (
        _candidate(1, state="review", content_type="vocabulary", due=due),
        _candidate(2, state="new", content_type="grammar"),
        _candidate(3, state="leech", content_type="kanji", due=due),
    )
    service = _service(candidates)

    selected = await service.async_prepare(
        profile_id="profile-1",
        track_id="track-1",
        session_type="bounded",
        settings={"requested_cards": 3},
    )

    assert [item.card_key for item in selected[:2]] == ["card-1", "card-2"]
    assert selected[2].card_key == "card-3"
    assert selected[2].payload["selection"]["reason"] == "leech_due"
