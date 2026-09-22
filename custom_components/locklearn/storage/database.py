"""Thread-confined SQLite access for LockLearn."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import threading
import uuid
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from ..const import DB_SCHEMA_VERSION
from ..core.clock import Clock, SystemClock
from .content import (
    ContentBuildResult,
    ContentGenerationBuilder,
    ContentGenerationManager,
    GenerationMetadata,
)
from .repositories import StateRepositories
from .schema import STATE_SCHEMA

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

    @property
    def content_root(self) -> Path:
        """Return the root containing current, staging, and immutable generations."""
        return self.content_db.parent

    @property
    def content_staging_dir(self) -> Path:
        """Return the same-filesystem staging directory used for atomic activation."""
        return self.content_root / "staging"

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


def _initialize_state_database(path: Path, schema: str, version: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        connection = sqlite3.connect(path)
        try:
            _configure_state_connection(connection)
            connection.executescript(schema)
            connection.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
            connection.commit()
        finally:
            connection.close()
        return

    connection = sqlite3.connect(path)
    try:
        _configure_state_connection(connection)
        table = connection.execute(
            """SELECT 1 FROM sqlite_master
               WHERE type = 'table' AND name = 'schema_version'"""
        ).fetchone()
        if table is None:
            raise RuntimeError(f"State database has no schema_version table: {path}")
        row = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if row is None:
            raise RuntimeError(f"State database has no schema version row: {path}")
        current = int(row[0])
        if current > version:
            raise RuntimeError(f"Unsupported future schema version {current} for {path}")
        if current == version:
            connection.executescript(schema)
            connection.commit()
            return
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        backup = path.with_name(f"{path.name}.pre-migration-v{current}.bak")
        backup.unlink(missing_ok=True)
        target = sqlite3.connect(backup)
        try:
            connection.backup(target)
        finally:
            target.close()
    finally:
        connection.close()

    _migrate_state_database(path, schema, current, version)


def _unlink_sqlite_files(path: Path) -> None:
    for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
        candidate.unlink(missing_ok=True)


def _migrate_state_database(path: Path, schema: str, current: int, target: int) -> None:
    if (current, target) != (1, 2):
        raise RuntimeError(f"No state migration path from {current} to {target}")

    candidate = path.with_name(f".{path.name}.v2-migration")
    _unlink_sqlite_files(candidate)
    connection = sqlite3.connect(candidate)
    try:
        _configure_state_connection(connection)
        connection.executescript(schema)
        connection.execute("ATTACH DATABASE ? AS legacy", (str(path),))
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("INSERT INTO schema_version(version) VALUES (2)")
        connection.execute(
            """INSERT INTO sessions(
                   id, profile_id, track_id, status, version, current_position,
                   started_at_utc, last_activity_at_utc
               )
               SELECT id, profile_id, track_id, status, version, current_position,
                      started_at_utc, last_activity_at_utc
               FROM legacy.sessions"""
        )
        connection.execute(
            """INSERT INTO session_answers(
                   id, session_id, question_id, answer_json, resulting_version, created_at_utc
               )
               SELECT id, session_id, question_id, answer_json, resulting_version, created_at_utc
               FROM legacy.session_answers"""
        )
        connection.execute(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, state, next_due_at_utc
               )
               SELECT profile_id, track_id, card_key, state, next_due_at_utc
               FROM legacy.progress"""
        )
        connection.execute(
            """INSERT INTO audit_events(
                   id, event_type, actor_user_id, profile_id, payload_json, created_at_utc
               )
               SELECT id, event_type, actor_user_id, profile_id, payload_json, created_at_utc
               FROM legacy.audit_events"""
        )
        connection.commit()
        connection.execute("DETACH DATABASE legacy")
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise RuntimeError("Migrated state database failed integrity_check")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Migrated state database failed foreign_key_check")
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()

    os.replace(candidate, path)
    _unlink_sqlite_files(candidate)


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
        self.content_generations = ContentGenerationManager(
            self.paths.content_db, self._long_executor
        )
        self._writer_connection: sqlite3.Connection | None = None
        self._writer_thread_id: int | None = None
        self._writes_gate = asyncio.Lock()
        self._backup_active = False
        self._closed = False
        self.repositories = StateRepositories.for_storage(self)

    @property
    def writer_thread_id(self) -> int | None:
        """Return the writer thread id for diagnostics/tests."""
        return self._writer_thread_id

    async def async_open(self) -> None:
        """Create schemas and the thread-confined writer connection."""
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(self._writer_executor, self._open_sync)
            await self.content_generations.async_open(built_at_utc=self._clock.now().isoformat())
        except Exception:
            await loop.run_in_executor(self._writer_executor, self._close_sync)
            await asyncio.to_thread(self._shutdown_executors)
            self._closed = True
            raise

    def _open_sync(self) -> None:
        _initialize_state_database(self.paths.state_db, STATE_SCHEMA, DB_SCHEMA_VERSION)
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
        async with await self.content_generations.acquire_reader() as lease:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._reader_executor, self._run_reader, operation, lease.path
            )

    def _run_reader(self, operation: Callable[[sqlite3.Connection], T], content_path: Path) -> T:
        connection = sqlite3.connect(_read_only_uri(self.paths.state_db), uri=True)
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "ATTACH DATABASE ? AS content",
                (_read_only_uri(content_path),),
            )
            return operation(connection)
        finally:
            connection.close()

    async def async_create_session(
        self,
        session_id: str,
        profile_id: str,
        track_id: str | None,
        *,
        session_type: str = "learn",
        strategy: str = "default",
        settings: dict[str, Any] | None = None,
        items: tuple[dict[str, Any], ...] = (),
    ) -> dict[str, Any]:
        """Persist a configured session and its prepared question state."""
        now = self._clock.now().isoformat()
        serialized_settings = json.dumps(
            settings or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def create(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO sessions(
                           id, profile_id, track_id, type, strategy, status, version,
                           current_position, started_at_utc, last_activity_at_utc,
                           question_count, settings_json
                       ) VALUES (?, ?, ?, ?, ?, 'active', 1, 0, ?, ?, ?, ?)""",
                    (
                        session_id,
                        profile_id,
                        track_id,
                        session_type,
                        strategy,
                        now,
                        now,
                        len(items),
                        serialized_settings,
                    ),
                )
                connection.executemany(
                    """INSERT INTO session_items(
                           session_id, position, question_id, card_key,
                           learning_item_id, prompt_facet_id, answer_facet_id,
                           status, payload_json
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        (
                            session_id,
                            position,
                            str(item["question_id"]),
                            str(item["card_key"]),
                            str(item["learning_item_id"]),
                            str(item["prompt_facet_id"]),
                            str(item["answer_facet_id"]),
                            "presented" if position == 0 else "queued",
                            json.dumps(
                                dict(item.get("payload", {})),
                                ensure_ascii=False,
                                separators=(",", ":"),
                                sort_keys=True,
                            ),
                        )
                        for position, item in enumerate(items)
                    ),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._async_writer(create)
        session = await self.async_get_session(session_id)
        assert session is not None
        return session

    async def async_get_session(self, session_id: str) -> dict[str, Any] | None:
        """Read a complete resumable session snapshot."""

        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT id, profile_id, track_id, type, strategy, status, version,
                          current_position, started_at_utc, last_activity_at_utc,
                          completed_at_utc, question_count, settings_json
                   FROM sessions WHERE id = ?""",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "id",
                "profile_id",
                "track_id",
                "type",
                "strategy",
                "status",
                "version",
                "current_position",
                "started_at_utc",
                "last_activity_at_utc",
                "completed_at_utc",
                "question_count",
                "settings_json",
            )
            result = dict(zip(keys, row, strict=True))
            result["settings"] = json.loads(str(result.pop("settings_json")))
            item_rows = connection.execute(
                """SELECT position, question_id, card_key, learning_item_id,
                          prompt_facet_id, answer_facet_id, status, payload_json
                   FROM session_items
                   WHERE session_id = ?
                   ORDER BY position""",
                (session_id,),
            ).fetchall()
            result["items"] = [
                {
                    "position": int(item[0]),
                    "question_id": str(item[1]),
                    "card_key": str(item[2]),
                    "learning_item_id": str(item[3]),
                    "prompt_facet_id": str(item[4]),
                    "answer_facet_id": str(item[5]),
                    "status": str(item[6]),
                    "payload": json.loads(str(item[7])),
                }
                for item in item_rows
            ]
            answer_rows = connection.execute(
                """SELECT id, question_id, answer_json, resulting_version, created_at_utc
                   FROM session_answers
                   WHERE session_id = ?
                   ORDER BY resulting_version""",
                (session_id,),
            ).fetchall()
            result["answers"] = [
                {
                    "id": int(answer[0]),
                    "question_id": str(answer[1]),
                    "answer": json.loads(str(answer[2])),
                    "resulting_version": int(answer[3]),
                    "created_at_utc": str(answer[4]),
                }
                for answer in answer_rows
            ]
            position = int(result["current_position"])
            items = result["items"]
            result["current_question"] = (
                items[position] if 0 <= position < len(items) else None
            )
            return result

        return await self._async_reader(read)

    async def async_answer_session(
        self,
        session_id: str,
        expected_version: int,
        question_id: str,
        answer: Any,
    ) -> dict[str, Any]:
        """Apply an answer with atomic session/question CAS semantics."""
        now = self._clock.now().isoformat()
        answer_json = json.dumps(answer, ensure_ascii=False, separators=(",", ":"))

        def answer_cas(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                session = connection.execute(
                    """SELECT status, version, current_position, question_count
                       FROM sessions WHERE id = ?""",
                    (session_id,),
                ).fetchone()
                if session is None:
                    connection.rollback()
                    raise SessionNotFoundError(session_id)
                status, version, position, question_count = session
                if str(status) != "active" or int(version) != expected_version:
                    connection.rollback()
                    raise StaleSessionError(session_id)
                item = connection.execute(
                    """SELECT question_id, status
                       FROM session_items
                       WHERE session_id = ? AND position = ?""",
                    (session_id, int(position)),
                ).fetchone()
                if item is None or str(item[0]) != question_id or str(item[1]) not in {
                    "queued",
                    "presented",
                }:
                    connection.rollback()
                    raise StaleSessionError(session_id)

                resulting_version = expected_version + 1
                next_position = int(position) + 1
                connection.execute(
                    """UPDATE session_items
                       SET status = 'answered'
                       WHERE session_id = ? AND position = ?""",
                    (session_id, int(position)),
                )
                if next_position < int(question_count):
                    connection.execute(
                        """UPDATE session_items
                           SET status = 'presented'
                           WHERE session_id = ? AND position = ? AND status = 'queued'""",
                        (session_id, next_position),
                    )
                cursor = connection.execute(
                    """UPDATE sessions
                       SET version = ?, current_position = ?, last_activity_at_utc = ?
                       WHERE id = ? AND version = ? AND status = 'active'""",
                    (
                        resulting_version,
                        next_position,
                        now,
                        session_id,
                        expected_version,
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    raise StaleSessionError(session_id)
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

    async def async_set_session_status(
        self,
        session_id: str,
        expected_version: int,
        *,
        status: str,
    ) -> dict[str, Any]:
        """CAS pause/resume/complete one persistent session."""
        if status not in {"active", "paused", "completed"}:
            raise ValueError(f"unsupported session status: {status}")
        now = self._clock.now().isoformat()

        def mutate(connection: sqlite3.Connection) -> None:
            completed_at = now if status == "completed" else None
            allowed_source = {
                "paused": ("active",),
                "active": ("paused",),
                "completed": ("active", "paused"),
            }[status]
            placeholders = ",".join("?" for _ in allowed_source)
            try:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    f"""UPDATE sessions
                        SET status = ?, version = version + 1,
                            last_activity_at_utc = ?,
                            completed_at_utc = CASE
                                WHEN ? = 'completed' THEN ?
                                ELSE completed_at_utc
                            END
                        WHERE id = ? AND version = ?
                          AND status IN ({placeholders})""",
                    (
                        status,
                        now,
                        status,
                        completed_at,
                        session_id,
                        expected_version,
                        *allowed_source,
                    ),
                )
                if cursor.rowcount != 1:
                    exists = connection.execute(
                        "SELECT 1 FROM sessions WHERE id = ?",
                        (session_id,),
                    ).fetchone()
                    connection.rollback()
                    if exists is None:
                        raise SessionNotFoundError(session_id)
                    raise StaleSessionError(session_id)
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._async_writer(mutate)
        session = await self.async_get_session(session_id)
        assert session is not None
        return session

    async def async_undo_session_answer(
        self,
        session_id: str,
        expected_version: int,
        *,
        actor_user_id: str | None = None,
    ) -> dict[str, Any]:
        """CAS-rewind session navigation while preserving answer history."""
        now = self._clock.now().isoformat()

        def undo(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                session = connection.execute(
                    """SELECT profile_id, status, version, current_position
                       FROM sessions WHERE id = ?""",
                    (session_id,),
                ).fetchone()
                if session is None:
                    connection.rollback()
                    raise SessionNotFoundError(session_id)
                profile_id, status, version, position = session
                if str(status) not in {"active", "paused"} or int(version) != expected_version:
                    connection.rollback()
                    raise StaleSessionError(session_id)
                previous_position = int(position) - 1
                if previous_position < 0:
                    connection.rollback()
                    raise StaleSessionError(session_id)
                item = connection.execute(
                    """SELECT question_id, status
                       FROM session_items
                       WHERE session_id = ? AND position = ?""",
                    (session_id, previous_position),
                ).fetchone()
                if item is None or str(item[1]) != "answered":
                    connection.rollback()
                    raise StaleSessionError(session_id)
                question_id = str(item[0])
                connection.execute(
                    """UPDATE session_items SET status = 'presented'
                       WHERE session_id = ? AND position = ?""",
                    (session_id, previous_position),
                )
                connection.execute(
                    """UPDATE session_items SET status = 'queued'
                       WHERE session_id = ? AND position = ? AND status = 'presented'""",
                    (session_id, int(position)),
                )
                cursor = connection.execute(
                    """UPDATE sessions
                       SET version = version + 1, current_position = ?,
                           status = 'active', last_activity_at_utc = ?
                       WHERE id = ? AND version = ?""",
                    (previous_position, now, session_id, expected_version),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    raise StaleSessionError(session_id)
                payload = json.dumps(
                    {
                        "session_id": session_id,
                        "question_id": question_id,
                        "previous_version": expected_version,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
                connection.execute(
                    """INSERT INTO audit_events(
                           event_type, actor_user_id, profile_id, payload_json, created_at_utc
                       ) VALUES ('session_undo_navigation', ?, ?, ?, ?)""",
                    (actor_user_id, str(profile_id), payload, now),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._async_writer(undo)
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

    async def async_dataset_inventory(self) -> list[dict[str, Any]]:
        """Return privacy-safe installed dataset metadata from the active generation."""

        def query(connection: sqlite3.Connection) -> list[dict[str, Any]]:
            package_rows = connection.execute(
                """SELECT package.dataset_id, version.version,
                          package.dataset_version_id,
                          package.canonical_content_hash,
                          package.built_at_utc
                   FROM content.dataset_packages AS package
                   JOIN content.dataset_versions AS version
                     ON version.dataset_version_id = package.dataset_version_id
                   ORDER BY package.dataset_id"""
            ).fetchall()
            result: list[dict[str, Any]] = []
            for (
                raw_dataset_id,
                raw_version,
                raw_version_id,
                raw_hash,
                raw_built_at,
            ) in package_rows:
                dataset_id = str(raw_dataset_id)
                source_rows = connection.execute(
                    """SELECT DISTINCT source.source_id, snapshot.upstream_version,
                              snapshot.upstream_date, snapshot.retrieved_at,
                              snapshot.source_url, snapshot.adapter_version
                       FROM content.provenance_records AS provenance
                       JOIN content.source_snapshots AS snapshot
                         ON snapshot.snapshot_id = provenance.source_snapshot_id
                       JOIN content.sources AS source
                         ON source.source_id = snapshot.source_id
                       WHERE provenance.dataset_id = ?
                       ORDER BY source.source_id, snapshot.snapshot_id""",
                    (dataset_id,),
                ).fetchall()
                licenses = [
                    str(row[0])
                    for row in connection.execute(
                        """SELECT DISTINCT license_id
                           FROM content.dataset_licenses
                           WHERE dataset_id = ?
                           ORDER BY license_id""",
                        (dataset_id,),
                    ).fetchall()
                ]
                pack_versions = [
                    str(row[0])
                    for row in connection.execute(
                        """SELECT version.pack_version_id
                           FROM content.packs AS pack
                           JOIN content.pack_versions AS version
                             ON version.pack_id = pack.pack_id
                           WHERE pack.dataset_id = ?
                           ORDER BY version.pack_version_id""",
                        (dataset_id,),
                    ).fetchall()
                ]
                result.append(
                    {
                        "dataset_id": dataset_id,
                        "version": str(raw_version),
                        "dataset_version_id": str(raw_version_id),
                        "canonical_content_hash": str(raw_hash),
                        "built_at_utc": str(raw_built_at),
                        "sources": tuple(
                            {
                                "source_id": str(row[0]),
                                "upstream_version": str(row[1]),
                                "upstream_date": None if row[2] is None else str(row[2]),
                                "retrieved_at": str(row[3]),
                                "source_url": str(row[4]),
                                "adapter_version": str(row[5]),
                            }
                            for row in source_rows
                        ),
                        "licenses": tuple(licenses),
                        "pack_version_ids": tuple(pack_versions),
                    }
                )
            return result

        return await self._async_reader(query)

    async def async_asset_metadata(self, asset_id: str) -> dict[str, Any] | None:
        """Resolve one public dataset asset from the active content generation."""

        def query(connection: sqlite3.Connection) -> dict[str, Any] | None:
            table = connection.execute(
                """SELECT 1 FROM content.sqlite_master
                   WHERE type = 'table' AND name = 'assets_metadata'"""
            ).fetchone()
            if table is None:
                return None
            row = connection.execute(
                """SELECT asset.asset_id, asset.dataset_id, version.version,
                          asset.kind, asset.path, asset.sha256, asset.byte_size,
                          asset.mime_type, asset.width, asset.height,
                          asset.license_id, asset.attribution
                   FROM content.assets_metadata AS asset
                   JOIN content.dataset_packages AS package
                     ON package.dataset_id = asset.dataset_id
                   JOIN content.dataset_versions AS version
                     ON version.dataset_version_id = package.dataset_version_id
                   WHERE asset.asset_id = ?""",
                (asset_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "asset_id",
                "dataset_id",
                "dataset_version",
                "kind",
                "path",
                "sha256",
                "byte_size",
                "mime_type",
                "width",
                "height",
                "license_id",
                "attribution",
            )
            return dict(zip(keys, row, strict=True))

        return await self._async_reader(query)

    async def async_pack_inventory(self) -> tuple[dict[str, Any], ...]:
        """Return active Pack/PackVersion metadata from the content generation."""

        def query(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT pack.pack_id, pack.name, version.pack_version_id,
                          version.version, version.curation_policy_id,
                          metadata.generation_id,
                          stats.total_items, stats.total_cards
                   FROM content.packs AS pack
                   JOIN content.pack_versions AS version ON version.pack_id = pack.pack_id
                   JOIN content.generation_metadata AS metadata
                   LEFT JOIN content.pack_version_stats AS stats
                     ON stats.pack_version_id = version.pack_version_id
                   ORDER BY pack.name COLLATE NOCASE, pack.pack_id, version.version"""
            ).fetchall()
            return tuple(
                {
                    "pack_id": str(row[0]),
                    "name": str(row[1]),
                    "pack_version_id": str(row[2]),
                    "version": str(row[3]),
                    "curation_policy_id": None if row[4] is None else str(row[4]),
                    "generation_id": str(row[5]),
                    "total_items": 0 if row[6] is None else int(row[6]),
                    "total_cards": 0 if row[7] is None else int(row[7]),
                }
                for row in rows
            )

        return await self._async_reader(query)

    async def async_validate_pack_version_reference(self, pack_version_id: str) -> bool:
        """Validate a state -> content PackVersion reference against active content."""

        def query(connection: sqlite3.Connection) -> bool:
            return (
                connection.execute(
                    """SELECT 1 FROM content.pack_versions
                       WHERE pack_version_id = ?""",
                    (pack_version_id,),
                ).fetchone()
                is not None
            )

        return await self._async_reader(query)

    async def async_validate_card_reference(
        self,
        *,
        card_key: str,
        learning_item_id: str,
        prompt_facet_id: str,
        answer_facet_id: str,
    ) -> bool:
        """Validate a complete state -> content CardDefinition identity."""

        def query(connection: sqlite3.Connection) -> bool:
            return (
                connection.execute(
                    """SELECT 1
                       FROM content.card_definitions AS card
                       JOIN content.learning_items AS item
                         ON item.learning_item_id = card.learning_item_id
                       JOIN content.facets AS prompt
                         ON prompt.facet_id = card.prompt_facet_id
                       JOIN content.facets AS answer
                         ON answer.facet_id = card.answer_facet_id
                       WHERE card.card_key = ?
                         AND card.learning_item_id = ?
                         AND card.prompt_facet_id = ?
                         AND card.answer_facet_id = ?
                         AND card.lifecycle_status = 'active'
                         AND item.lifecycle_status = 'active'
                         AND prompt.lifecycle_status = 'active'
                         AND answer.lifecycle_status = 'active'""",
                    (
                        card_key,
                        learning_item_id,
                        prompt_facet_id,
                        answer_facet_id,
                    ),
                ).fetchone()
                is not None
            )

        return await self._async_reader(query)

    async def async_cross_domain_integrity_issues(self) -> tuple[dict[str, str], ...]:
        """Audit state references that SQLite cannot enforce across content.db."""

        def query(connection: sqlite3.Connection) -> tuple[dict[str, str], ...]:
            issues: list[dict[str, str]] = []
            for track_id, pack_version_id in connection.execute(
                "SELECT track_id, pack_version_id FROM track_pack_versions"
            ).fetchall():
                exists = connection.execute(
                    "SELECT 1 FROM content.pack_versions WHERE pack_version_id = ?",
                    (pack_version_id,),
                ).fetchone()
                if exists is None:
                    issues.append(
                        {
                            "table": "track_pack_versions",
                            "row_id": str(track_id),
                            "reference": str(pack_version_id),
                            "reason": "missing_pack_version",
                        }
                    )

            state_card_queries = (
                (
                    "progress",
                    """SELECT profile_id || ':' || track_id || ':' || card_key,
                              card_key, learning_item_id, prompt_facet_id, answer_facet_id
                       FROM progress
                       WHERE learning_item_id IS NOT NULL""",
                ),
                (
                    "review_events",
                    """SELECT id, card_key, learning_item_id, prompt_facet_id, answer_facet_id
                       FROM review_events""",
                ),
                (
                    "session_items",
                    """SELECT session_id || ':' || question_id,
                              card_key, learning_item_id, prompt_facet_id, answer_facet_id
                       FROM session_items""",
                ),
            )
            for table_name, sql in state_card_queries:
                for row_id, card_key, item_id, prompt_id, answer_id in connection.execute(
                    sql
                ).fetchall():
                    exists = connection.execute(
                        """SELECT 1 FROM content.card_definitions
                           WHERE card_key = ? AND learning_item_id = ?
                             AND prompt_facet_id = ? AND answer_facet_id = ?""",
                        (card_key, item_id, prompt_id, answer_id),
                    ).fetchone()
                    if exists is None:
                        issues.append(
                            {
                                "table": table_name,
                                "row_id": str(row_id),
                                "reference": str(card_key),
                                "reason": "missing_card_identity",
                            }
                        )
            return tuple(issues)

        return await self._async_reader(query)

    async def async_referenced_pack_version_ids(self) -> frozenset[str]:
        """Return every pack version referenced by persistent track state, when present."""

        def query(connection: sqlite3.Connection) -> frozenset[str]:
            table = connection.execute(
                """SELECT 1 FROM sqlite_master
                   WHERE type = 'table' AND name = 'track_pack_versions'"""
            ).fetchone()
            if table is None:
                return frozenset()
            rows = connection.execute(
                "SELECT DISTINCT pack_version_id FROM track_pack_versions"
            ).fetchall()
            return frozenset(str(row[0]) for row in rows)

        return await self._async_writer(query)

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
                   FROM content.pack_items AS member
                   JOIN content.learning_items AS item
                     ON item.learning_item_id = member.learning_item_id
                    AND item.lifecycle_status = 'active'
                   JOIN content.card_definitions AS card
                     ON card.learning_item_id = item.learning_item_id
                    AND card.lifecycle_status = 'active'
                   LEFT JOIN progress AS progress
                     ON progress.profile_id = ?
                    AND progress.track_id = ?
                    AND progress.card_key = card.card_key
                   WHERE member.pack_version_id = ? AND progress.card_key IS NULL
                   ORDER BY member.position, card.card_key LIMIT ?""",
                (profile_id, track_id, pack_version_id, limit),
            ).fetchall()
            return [row[0] for row in rows]

        return await self._async_reader(query)

    async def async_build_content_generation(
        self,
        packages: Iterable[Path],
        destination: Path,
        *,
        generation_id: str | None = None,
    ) -> ContentBuildResult:
        """Build a validated candidate without making it visible to readers."""
        package_list = tuple(packages)
        selected_generation_id = generation_id or f"generation-{uuid.uuid4().hex}"
        async with await self.content_generations.acquire_reader() as lease:
            loop = asyncio.get_running_loop()
            builder = ContentGenerationBuilder()
            future = loop.run_in_executor(
                self._long_executor,
                lambda: builder.build(
                    package_list,
                    destination,
                    generation_id=selected_generation_id,
                    built_at_utc=self._clock.now().isoformat(),
                    previous_generation=lease.path,
                ),
            )
            cancelled = False
            while True:
                try:
                    result = await asyncio.shield(future)
                    break
                except asyncio.CancelledError:
                    cancelled = True
            if cancelled:
                raise asyncio.CancelledError
            return result

    async def async_activate_content_generation(self, candidate: Path) -> GenerationMetadata:
        """Activate a validated candidate after every old reader has drained."""
        return await self.content_generations.async_activate(candidate)

    async def async_rollback_content_generation(self) -> GenerationMetadata:
        """Reactivate the retained previous generation."""
        return await self.content_generations.async_rollback()

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
        await self.content_generations.async_close()
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
