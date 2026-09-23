"""P2.1 persistent state schema, migration, repositories, and content references."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from custom_components.locklearn.const import DB_SCHEMA_VERSION
from custom_components.locklearn.storage import (
    CardReference,
    ContentReferenceError,
    ProfileRecord,
    SQLiteStorage,
    StoragePaths,
    TrackRecord,
)
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids

_OLD_STATE_SCHEMA = """
CREATE TABLE schema_version (version INTEGER NOT NULL);
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    track_id TEXT,
    status TEXT NOT NULL,
    version INTEGER NOT NULL,
    current_position INTEGER NOT NULL,
    started_at_utc TEXT NOT NULL,
    last_activity_at_utc TEXT NOT NULL
);
CREATE TABLE session_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    resulting_version INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    UNIQUE(session_id, resulting_version)
);
CREATE TABLE progress (
    profile_id TEXT NOT NULL,
    track_id TEXT NOT NULL,
    card_key TEXT NOT NULL,
    state TEXT NOT NULL,
    next_due_at_utc TEXT,
    PRIMARY KEY(profile_id, track_id, card_key)
);
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_user_id TEXT,
    profile_id TEXT,
    payload_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);
"""


async def _open_storage(tmp_path: Path) -> SQLiteStorage:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    return storage


async def _activate_fixture_content(storage: SQLiteStorage, tmp_path: Path) -> str:
    package = create_package(tmp_path / "package.db", "v1")
    candidate = storage.paths.content_staging_dir / "content.next.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p2-state",
    )
    metadata = await storage.async_activate_content_generation(candidate)
    return metadata.generation_id


async def test_state_v2_contains_full_foundation_and_required_hot_indexes(tmp_path: Path) -> None:
    storage = await _open_storage(tmp_path)
    try:
        connection = sqlite3.connect(storage.paths.state_db)
        try:
            assert connection.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            assert {
                "profiles",
                "profile_members",
                "tracks",
                "track_pack_versions",
                "track_card_rules",
                "track_content_weights",
                "notification_targets",
                "progress",
                "review_events",
                "user_annotations",
                "sessions",
                "session_items",
                "session_answers",
                "exam_attempts",
                "scheduler_config",
                "scheduled_slots",
                "notification_interactions",
                "stats_daily",
                "settings",
            } <= tables

            indexes = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                ).fetchall()
            }
            assert {
                "progress_due",
                "review_events_card_created",
                "review_events_profile_created",
                "scheduled_slots_profile_scheduled_status",
                "notification_interactions_target_status_expires",
                "sessions_profile_status_activity",
            } <= indexes
            assert connection.execute("PRAGMA foreign_key_list(progress)").fetchall() == []
            assert connection.execute("PRAGMA foreign_key_list(review_events)").fetchall() == []
        finally:
            connection.close()
    finally:
        await storage.async_close()


async def test_v1_state_migrates_out_of_place_with_backup_and_preserves_rows(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state" / "state.db"
    state_path.parent.mkdir(parents=True)
    connection = sqlite3.connect(state_path)
    try:
        connection.executescript(_OLD_STATE_SCHEMA)
        connection.execute("INSERT INTO schema_version VALUES (1)")
        connection.execute(
            """INSERT INTO sessions VALUES (
                   'legacy-session', 'p0-probe:user', NULL, 'active', 1, 0,
                   '2026-09-22T10:00:00+00:00', '2026-09-22T10:00:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO session_answers(
                   session_id, question_id, answer_json, resulting_version, created_at_utc
               ) VALUES (
                   'legacy-session', 'q1', '{"choice":"a"}', 2,
                   '2026-09-22T10:01:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO progress VALUES (
                   'p0-probe:user', 'legacy-track', 'legacy-card', 'review',
                   '2026-09-23T10:00:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO audit_events(
                   event_type, actor_user_id, profile_id, payload_json, created_at_utc
               ) VALUES (
                   'legacy', 'user', 'p0-probe:user', '{}',
                   '2026-09-22T10:02:00+00:00'
               )"""
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(StoragePaths(state_path, tmp_path / "content" / "current.db"))
    await storage.async_open()
    try:
        migrated = sqlite3.connect(state_path)
        try:
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (DB_SCHEMA_VERSION,)
            assert migrated.execute("SELECT id, type, strategy FROM sessions").fetchone() == (
                "legacy-session",
                "learn",
                "default",
            )
            assert migrated.execute(
                "SELECT profile_id, track_id, card_key, state FROM progress"
            ).fetchone() == (
                "p0-probe:user",
                "legacy-track",
                "legacy-card",
                "review",
            )
            assert migrated.execute("SELECT COUNT(*) FROM audit_events").fetchone() == (1,)
        finally:
            migrated.close()

        backup = state_path.with_name("state.db.pre-migration-v1.bak")
        assert backup.is_file()
        old = sqlite3.connect(backup)
        try:
            assert old.execute("SELECT version FROM schema_version").fetchone() == (1,)
            assert old.execute("SELECT COUNT(*) FROM sessions").fetchone() == (1,)
        finally:
            old.close()
    finally:
        await storage.async_close()


async def test_repositories_keep_progress_lazy_and_validate_content_refs(tmp_path: Path) -> None:
    storage = await _open_storage(tmp_path)
    try:
        generation_id = await _activate_fixture_content(storage, tmp_path)
        now = "2026-09-22T20:00:00+00:00"
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
        await storage.repositories.tracks.async_insert(
            TrackRecord(
                track_id="track-1",
                profile_id="profile-1",
                name="Japanese",
                created_at_utc=now,
                updated_at_utc=now,
                source_language="ja",
                target_language="fr",
            )
        )
        await storage.repositories.tracks.async_pin_pack_version(
            track_id="track-1",
            pack_version_id="locklearn:pack-version:v1",
            dataset_generation=generation_id,
            integrated_at_utc=now,
        )

        state = sqlite3.connect(storage.paths.state_db)
        try:
            assert state.execute("SELECT COUNT(*) FROM progress").fetchone() == (0,)
        finally:
            state.close()

        prompt_id, answer_id = facet_ids(ITEM_A)
        card_key = card_identity(ITEM_A)[1]
        created = await storage.repositories.progress.async_create_if_absent(
            profile_id="profile-1",
            track_id="track-1",
            card=CardReference(
                card_key=card_key,
                learning_item_id=ITEM_A,
                prompt_facet_id=prompt_id,
                answer_facet_id=answer_id,
            ),
            dataset_generation=generation_id,
            normalization_version=1,
            updated_at_utc=now,
        )
        assert created is True
        assert (
            await storage.repositories.progress.async_create_if_absent(
                profile_id="profile-1",
                track_id="track-1",
                card=CardReference(
                    card_key=card_key,
                    learning_item_id=ITEM_A,
                    prompt_facet_id=prompt_id,
                    answer_facet_id=answer_id,
                ),
                dataset_generation=generation_id,
                normalization_version=1,
                updated_at_utc=now,
            )
            is False
        )

        with pytest.raises(ContentReferenceError, match="unknown active card"):
            await storage.repositories.progress.async_create_if_absent(
                profile_id="profile-1",
                track_id="track-1",
                card=CardReference(
                    card_key="locklearn:card-key:missing",
                    learning_item_id="locklearn:item:missing",
                    prompt_facet_id="locklearn:facet:missing:prompt",
                    answer_facet_id="locklearn:facet:missing:answer",
                ),
                dataset_generation=generation_id,
                normalization_version=1,
                updated_at_utc=now,
            )

        with pytest.raises(ContentReferenceError, match="pack_version"):
            await storage.repositories.tracks.async_pin_pack_version(
                track_id="track-1",
                pack_version_id="locklearn:pack-version:missing",
                dataset_generation=generation_id,
                integrated_at_utc=now,
            )
        assert await storage.async_cross_domain_integrity_issues() == ()
    finally:
        await storage.async_close()


async def test_cross_domain_integrity_audit_detects_raw_invalid_state(tmp_path: Path) -> None:
    storage = await _open_storage(tmp_path)
    try:
        await _activate_fixture_content(storage, tmp_path)

        def seed_invalid(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO progress(
                       profile_id, track_id, card_key, learning_item_id,
                       prompt_facet_id, answer_facet_id, state, updated_at_utc
                   ) VALUES (
                       'p', 't', 'missing-card', 'missing-item',
                       'missing-prompt', 'missing-answer', 'review', ''
                   )"""
            )
            connection.commit()

        await storage._async_writer(seed_invalid)
        issues = await storage.async_cross_domain_integrity_issues()
        assert issues == (
            {
                "table": "progress",
                "row_id": "p:t:missing-card",
                "reference": "missing-card",
                "reason": "missing_card_identity",
            },
        )
    finally:
        await storage.async_close()


async def test_v2_state_migrates_to_v3_and_accepts_leech_state(tmp_path: Path) -> None:
    from custom_components.locklearn.storage.schema import STATE_SCHEMA

    state_path = tmp_path / "state" / "state.db"
    state_path.parent.mkdir(parents=True)
    v2_schema = STATE_SCHEMA.replace(
        "state IN ('new', 'learning', 'review', 'relearning', 'leech')",
        "state IN ('new', 'learning', 'review', 'relearning')",
    )
    connection = sqlite3.connect(state_path)
    try:
        connection.executescript(v2_schema)
        connection.execute("INSERT INTO schema_version(version) VALUES (2)")
        connection.execute(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, state, updated_at_utc
               ) VALUES ('profile-v2', 'track-v2', 'card-v2', 'review', ?)""",
            ("2026-09-23T20:00:00+00:00",),
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(StoragePaths(state_path, tmp_path / "content" / "current.db"))
    await storage.async_open()
    try:
        migrated = sqlite3.connect(state_path)
        try:
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
            assert migrated.execute(
                "SELECT state FROM progress WHERE card_key = 'card-v2'"
            ).fetchone() == ("review",)
            migrated.execute(
                """UPDATE progress SET state = 'leech'
                   WHERE profile_id = 'profile-v2'
                     AND track_id = 'track-v2'
                     AND card_key = 'card-v2'"""
            )
            migrated.commit()
            assert migrated.execute(
                "SELECT state FROM progress WHERE card_key = 'card-v2'"
            ).fetchone() == ("leech",)
        finally:
            migrated.close()
        assert state_path.with_name("state.db.pre-migration-v2.bak").is_file()
    finally:
        await storage.async_close()
