"""Canonical ReviewEvent recording and rebuildable progress projection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..storage.repositories import (
    ProfilesRepository,
    ReviewEventRecord,
    ReviewEventsRepository,
)
from .clock import Clock, SystemClock


class ReviewEventValidationError(ValueError):
    """Raised when canonical review-event input is invalid."""


class ReviewEventService:
    """Record immutable audit events and materialize their progress post-state."""

    def __init__(
        self,
        events: ReviewEventsRepository,
        profiles: ProfilesRepository,
        *,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._events = events
        self._profiles = profiles
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))

    async def async_record(
        self,
        *,
        profile_id: str,
        track_id: str,
        learning_item_id: str,
        prompt_facet_id: str,
        answer_facet_id: str,
        card_key: str,
        mode: str,
        question_type: str,
        result: str,
        signal_quality: str,
        policy_version: int,
        dataset_generation: str,
        pre_state_snapshot: dict[str, Any],
        post_state_snapshot: dict[str, Any],
        hint_used: bool = False,
        retrieval_occurred: bool = False,
        answer_id: str | None = None,
        expected_answer_id: str | None = None,
        scheduled_interval_days: float | None = None,
        elapsed_days: float | None = None,
        grading_result: str | None = None,
        normalization_version: int | None = None,
        presentation_to_answer_ms: int | None = None,
        delivery_to_action_ms: int | None = None,
        session_id: str | None = None,
        notification_id: str | None = None,
    ) -> ReviewEventRecord:
        """Append one audit event with explicit cognitive and delivery latencies."""
        for field_name, value in (
            ("profile_id", profile_id),
            ("track_id", track_id),
            ("learning_item_id", learning_item_id),
            ("prompt_facet_id", prompt_facet_id),
            ("answer_facet_id", answer_facet_id),
            ("card_key", card_key),
            ("mode", mode),
            ("question_type", question_type),
            ("result", result),
            ("signal_quality", signal_quality),
            ("dataset_generation", dataset_generation),
        ):
            if not value.strip():
                raise ReviewEventValidationError(f"{field_name} must not be empty")
        if policy_version < 1:
            raise ReviewEventValidationError("policy_version must be >= 1")
        if normalization_version is not None and normalization_version < 1:
            raise ReviewEventValidationError("normalization_version must be >= 1")
        for field_name, value in (
            ("presentation_to_answer_ms", presentation_to_answer_ms),
            ("delivery_to_action_ms", delivery_to_action_ms),
        ):
            if value is not None and value < 0:
                raise ReviewEventValidationError(f"{field_name} must be >= 0")
        for field_name, value in (
            ("scheduled_interval_days", scheduled_interval_days),
            ("elapsed_days", elapsed_days),
        ):
            if value is not None and value < 0:
                raise ReviewEventValidationError(f"{field_name} must be >= 0")

        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise ReviewEventValidationError("profile does not exist")
        timezone_name = str(profile["timezone"])
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as err:
            raise ReviewEventValidationError("profile timezone is invalid") from err

        now = self._clock.now()
        local = now.astimezone(timezone)
        offset = local.utcoffset()
        utc_offset_minutes = 0 if offset is None else int(offset.total_seconds() // 60)

        event = ReviewEventRecord(
            id=self._id_factory(),
            profile_id=profile_id,
            track_id=track_id,
            learning_item_id=learning_item_id,
            prompt_facet_id=prompt_facet_id,
            answer_facet_id=answer_facet_id,
            card_key=card_key,
            mode=mode,
            question_type=question_type,
            result=result,
            answer_id=answer_id,
            expected_answer_id=expected_answer_id,
            hint_used=hint_used,
            retrieval_occurred=retrieval_occurred,
            scheduled_interval_days=scheduled_interval_days,
            elapsed_days=elapsed_days,
            grading_result=grading_result,
            signal_quality=signal_quality,
            policy_version=policy_version,
            dataset_generation=dataset_generation,
            normalization_version=normalization_version,
            pre_state_snapshot=pre_state_snapshot,
            post_state_snapshot=post_state_snapshot,
            presentation_to_answer_ms=presentation_to_answer_ms,
            delivery_to_action_ms=delivery_to_action_ms,
            session_id=session_id,
            notification_id=notification_id,
            created_at_utc=now.isoformat(),
            local_date=local.date().isoformat(),
            timezone_name=timezone_name,
            utc_offset_minutes=utc_offset_minutes,
        )
        await self._events.async_append_with_projection(event)
        return event

    async def async_rebuild_progress(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int:
        """Rebuild the progress materialization from immutable event snapshots."""
        return await self._events.async_rebuild_progress(
            profile_id=profile_id,
            track_id=track_id,
        )
