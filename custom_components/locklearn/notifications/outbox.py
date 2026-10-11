"""Durable, at-least-once Home Assistant notifications from committed reviews."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any

from ..storage.database import SQLiteStorage

_LOGGER = logging.getLogger(__name__)

EventEmitter = Callable[[str, dict[str, Any]], None]


class NotificationEventOutbox:
    """Persist HA event batches before dispatching, then acknowledge on success."""

    def __init__(self, storage: SQLiteStorage, *, emitter: EventEmitter) -> None:
        self._storage = storage
        self._emitter = emitter
        self._drain_lock = asyncio.Lock()
        self._replay_task: asyncio.Task[None] | None = None

    def start(self, replay: Callable[[], Awaitable[None]]) -> None:
        """Retry undelivered events while the HA config entry stays loaded."""
        if self._replay_task is not None:
            return

        async def run() -> None:
            while True:
                await asyncio.sleep(60)
                try:
                    await replay()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    _LOGGER.exception("LockLearn HA event outbox retry failed")

        self._replay_task = asyncio.create_task(run())

    async def async_close(self) -> None:
        """Stop retry operations before SQLite is closed."""
        task = self._replay_task
        self._replay_task = None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def async_publish(
        self, event_id: str, events: tuple[tuple[str, dict[str, Any]], ...]
    ) -> None:
        serialized = json.dumps(
            [{"name": name, "payload": payload} for name, payload in events],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def store(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    """UPDATE notification_event_outbox
                       SET payload_json = ?
                       WHERE event_id = ? AND delivered_at_utc IS NULL""",
                    (serialized, event_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("no pending notification outbox intent")
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(store)
        await self.async_drain()

    async def async_unfinalized(
        self, *, after: tuple[str, str] | None = None
    ) -> tuple[dict[str, Any], ...]:
        """Read a bounded page of unfinalized intents after a stable ordering cursor."""

        def decode_context(event_id: str, raw: str | None) -> dict[str, Any] | None:
            if raw is None:
                return None
            try:
                context = json.loads(raw)
            except (TypeError, ValueError):
                _LOGGER.error("Invalid outbox recovery JSON for event %s", event_id)
                return None
            return context if isinstance(context, dict) else None

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            parameters: tuple[str | None, str | None, str | None] = (
                (None, None, None) if after is None else (after[0], after[0], after[1])
            )
            rows = connection.execute(
                """SELECT o.event_id, o.context_json, e.profile_id, e.track_id,
                          e.mode, e.result, e.session_id, e.answer_id,
                          e.expected_answer_id, e.pre_state_snapshot,
                          e.post_state_snapshot, e.created_at_utc
                   FROM notification_event_outbox AS o
                   JOIN review_events AS e ON e.id = o.event_id
                   WHERE o.delivered_at_utc IS NULL AND o.payload_json IS NULL
                     AND (? IS NULL OR (o.created_at_utc, o.event_id) > (?, ?))
                   ORDER BY o.created_at_utc, o.event_id
                   LIMIT 100""",
                parameters,
            ).fetchall()
            return tuple(
                {
                    "event_id": row[0],
                    "context": decode_context(str(row[0]), row[1]),
                    "profile_id": row[2],
                    "track_id": row[3],
                    "mode": row[4],
                    "result": row[5],
                    "session_id": row[6],
                    "answer_id": row[7],
                    "expected_answer_id": row[8],
                    "pre_state_snapshot": json.loads(row[9]),
                    "post_state_snapshot": json.loads(row[10]),
                    "created_at_utc": row[11],
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_drain(self) -> None:
        """Emit pending batches; errors retain the batch for future retry."""
        async with self._drain_lock:
            while True:

                def read(connection: sqlite3.Connection) -> tuple[str, str] | None:
                    row = connection.execute(
                        """SELECT event_id, payload_json FROM notification_event_outbox
                           WHERE delivered_at_utc IS NULL AND payload_json IS NOT NULL
                           ORDER BY created_at_utc, event_id LIMIT 1"""
                    ).fetchone()
                    return None if row is None else (str(row[0]), str(row[1]))

                pending = await self._storage._async_reader(read)
                if pending is None:
                    return
                event_id, serialized = pending
                try:
                    for item in json.loads(serialized):
                        self._emitter(str(item["name"]), dict(item["payload"]))
                except Exception:
                    _LOGGER.exception("LockLearn HA event outbox delivery failed")
                    return

                def acknowledge(connection: sqlite3.Connection, event_id: str = event_id) -> None:
                    try:
                        connection.execute("BEGIN IMMEDIATE")
                        connection.execute(
                            """UPDATE notification_event_outbox
                               SET delivered_at_utc = strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                                   attempt_count = attempt_count + 1
                               WHERE event_id = ? AND delivered_at_utc IS NULL""",
                            (event_id,),
                        )
                        connection.commit()
                    except Exception:
                        if connection.in_transaction:
                            connection.rollback()
                        raise

                await self._storage._async_writer(acknowledge)
