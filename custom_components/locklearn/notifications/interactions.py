"""Persistent notification interaction and replay-protection service."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from ..core.acl import ProfileACLService, ProfilePermission
from ..core.clock import Clock, SystemClock
from ..storage.repositories import (
    NotificationInteractionRecord,
    NotificationInteractionsRepository,
)


class NotificationInteractionValidationError(ValueError):
    """Raised when an interaction or action request is malformed."""


class NotificationStage(StrEnum):
    """Persistent notification protocol stages."""

    PROMPT = "prompt"
    REVEALED = "revealed"
    ANSWERED = "answered"


class NotificationActionDisposition(StrEnum):
    """Outcome of attempting to claim one notification action token."""

    CONSUMED = "consumed"
    EXPIRED = "expired"
    REPLAYED = "replayed"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True, slots=True)
class NotificationActionResult:
    """Safe claim result; only CONSUMED carries interaction state forward."""

    disposition: NotificationActionDisposition
    interaction: dict[str, Any] | None = None

    @property
    def may_apply_pedagogical_result(self) -> bool:
        """Return whether downstream code may mutate ReviewEvent/Progress."""
        return self.disposition is NotificationActionDisposition.CONSUMED


class NotificationInteractionService:
    """Issue opaque stage tokens and enforce single-use action consumption."""

    def __init__(
        self,
        repository: NotificationInteractionsRepository,
        acl: ProfileACLService,
        *,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._acl = acl
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._token_factory = token_factory or (lambda: secrets.token_urlsafe(32))

    @staticmethod
    def _require_text(field_name: str, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise NotificationInteractionValidationError(f"{field_name} must not be empty")
        return normalized

    @staticmethod
    def _utc_iso(field_name: str, value: datetime) -> str:
        if value.tzinfo is None or value.utcoffset() is None:
            raise NotificationInteractionValidationError(f"{field_name} must be timezone-aware")
        return value.astimezone(UTC).isoformat()

    async def async_create(
        self,
        *,
        profile_id: str,
        target_id: str,
        stage: NotificationStage | str,
        expires_at: datetime,
        tag: str | None = None,
        track_id: str | None = None,
        card_key: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> NotificationInteractionRecord:
        """Persist one fresh bearer token for one actionable notification stage."""
        now = self._clock.now()
        expires_at_utc = self._utc_iso("expires_at", expires_at)
        if expires_at.astimezone(UTC) <= now.astimezone(UTC):
            raise NotificationInteractionValidationError(
                "expires_at must be later than interaction creation"
            )
        try:
            resolved_stage = NotificationStage(stage)
        except ValueError as err:
            raise NotificationInteractionValidationError(
                "stage must be prompt, revealed, or answered"
            ) from err

        interaction = NotificationInteractionRecord(
            interaction_id=self._require_text("interaction_id", self._id_factory()),
            token=self._require_text("token", self._token_factory()),
            profile_id=self._require_text("profile_id", profile_id),
            target_id=self._require_text("target_id", target_id),
            track_id=None if track_id is None else self._require_text("track_id", track_id),
            card_key=None if card_key is None else self._require_text("card_key", card_key),
            stage=resolved_stage.value,
            tag=None if tag is None else self._require_text("tag", tag),
            created_at_utc=self._utc_iso("created_at", now),
            expires_at_utc=expires_at_utc,
            payload=dict(payload or {}),
        )
        await self._repository.async_insert(interaction)
        return interaction

    async def async_clear_tag(self, *, tag: str) -> dict[str, Any] | None:
        """Clear one pending visible notification without producing learning state."""
        resolved_tag = self._require_text("tag", tag)
        return await self._repository.async_clear_by_tag(
            tag=resolved_tag,
            cleared_at_utc=self._utc_iso("cleared_at", self._clock.now()),
        )

    async def async_consume_action(
        self,
        *,
        token: str,
        action_id: str,
        actor_user_id: str | None,
    ) -> NotificationActionResult:
        """Claim an action once; user context is ACL-checked whenever HA supplies it."""
        resolved_token = self._require_text("token", token)
        resolved_action = self._require_text("action_id", action_id)
        actor = (
            None if actor_user_id is None else self._require_text("actor_user_id", actor_user_id)
        )
        now_utc = self._utc_iso("action_at", self._clock.now())

        if actor is not None:
            interaction = await self._repository.async_get_by_token(resolved_token)
            if interaction is not None:
                allowed = await self._acl.async_can(
                    profile_id=str(interaction["profile_id"]),
                    ha_user_id=actor,
                    permission=ProfilePermission.ANSWER,
                )
                if not allowed:
                    await self._repository.async_audit_rejection(
                        token=resolved_token,
                        actor_user_id=actor,
                        reason="user_context_forbidden",
                        created_at_utc=now_utc,
                    )
                    return NotificationActionResult(NotificationActionDisposition.FORBIDDEN)

        claimed = await self._repository.async_consume(
            token=resolved_token,
            action_id=resolved_action,
            actor_user_id=actor,
            action_at_utc=now_utc,
        )
        disposition = NotificationActionDisposition(claimed.disposition)
        return NotificationActionResult(
            disposition,
            interaction=(
                claimed.interaction
                if disposition is NotificationActionDisposition.CONSUMED
                else None
            ),
        )
