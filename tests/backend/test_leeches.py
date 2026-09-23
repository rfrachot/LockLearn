"""P3.11 leech detection, confusion matrix and annotation tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from custom_components.locklearn.core.difficulties import DifficultyService
from custom_components.locklearn.core.leeches import LeechPolicyV1
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.reviews import ReviewEventService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


@dataclass
class _FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def _snapshot(
    *,
    profile_id: str,
    track_id: str,
    card_key: str,
    learning_item_id: str,
    prompt_facet_id: str,
    answer_facet_id: str,
    verified_correct_count: int,
    verified_wrong_count: int,
) -> dict[str, object]:
    now = "2026-09-23T20:00:00+00:00"
    return {
        "profile_id": profile_id,
        "track_id": track_id,
        "card_key": card_key,
        "learning_item_id": learning_item_id,
        "prompt_facet_id": prompt_facet_id,
        "answer_facet_id": answer_facet_id,
        "state": "review",
        "mastery": 0.35,
        "box": 3,
        "seen_count": verified_correct_count + verified_wrong_count,
        "verified_correct_count": verified_correct_count,
        "verified_wrong_count": verified_wrong_count,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-08-01T20:00:00+00:00",
        "last_seen_at_utc": now,
        "last_result": "wrong" if verified_wrong_count else "correct",
        "next_due_at_utc": "2026-09-24T20:00:00+00:00",
        "streak_correct": 0,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": now,
        "verified_success_since_box": 0,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-p3-11",
        "normalization_version": 1,
        "updated_at_utc": now,
    }


async def _setup(
    tmp_path: Path,
) -> tuple[
    SQLiteStorage,
    ReviewEventService,
    DifficultyService,
    dict[str, str],
]:
    clock = _FixedClock(datetime(2026, 9, 23, 20, 0, tzinfo=UTC))
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()

    package = create_package(
        tmp_path / "p3-11.db",
        "p3-11",
        active_item_ids=(ITEM_A,),
    )
    candidate = storage.paths.content_staging_dir / "generation-p3-11.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p3-11",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "profile-p3-11",
    )
    await profiles.async_create_profile(
        name="P3.11",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )

    tracks = TrackService(
        storage.repositories.tracks,
        clock=clock,
        id_factory=lambda: "track-p3-11",
    )
    card_key = card_identity(ITEM_A)[1]
    await tracks.async_create_track(
        profile_id="profile-p3-11",
        name="P3.11 Track",
        pack_version_id="locklearn:pack-version:p3-11",
        source_language="en",
        target_language="fr",
        explicit_card_keys=(card_key,),
    )

    prompt_id, answer_id = facet_ids(ITEM_A)
    identity = {
        "profile_id": "profile-p3-11",
        "track_id": "track-p3-11",
        "learning_item_id": ITEM_A,
        "prompt_facet_id": prompt_id,
        "answer_facet_id": answer_id,
        "card_key": card_key,
    }
    event_ids = iter(f"event-p3-11-{index:02d}" for index in range(1, 20))
    reviews = ReviewEventService(
        storage.repositories.review_events,
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: next(event_ids),
    )
    difficulties = DifficultyService(
        storage.repositories.progress,
        storage.repositories.review_events,
        storage.repositories.user_annotations,
        reviews,
        clock=clock,
        id_factory=lambda: "annotation-p3-11",
    )
    return storage, reviews, difficulties, identity


def test_leech_policy_v1_uses_versioned_thresholds() -> None:
    now = datetime(2026, 9, 23, 20, 0, tzinfo=UTC)
    history = tuple(
        {
            "mode": "verified_mcq",
            "result": "wrong" if index < 5 else "correct",
            "retrieval_occurred": True,
            "signal_quality": "medium",
            "pre_state_snapshot": {"state": "review"},
            "created_at_utc": f"2026-09-{14 + index:02d}T20:00:00+00:00",
        }
        for index in range(9)
    )
    decision = LeechPolicyV1().evaluate(
        history,
        current={
            "mode": "verified_mcq",
            "result": "wrong",
            "retrieval_occurred": True,
            "signal_quality": "medium",
            "pre_state_snapshot": {"state": "review"},
            "created_at_utc": now.isoformat(),
        },
        now=now,
    )

    assert decision.detected is True
    assert decision.policy_version == 1
    assert decision.recent_verified_attempts == 10
    assert decision.recent_verified_failures == 6
    assert decision.reason == "recent_verified_failures"


async def test_leech_detection_confusions_mnemonic_and_reactivation(tmp_path: Path) -> None:
    storage, reviews, difficulties, identity = await _setup(tmp_path)
    try:
        correct = 0
        wrong = 0
        for index in range(10):
            result = "wrong" if index in {0, 1, 2, 3, 4, 9} else "correct"
            pre = _snapshot(
                **identity,
                verified_correct_count=correct,
                verified_wrong_count=wrong,
            )
            if result == "correct":
                correct += 1
            else:
                wrong += 1
            post = _snapshot(
                **identity,
                verified_correct_count=correct,
                verified_wrong_count=wrong,
            )
            event = await reviews.async_record(
                **identity,
                mode="verified_mcq",
                question_type="mcq",
                result=result,
                signal_quality="medium",
                policy_version=1,
                dataset_generation="generation-p3-11",
                normalization_version=1,
                pre_state_snapshot=pre,
                post_state_snapshot=post,
                retrieval_occurred=True,
                answer_id="chosen-wrong" if result == "wrong" else "expected-answer",
                expected_answer_id="expected-answer",
            )
            if index < 9:
                assert event.post_state_snapshot["state"] == "review"
            else:
                assert event.post_state_snapshot["state"] == "leech"
                assert event.post_state_snapshot["leech_policy_version"] == 1
                assert event.post_state_snapshot["leech_reason"] == "recent_verified_failures"

        progress = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert progress is not None
        assert progress["state"] == "leech"
        assert float(progress["leech_score"]) >= 1.0

        confusions = await difficulties.async_list_confusions(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert confusions == (
            {
                "card_key": identity["card_key"],
                "expected_answer_id": "expected-answer",
                "chosen_answer_id": "chosen-wrong",
                "count": 6,
            },
        )

        annotation = await difficulties.async_create_annotation(
            profile_id=identity["profile_id"],
            card_key=identity["card_key"],
            note="Mnemonic personnel",
        )
        assert annotation["note"] == "Mnemonic personnel"

        listed = await difficulties.async_list(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert len(listed) == 1
        assert listed[0]["recommended_remediation"] == "edit_personal_mnemonic"
        assert listed[0]["annotations"][0]["annotation_id"] == "annotation-p3-11"
        assert listed[0]["confusions"][0]["count"] == 6

        updated = await difficulties.async_update_annotation(
            profile_id=identity["profile_id"],
            annotation_id="annotation-p3-11",
            note="Mnemonic amélioré",
        )
        assert updated["note"] == "Mnemonic amélioré"

        reactivated = await difficulties.async_reactivate_leech(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert reactivated["state"] == "review"
        assert (
            await storage.repositories.progress.async_list_leeches(
                profile_id=identity["profile_id"],
                track_id=identity["track_id"],
            )
            == ()
        )

        events = await storage.repositories.review_events.async_list_for_card(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert events[-1]["mode"] == "leech_reactivation"
        assert events[-1]["retrieval_occurred"] is False

        await difficulties.async_delete_annotation(
            profile_id=identity["profile_id"],
            annotation_id="annotation-p3-11",
        )
        assert (
            await difficulties.async_list_annotations(profile_id=identity["profile_id"])
            == ()
        )
    finally:
        await storage.async_close()
