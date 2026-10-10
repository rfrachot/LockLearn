"""F04: mobile event delivery intent must be atomic with the canonical ReviewEvent."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from custom_components.locklearn.const import DB_SCHEMA_VERSION
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from custom_components.locklearn.storage.database import validate_state_database_file
from custom_components.locklearn.storage.schema import STATE_SCHEMA


def _insert_mobile_event(connection: sqlite3.Connection, event_id: str, *, mode: str = "verified_mcq") -> None:
    connection.execute(
        """INSERT INTO review_events(
            id, profile_id, track_id, learning_item_id, prompt_facet_id,
            answer_facet_id, card_key, mode, question_type, result, hint_used,
            retrieval_occurred, signal_quality, policy_version, dataset_generation,
            pre_state_snapshot, post_state_snapshot, notification_id,
            created_at_utc, local_date, timezone_name, utc_offset_minutes
        ) VALUES (?, 'p', 't', 'item', 'prompt', 'answer', 'card', ?, 'mcq',
                  'correct', 0, 1, 'medium', 1, 'generation', '{}', '{}',
                  'interaction-1', '2026-10-10T10:00:00+00:00', '2026-10-10', 'UTC', 0)""",
        (event_id, mode),
    )


async def test_mobile_event_creates_atomic_outbox_intent(tmp_path: Path) -> None:
    storage = SQLiteStorage(StoragePaths(tmp_path / "state.db", tmp_path / "content.db"))
    await storage.async_open()
    try:
        def commit(connection: sqlite3.Connection) -> None:
            connection.execute("BEGIN IMMEDIATE")
            _insert_mobile_event(connection, "mobile-1")
            connection.commit()

        await storage._async_writer(commit)
        connection = sqlite3.connect(storage.paths.state_db)
        try:
            assert connection.execute(
                "SELECT event_id, payload_json, delivered_at_utc, attempt_count FROM notification_event_outbox"
            ).fetchall() == [("mobile-1", None, None, 0)]
        finally:
            connection.close()
    finally:
        await storage.async_close()


async def test_rolled_back_review_has_no_outbox_intent(tmp_path: Path) -> None:
    storage = SQLiteStorage(StoragePaths(tmp_path / "state.db", tmp_path / "content.db"))
    await storage.async_open()
    try:
        def fail(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                _insert_mobile_event(connection, "rolled-back")
                raise RuntimeError("simulated projection failure")
            except Exception:
                connection.rollback()
                raise

        with pytest.raises(RuntimeError, match="simulated projection failure"):
            await storage._async_writer(fail)
        connection = sqlite3.connect(storage.paths.state_db)
        try:
            assert connection.execute(
                "SELECT COUNT(*) FROM review_events WHERE id = 'rolled-back'"
            ).fetchone() == (0,)
            assert connection.execute(
                "SELECT COUNT(*) FROM notification_event_outbox"
            ).fetchone() == (0,)
        finally:
            connection.close()
    finally:
        await storage.async_close()


async def test_existing_state_v5_migrates_without_replaying_old_events(tmp_path: Path) -> None:
    paths = StoragePaths(tmp_path / "state.db", tmp_path / "content.db")
    connection = sqlite3.connect(paths.state_db)
    try:
        connection.executescript(STATE_SCHEMA)
        connection.execute("INSERT INTO schema_version VALUES (5)")
        _insert_mobile_event(connection, "historical")
        connection.execute("DROP TRIGGER review_events_mobile_outbox")
        connection.execute("DROP TABLE notification_event_outbox")
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(paths)
    await storage.async_open()
    try:
        assert validate_state_database_file(paths.state_db) == DB_SCHEMA_VERSION
        connection = sqlite3.connect(paths.state_db)
        try:
            assert connection.execute(
                "SELECT COUNT(*) FROM review_events WHERE id = 'historical'"
            ).fetchone() == (1,)
            assert connection.execute(
                "SELECT COUNT(*) FROM notification_event_outbox"
            ).fetchone() == (0,)
            _insert_mobile_event(connection, "new-mobile")
            connection.commit()
            assert connection.execute(
                "SELECT event_id FROM notification_event_outbox"
            ).fetchall() == [("new-mobile",)]
        finally:
            connection.close()
    finally:
        await storage.async_close()
