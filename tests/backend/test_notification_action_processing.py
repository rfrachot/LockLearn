"""P4.8 notification action -> canonical ReviewEvent integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from custom_components.locklearn.core.acl import ProfileACLService
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.review_policy import ReviewPolicyV1
from custom_components.locklearn.core.reviews import ReviewEventService
from custom_components.locklearn.core.scheduler import SchedulerService
from custom_components.locklearn.core.signals import SignalPolicy
from custom_components.locklearn.core.stats import StatsService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.notifications.actions import NotificationActionProcessor
from custom_components.locklearn.notifications.interactions import (
    NotificationActionDisposition,
    NotificationInteractionService,
)
from custom_components.locklearn.notifications.renderers import encode_action_id
from custom_components.locklearn.storage import (
    NotificationTargetRecord,
    SQLiteStorage,
    StoragePaths,
)
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


@dataclass
class FixedClock:
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
    state: str = "review",
    box: int = 2,
    seen_count: int = 4,
    verified_correct_count: int = 2,
    verified_wrong_count: int = 1,
) -> dict[str, Any]:
    return {
        "profile_id": profile_id,
        "track_id": track_id,
        "card_key": card_key,
        "learning_item_id": learning_item_id,
        "prompt_facet_id": prompt_facet_id,
        "answer_facet_id": answer_facet_id,
        "state": state,
        "mastery": 0.4,
        "box": box,
        "seen_count": seen_count,
        "verified_correct_count": verified_correct_count,
        "verified_wrong_count": verified_wrong_count,
        "self_known_count": 0,
        "self_review_count": 0,
        "first_seen_at_utc": "2026-09-01T20:00:00+00:00",
        "last_seen_at_utc": "2026-09-23T20:00:00+00:00",
        "last_result": "correct",
        "next_due_at_utc": "2026-09-24T18:00:00+00:00",
        "streak_correct": 1,
        "leech_score": 0.0,
        "difficulty_factor": 1.0,
        "last_verified_at_utc": "2026-09-23T20:00:00+00:00",
        "verified_success_since_box": 0,
        "user_state": "active",
        "suspend_until_utc": None,
        "example_rotation_index": 0,
        "content_status": "active",
        "policy_version": 1,
        "dataset_generation": "generation-p48",
        "normalization_version": 1,
        "updated_at_utc": "2026-09-23T20:00:00+00:00",
    }


async def _setup(
    tmp_path: Path,
    *,
    shared_device: bool = False,
    seed_progress: bool = True,
) -> tuple[
    SQLiteStorage,
    NotificationActionProcessor,
    NotificationInteractionService,
    dict[str, str],
    list[tuple[str, dict[str, Any]]],
]:
    clock = FixedClock(datetime(2026, 9, 24, 20, 0, tzinfo=UTC))
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()
    package = create_package(
        tmp_path / "p48-package.db",
        "p48",
        active_item_ids=(ITEM_A,),
    )
    candidate = storage.paths.content_staging_dir / "generation-p48.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p48",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "profile-p48",
    )
    await profiles.async_create_profile(
        name="P4.8",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner-user",),
    )
    tracks = TrackService(
        storage.repositories.tracks,
        clock=clock,
        id_factory=lambda: "track-p48",
    )
    card_key = card_identity(ITEM_A)[1]
    await tracks.async_create_track(
        profile_id="profile-p48",
        name="P4.8 Track",
        pack_version_id="locklearn:pack-version:p48",
        source_language="en",
        target_language="en-US",
        explicit_card_keys=(card_key,),
    )
    await storage.repositories.notification_targets.async_insert(
        NotificationTargetRecord(
            target_id="target-p48",
            profile_id="profile-p48",
            device_registry_id="device-p48",
            platform="android",
            friendly_name="P4.8 phone",
            shared_device=shared_device,
            created_at_utc=clock.now().isoformat(),
            updated_at_utc=clock.now().isoformat(),
        )
    )

    prompt_id, answer_id = facet_ids(ITEM_A)
    identity = {
        "profile_id": "profile-p48",
        "track_id": "track-p48",
        "card_key": card_key,
        "learning_item_id": ITEM_A,
        "prompt_facet_id": prompt_id,
        "answer_facet_id": answer_id,
    }
    if seed_progress:
        seed = ReviewEventService(
            storage.repositories.review_events,
            storage.repositories.profiles,
            clock=FixedClock(datetime(2026, 9, 23, 20, 0, tzinfo=UTC)),
            id_factory=lambda: "event-seed",
        )
        snapshot = _snapshot(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
            learning_item_id=identity["learning_item_id"],
            prompt_facet_id=identity["prompt_facet_id"],
            answer_facet_id=identity["answer_facet_id"],
        )
        await seed.async_record(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            learning_item_id=identity["learning_item_id"],
            prompt_facet_id=identity["prompt_facet_id"],
            answer_facet_id=identity["answer_facet_id"],
            card_key=identity["card_key"],
            mode="verified_mcq",
            question_type="mcq",
            result="correct",
            signal_quality="medium",
            policy_version=1,
            dataset_generation="generation-p48",
            normalization_version=1,
            pre_state_snapshot=snapshot,
            post_state_snapshot=snapshot,
            retrieval_occurred=True,
        )

    review_policy = ReviewPolicyV1(clock=clock)
    reviews = ReviewEventService(
        storage.repositories.review_events,
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "event-action",
    )
    stats = StatsService(
        storage.repositories.profiles,
        storage.repositories.tracks,
        storage.repositories.progress,
        storage.repositories.review_events,
        review_policy=review_policy,
        clock=clock,
    )
    scheduler = SchedulerService(
        storage.repositories.profiles,
        storage.repositories.tracks,
        storage.repositories.notification_targets,
        storage.repositories.scheduler,
        storage.repositories.settings,
        clock=clock,
    )
    interactions = NotificationInteractionService(
        storage.repositories.notification_interactions,
        ProfileACLService(storage.repositories.profiles),
        clock=clock,
        id_factory=lambda: "interaction-p48",
        token_factory=lambda: "token-p48",
    )
    emitted: list[tuple[str, dict[str, Any]]] = []
    processor = NotificationActionProcessor(
        interactions,
        storage.repositories.profiles,
        storage.repositories.tracks,
        storage.repositories.progress,
        storage.repositories.notification_targets,
        scheduler,
        reviews,
        storage.repositories.review_events,
        SignalPolicy(review_policy),
        review_policy,
        stats,
        dataset_generation=lambda: storage.content_generations.active_metadata.generation_id,
        event_emitter=lambda name, data: emitted.append((name, dict(data))),
        clock=clock,
    )
    return storage, processor, interactions, identity, emitted


async def test_duplicate_quiz_interaction_applies_and_emits_exactly_once(
    tmp_path: Path,
) -> None:
    storage, processor, interactions, identity, emitted = await _setup(tmp_path)
    try:
        interaction = await interactions.async_create(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            target_id="target-p48",
            card_key=identity["card_key"],
            stage="prompt",
            expires_at=datetime(2026, 9, 24, 20, 30, tzinfo=UTC),
            payload={
                "kind": "quiz",
                "option_ids": ["answer-correct", "answer-wrong"],
                "expected_answer_id": "answer-correct",
            },
        )
        action = encode_action_id(interaction.token, "choice_0")

        first = await processor.async_handle_mobile_action(
            action_id=action,
            actor_user_id="owner-user",
        )
        second = await processor.async_handle_mobile_action(
            action_id=action,
            actor_user_id="owner-user",
        )

        assert first is not None
        assert first.disposition is NotificationActionDisposition.CONSUMED
        assert first.pedagogical_applied is True
        assert first.review_event_id == "event-action"
        assert second is not None
        assert second.disposition is NotificationActionDisposition.REPLAYED
        assert second.pedagogical_applied is False

        events = await storage.repositories.review_events.async_list_scope_events(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert [event["id"] for event in events] == ["event-seed", "event-action"]

        names = [name for name, _data in emitted]
        assert names.count("locklearn_answered") == 1
        assert names.count("locklearn_quiz_correct") == 1
        answered = next(data for name, data in emitted if name == "locklearn_answered")
        assert answered["event_id"] == "event-action"
        assert answered["interaction_id"] == "interaction-p48"
        assert answered["result"] == "correct"
        assert "prompt" not in answered
        assert "answer" not in answered
        assert "user_response" not in answered
    finally:
        await storage.async_close()


async def test_untrusted_shared_device_quiz_cannot_cross_verified_gate(
    tmp_path: Path,
) -> None:
    storage, processor, interactions, identity, _emitted = await _setup(
        tmp_path,
        shared_device=True,
    )
    try:
        interaction = await interactions.async_create(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            target_id="target-p48",
            card_key=identity["card_key"],
            stage="prompt",
            expires_at=datetime(2026, 9, 24, 20, 30, tzinfo=UTC),
            payload={
                "kind": "quiz",
                "option_ids": ["answer-correct", "answer-wrong"],
                "expected_answer_id": "answer-correct",
            },
        )
        result = await processor.async_handle_mobile_action(
            action_id=encode_action_id(interaction.token, "choice_0"),
            actor_user_id="owner-user",
        )
        assert result is not None
        assert result.pedagogical_applied is True

        progress = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert progress is not None
        assert progress["box"] == 2

        events = await storage.repositories.review_events.async_list_scope_events(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert events[-1]["signal_quality"] == "reduced"
    finally:
        await storage.async_close()


async def test_new_teaser_idk_is_introduction_not_failure(tmp_path: Path) -> None:
    storage, processor, interactions, identity, emitted = await _setup(
        tmp_path,
        seed_progress=False,
    )
    try:
        interaction = await interactions.async_create(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            target_id="target-p48",
            card_key=identity["card_key"],
            stage="prompt",
            expires_at=datetime(2026, 9, 24, 20, 30, tzinfo=UTC),
            payload={
                "kind": "learning",
                "selection_reason": "teaser_new",
            },
        )
        result = await processor.async_handle_mobile_action(
            action_id=encode_action_id(interaction.token, "idk"),
            actor_user_id="owner-user",
        )
        assert result is not None
        assert result.pedagogical_applied is True

        progress = await storage.repositories.progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        assert progress is not None
        assert progress["state"] == "learning"
        assert progress["last_result"] == "exposure"
        assert progress["verified_wrong_count"] == 0

        events = await storage.repositories.review_events.async_list_scope_events(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        assert len(events) == 1
        assert events[0]["mode"] == "introduction"
        assert events[0]["retrieval_occurred"] is False
        assert all(name != "locklearn_answered" for name, _data in emitted)
    finally:
        await storage.async_close()
