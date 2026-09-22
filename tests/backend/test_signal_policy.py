"""P3.4 verified-retrieval gate and signal weighting tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from custom_components.locklearn.core.review_policy import ReviewPolicyV1
from custom_components.locklearn.core.signals import (
    SignalMode,
    SignalOutcome,
    SignalPolicy,
    SignalQuality,
)


@dataclass
class _MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def _review_snapshot(*, box: int, verified_success_since_box: int = 0) -> dict[str, Any]:
    return {
        "profile_id": "profile-1",
        "track_id": "track-1",
        "card_key": "card-1",
        "learning_item_id": "item-1",
        "prompt_facet_id": "prompt-1",
        "answer_facet_id": "answer-1",
        "state": "review",
        "mastery": 0.4,
        "box": box,
        "seen_count": 4,
        "verified_correct_count": 2,
        "verified_wrong_count": 1,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-09-01T20:00:00+00:00",
        "last_seen_at_utc": "2026-09-20T20:00:00+00:00",
        "last_result": "correct",
        "next_due_at_utc": "2026-09-22T19:00:00+00:00",
        "streak_correct": 1,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": "2026-09-20T20:00:00+00:00",
        "verified_success_since_box": verified_success_since_box,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-1",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-20T20:00:00+00:00",
    }


def _policy() -> SignalPolicy:
    clock = _MutableClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
    return SignalPolicy(ReviewPolicyV1(clock=clock), verified_gate_box=2)


def test_visible_answer_self_assessment_cannot_promote_srs() -> None:
    signals = _policy()
    decision = signals.evaluate(
        mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL,
        result="known",
        retrieval_occurred=False,
        answer_visible_before_assessment=True,
    )

    applied = signals.apply_review_signal(_review_snapshot(box=1), decision=decision)

    assert decision.outcome is SignalOutcome.NEUTRAL
    assert decision.signal_quality is SignalQuality.NONE
    assert decision.verified is False
    assert applied.transition is None
    assert applied.box_promotion_allowed is False


def test_self_assessment_without_retrieval_is_neutral() -> None:
    signals = _policy()
    decision = signals.evaluate(
        mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL,
        result="known",
        retrieval_occurred=False,
    )

    assert decision.outcome is SignalOutcome.NEUTRAL
    assert decision.reason == "self_assessment_without_retrieval"


def test_verified_modes_require_actual_retrieval() -> None:
    signals = _policy()
    with pytest.raises(ValueError, match="requires retrieval_occurred"):
        signals.evaluate(
            mode=SignalMode.VERIFIED_FREE_TEXT,
            result="correct",
            retrieval_occurred=False,
        )


def test_post_retrieval_self_assessment_can_reach_gate_but_not_cross_it_alone() -> None:
    signals = _policy()
    decision = signals.evaluate(
        mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL,
        result="known",
        retrieval_occurred=True,
    )

    below_gate = signals.apply_review_signal(_review_snapshot(box=1), decision=decision)
    assert below_gate.transition is not None
    assert below_gate.transition.post_state["box"] == 2
    assert below_gate.transition.post_state["verified_correct_count"] == 2

    at_gate = signals.apply_review_signal(_review_snapshot(box=2), decision=decision)
    assert at_gate.transition is not None
    assert at_gate.box_promotion_allowed is False
    assert at_gate.transition.post_state["box"] == 2
    assert at_gate.transition.post_state["verified_correct_count"] == 2


def test_verified_retrieval_crosses_gate_then_requires_new_verified_evidence() -> None:
    signals = _policy()
    verified = signals.evaluate(
        mode=SignalMode.VERIFIED_FREE_TEXT,
        result="correct",
        retrieval_occurred=True,
    )

    crossed = signals.apply_review_signal(_review_snapshot(box=2), decision=verified)
    assert crossed.transition is not None
    assert crossed.transition.post_state["box"] == 3
    assert crossed.transition.post_state["verified_correct_count"] == 3
    assert crossed.transition.post_state["verified_success_since_box"] == 0

    weak = signals.evaluate(
        mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL,
        result="known",
        retrieval_occurred=True,
    )
    blocked = signals.apply_review_signal(crossed.transition.post_state, decision=weak)
    assert blocked.transition is not None
    assert blocked.transition.post_state["box"] == 3


def test_prior_verified_success_in_current_box_can_authorize_next_gate_crossing() -> None:
    signals = _policy()
    weak = signals.evaluate(
        mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL,
        result="known",
        retrieval_occurred=True,
    )

    applied = signals.apply_review_signal(
        _review_snapshot(box=3, verified_success_since_box=1),
        decision=weak,
    )

    assert applied.transition is not None
    assert applied.box_promotion_allowed is True
    assert applied.transition.post_state["box"] == 4
    assert applied.transition.post_state["verified_success_since_box"] == 0


def test_untrusted_shared_device_signal_is_reduced_and_cannot_cross_gate() -> None:
    signals = _policy()
    decision = signals.evaluate(
        mode=SignalMode.VERIFIED_MCQ,
        result="correct",
        retrieval_occurred=True,
        shared_device=True,
        shared_device_trusted=False,
    )
    applied = signals.apply_review_signal(_review_snapshot(box=2), decision=decision)

    assert decision.signal_quality is SignalQuality.REDUCED
    assert decision.verified is False
    assert decision.gate_eligible is False
    assert applied.transition is not None
    assert applied.transition.post_state["box"] == 2
    assert applied.transition.post_state["verified_correct_count"] == 2


def test_explicitly_trusted_shared_device_can_cross_verified_gate() -> None:
    signals = _policy()
    decision = signals.evaluate(
        mode=SignalMode.VERIFIED_MCQ,
        result="correct",
        retrieval_occurred=True,
        shared_device=True,
        shared_device_trusted=True,
    )
    applied = signals.apply_review_signal(_review_snapshot(box=2), decision=decision)

    assert decision.verified is True
    assert decision.gate_eligible is True
    assert applied.transition is not None
    assert applied.transition.post_state["box"] == 3


def test_hint_reduces_quality_and_disables_difficulty_reward() -> None:
    signals = _policy()
    decision = signals.evaluate(
        mode=SignalMode.VERIFIED_FREE_TEXT,
        result="correct",
        retrieval_occurred=True,
        hint_used=True,
    )
    applied = signals.apply_review_signal(
        _review_snapshot(box=2),
        decision=decision,
        hint_used=True,
    )

    assert decision.signal_quality is SignalQuality.WEAK
    assert decision.verified is True
    assert decision.reward_difficulty is False
    assert applied.transition is not None
    assert applied.transition.post_state["difficulty_factor"] == pytest.approx(1.0)


def test_idk_is_distinct_verified_failure_and_unrecognized_is_neutral() -> None:
    signals = _policy()
    idk = signals.evaluate(
        mode=SignalMode.VERIFIED_MCQ,
        result="idk",
        retrieval_occurred=True,
    )
    idk_applied = signals.apply_review_signal(_review_snapshot(box=4), decision=idk)

    assert idk.outcome is SignalOutcome.NEGATIVE
    assert idk.reason == "idk_retrieval_failure"
    assert idk_applied.transition is not None
    assert idk_applied.transition.entered_relearning is True
    assert idk_applied.transition.post_state["verified_wrong_count"] == 2
    assert idk_applied.transition.post_state["box"] == 2

    unrecognized = signals.evaluate(
        mode=SignalMode.VERIFIED_FREE_TEXT,
        result="unrecognized",
        retrieval_occurred=True,
    )
    neutral = signals.apply_review_signal(_review_snapshot(box=4), decision=unrecognized)
    assert unrecognized.outcome is SignalOutcome.NEUTRAL
    assert neutral.transition is None


def test_signal_policy_has_no_notification_latency_input() -> None:
    signals = _policy()
    with pytest.raises(TypeError):
        signals.evaluate(
            mode=SignalMode.VERIFIED_MCQ,
            result="correct",
            retrieval_occurred=True,
            delivery_to_action_ms=999_999,  # type: ignore[call-arg]
        )
