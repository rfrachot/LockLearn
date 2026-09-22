"""Persistent session service with optimistic concurrency and resumable state."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from ..storage.database import SQLiteStorage

SessionListener = Callable[[dict[str, Any]], None]


class SessionValidationError(ValueError):
    """Raised when a prepared session is internally inconsistent."""


@dataclass(frozen=True, slots=True)
class SessionQuestion:
    """Prepared question state persisted for cross-client resume."""

    question_id: str
    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    payload: dict[str, Any]

    def as_storage_dict(self) -> dict[str, Any]:
        """Return the stable storage representation."""
        return {
            "question_id": self.question_id,
            "card_key": self.card_key,
            "learning_item_id": self.learning_item_id,
            "prompt_facet_id": self.prompt_facet_id,
            "answer_facet_id": self.answer_facet_id,
            "payload": dict(self.payload),
        }


class SessionService:
    """Coordinate persistent session lifecycle, CAS mutations and subscriptions."""

    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage
        self._listeners: dict[str, set[SessionListener]] = {}

    @property
    def subscriber_count(self) -> int:
        """Return the active subscriber count for lifecycle diagnostics."""
        return sum(len(listeners) for listeners in self._listeners.values())

    async def async_start(
        self,
        profile_id: str,
        track_id: str | None = None,
        *,
        session_type: str = "learn",
        strategy: str = "default",
        settings: dict[str, Any] | None = None,
        questions: tuple[SessionQuestion, ...] = (),
    ) -> dict[str, Any]:
        """Start a persistent session with optional backend-prepared questions."""
        if not profile_id.strip():
            raise SessionValidationError("profile_id must not be empty")
        if not session_type.strip():
            raise SessionValidationError("session_type must not be empty")
        if not strategy.strip():
            raise SessionValidationError("strategy must not be empty")
        if len({question.question_id for question in questions}) != len(questions):
            raise SessionValidationError("question_id values must be unique")

        if track_id is not None:
            track = await self._storage.repositories.tracks.async_get(track_id)
            if track is None or str(track["profile_id"]) != profile_id:
                raise SessionValidationError("track does not belong to profile")

        if questions:
            if track_id is None:
                raise SessionValidationError("prepared questions require a track")
            enabled_rules = await self._storage.repositories.tracks.async_get_card_rules(track_id)
            enabled_cards = {
                str(rule["card_key"])
                for rule in enabled_rules
                if rule["card_key"] is not None and bool(rule["enabled"])
            }
            for question in questions:
                if question.card_key not in enabled_cards:
                    raise SessionValidationError(
                        f"card is not enabled in track: {question.card_key}"
                    )
                valid = await self._storage.async_validate_card_reference(
                    card_key=question.card_key,
                    learning_item_id=question.learning_item_id,
                    prompt_facet_id=question.prompt_facet_id,
                    answer_facet_id=question.answer_facet_id,
                )
                if not valid:
                    raise SessionValidationError(
                        f"unknown active card reference: {question.card_key}"
                    )

        active_generation = self._storage.content_generations.active_metadata.generation_id
        persisted_items: list[dict[str, Any]] = []
        for question in questions:
            item = question.as_storage_dict()
            payload = dict(item["payload"])
            payload["dataset_generation"] = active_generation
            item["payload"] = payload
            persisted_items.append(item)

        return await self._storage.async_create_session(
            uuid4().hex,
            profile_id,
            track_id,
            session_type=session_type,
            strategy=strategy,
            settings=settings,
            items=tuple(persisted_items),
        )

    async def async_get(self, session_id: str) -> dict[str, Any] | None:
        """Get the complete resumable session snapshot."""
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
            session_id,
            expected_version,
            question_id,
            answer,
        )
        self._publish(session_id, state)
        return state

    async def async_pause(
        self,
        session_id: str,
        expected_version: int,
    ) -> dict[str, Any]:
        """Pause one session using optimistic concurrency."""
        state = await self._storage.async_set_session_status(
            session_id,
            expected_version,
            status="paused",
        )
        self._publish(session_id, state)
        return state

    async def async_resume(
        self,
        session_id: str,
        expected_version: int,
    ) -> dict[str, Any]:
        """Resume one paused session using optimistic concurrency."""
        state = await self._storage.async_set_session_status(
            session_id,
            expected_version,
            status="active",
        )
        self._publish(session_id, state)
        return state

    async def async_complete(
        self,
        session_id: str,
        expected_version: int,
    ) -> dict[str, Any]:
        """Complete one session using optimistic concurrency."""
        state = await self._storage.async_set_session_status(
            session_id,
            expected_version,
            status="completed",
        )
        self._publish(session_id, state)
        return state

    async def async_undo(
        self,
        session_id: str,
        expected_version: int,
        *,
        actor_user_id: str | None = None,
    ) -> dict[str, Any]:
        """Undo only session navigation; P3.12 owns pedagogical progress undo."""
        state = await self._storage.async_undo_session_answer(
            session_id,
            expected_version,
            actor_user_id=actor_user_id,
        )
        self._publish(session_id, state)
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

    def _publish(self, session_id: str, state: dict[str, Any]) -> None:
        for listener in tuple(self._listeners.get(session_id, ())):
            listener(state)

    def close(self) -> None:
        """Detach all subscribers on integration unload."""
        self._listeners.clear()
