"""Dashboard warning surface for unrecorded mobile notification responses."""

from __future__ import annotations

from datetime import UTC, timedelta

from ..core.clock import Clock, SystemClock
from ..storage.repositories import NotificationWarningsRepository


class NotificationWarningService:
    """Expose recent failed mobile confirmations without learned content."""

    def __init__(
        self,
        repository: NotificationWarningsRepository,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or SystemClock()

    async def async_recent_unrecorded(
        self,
        *,
        profile_id: str,
        lookback_hours: int = 168,
        limit: int = 20,
    ) -> dict[str, object]:
        """Return a bounded private dashboard warning summary."""
        if lookback_hours < 1 or lookback_hours > 24 * 30:
            raise ValueError("lookback_hours must be within 1..720")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be within 1..100")
        now = self._clock.now().astimezone(UTC)
        since = now - timedelta(hours=lookback_hours)
        items = await self._repository.async_recent_unrecorded_mobile_responses(
            profile_id=profile_id,
            since_utc=since.isoformat(),
            limit=limit,
        )
        return {
            "profile_id": profile_id,
            "warning": bool(items),
            "message_key": ("recent_unrecorded_mobile_responses" if items else None),
            "count": len(items),
            "items": list(items),
            "since_utc": since.isoformat(),
        }
