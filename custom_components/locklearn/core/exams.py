"""P7.1: persistent closed-book MCQ exams with deferred correction."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from .clock import Clock, SystemClock
from typing import Any
from uuid import uuid4

from .quiz import QuizConstructionError
from .quiz_sessions import QuizSessionService
from .sessions import SessionQuestion, SessionService
from ..storage.database import SQLiteStorage, StaleSessionError


class ExamError(ValueError):
    """An exam request violates the persistent exam contract."""


class ExamService:
    """Freeze questions and private answer keys; reveal only after final submit."""

    def __init__(
        self, storage: SQLiteStorage, sessions: SessionService,
        quiz_sessions: QuizSessionService, *, clock: Clock | None = None,
    ) -> None:
        self._storage = storage
        self._sessions = sessions
        self._quiz_sessions = quiz_sessions
        self._clock = clock or SystemClock()

    async def async_start(
        self, *, profile_id: str, track_id: str,
        requested_cards: int = 20, content_types: list[str] | None = None,
    ) -> dict[str, Any]:
        if isinstance(requested_cards, bool) or not 1 <= requested_cards <= 100:
            raise ExamError("requested_cards must be within 1..100")
        if content_types is not None and (
            not isinstance(content_types, list)
            or not all(isinstance(value, str) and value for value in content_types)
        ):
            raise ExamError("content_types must be a list of non-empty strings")
        track = await self._storage.repositories.tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise ExamError("track does not belong to profile")
        rows = await self._storage.repositories.tracks.async_session_candidates(
            profile_id=profile_id, track_id=track_id,
        )
        allowed = set(content_types) if content_types is not None else None
        candidates = [
            row for row in rows
            if row["state"] != "new" and row.get("user_state", "active") == "active"
            and row.get("suspend_until_utc") is None
            and (allowed is None or row["content_type"] in allowed)
        ]
        # Stratify by content type rather than ranking by weakest SRS first.
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in candidates:
            groups[str(row["content_type"])].append(row)
        for group in groups.values():
            group.sort(key=lambda row: (int(row["pack_position"]), str(row["card_key"])))
        ordered: list[dict[str, Any]] = []
        used_items: set[str] = set()
        while groups and len(ordered) < requested_cards:
            for name in sorted(tuple(groups)):
                group = groups[name]
                while group and str(group[0]["learning_item_id"]) in used_items:
                    group.pop(0)
                if group:
                    row = group.pop(0)
                    ordered.append(row)
                    used_items.add(str(row["learning_item_id"]))
                if not group:
                    del groups[name]
                if len(ordered) >= requested_cards:
                    break

        catalog = await self._quiz_sessions._load_catalog(track_id)
        questions: list[SessionQuestion] = []
        private_keys: dict[str, dict[str, str]] = {}
        for row in ordered:
            meta = catalog.get(str(row["card_key"]))
            if meta is None or not meta.answer_terms:
                continue
            presentation = await self._quiz_sessions._presentation.async_for_card(
                track_id=track_id, card_key=meta.card_key,
            )
            try:
                question = self._quiz_sessions._build_choice_question(
                    meta,
                    catalog=catalog,
                    state=str(row["state"]),
                    presentation=presentation,
                    cloze_prompt=None,
                    quiz_format="mcq",
                    option_count=4,
                    presentation_index=len(questions),
                )
            except QuizConstructionError:
                continue
            question_id = f"exam-{len(questions) + 1}-{meta.card_key}"
            payload = self._quiz_sessions._base_payload(
                "mcq", presentation=presentation, meta=meta,
            )
            payload.update({
                "prompt_text": question.prompt_text,
                "context_hint": question.context_hint,
                "options": [
                    {"answer_id": option.answer_id, "text": option.display_text}
                    for option in question.options
                ],
                "reportable": False,
                "hint_blocks": [],
            })
            questions.append(SessionQuestion(
                question_id=question_id,
                card_key=meta.card_key,
                learning_item_id=meta.learning_item_id,
                prompt_facet_id=meta.prompt_facet_id,
                answer_facet_id=meta.answer_facet_id,
                payload={"quiz": payload},
            ))
            private_keys[question_id] = {
                "answer_id": meta.canonical_answer.term_id,
                "answer_text": meta.canonical_answer.text,
            }
        if not questions:
            raise ExamError("no eligible questions with safe MCQ distractors")
        session = await self._sessions.async_start(
            profile_id, track_id, session_type="exam",
            strategy="balanced", settings={
                "requested_cards": requested_cards,
                "content_types": content_types,
            }, questions=tuple(questions),
        )
        now = self._clock.now().isoformat()
        def insert(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO exam_attempts (
                       attempt_id, profile_id, track_id, status, settings_json,
                       question_count, started_at_utc
                   ) VALUES (?, ?, ?, 'active', ?, ?, ?)""",
                (
                    session["id"], profile_id, track_id,
                    json.dumps({"expected": private_keys}, sort_keys=True),
                    len(questions), now,
                ),
            )
            connection.commit()
        await self._storage._async_writer(insert)
        return session

    async def async_answer(
        self, session_id: str, expected_version: int,
        question_id: str, selected_answer_id: str | None,
    ) -> dict[str, Any]:
        state = await self._sessions.async_get(session_id)
        if state is None or state.get("type") != "exam":
            raise ExamError("exam session not found")
        current = state.get("current_question")
        if (
            state["status"] != "active"
            or int(state["version"]) != expected_version
            or not isinstance(current, dict)
            or current["question_id"] != question_id
        ):
            raise StaleSessionError(session_id)
        payload = current["payload"].get("quiz", {})
        choices = {
            item["answer_id"] for item in payload.get("options", [])
            if isinstance(item, dict) and isinstance(item.get("answer_id"), str)
        }
        if selected_answer_id is not None and selected_answer_id not in choices:
            raise ExamError("selected answer does not belong to the frozen exam question")
        # The writer transaction is CAS; concurrent clients cannot record twice.
        return await self._sessions.async_answer(
            session_id, expected_version, question_id,
            {"selected_answer_id": selected_answer_id, "kind": "exam"},
        )

    async def async_finish(self, session_id: str, expected_version: int) -> dict[str, Any]:
        """Commit final score and status together; nothing is graded during answering."""
        now = self._clock.now().isoformat()
        def finish(connection: sqlite3.Connection) -> dict[str, Any]:
            connection.execute("BEGIN IMMEDIATE")
            try:
                session = connection.execute(
                    """SELECT profile_id, track_id, status, version, question_count,
                              current_position FROM sessions WHERE id = ? AND type = 'exam'""",
                    (session_id,),
                ).fetchone()
                exam = connection.execute(
                    "SELECT settings_json, status FROM exam_attempts WHERE attempt_id = ?",
                    (session_id,),
                ).fetchone()
                if session is None or exam is None:
                    raise ExamError("exam not found")
                if (
                    session[2] != "active" or exam[1] != "active"
                    or int(session[3]) != expected_version
                    or int(session[5]) != int(session[4])
                ):
                    raise StaleSessionError(session_id)
                expected = json.loads(str(exam[0]))["expected"]
                rows = connection.execute(
                    """SELECT item.question_id, item.payload_json, answer.answer_json
                       FROM session_items AS item
                       JOIN session_answers AS answer
                         ON answer.session_id = item.session_id
                        AND answer.question_id = item.question_id
                       WHERE item.session_id = ? ORDER BY item.position""",
                    (session_id,),
                ).fetchall()
                if len(rows) != int(session[4]):
                    raise ExamError("exam is not fully answered")
                results = []
                correct_count = 0
                for question_id, payload_json, answer_json in rows:
                    item = json.loads(str(payload_json))["quiz"]
                    chosen = json.loads(str(answer_json)).get("selected_answer_id")
                    key = expected[str(question_id)]
                    correct = chosen == key["answer_id"]
                    correct_count += int(correct)
                    selected = next(
                        (
                            option["text"] for option in item["options"]
                            if option["answer_id"] == chosen
                        ), None,
                    )
                    results.append({
                        "question_id": question_id,
                        "prompt": item["prompt_text"],
                        "context": item.get("context_hint"),
                        "given": selected,
                        "correct": key["answer_text"],
                        "result": "correct" if correct else ("idk" if chosen is None else "wrong"),
                    })
                summary = {
                    "correct": correct_count, "total": len(results),
                    "percentage": round(correct_count * 100 / len(results), 2),
                    "questions": results,
                }
                connection.execute(
                    """UPDATE sessions SET status = 'completed',
                           version = version + 1, completed_at_utc = ?,
                           last_activity_at_utc = ?
                       WHERE id = ?""",
                    (now, now, session_id),
                )
                connection.execute(
                    """UPDATE exam_attempts SET status = 'completed', correct_count = ?,
                           completed_at_utc = ?, result_json = ?
                       WHERE attempt_id = ?""",
                    (correct_count, now, json.dumps(summary), session_id),
                )
                connection.commit()
                return summary
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise
        result = await self._storage._async_writer(finish)
        session = await self._sessions.async_get(session_id)
        assert session is not None
        self._sessions.publish(session_id, session)
        return {"result": result, "session": session}

    async def async_result(self, session_id: str) -> dict[str, Any]:
        """Never disclose grade/answer keys while an exam remains open."""
        def read(connection: sqlite3.Connection) -> dict[str, Any]:
            row = connection.execute(
                "SELECT status, result_json FROM exam_attempts WHERE attempt_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise ExamError("exam not found")
            if row[0] != "completed" or row[1] is None:
                raise ExamError("exam result is unavailable until completion")
            return json.loads(str(row[1]))
        return await self._storage._async_reader(read)
