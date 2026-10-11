"""Exam policy regressions for private answer keys and deferred scoring."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from custom_components.locklearn.core.exams import ExamError, ExamService
from custom_components.locklearn.core.sessions import SessionService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from custom_components.locklearn.storage.database import StaleSessionError
from custom_components.locklearn.storage.repositories import ProfileRecord, ReviewEventsRepository


class _FakeSessions:
    def __init__(self) -> None:
        self.current = {
            "id": "exam-1",
            "type": "exam",
            "status": "active",
            "version": 1,
            "current_question": {
                "question_id": "q1",
                "payload": {
                    "quiz": {
                        "options": [
                            {"answer_id": "a", "text": "One"},
                            {"answer_id": "b", "text": "Two"},
                        ]
                    }
                },
            },
        }
        self.answers: list[dict[str, Any]] = []

    async def async_get(self, session_id: str) -> dict[str, Any]:
        assert session_id == "exam-1"
        return self.current

    async def async_answer(
        self,
        session_id: str,
        expected_version: int,
        question_id: str,
        answer: dict[str, Any],
        *,
        allow_exam: bool = False,
    ) -> dict[str, Any]:
        assert allow_exam
        assert expected_version == self.current["version"]
        self.answers.append(answer)
        self.current = {
            **self.current,
            "version": 2,
            "current_question": None,
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


@pytest.mark.asyncio
async def test_exam_finish_is_atomic_neutral_and_replay_safe(tmp_path: Any) -> None:
    paths = StoragePaths(tmp_path / "state.db", tmp_path / "content.db")
    storage = SQLiteStorage(paths)
    await storage.async_open()

    class _SessionReader:
        async def async_get(self, session_id: str) -> dict[str, Any] | None:
            return await storage.async_get_session(session_id)

        def publish(self, session_id: str, state: dict[str, Any]) -> None:
            del session_id, state

    try:
        await storage.repositories.profiles.async_insert(
            ProfileRecord(
                profile_id="profile-1",
                name="Exam profile",
                preset="standard",
                timezone="Europe/Paris",
                created_at_utc="2026-01-01T00:00:00+00:00",
                updated_at_utc="2026-01-01T00:00:00+00:00",
            )
        )
        snapshot = {
            "profile_id": "profile-1",
            "track_id": "track-1",
            "card_key": "card-1",
            "learning_item_id": "item-1",
            "prompt_facet_id": "facet-ja",
            "answer_facet_id": "facet-en",
            "state": "review",
            "mastery": 0.4,
            "box": 2,
            "seen_count": 3,
            "verified_correct_count": 1,
            "verified_wrong_count": 1,
            "self_known_count": 0,
            "self_review_count": 1,
            "first_seen_at_utc": "2026-01-01T00:00:00+00:00",
            "last_seen_at_utc": "2026-01-01T00:00:00+00:00",
            "last_result": "wrong",
            "next_due_at_utc": "2026-01-02T00:00:00+00:00",
            "streak_correct": 0,
            "leech_score": 0.1,
            "difficulty_factor": 1.0,
            "last_verified_at_utc": None,
            "verified_success_since_box": 0,
            "user_state": "active",
            "suspend_until_utc": None,
            "example_rotation_index": 0,
            "content_status": "active",
            "policy_version": 1,
            "dataset_generation": "fixture",
            "normalization_version": 1,
            "updated_at_utc": "2026-01-01T00:00:00+00:00",
        }

        def insert_progress(connection: Any) -> None:
            columns = ReviewEventsRepository._PROGRESS_COLUMNS
            connection.execute(
                f"INSERT INTO progress({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                tuple(snapshot[column] for column in columns),
            )
            connection.commit()

        await storage._async_writer(insert_progress)
        await storage.async_create_session(
            "exam-atomic",
            "profile-1",
            "track-1",
            session_type="exam",
            strategy="exam",
            settings={"requested_cards": 1, "direction": "any"},
            items=(
                {
                    "question_id": "q1",
                    "card_key": "card-1",
                    "learning_item_id": "item-1",
                    "prompt_facet_id": "facet-ja",
                    "answer_facet_id": "facet-en",
                    "payload": {
                        "quiz": {
                            "prompt_text": "猫",
                            "context_hint": "animal",
                            "options": [
                                {"answer_id": "a", "text": "cat"},
                                {"answer_id": "b", "text": "dog"},
                            ],
                        }
                    },
                },
            ),
            exam_attempt={
                "settings": {"expected": {"q1": {"answer_id": "a", "answer_text": "cat"}}}
            },
        )
        with pytest.raises(ValueError, match="exam answer endpoint"):
            await storage.async_answer_session("exam-atomic", 1, "q1", {"selected_answer_id": "a"})
        with pytest.raises(ValueError, match="exam/finish"):
            await storage.async_set_session_status("exam-atomic", 1, status="completed")
        with pytest.raises(ValueError, match="cannot be undone"):
            await storage.async_undo_session_answer("exam-atomic", 1)
        sessions = SessionService(storage)
        answered = await sessions.async_answer(
            "exam-atomic",
            1,
            "q1",
            {"selected_answer_id": "a", "kind": "exam"},
            allow_exam=True,
        )
        assert "expected" not in json.dumps(answered)
        exam = ExamService(storage, cast(Any, _SessionReader()), cast(Any, None))
        with pytest.raises(ExamError, match="unavailable"):
            await exam.async_result("exam-atomic")

        def delete_progress(connection: Any) -> None:
            connection.execute(
                "DELETE FROM progress WHERE profile_id = 'profile-1' AND card_key = 'card-1'"
            )
            connection.commit()

        await storage._async_writer(delete_progress)
        with pytest.raises(ExamError, match="no progress"):
            await exam.async_finish("exam-atomic", 2)
        history = await storage.async_list_exam_attempts("profile-1")
        assert history["cursor"] is None
        assert history["items"][0]["attempt_id"] == "exam-atomic"
        assert history["items"][0]["status"] == "active"
        assert history["items"][0]["question_count"] == 1
        assert history["items"][0]["correct_count"] == 0
        assert history["items"][0]["session_status"] == "active"
        assert (
            await storage._async_reader(
                lambda connection: connection.execute(
                    "SELECT COUNT(*) FROM review_events"
                ).fetchone()[0]
            )
            == 0
        )

        await storage._async_writer(insert_progress)
        finished = await exam.async_finish("exam-atomic", 2)
        assert finished["result"]["questions"] == [
            {
                "question_id": "q1",
                "prompt": "猫",
                "context": "animal",
                "given": "cat",
                "correct": "cat",
                "result": "correct",
            }
        ]
        with pytest.raises(StaleSessionError):
            await exam.async_finish("exam-atomic", 2)
        event = await storage._async_reader(
            lambda connection: connection.execute(
                "SELECT mode, retrieval_occurred, signal_quality, expected_answer_id, "
                "pre_state_snapshot, post_state_snapshot FROM review_events"
            ).fetchone()
        )
        assert event[0:4] == ("exam_retrieval", 1, "none", "a")
        assert event[4] == event[5]
        current_progress = await storage._async_reader(
            lambda connection: connection.execute(
                "SELECT box, verified_correct_count FROM progress WHERE card_key = 'card-1'"
            ).fetchone()
        )
        assert current_progress == (2, 1)
    finally:
        await storage.async_close()


def test_exam_selection_helpers_are_filterable_and_not_srs_ranked() -> None:
    track = {"source_language": "ja", "target_language": "fr"}
    row = {
        "content_type": "vocabulary",
        "tag_ids": ("locklearn:tag:level:n5", "locklearn:tag:food"),
        "difficulty_factor": 1.0,
        "pack_position": 4,
        "card_key": "card-a",
        "prompt_language": "ja",
        "answer_language": "fr",
    }
    assert ExamService._matches_direction(row, track, "forward")
    assert not ExamService._matches_direction(row, track, "reverse")
    assert ExamService._matches_levels(row, {"n5"})
    assert not ExamService._matches_levels(row, {"n4"})
    assert ExamService._stratum(row) == ("vocabulary", "locklearn:tag:level:n5", "standard")
    assert ExamService._ordering_key(row, "seed", True) != (4, "card-a")


@pytest.mark.asyncio
async def test_exam_attempt_and_frozen_session_are_created_atomically(tmp_path: Any) -> None:
    storage = SQLiteStorage(StoragePaths(tmp_path / "state.db", tmp_path / "content.db"))
    await storage.async_open()
    try:
        state = await storage.async_create_session(
            "exam-atomic",
            "profile-1",
            "track-1",
            session_type="exam",
            strategy="balanced",
            settings={"direction": "any"},
            items=(
                {
                    "question_id": "q1",
                    "card_key": "card-1",
                    "learning_item_id": "item-1",
                    "prompt_facet_id": "prompt-1",
                    "answer_facet_id": "answer-1",
                    "payload": {"quiz": {"options": [{"answer_id": "a", "text": "A"}]}},
                },
            ),
            exam_attempt={"settings": {"expected": {"q1": {"answer_id": "a"}}}},
        )
        assert state["type"] == "exam"
        assert "expected" not in state["settings"]
        attempt = await storage._async_reader(
            lambda connection: connection.execute(
                "SELECT status, settings_json FROM exam_attempts WHERE attempt_id = ?",
                ("exam-atomic",),
            ).fetchone()
        )
        assert attempt is not None
        assert attempt[0] == "active"
        assert '"answer_id":"a"' in str(attempt[1])
        history = await storage.async_list_exam_attempts("profile-1")
        assert history["items"][0]["attempt_id"] == "exam-atomic"
    finally:
        await storage.async_close()
