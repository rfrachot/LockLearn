"""P3.2 introduction and short-step state machine tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from custom_components.locklearn.core.learning import (
    LearningStateError,
    LearningStateMachine,
)


@dataclass
class _MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def _snapshot(state: str) -> dict[str, object]:
    return {
        "profile_id": "profile-1",
        "track_id": "track-1",
        "card_key": "card-1",
        "learning_item_id": "item-1",
        "prompt_facet_id": "prompt-1",
        "answer_facet_id": "answer-1",
        "state": state,
        "mastery": 0.0,
        "box": 0,
        "seen_count": 0,
        "verified_correct_count": 0,
        "verified_wrong_count": 0,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": None,
        "last_seen_at_utc": None,
        "last_result": None,
        "next_due_at_utc": None,
        "streak_correct": 0,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": None,
        "verified_success_since_box": 0,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-1",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-22T20:00:00+00:00",
    }


def test_first_exposure_is_introduction_not_failure() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    machine = LearningStateMachine(clock=clock)

    transition = machine.introduce(_snapshot("new"))

    assert transition.mode == "introduction"
    assert transition.retrieval_occurred is False
    assert transition.post_state["state"] == "learning"
    assert transition.post_state["last_result"] == "exposure"
    assert transition.post_state["verified_wrong_count"] == 0
    assert transition.post_state["streak_correct"] == 0
    assert transition.next_due_in_minutes == 1
    assert transition.post_state["next_due_at_utc"] == "2026-09-22T20:01:00+00:00"


def test_learning_steps_follow_one_ten_sixty_minutes_before_long_review() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    machine = LearningStateMachine(clock=clock)
    current = machine.introduce(_snapshot("new")).post_state

    clock.current = datetime(2026, 9, 22, 20, 1, tzinfo=UTC)
    first = machine.learning_result(current, success=True)
    assert first.retrieval_occurred is True
    assert first.next_due_in_minutes == 10
    assert first.ready_for_long_review is False

    clock.current = datetime(2026, 9, 22, 20, 11, tzinfo=UTC)
    second = machine.learning_result(first.post_state, success=True)
    assert second.next_due_in_minutes == 60
    assert second.ready_for_long_review is False

    clock.current = datetime(2026, 9, 22, 21, 11, tzinfo=UTC)
    third = machine.learning_result(second.post_state, success=True)
    assert third.ready_for_long_review is True
    assert third.next_due_in_minutes is None
    assert third.post_state["state"] == "learning"
    assert third.post_state["next_due_at_utc"] is None


def test_learning_failure_never_retests_immediately() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    machine = LearningStateMachine(clock=clock)
    current = machine.introduce(_snapshot("new")).post_state
    current["streak_correct"] = 2

    clock.current = datetime(2026, 9, 22, 20, 30, tzinfo=UTC)
    failure = machine.learning_result(current, success=False)

    assert failure.post_state["state"] == "learning"
    assert failure.post_state["last_result"] == "wrong"
    assert failure.post_state["streak_correct"] == 0
    assert failure.next_due_in_minutes == 1
    assert failure.post_state["next_due_at_utc"] == "2026-09-22T20:31:00+00:00"


def test_relearning_uses_ten_then_sixty_minute_steps_and_resets_on_failure() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    machine = LearningStateMachine(clock=clock)

    entered = machine.enter_relearning(_snapshot("review"))
    assert entered.post_state["state"] == "relearning"
    assert entered.next_due_in_minutes == 10
    assert entered.post_state["next_due_at_utc"] == "2026-09-22T20:10:00+00:00"

    clock.current = datetime(2026, 9, 22, 20, 10, tzinfo=UTC)
    first = machine.relearning_result(entered.post_state, success=True)
    assert first.next_due_in_minutes == 60
    assert first.ready_for_long_review is False

    clock.current = datetime(2026, 9, 22, 20, 20, tzinfo=UTC)
    reset = machine.relearning_result(first.post_state, success=False)
    assert reset.next_due_in_minutes == 10
    assert reset.post_state["streak_correct"] == 0
    assert reset.post_state["next_due_at_utc"] == "2026-09-22T20:30:00+00:00"

    clock.current = datetime(2026, 9, 22, 20, 30, tzinfo=UTC)
    retry = machine.relearning_result(reset.post_state, success=True)
    clock.current = datetime(2026, 9, 22, 21, 30, tzinfo=UTC)
    graduated = machine.relearning_result(retry.post_state, success=True)
    assert graduated.ready_for_long_review is True
    assert graduated.post_state["state"] == "relearning"
    assert graduated.post_state["next_due_at_utc"] is None


def test_short_step_machine_rejects_wrong_state_and_invalid_step_config() -> None:
    machine = LearningStateMachine(
        clock=_MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    )

    with pytest.raises(LearningStateError, match="expected state 'new'"):
        machine.introduce(_snapshot("learning"))

    with pytest.raises(LearningStateError, match="review or leech"):
        machine.enter_relearning(_snapshot("learning"))

    with pytest.raises(LearningStateError, match="positive delays"):
        LearningStateMachine(learning_steps_minutes=(0, 10, 60))

    with pytest.raises(LearningStateError, match="monotonic"):
        LearningStateMachine(relearning_steps_minutes=(60, 10))
