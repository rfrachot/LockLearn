"""Injectable clock boundary for persistent domain timestamps."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Provide the current aware UTC time."""

    def now(self) -> datetime:
        """Return the current time."""
        ...


class SystemClock:
    """Production UTC clock."""

    def now(self) -> datetime:
        """Return the current aware UTC time."""
        return datetime.now(UTC)
