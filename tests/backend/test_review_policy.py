"""P3.3 deterministic V1 ReviewPolicy tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from custom_components.locklearn.core.learning import LearningStateMachine
from custom_components.locklearn.core.review_policy import (
    DEFAULT_BOX_INTERVAL_DAYS,
    ReviewPolicyError,
    ReviewPolicyV1,
)


@dataclass
class _MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def _review_snapshot(
    *,
    box: int = 2,
    difficulty_factor: float = 1.0,
    last_verified_at_utc: str = "2026-09-20T20:00:00+00:00",
    next_due_at_utc: str = "2026-09-21T20:00:00+00:00",
) -> dict[str, object]:
    return {
        "profile_id": "profile-1",
        "track_id": "track-1",
        "card_key": "card-1",
        "learning_item_id": "item-1",
        "prompt_facet_id": "prompt-1",
        "answer_facet_id": "answer-1",
        "state": "review",
        "mastery": 0.5,
        "box": box,
        "seen_count": 5,
        "verified_correct_count": 4,
        "verified_wrong_count": 1,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-09-01T20:00:00+00:00",
        "last_seen_at_utc": last_verified_at_utc,
        "last_result": "correct",
        "next_due_at_utc": next_due_at_utc,
        "streak_correct": 2,
        "leech_score": 0.0,
        "difficulty_factor": difficulty_factor,
        "last_verified_at_utc": last_verified_at_utc,
        "verified_success_since_box": 1,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-1",
        "normalization_version": 1,
        "updated_at_utc": last_verified_at_utc,
    }


def test_success_promotes_box_updates_difficulty_and_is_deterministic() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    policy = ReviewPolicyV1(clock=clock)
    snapshot = _review_snapshot()

    first = policy.review_success(snapshot)
    second = policy.review_success(snapshot)

    assert first.policy_version == 1
    assert first.post_state["state"] == "review"
    assert first.post_state["box"] == 3
    assert first.post_state["difficulty_factor"] == pytest.approx(1.05)
    assert first.post_state["verified_correct_count"] == 5
    assert first.effective_interval_days == second.effective_interval_days
    assert first.post_state["next_due_at_utc"] == second.post_state["next_due_at_utc"]


def test_success_with_hint_does_not_increase_difficulty() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    policy = ReviewPolicyV1(clock=clock)

    transition = policy.review_success(_review_snapshot(), hint_used=True)

    assert transition.post_state["difficulty_factor"] == pytest.approx(1.0)
    assert transition.post_state["box"] == 3


def test_failure_demotes_by_two_boxes_and_enters_relearning() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    learning = LearningStateMachine(clock=clock)
    policy = ReviewPolicyV1(clock=clock, learning=learning)

    transition = policy.review_failure(_review_snapshot(box=5))

    assert transition.entered_relearning is True
    assert transition.post_state["state"] == "relearning"
    assert transition.post_state["box"] == 3
    assert transition.post_state["difficulty_factor"] == pytest.approx(0.85)
    assert transition.post_state["verified_wrong_count"] == 2
    assert transition.post_state["next_due_at_utc"] == "2026-09-22T20:10:00+00:00"


def test_difficulty_factor_is_bounded() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    policy = ReviewPolicyV1(clock=clock)

    low = policy.review_failure(_review_snapshot(difficulty_factor=0.6))
    high = policy.review_success(_review_snapshot(difficulty_factor=2.0))

    assert low.post_state["difficulty_factor"] == pytest.approx(0.6)
    assert high.post_state["difficulty_factor"] == pytest.approx(2.0)


def test_overdue_success_never_schedules_shorter_than_demonstrated_retention() -> None:
    clock = _MutableClock(datetime(2026, 9, 30, 20, 0, tzinfo=UTC))
    policy = ReviewPolicyV1(clock=clock)
    snapshot = _review_snapshot(
        box=2,
        last_verified_at_utc="2026-09-20T20:00:00+00:00",
        next_due_at_utc="2026-09-21T20:00:00+00:00",
    )

    transition = policy.review_success(snapshot)

    assert transition.scheduled_interval_days == pytest.approx(1.0)
    assert transition.elapsed_days == pytest.approx(10.0)
    assert transition.effective_interval_days is not None
    assert transition.effective_interval_days >= 10.0


def test_mastery_is_non_terminal_and_decays_with_time() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    policy = ReviewPolicyV1(clock=clock)
    snapshot = _review_snapshot(box=6)

    current = policy.mastery(snapshot)
    clock.current = datetime(2026, 11, 22, 20, 0, tzinfo=UTC)
    later = policy.mastery(snapshot)

    assert 0 <= later < current <= 1
    assert snapshot["state"] == "review"


def test_completed_short_steps_graduate_to_review_without_recomputing_short_steps() -> None:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    learning = LearningStateMachine(clock=clock)
    policy = ReviewPolicyV1(clock=clock, learning=learning)

    snapshot = {
        **_review_snapshot(box=0),
        "state": "learning",
        "card_key": "card-learning",
        "verified_correct_count": 0,
        "verified_wrong_count": 0,
        "streak_correct": 2,
        "next_due_at_utc": None,
    }
    transition = learning.learning_result(snapshot, success=True)
    assert transition.ready_for_long_review is True

    graduated = policy.graduate_short_steps(transition)

    assert graduated.post_state["state"] == "review"
    assert graduated.post_state["box"] == 1
    assert graduated.effective_interval_days is not None
    assert graduated.post_state["next_due_at_utc"] is not None


def test_policy_rejects_non_review_long_transition_and_invalid_config() -> None:
    policy = ReviewPolicyV1(
        clock=_MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    )
    snapshot = _review_snapshot()
    snapshot["state"] = "learning"

    with pytest.raises(ReviewPolicyError, match="requires state 'review'"):
        policy.review_success(snapshot)

    with pytest.raises(ReviewPolicyError, match="relapse_penalty"):
        ReviewPolicyV1(relapse_penalty=-1)

    with pytest.raises(ReviewPolicyError, match="jitter_fraction"):
        ReviewPolicyV1(jitter_fraction=0.5)
