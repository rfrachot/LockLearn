"""Persistent one-shot return reminders for Learn/Quiz readiness."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

from ..notifications.delivery import NotificationDeliveryService
from ..notifications.renderers import (
    PANEL_URI,
    NotificationRenderMode,
    RenderedNotification,
)
from .clock import Clock, SystemClock
from .session_selection import SessionSelectionError, SessionSelectionService

_LOGGER = logging.getLogger(__name__)
_KEY_PREFIX = "ready_reminder:"


class ReadyReminderError(ValueError):
    """Raised when a readiness reminder cannot be armed safely."""


class _Settings(Protocol):
    async def async_set(self, key: str, value: Any, *, updated_at_utc: str) -> None: ...
    async def async_get(self, key: str) -> Any | None: ...
    async def async_delete(self, key: str) -> bool: ...
    async def async_list_prefix(self, prefix: str) -> dict[str, Any]: ...


class _Profiles(Protocol):
    async def async_get(self, profile_id: str) -> dict[str, Any] | None: ...


class _Targets(Protocol):
    async def async_get(self, target_id: str) -> dict[str, Any] | None: ...
    async def async_list_for_profile(
        self, profile_id: str, *, enabled_only: bool = True
    ) -> tuple[dict[str, Any], ...]: ...


class ReadyReminderService:
    """Own idempotent profile+track+mode reminders and their one-shot timers."""

    def __init__(
        self,
        settings: _Settings,
        profiles: _Profiles,
        targets: _Targets,
        availability: SessionSelectionService,
        delivery: NotificationDeliveryService,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._settings = settings
        self._profiles = profiles
        self._targets = targets
        self._availability = availability
        self._delivery = delivery
        self._clock = clock or SystemClock()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._closed = False

    @staticmethod
    def _scope_key(profile_id: str, track_id: str, mode: str) -> str:
        digest = hashlib.sha256(f"{profile_id}|{track_id}|{mode}".encode()).hexdigest()[:24]
        return f"{_KEY_PREFIX}{digest}"

    async def async_start(self) -> None:
        """Restore pending reminders after Home Assistant reload/restart."""
        self._closed = False
        for key, raw in (await self._settings.async_list_prefix(_KEY_PREFIX)).items():
            if isinstance(raw, Mapping):
                self._schedule(key, dict(raw))

    async def async_status(
        self,
        *,
        profile_id: str,
        track_id: str,
        mode: str,
    ) -> dict[str, Any]:
        """Return reminder state without exposing device-registry identifiers."""
        normalized = self._validate_mode(mode)
        key = self._scope_key(profile_id, track_id, normalized)
        raw = await self._settings.async_get(key)
        targets = await self._targets.async_list_for_profile(profile_id, enabled_only=True)
        return {
            "active": isinstance(raw, Mapping),
            "mode": normalized,
            "scheduled_for_utc": (
                None if not isinstance(raw, Mapping) else raw.get("scheduled_for_utc")
            ),
            "target_available": bool(targets),
        }

    async def async_arm(
        self,
        *,
        profile_id: str,
        track_id: str,
        mode: str,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        """Create or replace exactly one readiness reminder for the scope."""
        normalized = self._validate_mode(mode)
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise ReadyReminderError("profile does not exist")
        availability = await self._availability.async_availability(
            profile_id=profile_id,
            track_id=track_id,
            session_type=normalized,
        )
        if int(availability["available_now"]) > 0:
            raise ReadyReminderError("the requested mode is already ready")
        scheduled_for = availability.get("next_available_at_utc")
        if not isinstance(scheduled_for, str):
            raise ReadyReminderError("no reliable next availability exists")

        target = await self._resolve_target(profile_id, target_id)
        now = self._clock.now().astimezone(UTC)
        scheduled = datetime.fromisoformat(scheduled_for).astimezone(UTC)
        if scheduled <= now:
            raise ReadyReminderError("next availability is not in the future")

        key = self._scope_key(profile_id, track_id, normalized)
        state = {
            "reminder_id": key.removeprefix(_KEY_PREFIX),
            "profile_id": profile_id,
            "track_id": track_id,
            "mode": normalized,
            "target_id": str(target["target_id"]),
            "scheduled_for_utc": scheduled.isoformat(),
            "armed_at_utc": now.isoformat(),
        }
        await self._settings.async_set(key, state, updated_at_utc=now.isoformat())
        self._schedule(key, state)
        return {
            "active": True,
            "mode": normalized,
            "scheduled_for_utc": state["scheduled_for_utc"],
            "target_available": True,
        }

    async def async_cancel(
        self,
        *,
        profile_id: str,
        track_id: str,
        mode: str,
    ) -> dict[str, Any]:
        """Cancel the unique reminder for the scope."""
        normalized = self._validate_mode(mode)
        key = self._scope_key(profile_id, track_id, normalized)
        task = self._tasks.pop(key, None)
        if task is not None:
            task.cancel()
        await self._settings.async_delete(key)
        return {
            "active": False,
            "mode": normalized,
            "scheduled_for_utc": None,
            "target_available": bool(
                await self._targets.async_list_for_profile(profile_id, enabled_only=True)
            ),
        }

    async def async_fire_due(self, key: str) -> str:
        """Revalidate a due reminder and send, move or cancel it."""
        raw = await self._settings.async_get(key)
        if not isinstance(raw, Mapping):
            return "missing"
        state = dict(raw)
        try:
            profile_id = str(state["profile_id"])
            track_id = str(state["track_id"])
            mode = self._validate_mode(str(state["mode"]))
            scheduled = datetime.fromisoformat(str(state["scheduled_for_utc"])).astimezone(UTC)
        except (KeyError, TypeError, ValueError) as err:
            await self._settings.async_delete(key)
            raise ReadyReminderError("persisted reminder is invalid") from err

        now = self._clock.now().astimezone(UTC)
        if scheduled > now:
            self._schedule(key, state)
            return "not_due"

        try:
            availability = await self._availability.async_availability(
                profile_id=profile_id,
                track_id=track_id,
                session_type=mode,
            )
        except SessionSelectionError:
            await self._settings.async_delete(key)
            return "cancelled"

        if int(availability["available_now"]) > 0:
            profile = await self._profiles.async_get(profile_id)
            target = await self._targets.async_get(str(state["target_id"]))
            if (
                profile is None
                or target is None
                or str(target["profile_id"]) != profile_id
                or not bool(target["enabled"])
            ):
                await self._settings.async_delete(key)
                return "cancelled"
            rendered = self._render_ready(
                profile=profile,
                target=target,
                mode=mode,
                key=key,
            )
            try:
                await self._delivery.async_send(rendered)
            except Exception:
                _LOGGER.exception("Ready reminder delivery failed")
                await self._settings.async_delete(key)
                return "delivery_failed"
            await self._settings.async_delete(key)
            return "sent"

        moved = availability.get("next_available_at_utc")
        if isinstance(moved, str):
            moved_at = datetime.fromisoformat(moved).astimezone(UTC)
            if moved_at > now:
                state["scheduled_for_utc"] = moved_at.isoformat()
                await self._settings.async_set(key, state, updated_at_utc=now.isoformat())
                self._schedule(key, state)
                return "rescheduled"

        await self._settings.async_delete(key)
        return "cancelled"

    async def _resolve_target(self, profile_id: str, target_id: str | None) -> dict[str, Any]:
        if target_id is not None:
            target = await self._targets.async_get(target_id)
            if (
                target is None
                or str(target["profile_id"]) != profile_id
                or not bool(target["enabled"])
            ):
                raise ReadyReminderError("notification target is unavailable")
            return target
        targets = await self._targets.async_list_for_profile(profile_id, enabled_only=True)
        if not targets:
            raise ReadyReminderError("no enabled notification target is configured")
        return targets[0]

    @staticmethod
    def _validate_mode(mode: str) -> str:
        normalized = mode.strip().lower()
        if normalized not in {"learn", "quiz"}:
            raise ReadyReminderError("reminder mode must be learn or quiz")
        return normalized

    @staticmethod
    def _render_ready(
        *,
        profile: dict[str, Any],
        target: dict[str, Any],
        mode: str,
        key: str,
    ) -> RenderedNotification:
        profile_name = str(profile.get("name") or "LockLearn")
        shared = bool(target.get("shared_device"))
        title = f"LockLearn · {profile_name}" if shared else "LockLearn"
        message = (
            "Une session d'apprentissage est prête." if mode == "learn" else "Un quiz est prêt."
        )
        return RenderedNotification(
            profile_id=str(profile["profile_id"]),
            target_id=str(target["target_id"]),
            tag=f"locklearn-ready-{key.removeprefix(_KEY_PREFIX)}",
            stage="ready",
            mode=NotificationRenderMode.PANEL_HANDOFF,
            title=title,
            message=message,
            data={
                "tag": f"locklearn-ready-{key.removeprefix(_KEY_PREFIX)}",
                "ttl": 3600,
                "visibility": str(target.get("lockscreen_visibility") or "private"),
                "actions": [{"action": "URI", "title": "Ouvrir LockLearn", "uri": PANEL_URI}],
            },
            pedagogical_signal="no_result",
            panel_required=True,
        )

    def _schedule(self, key: str, state: dict[str, Any]) -> None:
        old = self._tasks.pop(key, None)
        if old is not None:
            old.cancel()
        if self._closed:
            return
        try:
            due = datetime.fromisoformat(str(state["scheduled_for_utc"])).astimezone(UTC)
        except (KeyError, TypeError, ValueError):
            return
        delay = max(0.0, (due - self._clock.now().astimezone(UTC)).total_seconds())

        async def runner() -> None:
            try:
                await asyncio.sleep(delay)
                await self.async_fire_due(key)
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Ready reminder task failed")
            finally:
                current = self._tasks.get(key)
                if current is asyncio.current_task():
                    self._tasks.pop(key, None)

        self._tasks[key] = asyncio.create_task(
            runner(),
            name=f"locklearn-ready-reminder-{key.removeprefix(_KEY_PREFIX)}",
        )

    def close(self) -> None:
        """Cancel in-memory timers; persistent state remains for restart restore."""
        self._closed = True
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
