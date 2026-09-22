"""P3.8 persistent-session, CAS and cross-client resume tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.sessions import SessionQuestion, SessionService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from custom_components.locklearn.storage.database import StaleSessionError
from tests.backend.content_db_helpers import ITEM_A, ITEM_B, card_identity, create_package, facet_ids


@dataclass
class _MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


async def _configured_storage(
    tmp_path: Path,
) -> tuple[SQLiteStorage, SessionService, _MutableClock]:
    clock = _MutableClock(datetime(2026, 9, 22, 22, 0, tzinfo=UTC))
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()

    package = create_package(
        tmp_path / "sessions-package.db",
        "sessions",
        active_item_ids=(ITEM_A, ITEM_B),
    )
    candidate = storage.paths.content_staging_dir / "generation-sessions.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-sessions",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "profile-sessions",
    )
    await profiles.async_create_profile(
        name="Sessions",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )

    tracks = TrackService(
        storage.repositories.tracks,
        clock=clock,
        id_factory=lambda: "track-sessions",
    )
    await tracks.async_create_track(
        profile_id="profile-sessions",
        name="Sessions Track",
        pack_version_id="locklearn:pack-version:sessions",
        source_language="en",
        target_language="fr",
        explicit_card_keys=(card_identity(ITEM_A)[1], card_identity(ITEM_B)[1]),
    )
    return storage, SessionService(storage), clock


def _question(item_id: str, question_id: str) -> SessionQuestion:
    prompt_id, answer_id = facet_ids(item_id)
    return SessionQuestion(
        question_id=question_id,
        card_key=card_identity(item_id)[1],
        learning_item_id=item_id,
        prompt_facet_id=prompt_id,
        answer_facet_id=answer_id,
        payload={
            "format": "mcq",
            "dataset_generation": "generation-sessions",
            "presentation_index": 0,
        },
    )


async def test_session_persists_strategy_settings_questions_and_answers(
    tmp_path: Path,
) -> None:
    storage, sessions, clock = await _configured_storage(tmp_path)
    paths = storage.paths
    try:
        started = await sessions.async_start(
            "profile-sessions",
            "track-sessions",
            session_type="bounded",
            strategy="due_then_new",
            settings={"requested_cards": 2, "content_types": ["vocabulary"]},
            questions=(_question(ITEM_A, "q-a"), _question(ITEM_B, "q-b")),
        )

        assert started["type"] == "bounded"
        assert started["strategy"] == "due_then_new"
        assert started["question_count"] == 2
        assert started["current_position"] == 0
        assert started["settings"]["requested_cards"] == 2
        assert started["current_question"]["question_id"] == "q-a"
        assert [item["status"] for item in started["items"]] == ["presented", "queued"]

        answered = await sessions.async_answer(
            started["id"],
            1,
            "q-a",
            {"choice": "answer-a"},
        )
        assert answered["version"] == 2
        assert answered["current_position"] == 1
        assert answered["current_question"]["question_id"] == "q-b"
        assert [item["status"] for item in answered["items"]] == ["answered", "presented"]
        assert answered["answers"][0]["answer"] == {"choice": "answer-a"}

        clock.current = datetime(2026, 9, 22, 22, 5, tzinfo=UTC)
        paused = await sessions.async_pause(started["id"], 2)
        assert paused["status"] == "paused"
        assert paused["version"] == 3
    finally:
        sessions.close()
        await storage.async_close()

    reopened = SQLiteStorage(paths, clock=clock)
    await reopened.async_open()
    try:
        resumed_snapshot = await reopened.async_get_session(started["id"])
        assert resumed_snapshot is not None
        assert resumed_snapshot["status"] == "paused"
        assert resumed_snapshot["version"] == 3
        assert resumed_snapshot["current_question"]["question_id"] == "q-b"
        assert resumed_snapshot["answers"][0]["question_id"] == "q-a"
        assert resumed_snapshot["settings"]["content_types"] == ["vocabulary"]
    finally:
        await reopened.async_close()


async def test_exactly_one_same_version_answer_wins(tmp_path: Path) -> None:
    storage, sessions, _clock = await _configured_storage(tmp_path)
    try:
        started = await sessions.async_start(
            "profile-sessions",
            "track-sessions",
            questions=(_question(ITEM_A, "q-a"),),
        )
        results = await asyncio.gather(
            sessions.async_answer(started["id"], 1, "q-a", {"choice": "a"}),
            sessions.async_answer(started["id"], 1, "q-a", {"choice": "b"}),
            return_exceptions=True,
        )

        assert sum(isinstance(result, dict) for result in results) == 1
        assert sum(isinstance(result, StaleSessionError) for result in results) == 1
        winner = next(result for result in results if isinstance(result, dict))
        assert winner["version"] == 2
        assert winner["current_position"] == 1
        assert len(winner["answers"]) == 1
    finally:
        sessions.close()
        await storage.async_close()


async def test_wrong_question_id_is_rejected_by_same_cas_boundary(tmp_path: Path) -> None:
    storage, sessions, _clock = await _configured_storage(tmp_path)
    try:
        started = await sessions.async_start(
            "profile-sessions",
            "track-sessions",
            questions=(_question(ITEM_A, "q-a"),),
        )

        try:
            await sessions.async_answer(
                started["id"],
                1,
                "not-current",
                {"choice": "a"},
            )
        except StaleSessionError:
            pass
        else:
            raise AssertionError("answer for a non-current question was accepted")

        snapshot = await sessions.async_get(started["id"])
        assert snapshot is not None
        assert snapshot["version"] == 1
        assert snapshot["current_position"] == 0
        assert snapshot["answers"] == []
    finally:
        sessions.close()
        await storage.async_close()


async def test_pause_resume_complete_and_navigation_undo_are_versioned(
    tmp_path: Path,
) -> None:
    storage, sessions, _clock = await _configured_storage(tmp_path)
    try:
        started = await sessions.async_start(
            "profile-sessions",
            "track-sessions",
            questions=(_question(ITEM_A, "q-a"), _question(ITEM_B, "q-b")),
        )
        answered = await sessions.async_answer(
            started["id"],
            1,
            "q-a",
            {"choice": "a"},
        )
        paused = await sessions.async_pause(started["id"], 2)
        assert paused["status"] == "paused"
        assert paused["version"] == 3

        resumed = await sessions.async_resume(started["id"], 3)
        assert resumed["status"] == "active"
        assert resumed["version"] == 4

        undone = await sessions.async_undo(
            started["id"],
            4,
            actor_user_id="owner",
        )
        assert undone["version"] == 5
        assert undone["current_position"] == 0
        assert undone["current_question"]["question_id"] == "q-a"
        assert [item["status"] for item in undone["items"]] == ["presented", "queued"]
        assert len(undone["answers"]) == 1

        reanswered = await sessions.async_answer(
            started["id"],
            5,
            "q-a",
            {"choice": "new-a"},
        )
        assert reanswered["version"] == 6
        assert len(reanswered["answers"]) == 2

        completed = await sessions.async_complete(started["id"], 6)
        assert completed["status"] == "completed"
        assert completed["version"] == 7
        assert completed["completed_at_utc"] is not None

        try:
            await sessions.async_resume(started["id"], 7)
        except StaleSessionError:
            pass
        else:
            raise AssertionError("completed session resumed")
    finally:
        sessions.close()
        await storage.async_close()


async def test_subscriber_receives_winning_mutations_only(tmp_path: Path) -> None:
    storage, sessions, _clock = await _configured_storage(tmp_path)
    try:
        started = await sessions.async_start(
            "profile-sessions",
            "track-sessions",
            questions=(_question(ITEM_A, "q-a"),),
        )
        events: list[dict[str, Any]] = []
        unsubscribe = sessions.subscribe(started["id"], events.append)
        try:
            await sessions.async_answer(
                started["id"],
                1,
                "q-a",
                {"choice": "a"},
            )
            try:
                await sessions.async_answer(
                    started["id"],
                    1,
                    "q-a",
                    {"choice": "b"},
                )
            except StaleSessionError:
                pass
            else:
                raise AssertionError("stale answer unexpectedly won")
        finally:
            unsubscribe()

        assert [event["version"] for event in events] == [2]
        assert sessions.subscriber_count == 0
    finally:
        sessions.close()
        await storage.async_close()
