"""Beta.3 safety contract for explicit early Learn continuation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from custom_components.locklearn.core.learning_sessions import (
    LearningSessionError,
    LearningSessionService,
)


@dataclass
class _Clock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def _service() -> LearningSessionService:
    service = object.__new__(LearningSessionService)
    service._clock = _Clock(datetime(2026, 9, 29, 12, 0, tzinfo=UTC))
    return service


def _question(*, reason: str, progress_state: str = "learning") -> dict[str, object]:
    return {
        "payload": {
            "available_at_utc": "2026-09-29T12:10:00+00:00",
            "selection": {
                "progress_state": progress_state,
                "reason": reason,
            },
        }
    }


def test_post_introduction_learning_step_can_be_explicitly_continued_early() -> None:
    service = _service()

    with pytest.raises(LearningSessionError, match="not due yet"):
        service._require_question_available(_question(reason="learning_step"))

    service._require_question_available(
        _question(reason="learning_step"),
        allow_early=True,
    )


@pytest.mark.parametrize(
    ("progress_state", "reason"),
    (
        ("relearning", "relearning_due"),
        ("learning", "learning_due"),
        ("review", "review_due"),
    ),
)
def test_early_override_never_bypasses_non_introduction_cooldowns(
    progress_state: str,
    reason: str,
) -> None:
    service = _service()

    with pytest.raises(LearningSessionError, match="not due yet"):
        service._require_question_available(
            _question(progress_state=progress_state, reason=reason),
            allow_early=True,
        )
