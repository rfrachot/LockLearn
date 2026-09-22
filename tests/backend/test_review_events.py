"""P3.1 ReviewEvent audit log and progress projection tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.reviews import ReviewEventService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 22, 21, 30, tzinfo=UTC)


def _snapshot(
    *,
    profile_id: str,
    track_id: str,
    card_key: str,
    learning_item_id: str,
    prompt_facet_id: str,
    answer_facet_id: str,
    state: str,
    seen_count: int,
    verified_correct_count: int,
    next_due_at_utc: str | None,
) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "track_id": track_id,
        "card_key": card_key,
        "learning_item_id": learning_item_id,
        "prompt_facet_id": prompt_facet_id,
        "answer_facet_id": answer_facet_id,
        "state": state,
        "mastery": 0.2 if state == "learning" else 0.0,
        "box": 1 if state == "learning" else 0,
        "seen_count": seen_count,
        "verified_correct_count": verified_correct_count,
        "verified_wrong_count": 0,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-09-22T21:30:00+00:00" if seen_count else None,
        "last_seen_at_utc": "2026-09-22T21:30:00+00:00" if seen_count else None,
        "last_result": "correct" if verified_correct_count else None,
        "next_due_at_utc": next_due_at_utc,
        "streak_correct": verified_correct_count,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": ("2026-09-22T21:30:00+00:00" if verified_correct_count else None),
        "verified_success_since_box": verified_correct_count,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-review",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-22T21:30:00+00:00",
    }


async def _setup(tmp_path: Path) -> tuple[SQLiteStorage, ReviewEventService, dict[str, Any]]:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()

    package = create_package(tmp_path / "review-package.db", "review", active_item_ids=(ITEM_A,))
    candidate = storage.paths.content_staging_dir / "generation-review.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-review",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=_FixedClock(),
        id_factory=lambda: "profile-review",
    )
    await profiles.async_create_profile(
        name="Reviewer",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )

    tracks = TrackService(
        storage.repositories.tracks,
        clock=_FixedClock(),
        id_factory=lambda: "track-review",
    )
    await tracks.async_create_track(
        profile_id="profile-review",
        name="Review Track",
        pack_version_id="locklearn:pack-version:review",
        source_language="en",
        target_language="en-US",
        explicit_card_keys=(card_identity(ITEM_A)[1],),
    )

    prompt_id, answer_id = facet_ids(ITEM_A)
    identity = {
        "profile_id": "profile-review",
        "track_id": "track-review",
        "learning_item_id": ITEM_A,
        "prompt_facet_id": prompt_id,
        "answer_facet_id": answer_id,
        "card_key": card_identity(ITEM_A)[1],
    }
    service = ReviewEventService(
        storage.repositories.review_events,
        storage.repositories.profiles,
        clock=_FixedClock(),
        id_factory=lambda: "event-review-1",
    )
    return storage, service, identity


async def test_event_append_materializes_progress_and_preserves_latency_semantics(
    tmp_path: Path,
) -> None:
    storage, service, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(
            **identity,
            state="new",
            seen_count=0,
            verified_correct_count=0,
            next_due_at_utc=None,
        )
        post = _snapshot(
            **identity,
            state="learning",
            seen_count=1,
            verified_correct_count=1,
            next_due_at_utc="2026-09-23T21:30:00+00:00",
        )
        event = await service.async_record(
            **identity,
            mode="verified_mcq",
            question_type="mcq",
            result="correct",
            signal_quality="verified",
            policy_version=1,
            dataset_generation="generation-review",
            normalization_version=1,
            pre_state_snapshot=pre,
            post_state_snapshot=post,
            retrieval_occurred=True,
            presentation_to_answer_ms=None,
            delivery_to_action_ms=48_000,
        )

        assert event.local_date == "2026-09-22"
        assert event.timezone_name == "Europe/Paris"
        assert event.utc_offset_minutes == 120
        assert event.presentation_to_answer_ms is None
        assert event.delivery_to_action_ms == 48_000

        progress = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert progress is not None
        assert progress["state"] == "learning"
        assert progress["verified_correct_count"] == 1

        events = await storage.repositories.review_events.async_list_for_card(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert len(events) == 1
        assert events[0]["presentation_to_answer_ms"] is None
        assert events[0]["delivery_to_action_ms"] == 48_000
        assert events[0]["normalization_version"] == 1
        assert events[0]["post_state_snapshot"]["state"] == "learning"
    finally:
        await storage.async_close()


async def test_progress_rebuild_uses_latest_event_snapshot(tmp_path: Path) -> None:
    storage, service, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(
            **identity,
            state="new",
            seen_count=0,
            verified_correct_count=0,
            next_due_at_utc=None,
        )
        first = _snapshot(
            **identity,
            state="learning",
            seen_count=1,
            verified_correct_count=1,
            next_due_at_utc="2026-09-23T21:30:00+00:00",
        )
        await service.async_record(
            **identity,
            mode="verified_mcq",
            question_type="mcq",
            result="correct",
            signal_quality="verified",
            policy_version=1,
            dataset_generation="generation-review",
            normalization_version=1,
            pre_state_snapshot=pre,
            post_state_snapshot=first,
            retrieval_occurred=True,
        )

        second_service = ReviewEventService(
            storage.repositories.review_events,
            storage.repositories.profiles,
            clock=_FixedClock(),
            id_factory=lambda: "event-review-2",
        )
        second = dict(first)
        second.update(
            {
                "state": "review",
                "box": 2,
                "seen_count": 2,
                "verified_correct_count": 2,
                "streak_correct": 2,
                "verified_success_since_box": 2,
                "next_due_at_utc": "2026-09-25T21:30:00+00:00",
            }
        )
        await second_service.async_record(
            **identity,
            mode="verified_free_text",
            question_type="free_text",
            result="correct",
            signal_quality="verified",
            policy_version=1,
            dataset_generation="generation-review",
            normalization_version=1,
            pre_state_snapshot=first,
            post_state_snapshot=second,
            retrieval_occurred=True,
            presentation_to_answer_ms=1_200,
        )

        def corrupt(connection: sqlite3.Connection) -> None:
            connection.execute(
                """UPDATE progress
                   SET state = 'new', box = 0, seen_count = 0,
                       verified_correct_count = 0
                   WHERE profile_id = ? AND track_id = ? AND card_key = ?""",
                (
                    identity["profile_id"],
                    identity["track_id"],
                    identity["card_key"],
                ),
            )
            connection.commit()

        await storage._async_writer(corrupt)
        rebuilt = await service.async_rebuild_progress(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert rebuilt == 1

        progress = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert progress is not None
        assert progress["state"] == "review"
        assert progress["box"] == 2
        assert progress["seen_count"] == 2
        assert progress["verified_correct_count"] == 2
    finally:
        await storage.async_close()
