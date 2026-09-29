"""P3.12 undo, integrity rebuild and algorithmic recompute tests."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from custom_components.locklearn.core.integrity import IntegrityService
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.progress_state import ProgressUserStateService
from custom_components.locklearn.core.reviews import ReviewEventService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


@dataclass
class _MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def _snapshot(
    identity: dict[str, str],
    *,
    state: str = "review",
    box: int = 1,
    seen_count: int = 1,
    verified_correct_count: int = 0,
    verified_wrong_count: int = 0,
    due: str | None = "2026-09-24T20:00:00+00:00",
) -> dict[str, object]:
    return {
        **identity,
        "state": state,
        "mastery": 0.3,
        "box": box,
        "seen_count": seen_count,
        "verified_correct_count": verified_correct_count,
        "verified_wrong_count": verified_wrong_count,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-09-20T20:00:00+00:00",
        "last_seen_at_utc": "2026-09-23T20:00:00+00:00",
        "last_result": "correct" if verified_correct_count else "wrong",
        "next_due_at_utc": due,
        "streak_correct": 0,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": "2026-09-23T20:00:00+00:00",
        "verified_success_since_box": 0,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-p3-12",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-23T20:00:00+00:00",
    }


async def _setup(
    tmp_path: Path,
) -> tuple[
    SQLiteStorage,
    ReviewEventService,
    IntegrityService,
    _MutableClock,
    dict[str, str],
]:
    clock = _MutableClock(datetime(2026, 9, 23, 20, 0, tzinfo=UTC))
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()
    package = create_package(
        tmp_path / "p3-12.db",
        "p3-12",
        active_item_ids=(ITEM_A,),
    )
    candidate = storage.paths.content_staging_dir / "generation-p3-12.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p3-12",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "profile-p3-12",
    )
    await profiles.async_create_profile(
        name="P3.12",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )
    card_key = card_identity(ITEM_A)[1]
    tracks = TrackService(
        storage.repositories.tracks,
        clock=clock,
        id_factory=lambda: "track-p3-12",
    )
    await tracks.async_create_track(
        profile_id="profile-p3-12",
        name="P3.12 Track",
        pack_version_id="locklearn:pack-version:p3-12",
        source_language="en",
        target_language="fr",
        explicit_card_keys=(card_key,),
    )
    prompt_id, answer_id = facet_ids(ITEM_A)
    identity = {
        "profile_id": "profile-p3-12",
        "track_id": "track-p3-12",
        "learning_item_id": ITEM_A,
        "prompt_facet_id": prompt_id,
        "answer_facet_id": answer_id,
        "card_key": card_key,
    }
    event_ids = iter(f"event-p3-12-{index}" for index in range(1, 20))
    review_service = ReviewEventService(
        storage.repositories.review_events,
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: next(event_ids),
    )
    undo_ids = iter(f"undo-p3-12-{index}" for index in range(1, 10))
    integrity = IntegrityService(
        storage.repositories.review_events,
        storage.repositories.progress,
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: next(undo_ids),
    )
    return storage, review_service, integrity, clock, identity


async def _record(
    service: ReviewEventService,
    identity: dict[str, str],
    *,
    pre: dict[str, object],
    post: dict[str, object],
    mode: str = "verified_mcq",
    result: str = "correct",
) -> None:
    await service.async_record(
        profile_id=identity["profile_id"],
        track_id=identity["track_id"],
        learning_item_id=identity["learning_item_id"],
        prompt_facet_id=identity["prompt_facet_id"],
        answer_facet_id=identity["answer_facet_id"],
        card_key=identity["card_key"],
        mode=mode,
        question_type="mcq",
        result=result,
        signal_quality="medium" if mode == "verified_mcq" else "none",
        policy_version=1,
        dataset_generation="generation-p3-12",
        normalization_version=1,
        pre_state_snapshot=pre,
        post_state_snapshot=post,
        retrieval_occurred=mode == "verified_mcq",
    )


async def test_undo_uses_compensating_snapshots_and_can_walk_back_twice(tmp_path: Path) -> None:
    storage, reviews, integrity, clock, identity = await _setup(tmp_path)
    try:
        base = _snapshot(identity, box=1, seen_count=1)
        first = _snapshot(
            identity,
            box=2,
            seen_count=2,
            verified_correct_count=1,
            due="2026-09-26T20:00:00+00:00",
        )
        await _record(reviews, identity, pre=base, post=first)
        clock.current = datetime(2026, 9, 23, 20, 1, tzinfo=UTC)
        second = _snapshot(
            identity,
            box=1,
            seen_count=3,
            verified_correct_count=1,
            verified_wrong_count=1,
            due="2026-09-23T20:11:00+00:00",
        )
        await _record(reviews, identity, pre=first, post=second, result="wrong")

        clock.current = datetime(2026, 9, 23, 20, 2, tzinfo=UTC)
        undo_second = await integrity.async_undo_last(
            actor_user_id="owner",
            profile_id=identity["profile_id"],
        )
        assert undo_second["progress"]["box"] == 2
        assert undo_second["progress"]["seen_count"] == 2
        assert undo_second["progress"]["verified_wrong_count"] == 0

        clock.current = datetime(2026, 9, 23, 20, 3, tzinfo=UTC)
        undo_first = await integrity.async_undo_last(
            actor_user_id="owner",
            profile_id=identity["profile_id"],
        )
        assert undo_first["progress"]["box"] == 1
        assert undo_first["progress"]["seen_count"] == 1
        assert undo_first["progress"]["verified_correct_count"] == 0

        with sqlite3.connect(storage.paths.state_db) as connection:
            assert connection.execute(
                "SELECT COUNT(*) FROM audit_events WHERE event_type = 'progress_undo'"
            ).fetchone() == (2,)
            assert connection.execute(
                "SELECT COUNT(*) FROM review_events WHERE mode = 'undo_compensation'"
            ).fetchone() == (2,)
    finally:
        await storage.async_close()


async def test_snapshot_rebuild_repairs_srs_and_preserves_user_overlay(tmp_path: Path) -> None:
    storage, reviews, integrity, _clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, box=1)
        post = _snapshot(
            identity,
            box=3,
            seen_count=4,
            verified_correct_count=3,
            due="2026-10-01T20:00:00+00:00",
        )
        await _record(reviews, identity, pre=pre, post=post)

        def mutate(connection: sqlite3.Connection) -> None:
            connection.execute(
                """UPDATE progress
                   SET state = 'new', box = 0, seen_count = 99,
                       user_state = 'suspended', next_due_at_utc = NULL
                   WHERE profile_id = ? AND track_id = ? AND card_key = ?""",
                (
                    identity["profile_id"],
                    identity["track_id"],
                    identity["card_key"],
                ),
            )
            connection.commit()

        await storage._async_writer(mutate)
        result = await integrity.async_rebuild_progress(profile_id=identity["profile_id"])
        assert result == {"rebuilt_cards": 1}

        rebuilt = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert rebuilt is not None
        assert rebuilt["state"] == "review"
        assert rebuilt["box"] == 3
        assert rebuilt["seen_count"] == 4
        assert rebuilt["user_state"] == "suspended"
        assert rebuilt["next_due_at_utc"] == "2026-10-01T20:00:00+00:00"
    finally:
        await storage.async_close()


async def test_recompute_v1_reports_divergence_and_applies_supported_history(
    tmp_path: Path,
) -> None:
    storage, reviews, integrity, _clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, box=1, verified_correct_count=0)
        intentionally_wrong_historical = _snapshot(
            identity,
            box=1,
            seen_count=2,
            verified_correct_count=1,
            due="2026-09-24T20:00:00+00:00",
        )
        await _record(
            reviews,
            identity,
            pre=pre,
            post=intentionally_wrong_historical,
        )

        report = await integrity.async_recompute_progress(
            target_policy_version=1,
            profile_id=identity["profile_id"],
        )
        assert report.applied is True
        assert report.fallback_event_count == 0
        assert report.divergence_count == 1
        assert "box" in report.divergences[0]["changed_fields"]

        recomputed = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert recomputed is not None
        assert recomputed["box"] == 2
        assert recomputed["verified_correct_count"] == 1
    finally:
        await storage.async_close()


async def test_recompute_with_unsupported_event_reports_fallback_without_applying(
    tmp_path: Path,
) -> None:
    storage, reviews, integrity, _clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, box=1)
        post = _snapshot(identity, box=4, seen_count=8, verified_correct_count=6)
        await _record(
            reviews,
            identity,
            pre=pre,
            post=post,
            mode="legacy_custom",
            result="custom",
        )

        report = await integrity.async_recompute_progress(
            target_policy_version=1,
            profile_id=identity["profile_id"],
        )
        assert report.applied is False
        assert report.fallback_event_count == 1
        assert report.fallback_events[0]["mode"] == "legacy_custom"

        unchanged = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert unchanged is not None
        assert unchanged["box"] == 4
    finally:
        await storage.async_close()


async def test_stats_rebuild_is_independent_projection(tmp_path: Path) -> None:
    storage, reviews, integrity, clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, box=1)
        first = _snapshot(
            identity,
            box=2,
            seen_count=2,
            verified_correct_count=1,
        )
        await _record(reviews, identity, pre=pre, post=first)
        clock.current = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
        second = _snapshot(
            identity,
            box=1,
            seen_count=3,
            verified_correct_count=1,
            verified_wrong_count=1,
        )
        await _record(reviews, identity, pre=first, post=second, result="wrong")

        result = await integrity.async_rebuild_stats(profile_id=identity["profile_id"])
        assert result == {"rebuilt_days": 2}

        with sqlite3.connect(storage.paths.state_db) as connection:
            rows = connection.execute(
                """SELECT local_date, verified_retrievals, verified_correct, verified_wrong
                   FROM stats_daily ORDER BY local_date"""
            ).fetchall()
        assert rows == [
            ("2026-09-23", 1, 1, 0),
            ("2026-09-24", 1, 0, 1),
        ]
    finally:
        await storage.async_close()


async def test_snapshot_rebuild_preserves_overlay_only_progress_row(tmp_path: Path) -> None:
    storage, _reviews, integrity, _clock, identity = await _setup(tmp_path)
    try:
        progress_state = ProgressUserStateService(
            storage.repositories.tracks,
            storage.repositories.progress,
            dataset_generation=lambda: storage.content_generations.active_metadata.generation_id,
        )
        await progress_state.async_set_user_state(
            actor_user_id="owner",
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
            user_state="known_already",
        )

        result = await integrity.async_rebuild_progress(profile_id=identity["profile_id"])
        assert result == {"rebuilt_cards": 1}
        preserved = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert preserved is not None
        assert preserved["state"] == "new"
        assert preserved["user_state"] == "known_already"
        assert preserved["seen_count"] == 0
    finally:
        await storage.async_close()


async def test_stats_rebuild_excludes_undone_response(tmp_path: Path) -> None:
    storage, reviews, integrity, clock, identity = await _setup(tmp_path)
    try:
        pre = _snapshot(identity, box=1)
        first = _snapshot(
            identity,
            box=2,
            seen_count=2,
            verified_correct_count=1,
        )
        await _record(reviews, identity, pre=pre, post=first)
        clock.current = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
        second = _snapshot(
            identity,
            box=1,
            seen_count=3,
            verified_correct_count=1,
            verified_wrong_count=1,
        )
        await _record(reviews, identity, pre=first, post=second, result="wrong")
        clock.current = datetime(2026, 9, 24, 20, 1, tzinfo=UTC)
        await integrity.async_undo_last(
            actor_user_id="owner",
            profile_id=identity["profile_id"],
        )

        result = await integrity.async_rebuild_stats(profile_id=identity["profile_id"])
        assert result == {"rebuilt_days": 1}
        with sqlite3.connect(storage.paths.state_db) as connection:
            rows = connection.execute(
                """SELECT local_date, verified_retrievals, verified_correct, verified_wrong
                   FROM stats_daily ORDER BY local_date"""
            ).fetchall()
        assert rows == [("2026-09-23", 1, 1, 0)]
    finally:
        await storage.async_close()
