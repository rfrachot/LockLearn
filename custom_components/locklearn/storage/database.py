"""Thread-confined SQLite access for LockLearn."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from ..const import CONTENT_SCHEMA_VERSION, DB_SCHEMA_VERSION
from ..core.clock import Clock, SystemClock
from .schema import CONTENT_SCHEMA, STATE_SCHEMA

T = TypeVar("T")


class SessionNotFoundError(LookupError):
    """Raised when a session does not exist."""


class StaleSessionError(RuntimeError):
    """Raised when a session CAS loses a race."""


@dataclass(frozen=True, slots=True)
class StoragePaths:
    """Physically separate persistent-state and reconstructible-content paths."""

    state_db: Path
    content_db: Path

    @classmethod
    def from_config_dir(cls, config_dir: str) -> StoragePaths:
        """Build paths outside the custom integration directory."""
        root = Path(config_dir)
        return cls(
            state_db=root / ".storage" / "locklearn" / "state.db",
            content_db=root / "locklearn-content" / "current.db",
        )


def _read_only_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _configure_state_connection(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA foreign_keys = ON")


def _initialize_database(path: Path, schema: str, version: int, *, state: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_immutable_content = not state and path.exists()
    connection = sqlite3.connect(
        _read_only_uri(path) if existing_immutable_content else path,
        uri=existing_immutable_content,
    )
    try:
        if existing_immutable_content:
            row = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if row is None or row[0] != version:
                found = None if row is None else row[0]
                raise RuntimeError(f"Unsupported schema version {found} for {path}")
            return
        if state:
            _configure_state_connection(connection)
        else:
            connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)
        row = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if row is None:
            connection.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
        elif row[0] != version:
            raise RuntimeError(f"Unsupported schema version {row[0]} for {path}")
        connection.commit()
    finally:
        connection.close()


class SQLiteStorage:
    """Own SQLite connections and keep all database I/O off the event loop.

    The state writer connection is created and used only by a single dedicated
    executor thread. Every read gets a short-lived connection on a separate
    reader executor. No connection crosses either boundary.
    """

    def __init__(self, paths: StoragePaths, clock: Clock | None = None) -> None:
        self.paths = paths
        self._clock = clock or SystemClock()
        self._writer_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="locklearn-db-w"
        )
        self._reader_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="locklearn-db-r"
        )
        self._long_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="locklearn-db-long"
        )
        self._writer_connection: sqlite3.Connection | None = None
        self._writer_thread_id: int | None = None
        self._writes_gate = asyncio.Lock()
        self._backup_active = False
        self._closed = False

    @property
    def writer_thread_id(self) -> int | None:
        """Return the writer thread id for diagnostics/tests."""
        return self._writer_thread_id

    async def async_open(self) -> None:
        """Create schemas and the thread-confined writer connection."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._writer_executor, self._open_sync)

    def _open_sync(self) -> None:
        _initialize_database(self.paths.state_db, STATE_SCHEMA, DB_SCHEMA_VERSION, state=True)
        _initialize_database(
            self.paths.content_db, CONTENT_SCHEMA, CONTENT_SCHEMA_VERSION, state=False
        )
        self._writer_connection = sqlite3.connect(self.paths.state_db)
        _configure_state_connection(self._writer_connection)
        self._writer_thread_id = threading.get_ident()

    async def _async_writer(self, operation: Callable[[sqlite3.Connection], T]) -> T:
        if self._closed:
            raise RuntimeError("LockLearn storage is closed")
        async with self._writes_gate:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self._writer_executor, self._run_writer, operation)

    def _run_writer(self, operation: Callable[[sqlite3.Connection], T]) -> T:
        connection = self._writer_connection
        if connection is None:
            raise RuntimeError("LockLearn storage is not open")
        if threading.get_ident() != self._writer_thread_id:
            raise RuntimeError("State writer escaped its dedicated thread")
        return operation(connection)

    async def _async_reader(self, operation: Callable[[sqlite3.Connection], T]) -> T:
        if self._closed:
            raise RuntimeError("LockLearn storage is closed")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._reader_executor, self._run_reader, operation)

    def _run_reader(self, operation: Callable[[sqlite3.Connection], T]) -> T:
        connection = sqlite3.connect(_read_only_uri(self.paths.state_db), uri=True)
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "ATTACH DATABASE ? AS content",
                (_read_only_uri(self.paths.content_db),),
            )
            return operation(connection)
        finally:
            connection.close()

    async def async_create_session(
        self, session_id: str, profile_id: str, track_id: str | None
    ) -> dict[str, Any]:
        """Persist a new active session."""
        now = self._clock.now().isoformat()

        def create(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO sessions(
                       id, profile_id, track_id, status, version, current_position,
                       started_at_utc, last_activity_at_utc
                   ) VALUES (?, ?, ?, 'active', 1, 0, ?, ?)""",
                (session_id, profile_id, track_id, now, now),
            )
            connection.commit()

        await self._async_writer(create)
        session = await self.async_get_session(session_id)
        assert session is not None
        return session

    async def async_get_session(self, session_id: str) -> dict[str, Any] | None:
        """Read a session using a short-lived reader connection."""

        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT id, profile_id, track_id, status, version, current_position,
                          started_at_utc, last_activity_at_utc
                   FROM sessions WHERE id = ?""",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "id",
                "profile_id",
                "track_id",
                "status",
                "version",
                "current_position",
                "started_at_utc",
                "last_activity_at_utc",
            )
            return dict(zip(keys, row, strict=True))

        return await self._async_reader(read)

    async def async_answer_session(
        self,
        session_id: str,
        expected_version: int,
        question_id: str,
        answer: Any,
    ) -> dict[str, Any]:
        """Apply an answer with an atomic optimistic version check."""
        now = self._clock.now().isoformat()
        answer_json = json.dumps(answer, ensure_ascii=False, separators=(",", ":"))

        def answer_cas(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    """UPDATE sessions
                       SET version = version + 1,
                           current_position = current_position + 1,
                           last_activity_at_utc = ?
                       WHERE id = ? AND version = ? AND status = 'active'""",
                    (now, session_id, expected_version),
                )
                if cursor.rowcount != 1:
                    exists = connection.execute(
                        "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
                    ).fetchone()
                    connection.rollback()
                    if exists is None:
                        raise SessionNotFoundError(session_id)
                    raise StaleSessionError(session_id)
                resulting_version = expected_version + 1
                connection.execute(
                    """INSERT INTO session_answers(
                           session_id, question_id, answer_json, resulting_version, created_at_utc
                       ) VALUES (?, ?, ?, ?, ?)""",
                    (session_id, question_id, answer_json, resulting_version, now),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._async_writer(answer_cas)
        session = await self.async_get_session(session_id)
        assert session is not None
        return session

    async def async_append_audit(
        self,
        event_type: str,
        actor_user_id: str | None,
        profile_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        """Append a privacy-minimal audit event."""
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        now = self._clock.now().isoformat()

        def append(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO audit_events(
                       event_type, actor_user_id, profile_id, payload_json, created_at_utc
                   ) VALUES (?, ?, ?, ?, ?)""",
                (event_type, actor_user_id, profile_id, serialized, now),
            )
            connection.commit()

        await self._async_writer(append)

    async def async_due_cards(
        self, profile_id: str, track_id: str, before_utc: str, limit: int
    ) -> list[str]:
        """Run the P0 representative hot due query."""

        def query(connection: sqlite3.Connection) -> list[str]:
            rows = connection.execute(
                """SELECT card_key FROM progress
                   WHERE profile_id = ? AND track_id = ? AND state = 'review'
                     AND next_due_at_utc <= ?
                   ORDER BY next_due_at_utc, card_key LIMIT ?""",
                (profile_id, track_id, before_utc, limit),
            ).fetchall()
            return [row[0] for row in rows]

        return await self._async_reader(query)

    async def async_new_cards(
        self, profile_id: str, track_id: str, pack_version_id: str, limit: int
    ) -> list[str]:
        """Run the P0 content/state anti-join with one read-only content DB."""

        def query(connection: sqlite3.Connection) -> list[str]:
            rows = connection.execute(
                """SELECT card.card_key
                   FROM content.card_definitions AS card
                   LEFT JOIN progress AS progress
                     ON progress.profile_id = ?
                    AND progress.track_id = ?
                    AND progress.card_key = card.card_key
                   WHERE card.pack_version_id = ? AND progress.card_key IS NULL
                   ORDER BY card.ordinal LIMIT ?""",
                (profile_id, track_id, pack_version_id, limit),
            ).fetchall()
            return [row[0] for row in rows]

        return await self._async_reader(query)

    async def async_build_content_generation(
        self, packages: Iterable[Path], destination: Path
    ) -> int:
        """Merge prebuilt package DBs one at a time into a new generation."""
        package_list = tuple(packages)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._long_executor,
            _build_content_generation,
            package_list,
            destination,
        )

    async def async_backup_to(self, destination: Path) -> None:
        """Create a coherent state snapshot using SQLite's backup API."""

        def backup(connection: sqlite3.Connection) -> None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            target = sqlite3.connect(destination)
            try:
                connection.backup(target)
            finally:
                target.close()

        await self._async_writer(backup)

    async def async_prepare_ha_backup(self) -> None:
        """Pause new writes and checkpoint WAL until HA finishes archiving."""
        if self._backup_active:
            return
        await self._writes_gate.acquire()
        self._backup_active = True
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self._writer_executor,
                self._run_writer,
                lambda connection: connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall(),
            )
        except Exception:
            self._backup_active = False
            self._writes_gate.release()
            raise

    async def async_finish_ha_backup(self) -> None:
        """Resume writes after HA backup completion or failure."""
        if not self._backup_active:
            return
        self._backup_active = False
        self._writes_gate.release()

    async def async_close(self) -> None:
        """Drain and close all SQLite resources and executors."""
        if self._closed:
            return
        if self._backup_active:
            await self.async_finish_ha_backup()
        async with self._writes_gate:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._writer_executor, self._close_sync)
        self._closed = True
        await asyncio.to_thread(self._shutdown_executors)

    def _close_sync(self) -> None:
        if self._writer_connection is not None:
            self._writer_connection.close()
            self._writer_connection = None

    def _shutdown_executors(self) -> None:
        self._writer_executor.shutdown(wait=True, cancel_futures=True)
        self._reader_executor.shutdown(wait=True, cancel_futures=True)
        self._long_executor.shutdown(wait=True, cancel_futures=True)


def _build_content_generation(packages: tuple[Path, ...], destination: Path) -> int:
    """Synchronous content merge executed only on the long-operation worker."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    _initialize_database(destination, CONTENT_SCHEMA, CONTENT_SCHEMA_VERSION, state=False)
    connection = sqlite3.connect(destination, uri=True)
    inserted = 0
    try:
        for package in packages:
            connection.execute("ATTACH DATABASE ? AS package", (_read_only_uri(package),))
            try:
                before = connection.total_changes
                connection.execute(
                    """INSERT INTO card_definitions(card_key, pack_version_id, ordinal)
                       SELECT card_key, pack_version_id, ordinal
                       FROM package.card_definitions"""
                )
                connection.commit()
                inserted += connection.total_changes - before
            finally:
                connection.execute("DETACH DATABASE package")
        return inserted
    finally:
        connection.close()
