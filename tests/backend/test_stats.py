"""P3.13 statistics, calibration and streak tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.review_policy import ReviewPolicyV1
from custom_components.locklearn.core.reviews import ReviewEventService
from custom_components.locklearn.core.stats import StatsService
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
    seen: int,
    correct: int,
    wrong: int,
    due: str | None,
    self_known: int = 0,
) -> dict[str, object]:
    return {
        **identity,
        "state": "review",
        "mastery": 0.4,
        "box": 2,
        "seen_count": seen,
        "verified_correct_count": correct,
        "verified_wrong_count": wrong,
        "self_known_count": self_known,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-09-19T08:00:00+00:00",
        "last_seen_at_utc": "2026-09-21T08:00:00+00:00",
        "last_result": "correct" if correct >= wrong else "wrong",
        "next_due_at_utc": due,
        "streak_correct": correct,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": (
            "2026-09-21T08:00:00+00:00" if correct + wrong else None
        ),
        "verified_success_since_box": correct,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-p3-13",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-21T08:00:00+00:00",
    }


async def _setup(
    tmp_path: Path,
    *,
    now: datetime,
) -> tuple[SQLiteStorage, ReviewEventService, StatsService, _MutableClock, dict[str, str]]:
    clock = _MutableClock(now)
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()
    package = create_package(
        tmp_path / "p3-13.db",
        "p3-13",
        active_item_ids=(ITEM_A,),
    )
    candidate = storage.paths.content_staging_dir / "generation-p3-13.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p3-13",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "profile-p3-13",
    )
    await profiles.async_create_profile(
        name="P3.13",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )
    card_key = card_identity(ITEM_A)[1]
    tracks = TrackService(
        storage.repositories.tracks,
        clock=clock,
        id_factory=lambda: "track-p3-13",
    )
    await tracks.async_create_track(
        profile_id="profile-p3-13",
        name="P3.13 Track",
        pack_version_id="locklearn:pack-version:p3-13",
        source_language="en",
        target_language="fr",
        explicit_card_keys=(card_key,),
    )
    prompt_id, answer_id = facet_ids(ITEM_A)
    identity = {
        "profile_id": "profile-p3-13",
        "track_id": "track-p3-13",
        "learning_item_id": ITEM_A,
        "prompt_facet_id": prompt_id,
        "answer_facet_id": answer_id,
        "card_key": card_key,
    }
    ids = iter(f"event-p3-13-{index}" for index in range(1, 20))
    reviews = ReviewEventService(
        storage.repositories.review_events,
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: next(ids),
    )
    policy = ReviewPolicyV1(clock=clock)
    stats = StatsService(
        storage.repositories.profiles,
        storage.repositories.tracks,
        storage.repositories.progress,
        storage.repositories.review_events,
        review_policy=policy,
        clock=clock,
    )
    return storage, reviews, stats, clock, identity


async def _record(
    reviews: ReviewEventService,
    identity: dict[str, str],
    *,
    pre: dict[str, object],
    post: dict[str, object],
    mode: str,
    result: str,
    retrieval: bool,
    quality: str,
) -> None:
    await reviews.async_record(
        profile_id=identity["profile_id"],
        track_id=identity["track_id"],
        learning_item_id=identity["learning_item_id"],
        prompt_facet_id=identity["prompt_facet_id"],
        answer_facet_id=identity["answer_facet_id"],
        card_key=identity["card_key"],
        mode=mode,
        question_type="mcq",
        result=result,
        signal_quality=quality,
        policy_version=1,
        dataset_generation="generation-p3-13",
        normalization_version=1,
        pre_state_snapshot=pre,
        post_state_snapshot=post,
        retrieval_occurred=retrieval,
    )


async def test_daily_projection_and_metacognitive_calibration(tmp_path: Path) -> None:
    storage, reviews, stats, clock, identity = await _setup(
        tmp_path,
        now=datetime(2026, 9, 21, 8, 0, tzinfo=UTC),
    )
    try:
        pre = _snapshot(
            identity,
            seen=1,
            correct=0,
            wrong=0,
            due="2026-09-21T07:00:00+00:00",
        )
        self_known = _snapshot(
            identity,
            seen=2,
            correct=0,
            wrong=0,
            due="2026-09-21T07:00:00+00:00",
            self_known=1,
        )
        await _record(
            reviews,
            identity,
            pre=pre,
            post=self_known,
            mode="self_assessment_after_retrieval",
            result="known",
            retrieval=True,
            quality="weak",
        )

        clock.current = datetime(2026, 9, 22, 8, 0, tzinfo=UTC)
        failed = _snapshot(
            identity,
            seen=3,
            correct=0,
            wrong=1,
            due="2026-09-23T07:00:00+00:00",
            self_known=1,
        )
        await _record(
            reviews,
            identity,
            pre=self_known,
            post=failed,
            mode="verified_mcq",
            result="wrong",
            retrieval=True,
            quality="medium",
        )

        payload = await stats.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert payload["recent_verified_accuracy"] == {
            "correct": 0,
            "total": 1,
            "accuracy": 0.0,
            "window_limit": 30,
        }
        assert payload["latest_verified_retention"]["retained"] is False
        assert payload["calibration"]["declared_known_cards"] == 1
        assert payload["calibration"]["later_verified_cards"] == 1
        assert payload["calibration"]["later_verified_wrong"] == 1
        assert payload["calibration"]["later_verified_accuracy"] == 0.0
        assert len(payload["daily"]) == 2
        assert payload["daily"][0]["self_known"] == 1
        assert payload["daily"][0]["verified_retrievals"] == 0
        assert payload["daily"][1]["verified_wrong"] == 1
        assert all(row["timezone_name"] == "Europe/Paris" for row in payload["daily"])
    finally:
        await storage.async_close()


async def test_streak_uses_due_goal_neutral_day_and_one_grace_day(tmp_path: Path) -> None:
    storage, reviews, stats, clock, identity = await _setup(
        tmp_path,
        now=datetime(2026, 9, 21, 8, 0, tzinfo=UTC),
    )
    try:
        pre = _snapshot(
            identity,
            seen=1,
            correct=0,
            wrong=0,
            due="2026-09-21T00:00:00+00:00",
        )
        post = _snapshot(
            identity,
            seen=2,
            correct=1,
            wrong=0,
            due="2026-09-23T00:00:00+00:00",
        )
        await _record(
            reviews,
            identity,
            pre=pre,
            post=post,
            mode="verified_mcq",
            result="correct",
            retrieval=True,
            quality="medium",
        )

        clock.current = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
        payload = await stats.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert payload["due_today"] == 1
        assert payload["streak"]["days"] == 1
        assert payload["streak"]["grace_days"] == 1
        assert payload["streak"]["grace_days_used"] == 1
        assert payload["streak"]["today"]["status"] == "missed"
        assert payload["streak"]["today"]["due_opening"] == 1
        assert payload["streak"]["today"]["treated_due"] == 0
    finally:
        await storage.async_close()


async def test_historical_daily_timezone_is_not_rewritten_after_profile_change(
    tmp_path: Path,
) -> None:
    storage, reviews, stats, clock, identity = await _setup(
        tmp_path,
        now=datetime(2026, 9, 21, 21, 30, tzinfo=UTC),
    )
    try:
        pre = _snapshot(
            identity,
            seen=1,
            correct=0,
            wrong=0,
            due="2026-09-21T20:00:00+00:00",
        )
        first = _snapshot(
            identity,
            seen=2,
            correct=1,
            wrong=0,
            due="2026-09-22T20:00:00+00:00",
        )
        await _record(
            reviews,
            identity,
            pre=pre,
            post=first,
            mode="verified_mcq",
            result="correct",
            retrieval=True,
            quality="medium",
        )

        profiles = ProfileService(storage.repositories.profiles, clock=clock)
        await profiles.async_update_profile(
            profile_id=identity["profile_id"],
            timezone="Asia/Tokyo",
        )
        clock.current = datetime(2026, 9, 22, 0, 30, tzinfo=UTC)
        second = _snapshot(
            identity,
            seen=3,
            correct=2,
            wrong=0,
            due="2026-09-23T20:00:00+00:00",
        )
        await _record(
            reviews,
            identity,
            pre=first,
            post=second,
            mode="verified_mcq",
            result="correct",
            retrieval=True,
            quality="medium",
        )

        payload = await stats.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert [(row["local_date"], row["timezone_name"]) for row in payload["daily"]] == [
            ("2026-09-21", "Europe/Paris"),
            ("2026-09-22", "Asia/Tokyo"),
        ]
    finally:
        await storage.async_close()
