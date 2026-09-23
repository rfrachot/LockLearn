"""P3.10 user-owned card state and initial calibration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from .clock import Clock, SystemClock


class ProgressUserStateError(ValueError):
    """Raised when a user-state or calibration request is invalid."""


class CardUserState(StrEnum):
    """User-owned state kept distinct from SRS and content lifecycle."""

    ACTIVE = "active"
    KNOWN_ALREADY = "known_already"
    SUSPENDED = "suspended"
    BURIED = "buried"


class UserStateTracksRepository(Protocol):
    async def async_get(self, track_id: str) -> dict[str, Any] | None: ...
    async def async_card_reference(self, *, track_id: str, card_key: str) -> Any | None: ...
    async def async_session_candidates(
        self, *, profile_id: str, track_id: str
    ) -> tuple[dict[str, Any], ...]: ...


class UserStateProgressRepository(Protocol):
    async def async_get(
        self, *, profile_id: str, track_id: str, card_key: str
    ) -> dict[str, Any] | None: ...

    async def async_set_user_state(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str,
        card: Any,
        user_state: str,
        suspend_until_utc: str | None,
        dataset_generation: str,
        updated_at_utc: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class CalibrationSample:
    """Deterministic read-only sample of still-new cards."""

    requested_size: int
    available_count: int
    cards: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested_size": self.requested_size,
            "available_count": self.available_count,
            "cards": [dict(card) for card in self.cards],
        }


class ProgressUserStateService:
    """Manage user-owned card state without fabricating learning evidence."""

    def __init__(
        self,
        tracks: UserStateTracksRepository,
        progress: UserStateProgressRepository,
        *,
        dataset_generation: Callable[[], str],
        clock: Clock | None = None,
    ) -> None:
        self._tracks = tracks
        self._progress = progress
        self._dataset_generation = dataset_generation
        self._clock = clock or SystemClock()

    async def async_set_user_state(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str,
        card_key: str,
        user_state: CardUserState | str,
        suspend_until_utc: str | None = None,
    ) -> dict[str, Any]:
        """Set one card's user-owned state without changing SRS counters."""
        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise ProgressUserStateError("track does not belong to profile")
        card = await self._tracks.async_card_reference(track_id=track_id, card_key=card_key)
        if card is None:
            raise ProgressUserStateError("card is not enabled in track")

        try:
            resolved_state = CardUserState(user_state)
        except ValueError as err:
            raise ProgressUserStateError("unsupported user_state") from err

        now = self._clock.now()
        normalized_until = self._validate_suspend_until(
            resolved_state,
            suspend_until_utc,
            now=now,
        )
        await self._progress.async_set_user_state(
            actor_user_id=actor_user_id,
            profile_id=profile_id,
            track_id=track_id,
            card=card,
            user_state=resolved_state.value,
            suspend_until_utc=normalized_until,
            dataset_generation=self._dataset_generation(),
            updated_at_utc=now.isoformat(),
        )
        snapshot = await self._progress.async_get(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
        )
        if snapshot is None:
            raise RuntimeError("user-state mutation did not materialize progress")
        result = dict(snapshot)
        result["effective_user_state"] = (
            CardUserState.ACTIVE.value
            if self.is_effectively_active(result, now=now)
            else str(result["user_state"])
        )
        return result

    async def async_calibration_sample(
        self,
        *,
        profile_id: str,
        track_id: str,
        sample_size: int = 30,
    ) -> CalibrationSample:
        """Return a deterministic spread of new cards without mutating progress."""
        if isinstance(sample_size, bool) or not isinstance(sample_size, int):
            raise ProgressUserStateError("sample_size must be an integer")
        if not 20 <= sample_size <= 40:
            raise ProgressUserStateError("sample_size must be within [20, 40]")

        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise ProgressUserStateError("track does not belong to profile")

        now = self._clock.now()
        rows = await self._tracks.async_session_candidates(
            profile_id=profile_id,
            track_id=track_id,
        )
        eligible = [
            row
            for row in rows
            if str(row["state"]) == "new" and self.is_effectively_active(row, now=now)
        ]
        available_count = len(eligible)
        if available_count <= sample_size:
            selected = eligible
        else:
            selected = [
                eligible[((2 * index + 1) * available_count) // (2 * sample_size)]
                for index in range(sample_size)
            ]

        cards = tuple(
            {
                "card_key": str(row["card_key"]),
                "learning_item_id": str(row["learning_item_id"]),
                "prompt_facet_id": str(row["prompt_facet_id"]),
                "answer_facet_id": str(row["answer_facet_id"]),
                "content_type": str(row["content_type"]),
                "pack_position": int(row["pack_position"]),
            }
            for row in selected
        )
        return CalibrationSample(
            requested_size=sample_size,
            available_count=available_count,
            cards=cards,
        )

    @staticmethod
    def is_effectively_active(row: dict[str, Any], *, now: datetime) -> bool:
        """Resolve timed burial without mutating the stored user-owned state."""
        state = str(row.get("user_state", CardUserState.ACTIVE.value))
        if state == CardUserState.ACTIVE.value:
            return True
        if state != CardUserState.BURIED.value:
            return False
        until_raw = row.get("suspend_until_utc")
        if until_raw is None:
            return False
        until = ProgressUserStateService._parse_timestamp(str(until_raw))
        return until <= now

    @classmethod
    def _validate_suspend_until(
        cls,
        state: CardUserState,
        value: str | None,
        *,
        now: datetime,
    ) -> str | None:
        if state is CardUserState.BURIED:
            if value is None:
                raise ProgressUserStateError("buried state requires suspend_until_utc")
            until = cls._parse_timestamp(value)
            if until <= now:
                raise ProgressUserStateError("suspend_until_utc must be in the future")
            return until.isoformat()
        if value is not None:
            raise ProgressUserStateError("suspend_until_utc is valid only for buried state")
        return None

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as err:
            raise ProgressUserStateError("suspend_until_utc must be an ISO timestamp") from err
        if parsed.tzinfo is None:
            raise ProgressUserStateError("suspend_until_utc must be timezone-aware")
        return parsed
