"""Introduction and short learning/relearning step state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Any

from .clock import Clock, SystemClock

DEFAULT_LEARNING_STEPS_MINUTES = (1, 10, 60)
DEFAULT_RELEARNING_STEPS_MINUTES = (10, 60)


class LearningStateError(ValueError):
    """Raised when a short-step transition is not valid."""


class LearningStepAction(StrEnum):
    """Policy-neutral short-step outcomes consumed by later signal mapping."""

    INTRODUCTION = "introduction"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class LearningStepTransition:
    """One deterministic short-step state transition."""

    pre_state: dict[str, Any]
    post_state: dict[str, Any]
    action: LearningStepAction
    mode: str
    retrieval_occurred: bool
    next_due_in_minutes: int | None
    ready_for_long_review: bool = False


class LearningStateMachine:
    """Handle introduction and short steps without owning long-review policy."""

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        learning_steps_minutes: tuple[int, ...] = DEFAULT_LEARNING_STEPS_MINUTES,
        relearning_steps_minutes: tuple[int, ...] = DEFAULT_RELEARNING_STEPS_MINUTES,
    ) -> None:
        self._clock = clock or SystemClock()
        self._learning_steps = self._validate_steps(
            "learning_steps_minutes",
            learning_steps_minutes,
        )
        self._relearning_steps = self._validate_steps(
            "relearning_steps_minutes",
            relearning_steps_minutes,
        )

    @staticmethod
    def _validate_steps(name: str, steps: tuple[int, ...]) -> tuple[int, ...]:
        if not steps:
            raise LearningStateError(f"{name} must not be empty")
        if any(step <= 0 for step in steps):
            raise LearningStateError(f"{name} must contain only positive delays")
        if tuple(sorted(steps)) != steps:
            raise LearningStateError(f"{name} must be monotonic")
        return steps

    def introduce(self, snapshot: dict[str, Any]) -> LearningStepTransition:
        """Encode a new card before any retrieval attempt."""
        self._require_state(snapshot, "new")
        now = self._clock.now()
        post = dict(snapshot)
        post.update(
            {
                "state": "learning",
                "seen_count": int(snapshot.get("seen_count", 0)) + 1,
                "first_seen_at_utc": snapshot.get("first_seen_at_utc") or now.isoformat(),
                "last_seen_at_utc": now.isoformat(),
                "last_result": "exposure",
                "next_due_at_utc": (now + timedelta(minutes=self._learning_steps[0])).isoformat(),
                "streak_correct": 0,
                "updated_at_utc": now.isoformat(),
            }
        )
        return LearningStepTransition(
            pre_state=dict(snapshot),
            post_state=post,
            action=LearningStepAction.INTRODUCTION,
            mode="introduction",
            retrieval_occurred=False,
            next_due_in_minutes=self._learning_steps[0],
        )

    def learning_result(
        self,
        snapshot: dict[str, Any],
        *,
        success: bool,
    ) -> LearningStepTransition:
        """Advance or reset short learning steps after a real retrieval attempt."""
        self._require_state(snapshot, "learning")
        return self._short_step_result(
            snapshot,
            success=success,
            steps=self._learning_steps,
            failure_state="learning",
        )

    def enter_relearning(self, snapshot: dict[str, Any]) -> LearningStepTransition:
        """Enter relearning after a failure handled by the long-review policy."""
        if snapshot.get("state") not in {"review", "leech"}:
            raise LearningStateError("relearning can start only from review or leech")
        now = self._clock.now()
        post = dict(snapshot)
        post.update(
            {
                "state": "relearning",
                "last_seen_at_utc": now.isoformat(),
                "last_result": "wrong",
                "next_due_at_utc": (
                    now + timedelta(minutes=self._relearning_steps[0])
                ).isoformat(),
                "streak_correct": 0,
                "updated_at_utc": now.isoformat(),
            }
        )
        return LearningStepTransition(
            pre_state=dict(snapshot),
            post_state=post,
            action=LearningStepAction.FAILURE,
            mode="relearning_step",
            retrieval_occurred=True,
            next_due_in_minutes=self._relearning_steps[0],
        )

    def relearning_result(
        self,
        snapshot: dict[str, Any],
        *,
        success: bool,
    ) -> LearningStepTransition:
        """Advance or reset short relearning steps."""
        self._require_state(snapshot, "relearning")
        return self._short_step_result(
            snapshot,
            success=success,
            steps=self._relearning_steps,
            failure_state="relearning",
        )

    def _short_step_result(
        self,
        snapshot: dict[str, Any],
        *,
        success: bool,
        steps: tuple[int, ...],
        failure_state: str,
    ) -> LearningStepTransition:
        now = self._clock.now()
        post = dict(snapshot)
        seen_count = int(snapshot.get("seen_count", 0)) + 1
        if not success:
            post.update(
                {
                    "state": failure_state,
                    "seen_count": seen_count,
                    "last_seen_at_utc": now.isoformat(),
                    "last_result": "wrong",
                    "next_due_at_utc": (now + timedelta(minutes=steps[0])).isoformat(),
                    "streak_correct": 0,
                    "updated_at_utc": now.isoformat(),
                }
            )
            return LearningStepTransition(
                pre_state=dict(snapshot),
                post_state=post,
                action=LearningStepAction.FAILURE,
                mode=f"{failure_state}_step",
                retrieval_occurred=True,
                next_due_in_minutes=steps[0],
            )

        completed_steps = int(snapshot.get("streak_correct", 0)) + 1
        post.update(
            {
                "seen_count": seen_count,
                "last_seen_at_utc": now.isoformat(),
                "last_result": "correct",
                "streak_correct": completed_steps,
                "updated_at_utc": now.isoformat(),
            }
        )
        if completed_steps >= len(steps):
            post["next_due_at_utc"] = None
            return LearningStepTransition(
                pre_state=dict(snapshot),
                post_state=post,
                action=LearningStepAction.SUCCESS,
                mode=f"{failure_state}_step",
                retrieval_occurred=True,
                next_due_in_minutes=None,
                ready_for_long_review=True,
            )

        next_delay = steps[completed_steps]
        post["next_due_at_utc"] = (now + timedelta(minutes=next_delay)).isoformat()
        return LearningStepTransition(
            pre_state=dict(snapshot),
            post_state=post,
            action=LearningStepAction.SUCCESS,
            mode=f"{failure_state}_step",
            retrieval_occurred=True,
            next_due_in_minutes=next_delay,
        )

    @staticmethod
    def _require_state(snapshot: dict[str, Any], expected: str) -> None:
        actual = snapshot.get("state")
        if actual != expected:
            raise LearningStateError(f"expected state {expected!r}, got {actual!r}")
