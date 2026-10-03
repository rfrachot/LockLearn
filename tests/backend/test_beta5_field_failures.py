"""Regression coverage for failures found by the beta.5 real-HA qualification."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from custom_components.locklearn.core.learning_sessions import (
    LearningSessionError,
    LearningSessionService,
)
from tests.backend.test_integrity import _record, _setup, _snapshot


@pytest.mark.asyncio
async def test_undo_known_already_restores_target_owned_user_overlay(tmp_path: Path) -> None:
    """Undo must revert the overlay that the known_already event itself changed."""
    storage, reviews, integrity, _clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, state="new", box=0, seen_count=0, due=None)
        pre.update(
            {
                "mastery": 0.0,
                "self_known_count": 0,
                "first_seen_at_utc": None,
                "last_seen_at_utc": None,
                "last_result": None,
                "last_verified_at_utc": None,
                "user_state": "active",
                "suspend_until_utc": None,
            }
        )
        post = dict(pre)
        post.update(
            {
                "state": "review",
                "box": 1,
                "seen_count": 1,
                "self_known_count": 1,
                "first_seen_at_utc": "2026-09-23T20:00:00+00:00",
                "last_seen_at_utc": "2026-09-23T20:00:00+00:00",
                "last_result": "self_known",
                "next_due_at_utc": "2026-09-23T20:17:00+00:00",
                "user_state": "known_already",
            }
        )
        await _record(
            reviews,
            identity,
            pre=pre,
            post=post,
            mode="known_already",
            result="self_known",
        )

        result = await integrity.async_undo_last(
            actor_user_id="owner",
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )

        assert result["progress"]["state"] == "new"
        assert result["progress"]["box"] == 0
        assert result["progress"]["self_known_count"] == 0
        assert result["progress"]["user_state"] == "active"
        assert result["progress"]["next_due_at_utc"] is None

        persisted = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert persisted is not None
        assert persisted["state"] == "new"
        assert persisted["box"] == 0
        assert persisted["user_state"] == "active"
    finally:
        await storage.async_close()


@pytest.mark.asyncio
async def test_undo_preserves_overlay_not_owned_by_target_event(tmp_path: Path) -> None:
    """Independent user overlays still survive an ordinary SRS undo."""
    storage, reviews, integrity, _clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, box=1, seen_count=1)
        post = _snapshot(
            identity,
            box=2,
            seen_count=2,
            verified_correct_count=1,
            due="2026-09-26T20:00:00+00:00",
        )
        await _record(reviews, identity, pre=pre, post=post)

        def suspend(connection: Any) -> None:
            connection.execute(
                """UPDATE progress
                   SET user_state = 'suspended',
                       suspend_until_utc = '2026-09-30T20:00:00+00:00'
                   WHERE profile_id = ? AND track_id = ? AND card_key = ?""",
                (
                    identity["profile_id"],
                    identity["track_id"],
                    identity["card_key"],
                ),
            )
            connection.commit()

        await storage._async_writer(suspend)
        result = await integrity.async_undo_last(
            actor_user_id="owner",
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )

        assert result["progress"]["box"] == 1
        assert result["progress"]["user_state"] == "suspended"
        assert result["progress"]["suspend_until_utc"] == "2026-09-30T20:00:00+00:00"
    finally:
        await storage.async_close()


class _CanonicalSessions:
    def __init__(self, session: dict[str, Any]) -> None:
        self.session = session

    async def async_get(self, session_id: str) -> dict[str, Any] | None:
        assert session_id == self.session["id"]
        return self.session


@pytest.mark.asyncio
async def test_identical_learn_retry_returns_canonical_winner_after_question_advanced() -> None:
    answer = {
        "kind": "learning",
        "action": "known_already",
        "hint_used": False,
        "presentation_to_answer_ms": 1234,
    }
    canonical = {
        "id": "session-cas",
        "profile_id": "profile-1",
        "track_id": "track-1",
        "version": 2,
        "current_question": {"question_id": "q-2"},
        "answers": [
            {
                "question_id": "q-1",
                "answer": dict(answer),
                "resulting_version": 2,
            }
        ],
    }
    service = LearningSessionService(
        cast(Any, SimpleNamespace()),
        cast(Any, _CanonicalSessions(canonical)),
        cast(Any, SimpleNamespace()),
        cast(Any, SimpleNamespace(policy_version=1)),
        cast(Any, SimpleNamespace()),
        dataset_generation=lambda: "generation-test",
    )

    result = await service.async_answer("session-cas", 1, "q-1", answer)

    assert result is canonical
    assert result["version"] == 2


@pytest.mark.asyncio
async def test_conflicting_learn_retry_is_not_mistaken_for_canonical_winner() -> None:
    committed = {
        "kind": "learning",
        "action": "known_already",
        "hint_used": False,
    }
    conflicting = {
        "kind": "learning",
        "action": "introduce",
        "hint_used": False,
    }
    canonical = {
        "id": "session-cas",
        "profile_id": "profile-1",
        "track_id": "track-1",
        "version": 2,
        "current_question": {"question_id": "q-2"},
        "answers": [
            {
                "question_id": "q-1",
                "answer": committed,
                "resulting_version": 2,
            }
        ],
    }
    service = LearningSessionService(
        cast(Any, SimpleNamespace()),
        cast(Any, _CanonicalSessions(canonical)),
        cast(Any, SimpleNamespace()),
        cast(Any, SimpleNamespace(policy_version=1)),
        cast(Any, SimpleNamespace()),
        dataset_generation=lambda: "generation-test",
    )

    with pytest.raises(LearningSessionError, match="question is no longer current"):
        await service.async_answer("session-cas", 1, "q-1", conflicting)
