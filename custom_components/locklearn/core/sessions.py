"""Persistent session service with optimistic concurrency."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from ..storage.database import SQLiteStorage

SessionListener = Callable[[dict[str, Any]], None]


class SessionService:
    """Coordinate persistent session mutations and client subscriptions."""

    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage
        self._listeners: dict[str, set[SessionListener]] = {}

    @property
    def subscriber_count(self) -> int:
        """Return the active subscriber count for lifecycle diagnostics."""
        return sum(len(listeners) for listeners in self._listeners.values())

    async def async_start(self, profile_id: str, track_id: str | None = None) -> dict[str, Any]:
        """Start a persistent session."""
        return await self._storage.async_create_session(uuid4().hex, profile_id, track_id)

    async def async_get(self, session_id: str) -> dict[str, Any] | None:
        """Get a session."""
        return await self._storage.async_get_session(session_id)

    async def async_answer(
        self,
        session_id: str,
        expected_version: int,
        question_id: str,
        answer: Any,
    ) -> dict[str, Any]:
        """Apply one CAS answer and publish the winning state."""
        state = await self._storage.async_answer_session(
            session_id, expected_version, question_id, answer
        )
        for listener in tuple(self._listeners.get(session_id, ())):
            listener(state)
        return state

    def subscribe(self, session_id: str, listener: SessionListener) -> Callable[[], None]:
        """Subscribe to session changes and return a detach callback."""
        listeners = self._listeners.setdefault(session_id, set())
        listeners.add(listener)

        def unsubscribe() -> None:
            listeners.discard(listener)
            if not listeners:
                self._listeners.pop(session_id, None)

        return unsubscribe

    def close(self) -> None:
        """Detach all subscribers on integration unload."""
        self._listeners.clear()
