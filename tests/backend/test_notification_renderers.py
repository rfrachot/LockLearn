"""P4.7 capability-aware notification renderer tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from custom_components.locklearn.core.review_policy import ReviewPolicyV1
from custom_components.locklearn.core.signals import SignalMode, SignalPolicy
from custom_components.locklearn.notifications.capabilities import Capability, TargetCapabilities
from custom_components.locklearn.notifications.renderers import (
    CHANNEL_LEARNING,
    CHANNEL_QUIZ,
    CHANNEL_RELEARNING,
    NotificationRenderMode,
    NotificationRenderer,
    QuizOption,
    decode_action_id,
    effective_lockscreen_visibility,
)


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 24, 20, 0, tzinfo=UTC)


def _review_snapshot() -> dict[str, Any]:
    return {
        "profile_id": "profile-1",
        "track_id": "track-1",
        "card_key": "card-1",
        "learning_item_id": "item-1",
        "prompt_facet_id": "prompt-1",
        "answer_facet_id": "answer-1",
        "state": "review",
        "mastery": 0.4,
        "box": 2,
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
        "verified_success_since_box": 0,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-1",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-20T20:00:00+00:00",
    }


def _android(*, shared: bool = False) -> TargetCapabilities:
    return TargetCapabilities(
        device_registry_id="device-1",
        platform="android",
        replace_by_tag=Capability.SUPPORTED,
        silent_replace=Capability.UNSUPPORTED,
        action_data=Capability.SUPPORTED,
        visible_actions=3,
        shared_device=shared,
    )


def test_two_step_reveal_uses_same_tag_fresh_token_and_silent_preference() -> None:
    renderer = NotificationRenderer()
    target = _android()

    prompt = renderer.render_learning_prompt(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-1",
        tag="locklearn:slot-1",
        prompt="休",
        answer="repos",
        token="token-prompt",
        capabilities=target,
    )
    revealed = renderer.render_learning_revealed(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-1",
        tag=prompt.tag,
        answer="repos · se reposer",
        token="token-revealed",
        capabilities=target,
    )

    assert prompt.mode is NotificationRenderMode.TWO_STEP_REVEAL
    assert prompt.message == "休"
    assert "repos" not in prompt.message
    assert revealed.tag == prompt.tag
    assert revealed.data["alert_once"] is True
    assert revealed.message == "repos · se reposer"

    prompt_tokens = {
        decoded[0]
        for action in prompt.data["actions"]
        if (decoded := decode_action_id(action["action"])) is not None
    }
    revealed_tokens = {
        decoded[0]
        for action in revealed.data["actions"]
        if (decoded := decode_action_id(action["action"])) is not None
    }
    assert prompt_tokens == {"token-prompt"}
    assert revealed_tokens == {"token-revealed"}


def test_direct_exposure_fallback_cannot_promote_review_box() -> None:
    renderer = NotificationRenderer()
    fallback = renderer.render_learning_prompt(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-1",
        tag="locklearn:slot-1",
        prompt="休",
        answer="repos",
        token="unused-token",
        capabilities=TargetCapabilities(
            device_registry_id="device-1",
            platform="android",
        ),
    )

    assert fallback.mode is NotificationRenderMode.DIRECT_EXPOSURE
    assert fallback.pedagogical_signal == "exposure_only"
    assert "repos" in fallback.message
    assert "actions" not in fallback.data

    signals = SignalPolicy(ReviewPolicyV1(clock=FixedClock()))
    decision = signals.evaluate(
        mode=SignalMode.EXPOSURE,
        result="known",
        retrieval_occurred=False,
        answer_visible_before_assessment=True,
    )
    applied = signals.apply_review_signal(_review_snapshot(), decision=decision)
    assert applied.transition is None
    assert applied.box_promotion_allowed is False


def test_binary_quiz_uses_three_actions_and_full_mcq_hands_off_to_panel() -> None:
    renderer = NotificationRenderer()
    target = _android()
    binary = renderer.render_quiz_prompt(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-1",
        tag="locklearn:quiz-1",
        prompt="休",
        token="quiz-token",
        options=(
            QuizOption("rest", "se reposer"),
            QuizOption("wait", "attendre"),
        ),
        capabilities=target,
    )

    assert binary.mode is NotificationRenderMode.QUIZ_ACTIONS
    assert len(binary.data["actions"]) == 3
    assert binary.data["channel"] == CHANNEL_QUIZ
    assert binary.panel_required is False
    assert set(binary.action_semantics.values()) == {
        "choice:rest",
        "choice:wait",
        "idk",
    }

    full = renderer.render_quiz_prompt(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-1",
        tag="locklearn:quiz-2",
        prompt="休",
        token="quiz-token-2",
        options=(
            QuizOption("a", "A"),
            QuizOption("b", "B"),
            QuizOption("c", "C"),
            QuizOption("d", "D"),
        ),
        capabilities=target,
    )
    assert full.mode is NotificationRenderMode.PANEL_HANDOFF
    assert full.panel_required is True
    assert full.pedagogical_signal == "no_result"
    assert full.data["actions"] == [
        {"action": "URI", "title": "Open LockLearn", "uri": "/locklearn"}
    ]


def test_ios_binary_quiz_is_allowed_but_three_option_quiz_uses_panel() -> None:
    renderer = NotificationRenderer()
    ios = TargetCapabilities(
        device_registry_id="ipad-1",
        platform="ios",
        action_data=Capability.SUPPORTED,
        visible_actions=4,
    )
    binary = renderer.render_quiz_prompt(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-ipad",
        tag="locklearn:ios-binary",
        prompt="休",
        token="ios-token",
        options=(QuizOption("yes", "repos"), QuizOption("no", "attendre")),
        capabilities=ios,
    )
    larger = renderer.render_quiz_prompt(
        profile_id="profile-1",
        profile_name="Renaud",
        target_id="target-ipad",
        tag="locklearn:ios-larger",
        prompt="休",
        token="ios-token-2",
        options=(
            QuizOption("a", "A"),
            QuizOption("b", "B"),
            QuizOption("c", "C"),
        ),
        capabilities=ios,
    )
    assert binary.mode is NotificationRenderMode.QUIZ_ACTIONS
    assert larger.mode is NotificationRenderMode.PANEL_HANDOFF


def test_channels_shared_profile_label_and_profile_target_identity_stay_distinct() -> None:
    renderer = NotificationRenderer()
    shared = _android(shared=True)
    learning = renderer.render_learning_prompt(
        profile_id="profile-lou",
        profile_name="Lou",
        target_id="target-family-phone",
        tag="tag-learning",
        prompt="休",
        answer="repos",
        token="token-1",
        capabilities=shared,
        slot_type="learning",
    )
    relearning = renderer.render_learning_prompt(
        profile_id="profile-lou",
        profile_name="Lou",
        target_id="target-family-phone",
        tag="tag-relearning",
        prompt="休",
        answer="repos",
        token="token-2",
        capabilities=shared,
        slot_type="relearning",
    )
    assert learning.data["channel"] == CHANNEL_LEARNING
    assert relearning.data["channel"] == CHANNEL_RELEARNING
    assert learning.title.endswith("· Lou")
    assert learning.profile_id == "profile-lou"
    assert learning.target_id == "target-family-phone"
    assert learning.profile_id != learning.target_id


def test_visibility_defaults_private_for_child_and_shared_but_explicit_choice_is_kept() -> None:
    assert (
        effective_lockscreen_visibility(
            None,
            profile_preset="child",
            shared_device=False,
        )
        == "private"
    )
    assert (
        effective_lockscreen_visibility(
            None,
            profile_preset="standard",
            shared_device=True,
        )
        == "private"
    )
    assert (
        effective_lockscreen_visibility(
            "public",
            profile_preset="child",
            shared_device=True,
        )
        == "public"
    )
