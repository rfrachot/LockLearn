"""P5.2 Home dashboard aggregation over canonical backend state."""

from __future__ import annotations

from collections.abc import Protocol
from typing import Any

from .clock import Clock, SystemClock
from .stats import StatsService


class DashboardProfilesRepository(Protocol):
    async def async_get(self, profile_id: str) -> dict[str, Any] | None: ...


class DashboardTracksRepository(Protocol):
    async def async_list_for_profile(self, profile_id: str) -> tuple[dict[str, Any], ...]: ...


class DashboardSchedulerRepository(Protocol):
    async def async_next_slot(
        self,
        *,
        profile_id: str,
        track_id: str,
        after_utc: str,
    ) -> dict[str, Any] | None: ...


class DashboardStorage(Protocol):
    async def async_latest_session_summary(
        self,
        *,
        profile_id: str,
        track_id: str,
    ) -> dict[str, Any] | None: ...


class DashboardServiceError(ValueError):
    """Raised when a dashboard scope is invalid."""


class DashboardService:
    """Build the P5.2 Home payload without duplicating pedagogical calculations."""

    def __init__(
        self,
        profiles: DashboardProfilesRepository,
        tracks: DashboardTracksRepository,
        scheduler: DashboardSchedulerRepository,
        storage: DashboardStorage,
        stats: StatsService,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._profiles = profiles
        self._tracks = tracks
        self._scheduler = scheduler
        self._storage = storage
        self._stats = stats
        self._clock = clock or SystemClock()

    async def async_get(self, *, profile_id: str) -> dict[str, Any]:
        """Return one Profile Home dashboard using only canonical backend sources."""
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise DashboardServiceError("profile does not exist")

        now = self._clock.now()
        track_rows = tuple(
            track
            for track in await self._tracks.async_list_for_profile(profile_id)
            if str(track["status"]) == "active"
        )
        cards: list[dict[str, Any]] = []
        for track in track_rows:
            track_id = str(track["track_id"])
            stats = await self._stats.async_get(
                profile_id=profile_id,
                track_id=track_id,
            )
            last_session = await self._storage.async_latest_session_summary(
                profile_id=profile_id,
                track_id=track_id,
            )
            next_slot = await self._scheduler.async_next_slot(
                profile_id=profile_id,
                track_id=track_id,
                after_utc=now.isoformat(),
            )
            retention = stats["latest_verified_retention"]
            accuracy = stats["recent_verified_accuracy"]
            cards.append(
                {
                    "track_id": track_id,
                    "name": str(track["name"]),
                    "source_language": str(track["source_language"]),
                    "target_language": str(track["target_language"]),
                    "due_today": int(stats["due_today"]),
                    "recent_verified_retention": (
                        None
                        if retention is None
                        else {
                            "retained": bool(retention["retained"]),
                            "created_at_utc": str(retention["created_at_utc"]),
                        }
                    ),
                    "recent_verified_accuracy": {
                        "correct": int(accuracy["correct"]),
                        "total": int(accuracy["total"]),
                        "accuracy": accuracy["accuracy"],
                    },
                    "states": dict(stats["states"]),
                    "last_session": (
                        None
                        if last_session is None
                        else {
                            "session_id": str(last_session["session_id"]),
                            "session_type": str(last_session["session_type"]),
                            "status": str(last_session["status"]),
                            "question_count": int(last_session["question_count"]),
                            "answered_count": int(last_session["answered_count"]),
                            "started_at_utc": str(last_session["started_at_utc"]),
                            "last_activity_at_utc": str(last_session["last_activity_at_utc"]),
                            "completed_at_utc": last_session["completed_at_utc"],
                        }
                    ),
                    "next_notification": (
                        None
                        if next_slot is None
                        else {
                            "slot_type": str(next_slot["slot_type"]),
                            "status": str(next_slot["status"]),
                            "effective_for_utc": str(next_slot["effective_for_utc"]),
                        }
                    ),
                }
            )

        return {
            "profile": {
                "profile_id": profile_id,
                "name": str(profile["name"]),
                "preset": str(profile["preset"]),
                "timezone": str(profile["timezone"]),
            },
            "generated_at_utc": now.isoformat(),
            "tracks": cards,
        }
