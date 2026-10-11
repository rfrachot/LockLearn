"""Exam policy regressions for private answer keys and deferred scoring."""

from __future__ import annotations

from typing import Any, cast

import pytest

from custom_components.locklearn.core.exams import ExamError, ExamService
from custom_components.locklearn.storage.database import StaleSessionError


class _FakeSessions:
    def __init__(self) -> None:
        self.current = {
            "id": "exam-1", "type": "exam", "status": "active", "version": 1,
            "current_question": {
                "question_id": "q1",
                "payload": {"quiz": {"options": [
                    {"answer_id": "a", "text": "One"},
                    {"answer_id": "b", "text": "Two"},
                ]}},
            },
        }
        self.answers: list[dict[str, Any]] = []

    async def async_get(self, session_id: str) -> dict[str, Any]:
        assert session_id == "exam-1"
        return self.current

    async def async_answer(
        self, session_id: str, expected_version: int,
        question_id: str, answer: dict[str, Any],
    ) -> dict[str, Any]:
        assert expected_version == self.current["version"]
        self.answers.append(answer)
        self.current = {
            **self.current, "version": 2, "current_question": None,
        }
        return self.current


@pytest.mark.asyncio
async def test_exam_accepts_only_frozen_choices_without_immediate_feedback() -> None:
    sessions = _FakeSessions()
    exam = ExamService(cast(Any, None), cast(Any, sessions), cast(Any, None))
    with pytest.raises(ExamError, match="frozen exam question"):
        await exam.async_answer("exam-1", 1, "q1", "fabricated")
    assert sessions.answers == []

    state = await exam.async_answer("exam-1", 1, "q1", "b")
    assert state["version"] == 2
    assert sessions.answers == [{"selected_answer_id": "b", "kind": "exam"}]
    assert "feedback" not in state
    with pytest.raises(StaleSessionError):
        await exam.async_answer("exam-1", 1, "q1", "a")


@pytest.mark.asyncio
async def test_exam_idk_is_frozen_without_client_side_grading() -> None:
    sessions = _FakeSessions()
    exam = ExamService(cast(Any, None), cast(Any, sessions), cast(Any, None))
    state = await exam.async_answer("exam-1", 1, "q1", None)
    assert state["current_question"] is None
    assert sessions.answers == [{"selected_answer_id": None, "kind": "exam"}]
