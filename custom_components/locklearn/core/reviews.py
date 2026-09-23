"""Canonical ReviewEvent recording and rebuildable progress projection."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..storage.repositories import (
    ProfilesRepository,
    ReviewEventRecord,
    ReviewEventsRepository,
)
from .clock import Clock, SystemClock
from .leeches import LEECH_WINDOW_DAYS_V1, LeechPolicyV1


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
        leech_policy: LeechPolicyV1 | None = None,
    ) -> None:
        self._events = events
        self._profiles = profiles
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._leech_policy = leech_policy or LeechPolicyV1()

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
        for field_name, text_value in (
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
            if not text_value.strip():
                raise ReviewEventValidationError(f"{field_name} must not be empty")
        if policy_version < 1:
            raise ReviewEventValidationError("policy_version must be >= 1")
        if normalization_version is not None and normalization_version < 1:
            raise ReviewEventValidationError("normalization_version must be >= 1")
        for field_name, latency_value in (
            ("presentation_to_answer_ms", presentation_to_answer_ms),
            ("delivery_to_action_ms", delivery_to_action_ms),
        ):
            if latency_value is not None and latency_value < 0:
                raise ReviewEventValidationError(f"{field_name} must be >= 0")
        for field_name, interval_value in (
            ("scheduled_interval_days", scheduled_interval_days),
            ("elapsed_days", elapsed_days),
        ):
            if interval_value is not None and interval_value < 0:
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

        current_for_leech = {
            "mode": mode,
            "result": result,
            "retrieval_occurred": retrieval_occurred,
            "signal_quality": signal_quality,
            "pre_state_snapshot": pre_state_snapshot,
            "post_state_snapshot": post_state_snapshot,
            "created_at_utc": now.isoformat(),
        }
        resolved_post_state = dict(post_state_snapshot)
        if self._leech_policy.is_trusted_verified(current_for_leech):
            history = await self._events.async_recent_verified_card_events(
                profile_id=profile_id,
                track_id=track_id,
                card_key=card_key,
                since_utc=(now - timedelta(days=LEECH_WINDOW_DAYS_V1)).isoformat(),
            )
            leech = self._leech_policy.evaluate(
                history,
                current=current_for_leech,
                now=now,
            )
        else:
            leech = None
        if leech is not None and leech.detected:
            resolved_post_state.update(
                {
                    "state": "leech",
                    "leech_score": max(
                        float(resolved_post_state.get("leech_score", 0.0)),
                        leech.score,
                    ),
                    "leech_policy_version": leech.policy_version,
                    "leech_reason": leech.reason,
                    "leech_recent_verified_attempts": leech.recent_verified_attempts,
                    "leech_recent_verified_failures": leech.recent_verified_failures,
                    "leech_verified_relapses_in_window": leech.verified_relapses_in_window,
                }
            )

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
            post_state_snapshot=resolved_post_state,
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
