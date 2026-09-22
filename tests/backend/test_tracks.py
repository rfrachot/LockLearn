"""P2.4 Track configuration, pack pinning, and card-rule tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.locklearn.core.tracks import TrackService, TrackValidationError
from custom_components.locklearn.storage import ProfileRecord, SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, ITEM_B, card_identity, create_package

ITEM_C = "locklearn:item:c"


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 22, 21, 0, tzinfo=UTC)


def _directional_package(
    path: Path,
    version: str,
    *,
    active_item_ids: tuple[str, ...],
) -> Path:
    package = create_package(path, version, active_item_ids=active_item_ids)
    with sqlite3.connect(package) as connection:
        connection.execute("UPDATE facets SET language_tag = 'en' WHERE facet_key = 'prompt'")
        connection.execute("UPDATE facets SET language_tag = 'fr' WHERE facet_key = 'answer'")
        connection.commit()
    return package


async def _storage_with_v1(tmp_path: Path) -> SQLiteStorage:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    package = _directional_package(
        tmp_path / "package-v1.db",
        "v1",
        active_item_ids=(ITEM_A, ITEM_B),
    )
    candidate = storage.paths.content_staging_dir / "generation-v1.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-track-v1",
    )
    await storage.async_activate_content_generation(candidate)
    now = "2026-09-22T21:00:00+00:00"
    await storage.repositories.profiles.async_insert(
        ProfileRecord(
            profile_id="profile-1",
            name="Learner",
            preset="standard",
            timezone="Europe/Paris",
            created_at_utc=now,
            updated_at_utc=now,
        )
    )
    return storage


async def _activate_v2(storage: SQLiteStorage, tmp_path: Path) -> None:
    package = _directional_package(
        tmp_path / "package-v2.db",
        "v2",
        active_item_ids=(ITEM_A, ITEM_B, ITEM_C),
    )
    candidate = storage.paths.content_staging_dir / "generation-v2.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-track-v2",
    )
    await storage.async_activate_content_generation(candidate)


async def test_direction_configuration_resolves_to_exact_card_rules(tmp_path: Path) -> None:
    storage = await _storage_with_v1(tmp_path)
    service = TrackService(
        storage.repositories.tracks,
        clock=_FixedClock(),
        id_factory=lambda: "track-direction",
    )
    try:
        track = await service.async_create_track(
            profile_id="profile-1",
            name="French recognition",
            pack_version_id="locklearn:pack-version:v1",
            source_language="en",
            target_language="fr",
            content_weights={"vocabulary": 50},
        )

        assert track["track_id"] == "track-direction"
        assert track["pack_version_id"] == "locklearn:pack-version:v1"
        assert track["dataset_generation"] == "generation-track-v1"
        assert track["settings"]["card_selection_mode"] == "direction"

        rules = await storage.repositories.tracks.async_get_card_rules("track-direction")
        assert len(rules) == 2
        assert {rule["rule_kind"] for rule in rules} == {"direction_card"}
        assert {rule["card_key"] for rule in rules} == {
            card_identity(ITEM_A)[1],
            card_identity(ITEM_B)[1],
        }
        assert await storage.repositories.tracks.async_get_content_weights("track-direction") == {
            "vocabulary": 50.0
        }
    finally:
        await storage.async_close()


async def test_explicit_card_selection_is_limited_to_pinned_pack(tmp_path: Path) -> None:
    storage = await _storage_with_v1(tmp_path)
    service = TrackService(
        storage.repositories.tracks,
        clock=_FixedClock(),
        id_factory=lambda: "track-explicit",
    )
    try:
        selected = card_identity(ITEM_A)[1]
        track = await service.async_create_track(
            profile_id="profile-1",
            name="Focused",
            pack_version_id="locklearn:pack-version:v1",
            source_language="en",
            target_language="fr",
            explicit_card_keys=(selected,),
        )
        assert track["settings"]["card_selection_mode"] == "explicit"
        rules = await storage.repositories.tracks.async_get_card_rules("track-explicit")
        assert tuple(rule["card_key"] for rule in rules) == (selected,)

        with pytest.raises(TrackValidationError, match="not active in pinned pack"):
            await TrackService(
                storage.repositories.tracks,
                clock=_FixedClock(),
                id_factory=lambda: "track-invalid",
            ).async_create_track(
                profile_id="profile-1",
                name="Invalid",
                pack_version_id="locklearn:pack-version:v1",
                source_language="en",
                target_language="fr",
                explicit_card_keys=("locklearn:card-key:missing",),
            )
    finally:
        await storage.async_close()


async def test_pack_update_is_previewed_and_never_silently_integrated(tmp_path: Path) -> None:
    storage = await _storage_with_v1(tmp_path)
    service = TrackService(
        storage.repositories.tracks,
        clock=_FixedClock(),
        id_factory=lambda: "track-update",
    )
    try:
        await service.async_create_track(
            profile_id="profile-1",
            name="Update test",
            pack_version_id="locklearn:pack-version:v1",
            source_language="en",
            target_language="fr",
        )
        await _activate_v2(storage, tmp_path)

        before = await storage.repositories.tracks.async_get("track-update")
        assert before is not None
        assert before["pack_version_id"] == "locklearn:pack-version:v1"

        diff = await service.async_preview_pack_update(
            track_id="track-update",
            target_pack_version_id="locklearn:pack-version:v2",
        )
        assert diff.added_learning_item_ids == (ITEM_C,)

        still_pinned = await storage.repositories.tracks.async_get("track-update")
        assert still_pinned is not None
        assert still_pinned["pack_version_id"] == "locklearn:pack-version:v1"

        integrated = await service.async_integrate_pack_update(
            track_id="track-update",
            target_pack_version_id="locklearn:pack-version:v2",
        )
        assert integrated == diff
        after = await storage.repositories.tracks.async_get("track-update")
        assert after is not None
        assert after["pack_version_id"] == "locklearn:pack-version:v2"
        assert after["dataset_generation"] == "generation-track-v2"
        assert len(await storage.repositories.tracks.async_get_card_rules("track-update")) == 3
    finally:
        await storage.async_close()


async def test_content_weights_are_relative_non_negative_targets(tmp_path: Path) -> None:
    storage = await _storage_with_v1(tmp_path)
    service = TrackService(
        storage.repositories.tracks,
        clock=_FixedClock(),
        id_factory=lambda: "track-weights",
    )
    try:
        await service.async_create_track(
            profile_id="profile-1",
            name="Weights",
            pack_version_id="locklearn:pack-version:v1",
            source_language="en",
            target_language="fr",
        )
        await service.async_set_content_weights(
            track_id="track-weights",
            weights={"vocabulary": 50, "grammar": 20, "kanji": 30},
        )
        assert await storage.repositories.tracks.async_get_content_weights("track-weights") == {
            "grammar": 20.0,
            "kanji": 30.0,
            "vocabulary": 50.0,
        }

        with pytest.raises(TrackValidationError, match="non-negative"):
            await service.async_set_content_weights(
                track_id="track-weights",
                weights={"vocabulary": -1},
            )
    finally:
        await storage.async_close()
