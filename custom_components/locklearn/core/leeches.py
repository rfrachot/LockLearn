"""Versioned P3.11 leech detection policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

LEECH_POLICY_VERSION_V1 = 1
LEECH_WINDOW_DAYS_V1 = 60
LEECH_RECENT_ATTEMPTS_V1 = 10
LEECH_FAILURES_V1 = 6
LEECH_RELAPSES_V1 = 8

_VERIFIED_MODES = frozenset(
    {"verified_mcq", "verified_free_text", "verified_cloze", "exam_retrieval"}
)
_TRUSTED_QUALITIES = frozenset({"weak", "medium", "strong"})
_FAILURE_RESULTS = frozenset({"wrong", "idk"})


@dataclass(frozen=True, slots=True)
class LeechDecision:
    """Explainable result of one leech-policy evaluation."""

    detected: bool
    policy_version: int
    recent_verified_attempts: int
    recent_verified_failures: int
    verified_relapses_in_window: int
    score: float
    reason: str | None


class LeechPolicyV1:
    """Apply the V1 versioned thresholds from SPEC §31."""

    policy_version = LEECH_POLICY_VERSION_V1

    def evaluate(
        self,
        history: tuple[dict[str, Any], ...],
        *,
        current: dict[str, Any],
        now: datetime,
    ) -> LeechDecision:
        cutoff = now - timedelta(days=LEECH_WINDOW_DAYS_V1)
        events = [event for event in history if self._timestamp(event) >= cutoff]
        if self.is_trusted_verified(current):
            events.append(current)
        events.sort(key=self._timestamp, reverse=True)

        recent = events[:LEECH_RECENT_ATTEMPTS_V1]
        failures = sum(str(event.get("result")) in _FAILURE_RESULTS for event in recent)
        relapses = sum(self._is_verified_relapse(event) for event in events)
        trigger_failures = len(recent) >= LEECH_RECENT_ATTEMPTS_V1 and failures >= LEECH_FAILURES_V1
        trigger_relapses = relapses >= LEECH_RELAPSES_V1
        detected = trigger_failures or trigger_relapses
        score = max(
            failures / LEECH_FAILURES_V1,
            relapses / LEECH_RELAPSES_V1,
        )
        reason = (
            "recent_verified_failures"
            if trigger_failures
            else "verified_relapses"
            if trigger_relapses
            else None
        )
        return LeechDecision(
            detected=detected,
            policy_version=self.policy_version,
            recent_verified_attempts=len(recent),
            recent_verified_failures=failures,
            verified_relapses_in_window=relapses,
            score=round(score, 6),
            reason=reason,
        )

    @staticmethod
    def is_trusted_verified(event: dict[str, Any]) -> bool:
        return (
            bool(event.get("retrieval_occurred"))
            and str(event.get("mode")) in _VERIFIED_MODES
            and str(event.get("signal_quality")) in _TRUSTED_QUALITIES
            and str(event.get("result")) in {"correct", "wrong", "idk"}
        )

    @classmethod
    def _is_verified_relapse(cls, event: dict[str, Any]) -> bool:
        if not cls.is_trusted_verified(event):
            return False
        if str(event.get("result")) not in _FAILURE_RESULTS:
            return False
        pre = event.get("pre_state_snapshot")
        return isinstance(pre, dict) and str(pre.get("state")) in {"review", "leech"}

    @staticmethod
    def _timestamp(event: dict[str, Any]) -> datetime:
        raw = event.get("created_at_utc")
        if not isinstance(raw, str):
            raise ValueError("leech history event requires created_at_utc")
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            raise ValueError("leech history timestamp must be timezone-aware")
        return parsed
