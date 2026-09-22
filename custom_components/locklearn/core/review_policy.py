"""Deterministic V1 long-review policy."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .clock import Clock, SystemClock
from .learning import LearningStateMachine, LearningStepTransition

POLICY_VERSION_V1 = 1
DEFAULT_BOX_INTERVAL_DAYS = {
    1: 8 / 24,
    2: 1.0,
    3: 3.0,
    4: 7.0,
    5: 14.0,
    6: 30.0,
    7: 60.0,
}
DEFAULT_DIFFICULTY_BOUNDS = (0.6, 2.0)
DEFAULT_RELAPSE_PENALTY = 2
DEFAULT_JITTER_FRACTION = 0.10


class ReviewPolicyError(ValueError):
    """Raised when a V1 review transition is invalid."""


@dataclass(frozen=True, slots=True)
class ReviewTransition:
    """Deterministic result of one long-review policy transition."""

    pre_state: dict[str, Any]
    post_state: dict[str, Any]
    policy_version: int
    scheduled_interval_days: float | None
    elapsed_days: float | None
    effective_interval_days: float | None
    entered_relearning: bool = False


class ReviewPolicyV1:
    """Simple deterministic and explainable V1 long-review policy."""

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        learning: LearningStateMachine | None = None,
        relapse_penalty: int = DEFAULT_RELAPSE_PENALTY,
        jitter_fraction: float = DEFAULT_JITTER_FRACTION,
        difficulty_bounds: tuple[float, float] = DEFAULT_DIFFICULTY_BOUNDS,
    ) -> None:
        self._clock = clock or SystemClock()
        self._learning = learning or LearningStateMachine(clock=self._clock)
        if relapse_penalty < 0:
            raise ReviewPolicyError("relapse_penalty must be >= 0")
        if not 0 <= jitter_fraction <= 0.25:
            raise ReviewPolicyError("jitter_fraction must be within [0, 0.25]")
        lower, upper = difficulty_bounds
        if lower <= 0 or upper < lower:
            raise ReviewPolicyError("invalid difficulty_factor bounds")
        self._relapse_penalty = relapse_penalty
        self._jitter_fraction = jitter_fraction
        self._difficulty_bounds = difficulty_bounds

    @property
    def policy_version(self) -> int:
        """Stable policy version persisted in ReviewEvents."""
        return POLICY_VERSION_V1

    def graduate_short_steps(
        self,
        transition: LearningStepTransition,
    ) -> ReviewTransition:
        """Move a completed learning/relearning sequence into long review."""
        if not transition.ready_for_long_review:
            raise ReviewPolicyError("short-step transition is not ready for long review")
        snapshot = transition.post_state
        state = snapshot.get("state")
        if state not in {"learning", "relearning"}:
            raise ReviewPolicyError("only learning/relearning can graduate")

        now = self._clock.now()
        target_box = 1 if state == "learning" else max(1, int(snapshot.get("box", 0)))
        interval = self._jittered_interval(
            card_key=str(snapshot.get("card_key", "")),
            target_box=target_box,
            ordinal=int(snapshot.get("verified_correct_count", 0))
            + int(snapshot.get("verified_wrong_count", 0)),
            interval_days=DEFAULT_BOX_INTERVAL_DAYS[target_box] * self._difficulty(snapshot),
        )
        post = dict(snapshot)
        post.update(
            {
                "state": "review",
                "box": target_box,
                "next_due_at_utc": (now + timedelta(days=interval)).isoformat(),
                "streak_correct": 0,
                "policy_version": self.policy_version,
                "updated_at_utc": now.isoformat(),
            }
        )
        post["mastery"] = self.mastery(post, at=now)
        return ReviewTransition(
            pre_state=dict(snapshot),
            post_state=post,
            policy_version=self.policy_version,
            scheduled_interval_days=None,
            elapsed_days=None,
            effective_interval_days=interval,
        )

    def review_success(
        self,
        snapshot: dict[str, Any],
        *,
        hint_used: bool = False,
        promote_box: bool = True,
        verified: bool = True,
        reward_difficulty: bool = True,
    ) -> ReviewTransition:
        """Schedule a successful review with caller-supplied signal confidence."""
        self._require_review(snapshot)
        now = self._clock.now()
        scheduled_interval = self._scheduled_interval_days(snapshot)
        elapsed = self._elapsed_days(snapshot, now) if verified else None

        current_box = max(1, int(snapshot.get("box", 1)))
        target_box = (
            min(max(DEFAULT_BOX_INTERVAL_DAYS), current_box + 1) if promote_box else current_box
        )
        difficulty = self._difficulty(snapshot)
        if verified and reward_difficulty and not hint_used:
            difficulty = self._clamp_difficulty(difficulty * 1.05)

        base_adjusted = DEFAULT_BOX_INTERVAL_DAYS[target_box] * difficulty
        demonstrated_floor = base_adjusted if elapsed is None else max(base_adjusted, elapsed)
        jittered = self._jittered_interval(
            card_key=str(snapshot.get("card_key", "")),
            target_box=target_box,
            ordinal=int(snapshot.get("verified_correct_count", 0))
            + int(snapshot.get("verified_wrong_count", 0))
            + 1,
            interval_days=base_adjusted,
        )
        interval = max(demonstrated_floor, jittered)
        post = dict(snapshot)
        post.update(
            {
                "state": "review",
                "box": target_box,
                "seen_count": int(snapshot.get("seen_count", 0)) + 1,
                "verified_correct_count": int(snapshot.get("verified_correct_count", 0))
                + int(verified),
                "last_seen_at_utc": now.isoformat(),
                "last_result": "correct",
                "next_due_at_utc": (now + timedelta(days=interval)).isoformat(),
                "streak_correct": int(snapshot.get("streak_correct", 0)) + 1,
                "difficulty_factor": difficulty,
                "policy_version": self.policy_version,
                "updated_at_utc": now.isoformat(),
            }
        )
        if verified:
            post["last_verified_at_utc"] = now.isoformat()
        if target_box != current_box:
            post["verified_success_since_box"] = 0
        elif verified:
            post["verified_success_since_box"] = (
                int(snapshot.get("verified_success_since_box", 0)) + 1
            )
        post["mastery"] = self.mastery(post, at=now)
        return ReviewTransition(
            pre_state=dict(snapshot),
            post_state=post,
            policy_version=self.policy_version,
            scheduled_interval_days=scheduled_interval,
            elapsed_days=elapsed,
            effective_interval_days=interval,
        )

    def review_failure(
        self,
        snapshot: dict[str, Any],
        *,
        verified: bool = True,
        demote: bool = True,
    ) -> ReviewTransition:
        """Enter relearning, applying relapse penalties only to verified failures."""
        self._require_review(snapshot)
        now = self._clock.now()
        scheduled_interval = self._scheduled_interval_days(snapshot)
        elapsed = self._elapsed_days(snapshot, now)
        difficulty = self._difficulty(snapshot)
        if verified:
            difficulty = self._clamp_difficulty(difficulty * 0.85)
        demoted_box = int(snapshot.get("box", 0))
        if verified and demote:
            demoted_box = max(0, demoted_box - self._relapse_penalty)

        demoted = dict(snapshot)
        demoted.update(
            {
                "box": demoted_box,
                "seen_count": int(snapshot.get("seen_count", 0)) + 1,
                "verified_wrong_count": int(snapshot.get("verified_wrong_count", 0))
                + int(verified),
                "last_seen_at_utc": now.isoformat(),
                "last_result": "wrong",
                "streak_correct": 0,
                "difficulty_factor": difficulty,
                "verified_success_since_box": 0,
                "policy_version": self.policy_version,
                "updated_at_utc": now.isoformat(),
            }
        )
        if verified:
            demoted["last_verified_at_utc"] = now.isoformat()
        relearning = self._learning.enter_relearning(demoted)
        post = dict(relearning.post_state)
        post["mastery"] = self.mastery(post, at=now)
        return ReviewTransition(
            pre_state=dict(snapshot),
            post_state=post,
            policy_version=self.policy_version,
            scheduled_interval_days=scheduled_interval,
            elapsed_days=elapsed,
            effective_interval_days=None,
            entered_relearning=True,
        )

    def mastery(
        self,
        snapshot: dict[str, Any],
        *,
        at: datetime | None = None,
    ) -> float:
        """Return a non-terminal mastery label that decays with elapsed time."""
        moment = at or self._clock.now()
        box = max(0, min(max(DEFAULT_BOX_INTERVAL_DAYS), int(snapshot.get("box", 0))))
        box_score = box / max(DEFAULT_BOX_INTERVAL_DAYS)

        correct = int(snapshot.get("verified_correct_count", 0))
        wrong = int(snapshot.get("verified_wrong_count", 0))
        attempts = correct + wrong
        accuracy = 0.0 if attempts == 0 else correct / attempts
        raw = 0.7 * box_score + 0.3 * accuracy

        last_verified_raw = snapshot.get("last_verified_at_utc")
        if not isinstance(last_verified_raw, str) or not last_verified_raw:
            return round(max(0.0, min(1.0, raw)), 6)
        last_verified = datetime.fromisoformat(last_verified_raw)
        elapsed_days = max(0.0, (moment - last_verified).total_seconds() / 86400)
        reference = max(1.0, DEFAULT_BOX_INTERVAL_DAYS.get(max(1, box), 1.0) * 2)
        decay = math.pow(0.5, elapsed_days / reference)
        return round(max(0.0, min(1.0, raw * decay)), 6)

    def is_mastered(
        self,
        snapshot: dict[str, Any],
        *,
        threshold: float = 0.75,
    ) -> bool:
        """Return a display label without changing scheduling state."""
        if not 0 < threshold <= 1:
            raise ReviewPolicyError("mastery threshold must be within (0, 1]")
        return self.mastery(snapshot) >= threshold

    def _scheduled_interval_days(self, snapshot: dict[str, Any]) -> float | None:
        last_raw = snapshot.get("last_verified_at_utc")
        due_raw = snapshot.get("next_due_at_utc")
        if isinstance(last_raw, str) and last_raw and isinstance(due_raw, str) and due_raw:
            scheduled = (
                datetime.fromisoformat(due_raw) - datetime.fromisoformat(last_raw)
            ).total_seconds() / 86400
            return max(0.0, scheduled)
        box = int(snapshot.get("box", 0))
        return DEFAULT_BOX_INTERVAL_DAYS.get(box)

    @staticmethod
    def _elapsed_days(snapshot: dict[str, Any], now: datetime) -> float | None:
        last_raw = snapshot.get("last_verified_at_utc")
        if not isinstance(last_raw, str) or not last_raw:
            return None
        return max(
            0.0,
            (now - datetime.fromisoformat(last_raw)).total_seconds() / 86400,
        )

    def _difficulty(self, snapshot: dict[str, Any]) -> float:
        return self._clamp_difficulty(float(snapshot.get("difficulty_factor", 1.0)))

    def _clamp_difficulty(self, value: float) -> float:
        lower, upper = self._difficulty_bounds
        return max(lower, min(upper, value))

    def _jittered_interval(
        self,
        *,
        card_key: str,
        target_box: int,
        ordinal: int,
        interval_days: float,
    ) -> float:
        seed = f"{card_key}|{self.policy_version}|{target_box}|{ordinal}".encode()
        digest = hashlib.sha256(seed).digest()
        unit = int.from_bytes(digest[:8], "big") / (2**64 - 1)
        jitter = (unit * 2 - 1) * self._jitter_fraction
        return max(1 / 1440, interval_days * (1 + jitter))

    @staticmethod
    def _require_review(snapshot: dict[str, Any]) -> None:
        if snapshot.get("state") != "review":
            raise ReviewPolicyError("long-review transition requires state 'review'")
