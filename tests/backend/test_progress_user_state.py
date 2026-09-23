"""P3.10 user-owned progress state and calibration tests."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.progress_state import (
    ProgressUserStateError,
    ProgressUserStateService,
)
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, ITEM_B, card_identity, create_package


@dataclass
class _MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


async def _setup(
    tmp_path: Path,
) -> tuple[SQLiteStorage, ProgressUserStateService, _MutableClock, str, str]:
    clock = _MutableClock(datetime(2026, 9, 23, 12, 0, tzinfo=UTC))
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db"),
        clock=clock,
    )
    await storage.async_open()
    package = create_package(
        tmp_path / "p3-10.db",
        "p3-10",
        active_item_ids=(ITEM_A, ITEM_B),
    )
    candidate = storage.paths.content_staging_dir / "generation-p3-10.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p3-10",
    )
    await storage.async_activate_content_generation(candidate)

    profiles = ProfileService(
        storage.repositories.profiles,
        clock=clock,
        id_factory=lambda: "profile-p3-10",
    )
    await profiles.async_create_profile(
        name="P3.10",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )
    tracks = TrackService(
        storage.repositories.tracks,
        clock=clock,
        id_factory=lambda: "track-p3-10",
    )
    await tracks.async_create_track(
        profile_id="profile-p3-10",
        name="P3.10 Track",
        pack_version_id="locklearn:pack-version:p3-10",
        source_language="en",
        target_language="fr",
        explicit_card_keys=(card_identity(ITEM_A)[1], card_identity(ITEM_B)[1]),
    )
    service = ProgressUserStateService(
        storage.repositories.tracks,
        storage.repositories.progress,
        dataset_generation=lambda: storage.content_generations.active_metadata.generation_id,
        clock=clock,
    )
    return storage, service, clock, "profile-p3-10", "track-p3-10"


async def test_known_already_materializes_no_fake_review_and_reactivates(tmp_path: Path) -> None:
    storage, service, _clock, profile_id, track_id = await _setup(tmp_path)
    card_key = card_identity(ITEM_A)[1]
    try:
        result = await service.async_set_user_state(
            actor_user_id="owner",
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
            user_state="known_already",
        )
        assert result["user_state"] == "known_already"
        assert result["effective_user_state"] == "known_already"
        assert result["state"] == "new"
        assert result["seen_count"] == 0
        assert result["verified_correct_count"] == 0
        assert result["verified_wrong_count"] == 0
        assert result["next_due_at_utc"] is None

        with sqlite3.connect(storage.paths.state_db) as connection:
            assert connection.execute("SELECT COUNT(*) FROM review_events").fetchone() == (0,)
            assert connection.execute(
                """SELECT event_type FROM audit_events
                   WHERE profile_id = ? ORDER BY id""",
                (profile_id,),
            ).fetchall() == [("progress_user_state",)]

        active = await service.async_set_user_state(
            actor_user_id="owner",
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
            user_state="active",
        )
        assert active["user_state"] == "active"
        assert active["seen_count"] == 0
    finally:
        await storage.async_close()


async def test_calibration_is_read_only_and_timed_burial_expires_logically(
    tmp_path: Path,
) -> None:
    storage, service, clock, profile_id, track_id = await _setup(tmp_path)
    card_a = card_identity(ITEM_A)[1]
    try:
        sample = await service.async_calibration_sample(
            profile_id=profile_id,
            track_id=track_id,
            sample_size=20,
        )
        assert sample.available_count == 2
        assert {card["card_key"] for card in sample.cards} == {
            card_identity(ITEM_A)[1],
            card_identity(ITEM_B)[1],
        }
        with sqlite3.connect(storage.paths.state_db) as connection:
            assert connection.execute("SELECT COUNT(*) FROM progress").fetchone() == (0,)

        await service.async_set_user_state(
            actor_user_id="owner",
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_a,
            user_state="buried",
            suspend_until_utc="2026-09-23T13:00:00+00:00",
        )
        hidden = await service.async_calibration_sample(
            profile_id=profile_id,
            track_id=track_id,
            sample_size=20,
        )
        assert [card["card_key"] for card in hidden.cards] == [card_identity(ITEM_B)[1]]

        clock.current = datetime(2026, 9, 23, 14, 0, tzinfo=UTC)
        visible = await service.async_calibration_sample(
            profile_id=profile_id,
            track_id=track_id,
            sample_size=20,
        )
        assert {card["card_key"] for card in visible.cards} == {
            card_identity(ITEM_A)[1],
            card_identity(ITEM_B)[1],
        }
        stored = await storage.repositories.progress.async_get(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_a,
        )
        assert stored is not None
        assert stored["user_state"] == "buried"
    finally:
        await storage.async_close()


async def test_user_state_validation(tmp_path: Path) -> None:
    storage, service, _clock, profile_id, track_id = await _setup(tmp_path)
    card_key = card_identity(ITEM_A)[1]
    try:
        with pytest.raises(ProgressUserStateError, match="requires"):
            await service.async_set_user_state(
                actor_user_id="owner",
                profile_id=profile_id,
                track_id=track_id,
                card_key=card_key,
                user_state="buried",
            )
        with pytest.raises(ProgressUserStateError, match="only"):
            await service.async_set_user_state(
                actor_user_id="owner",
                profile_id=profile_id,
                track_id=track_id,
                card_key=card_key,
                user_state="suspended",
                suspend_until_utc="2026-09-24T12:00:00+00:00",
            )
    finally:
        await storage.async_close()
