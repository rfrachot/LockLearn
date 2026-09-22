"""SQLite concurrency, boundary and backup tests."""

import asyncio
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.locklearn.storage.database import (
    SQLiteStorage,
    StaleSessionError,
    StoragePaths,
)
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package


@dataclass(frozen=True)
class FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


@pytest.fixture
async def storage(tmp_path: Path):
    """Open isolated physical state/content databases."""
    instance = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await instance.async_open()
    yield instance
    await instance.async_close()


async def test_sqlite_io_is_thread_confined(storage: SQLiteStorage) -> None:
    """The dedicated writer never runs on the HA/event-loop thread."""
    event_loop_thread = threading.get_ident()
    await storage.async_create_session("s1", "p1", None)
    assert storage.writer_thread_id is not None
    assert storage.writer_thread_id != event_loop_thread


async def test_session_timestamps_use_injected_clock(tmp_path: Path) -> None:
    """Persistent time-sensitive state never reaches directly for wall time."""
    fixed = datetime(2026, 1, 2, 3, 4, tzinfo=UTC)
    instance = SQLiteStorage(
        StoragePaths(tmp_path / "state.db", tmp_path / "content.db"),
        clock=FixedClock(fixed),
    )
    await instance.async_open()
    try:
        session = await instance.async_create_session("s1", "p1", None)
        assert session["started_at_utc"] == fixed.isoformat()
    finally:
        await instance.async_close()


async def test_state_and_content_are_separate_and_pragmas_enabled(storage: SQLiteStorage) -> None:
    """State uses WAL/foreign keys while content remains a separate file."""
    assert storage.paths.state_db != storage.paths.content_db
    state = sqlite3.connect(storage.paths.state_db)
    try:
        assert state.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        state.execute("PRAGMA foreign_keys = ON")
        assert state.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert (
            state.execute("SELECT 1 FROM sqlite_master WHERE name='sessions'").fetchone()
            is not None
        )
        assert (
            state.execute("SELECT 1 FROM sqlite_master WHERE name='card_definitions'").fetchone()
            is None
        )
    finally:
        state.close()


async def test_storage_diagnostic_is_private_and_off_event_loop(storage: SQLiteStorage) -> None:
    """The diagnostic reports health/counts without returning stored rows."""
    await storage.async_create_session("s1", "p1", None)

    status = await storage.async_diagnostic_status()

    assert status == {
        "backup_active": False,
        "foreign_key_violation_count": 0,
        "integrity_check": ["ok"],
        "journal_mode": "wal",
        "reader_off_event_loop": True,
        "schema_version": 2,
        "session_answer_count": 0,
        "session_count": 1,
        "writer_initialized": True,
    }


async def test_session_cas_allows_only_one_client(storage: SQLiteStorage) -> None:
    """Two clients with the same expected version cannot both mutate."""
    await storage.async_create_session("s1", "p1", "t1")
    results = await asyncio.gather(
        storage.async_answer_session("s1", 1, "q1", {"choice": "a"}),
        storage.async_answer_session("s1", 1, "q1", {"choice": "b"}),
        return_exceptions=True,
    )
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, StaleSessionError) for result in results) == 1
    winner = next(result for result in results if isinstance(result, dict))
    assert winner["version"] == 2


async def test_backup_is_coherent_and_restorable(storage: SQLiteStorage, tmp_path: Path) -> None:
    """Connection.backup captures committed state after a WAL checkpoint."""
    await storage.async_create_session("s1", "p1", None)
    backup_path = tmp_path / "backup" / "state.db"
    await storage.async_backup_to(backup_path)

    restored = sqlite3.connect(backup_path)
    try:
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert restored.execute("SELECT id, version FROM sessions").fetchone() == ("s1", 1)
    finally:
        restored.close()


async def test_ha_backup_hook_pauses_and_resumes_user_writes(storage: SQLiteStorage) -> None:
    """Writes queue behind the backup checkpoint and resume after post-hook."""
    await storage.async_prepare_ha_backup()
    pending_write = asyncio.create_task(storage.async_create_session("s1", "p1", None))
    await asyncio.sleep(0)
    assert not pending_write.done()
    await storage.async_finish_ha_backup()
    session = await pending_write
    assert session["id"] == "s1"


async def test_content_merge_and_hot_queries(storage: SQLiteStorage, tmp_path: Path) -> None:
    """Packages merge one at a time and hot queries cross only the active DB."""
    package = create_package(tmp_path / "package.db", "v1")
    merged = storage.paths.content_staging_dir / "content.next.db"
    result = await storage.async_build_content_generation(
        (package,), merged, generation_id="generation-hot-query"
    )
    assert result.max_database_count == 2
    await storage.async_activate_content_generation(merged)

    pack_version_id = "locklearn:pack-version:v1"
    card_key = card_identity(ITEM_A)[1]
    assert await storage.async_new_cards("p1", "t1", pack_version_id, 5) == [card_key]
    now = datetime.now(UTC).isoformat()

    def seed(connection: sqlite3.Connection) -> None:
        connection.execute(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, state, next_due_at_utc
               ) VALUES (?, ?, ?, 'review', ?)""",
            ("p1", "t1", card_key, now),
        )
        connection.commit()

    await storage._async_writer(seed)
    assert await storage.async_due_cards("p1", "t1", now, 10) == [card_key]
