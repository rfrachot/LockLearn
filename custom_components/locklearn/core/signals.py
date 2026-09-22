"""Verified-retrieval gate and signal weighting for P3.4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .review_policy import ReviewPolicyV1, ReviewTransition


class SignalMode(StrEnum):
    EXPOSURE = "exposure"
    SELF_ASSESSMENT_AFTER_RETRIEVAL = "self_assessment_after_retrieval"
    VERIFIED_MCQ = "verified_mcq"
    VERIFIED_FREE_TEXT = "verified_free_text"
    VERIFIED_CLOZE = "verified_cloze"
    EXAM_RETRIEVAL = "exam_retrieval"


class SignalOutcome(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SignalQuality(StrEnum):
    NONE = "none"
    WEAK = "weak"
    REDUCED = "reduced"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass(frozen=True, slots=True)
class SignalDecision:
    """Normalized pedagogical meaning of one user interaction."""

    mode: SignalMode
    outcome: SignalOutcome
    signal_quality: SignalQuality
    retrieval_occurred: bool
    verified: bool
    gate_eligible: bool
    reward_difficulty: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AppliedReviewSignal:
    """ReviewPolicy application result plus gate metadata."""

    decision: SignalDecision
    transition: ReviewTransition | None
    box_promotion_allowed: bool


class SignalPolicy:
    """Map interaction semantics to safe SRS mutations."""

    def __init__(
        self,
        review_policy: ReviewPolicyV1,
        *,
        verified_gate_box: int = 2,
    ) -> None:
        if verified_gate_box < 0:
            raise ValueError("verified_gate_box must be >= 0")
        self._review_policy = review_policy
        self._verified_gate_box = verified_gate_box

    def evaluate(
        self,
        *,
        mode: SignalMode | str,
        result: str,
        retrieval_occurred: bool,
        answer_visible_before_assessment: bool = False,
        hint_used: bool = False,
        shared_device: bool = False,
        shared_device_trusted: bool = False,
    ) -> SignalDecision:
        """Normalize one interaction without mutating progress."""
        resolved_mode = SignalMode(mode)
        normalized_result = result.strip().lower()

        if resolved_mode is SignalMode.EXPOSURE:
            return SignalDecision(
                mode=resolved_mode,
                outcome=SignalOutcome.NEUTRAL,
                signal_quality=SignalQuality.NONE,
                retrieval_occurred=False,
                verified=False,
                gate_eligible=False,
                reward_difficulty=False,
                reason="exposure_only",
            )

        if normalized_result == "unrecognized":
            return SignalDecision(
                mode=resolved_mode,
                outcome=SignalOutcome.NEUTRAL,
                signal_quality=SignalQuality.NONE,
                retrieval_occurred=retrieval_occurred,
                verified=False,
                gate_eligible=False,
                reward_difficulty=False,
                reason="unrecognized_no_automatic_srs_failure",
            )

        if resolved_mode is SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL:
            positive = normalized_result in {"correct", "known", "knew", "easy", "hard"}
            negative = normalized_result in {"wrong", "review", "again", "idk"}
            if positive and (answer_visible_before_assessment or not retrieval_occurred):
                return SignalDecision(
                    mode=resolved_mode,
                    outcome=SignalOutcome.NEUTRAL,
                    signal_quality=SignalQuality.NONE,
                    retrieval_occurred=False,
                    verified=False,
                    gate_eligible=False,
                    reward_difficulty=False,
                    reason=(
                        "answer_visible_before_self_assessment"
                        if answer_visible_before_assessment
                        else "self_assessment_without_retrieval"
                    ),
                )
            if positive:
                return SignalDecision(
                    mode=resolved_mode,
                    outcome=SignalOutcome.POSITIVE,
                    signal_quality=SignalQuality.WEAK,
                    retrieval_occurred=retrieval_occurred,
                    verified=False,
                    gate_eligible=False,
                    reward_difficulty=False,
                    reason="post_retrieval_self_assessment",
                )
            if negative:
                return SignalDecision(
                    mode=resolved_mode,
                    outcome=SignalOutcome.NEGATIVE,
                    signal_quality=SignalQuality.WEAK,
                    retrieval_occurred=retrieval_occurred,
                    verified=False,
                    gate_eligible=False,
                    reward_difficulty=False,
                    reason="self_assessed_failure",
                )
            raise ValueError(f"unsupported self-assessment result: {result}")

        if not retrieval_occurred:
            raise ValueError("verified retrieval mode requires retrieval_occurred")

        if normalized_result == "idk":
            quality = SignalQuality.MEDIUM
            trusted = not shared_device or shared_device_trusted
            if shared_device and not shared_device_trusted:
                quality = SignalQuality.REDUCED
            return SignalDecision(
                mode=resolved_mode,
                outcome=SignalOutcome.NEGATIVE,
                signal_quality=quality,
                retrieval_occurred=True,
                verified=trusted,
                gate_eligible=trusted,
                reward_difficulty=False,
                reason="idk_retrieval_failure",
            )

        correct = normalized_result == "correct"
        wrong = normalized_result == "wrong"
        if not correct and not wrong:
            raise ValueError(f"unsupported verified retrieval result: {result}")

        if resolved_mode is SignalMode.VERIFIED_MCQ:
            quality = SignalQuality.MEDIUM
        else:
            quality = SignalQuality.STRONG

        trusted = not shared_device or shared_device_trusted
        if shared_device and not shared_device_trusted:
            quality = SignalQuality.REDUCED

        return SignalDecision(
            mode=resolved_mode,
            outcome=SignalOutcome.POSITIVE if correct else SignalOutcome.NEGATIVE,
            signal_quality=SignalQuality.WEAK if hint_used and trusted else quality,
            retrieval_occurred=True,
            verified=trusted,
            gate_eligible=trusted,
            reward_difficulty=correct and trusted and not hint_used,
            reason=(
                "hint_reduced"
                if hint_used and trusted
                else "shared_device_reduced"
                if shared_device and not shared_device_trusted
                else "verified_retrieval"
            ),
        )

    def apply_review_signal(
        self,
        snapshot: dict[str, Any],
        *,
        decision: SignalDecision,
        hint_used: bool = False,
    ) -> AppliedReviewSignal:
        """Apply one normalized signal to a card already in long review."""
        if decision.outcome is SignalOutcome.NEUTRAL:
            return AppliedReviewSignal(
                decision=decision,
                transition=None,
                box_promotion_allowed=False,
            )

        if decision.outcome is SignalOutcome.NEGATIVE:
            transition = self._review_policy.review_failure(
                snapshot,
                verified=decision.verified,
                demote=decision.verified,
            )
            return AppliedReviewSignal(
                decision=decision,
                transition=transition,
                box_promotion_allowed=False,
            )

        current_box = max(1, int(snapshot.get("box", 1)))
        target_box = current_box + 1
        needs_verified_gate = target_box > self._verified_gate_box
        verified_since_box = int(snapshot.get("verified_success_since_box", 0)) > 0
        gate_satisfied = not needs_verified_gate or decision.gate_eligible or verified_since_box
        promote_box = gate_satisfied

        transition = self._review_policy.review_success(
            snapshot,
            hint_used=hint_used,
            promote_box=promote_box,
            verified=decision.verified,
            reward_difficulty=decision.reward_difficulty,
        )
        return AppliedReviewSignal(
            decision=decision,
            transition=transition,
            box_promotion_allowed=promote_box,
        )
