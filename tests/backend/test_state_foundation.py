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
    StateMigrationError,
    StoragePaths,
    TrackRecord,
    UnsupportedStateSchemaError,
)
from custom_components.locklearn.storage import database as storage_database
from custom_components.locklearn.storage.schema import STATE_SCHEMA
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

def _state_schema_for_version(version: int) -> str:
    """Reconstruct the schema deltas that existed for state versions 2 through 4."""
    if version not in {2, 3, 4}:
        raise ValueError(f"Unsupported historical fixture version: {version}")

    schema = STATE_SCHEMA
    if version == 2:
        schema = schema.replace(
            "state IN ('new', 'learning', 'review', 'relearning', 'leech')",
            "state IN ('new', 'learning', 'review', 'relearning')",
            1,
        )

    selection_columns = """    deferred_until_utc TEXT,
    defer_reason TEXT,
    card_key TEXT,
    learning_item_id TEXT,
    prompt_facet_id TEXT,
    answer_facet_id TEXT,
    selection_reason TEXT,
    expired_reason TEXT,
"""
    if version <= 3:
        schema = schema.replace(selection_columns, "", 1)
        receptivity_start = schema.index(
            "CREATE TABLE IF NOT EXISTS receptivity_samples ("
        )
        receptivity_end = schema.index(
            "CREATE TABLE IF NOT EXISTS stats_daily (",
            receptivity_start,
        )
        schema = schema[:receptivity_start] + schema[receptivity_end:]
    else:
        schema = schema.replace(
            selection_columns,
            """    deferred_until_utc TEXT,
    defer_reason TEXT,
""",
            1,
        )
    return schema


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
                "receptivity_samples",
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
                "receptivity_samples_profile_hour",
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
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
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
    state_path = tmp_path / "state" / "state.db"
    state_path.parent.mkdir(parents=True)
    v2_schema = _state_schema_for_version(2)
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


async def test_v3_state_migrates_to_v4_with_receptivity_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state-v3" / "state.db"
    state_path.parent.mkdir(parents=True)
    v3_schema = _state_schema_for_version(3)

    connection = sqlite3.connect(state_path)
    try:
        connection.executescript(v3_schema)
        connection.execute("INSERT INTO schema_version(version) VALUES (3)")
        connection.execute(
            """INSERT INTO profiles(
                   profile_id, name, preset, timezone, status, settings_json,
                   created_at_utc, updated_at_utc
               ) VALUES (
                   'profile-v3', 'Legacy', 'standard', 'Europe/Paris', 'active',
                   '{}', '2026-09-24T05:00:00+00:00', '2026-09-24T05:00:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO scheduled_slots(
                   slot_id, profile_id, slot_type, scheduled_for_utc, status,
                   scheduler_config_version, seed, created_at_utc, updated_at_utc
               ) VALUES (
                   'slot-v3', 'profile-v3', 'notification',
                   '2026-09-24T08:00:00+00:00', 'scheduled', 1, 'seed',
                   '2026-09-24T05:00:00+00:00', '2026-09-24T05:00:00+00:00'
               )"""
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(StoragePaths(state_path, tmp_path / "content-v4" / "current.db"))
    await storage.async_open()
    try:
        migrated = sqlite3.connect(state_path)
        try:
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
            columns = {
                str(row[1])
                for row in migrated.execute("PRAGMA table_info(scheduled_slots)").fetchall()
            }
            assert {"deferred_until_utc", "defer_reason"} <= columns
            assert migrated.execute(
                "SELECT slot_id FROM scheduled_slots WHERE slot_id = 'slot-v3'"
            ).fetchone() == ("slot-v3",)
            assert migrated.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'receptivity_samples'"
            ).fetchone() == (1,)
        finally:
            migrated.close()
        assert state_path.with_name("state.db.pre-migration-v3.bak").is_file()
    finally:
        await storage.async_close()


async def test_v4_state_migrates_to_v5_with_notification_selection_state(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state-v4" / "state.db"
    state_path.parent.mkdir(parents=True)
    v4_schema = _state_schema_for_version(4)

    connection = sqlite3.connect(state_path)
    try:
        connection.executescript(v4_schema)
        connection.execute("INSERT INTO schema_version(version) VALUES (4)")
        connection.execute(
            """INSERT INTO profiles(
                   profile_id, name, preset, timezone, status, settings_json,
                   created_at_utc, updated_at_utc
               ) VALUES (
                   'profile-v4', 'Legacy', 'standard', 'Europe/Paris', 'active',
                   '{}', '2026-09-24T05:00:00+00:00', '2026-09-24T05:00:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO scheduled_slots(
                   slot_id, profile_id, slot_type, scheduled_for_utc,
                   deferred_until_utc, defer_reason, status,
                   scheduler_config_version, seed, created_at_utc, updated_at_utc
               ) VALUES (
                   'slot-v4', 'profile-v4', 'learning',
                   '2026-09-24T08:00:00+00:00', NULL, NULL, 'scheduled',
                   1, 'seed', '2026-09-24T05:00:00+00:00',
                   '2026-09-24T05:00:00+00:00'
               )"""
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(StoragePaths(state_path, tmp_path / "content-v5" / "current.db"))
    await storage.async_open()
    try:
        migrated = sqlite3.connect(state_path)
        try:
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
            columns = {
                str(row[1])
                for row in migrated.execute("PRAGMA table_info(scheduled_slots)").fetchall()
            }
            assert {
                "card_key",
                "learning_item_id",
                "prompt_facet_id",
                "answer_facet_id",
                "selection_reason",
                "expired_reason",
            } <= columns
            assert migrated.execute(
                "SELECT slot_id FROM scheduled_slots WHERE slot_id = 'slot-v4'"
            ).fetchone() == ("slot-v4",)
        finally:
            migrated.close()
        assert state_path.with_name("state.db.pre-migration-v4.bak").is_file()
    finally:
        await storage.async_close()


async def test_future_state_schema_is_rejected_without_mutation(tmp_path: Path) -> None:
    """A newer state DB is never downgraded or rewritten by an older build."""
    state_path = tmp_path / "future" / "state.db"
    state_path.parent.mkdir(parents=True)
    connection = sqlite3.connect(state_path)
    try:
        connection.execute("CREATE TABLE schema_version(version INTEGER NOT NULL)")
        connection.execute(
            "INSERT INTO schema_version(version) VALUES (?)",
            (DB_SCHEMA_VERSION + 1,),
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(
        StoragePaths(state_path, tmp_path / "content-future" / "current.db")
    )
    with pytest.raises(UnsupportedStateSchemaError, match="future schema version"):
        await storage.async_open()

    check = sqlite3.connect(state_path)
    try:
        assert check.execute("SELECT version FROM schema_version").fetchone() == (
            DB_SCHEMA_VERSION + 1,
        )
    finally:
        check.close()
    assert not list(state_path.parent.glob("state.db.pre-migration-*.bak"))


async def test_current_state_schema_is_validated_not_silently_repaired(
    tmp_path: Path,
) -> None:
    """A DB claiming the current version must already contain the released schema."""
    state_path = tmp_path / "malformed-current" / "state.db"
    state_path.parent.mkdir(parents=True)
    connection = sqlite3.connect(state_path)
    try:
        connection.execute("CREATE TABLE schema_version(version INTEGER NOT NULL)")
        connection.execute(
            "INSERT INTO schema_version(version) VALUES (?)",
            (DB_SCHEMA_VERSION,),
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(
        StoragePaths(state_path, tmp_path / "content-malformed" / "current.db")
    )
    with pytest.raises(StateMigrationError, match="missing required tables"):
        await storage.async_open()

    check = sqlite3.connect(state_path)
    try:
        tables = {
            str(row[0])
            for row in check.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert tables == {"schema_version"}
    finally:
        check.close()


async def test_mid_chain_migration_failure_preserves_backup_rolls_back_and_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed step rolls back while the original pre-migration snapshot remains usable."""
    state_path = tmp_path / "failure" / "state.db"
    state_path.parent.mkdir(parents=True)
    connection = sqlite3.connect(state_path)
    try:
        connection.executescript(_state_schema_for_version(2))
        connection.execute("INSERT INTO schema_version(version) VALUES (2)")
        connection.execute(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, state, updated_at_utc
               ) VALUES ('profile-failure', 'track-failure', 'card-failure', 'review', ?)""",
            ("2026-09-27T08:00:00+00:00",),
        )
        connection.commit()
    finally:
        connection.close()

    original_v3_to_v4 = storage_database._STATE_MIGRATIONS[3]

    def fail_v3_to_v4(path: Path, schema: str) -> None:
        del schema

        def fail_inside_transaction(connection: sqlite3.Connection) -> None:
            connection.execute(
                "ALTER TABLE scheduled_slots ADD COLUMN injected_failure TEXT"
            )
            raise RuntimeError("injected migration failure")

        storage_database._run_transactional_state_migration(
            path,
            3,
            4,
            fail_inside_transaction,
        )

    monkeypatch.setitem(storage_database._STATE_MIGRATIONS, 3, fail_v3_to_v4)

    storage = SQLiteStorage(
        StoragePaths(state_path, tmp_path / "content-failure" / "current.db")
    )
    with pytest.raises(StateMigrationError, match="recovery snapshot preserved") as error:
        await storage.async_open()

    backup = state_path.with_name("state.db.pre-migration-v2.bak")
    assert error.value.backup_path == backup
    assert backup.is_file()

    failed = sqlite3.connect(state_path)
    try:
        assert failed.execute("SELECT version FROM schema_version").fetchone() == (3,)
        columns = {
            str(row[1])
            for row in failed.execute("PRAGMA table_info(scheduled_slots)").fetchall()
        }
        assert "injected_failure" not in columns
        assert failed.execute(
            "SELECT card_key FROM progress WHERE profile_id = 'profile-failure'"
        ).fetchone() == ("card-failure",)
        assert failed.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert failed.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        failed.close()

    snapshot = sqlite3.connect(backup)
    try:
        assert snapshot.execute("SELECT version FROM schema_version").fetchone() == (2,)
        assert snapshot.execute(
            "SELECT card_key FROM progress WHERE profile_id = 'profile-failure'"
        ).fetchone() == ("card-failure",)
        assert snapshot.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    finally:
        snapshot.close()

    monkeypatch.setitem(
        storage_database._STATE_MIGRATIONS,
        3,
        original_v3_to_v4,
    )
    retry = SQLiteStorage(
        StoragePaths(state_path, tmp_path / "content-retry" / "current.db")
    )
    await retry.async_open()
    try:
        migrated = sqlite3.connect(state_path)
        try:
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
            assert migrated.execute(
                "SELECT card_key FROM progress WHERE profile_id = 'profile-failure'"
            ).fetchone() == ("card-failure",)
        finally:
            migrated.close()
    finally:
        await retry.async_close()
