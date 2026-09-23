"""P3.5 deterministic prerequisite, sibling, and confusable selection constraints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from .clock import Clock, SystemClock

DEFAULT_SIBLING_GAP_NEW_MINUTES = 1440
DEFAULT_SIBLING_GAP_REVIEW_MINUTES = 240


class SelectionRepository(Protocol):
    async def async_get(self, track_id: str) -> dict[str, Any] | None: ...

    async def async_selection_constraints(
        self,
        *,
        profile_id: str,
        track_id: str,
        pack_version_id: str,
        learning_item_id: str,
        card_key: str,
    ) -> dict[str, Any]: ...


class SelectionConstraintError(ValueError):
    """Raised when selection-constraint inputs or configuration are invalid."""


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    """Explain whether one CardDefinition may be selected now."""

    eligible: bool
    reasons: tuple[str, ...]
    blocked_until_utc: str | None = None


class SelectionConstraintService:
    """Evaluate P3.5 constraints without owning later session/scheduler ranking."""

    def __init__(
        self,
        tracks: SelectionRepository,
        *,
        clock: Clock | None = None,
        sibling_gap_new_minutes: int = DEFAULT_SIBLING_GAP_NEW_MINUTES,
        sibling_gap_review_minutes: int = DEFAULT_SIBLING_GAP_REVIEW_MINUTES,
    ) -> None:
        self._tracks = tracks
        self._clock = clock or SystemClock()
        self._default_new_gap = self._validate_gap(
            "sibling_gap_new_minutes",
            sibling_gap_new_minutes,
        )
        self._default_review_gap = self._validate_gap(
            "sibling_gap_review_minutes",
            sibling_gap_review_minutes,
        )

    async def async_evaluate(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        learning_item_id: str,
        state: str,
    ) -> SelectionDecision:
        """Evaluate prerequisites and spacing for one selected Track card."""
        if state not in {"new", "learning", "review", "relearning", "leech"}:
            raise SelectionConstraintError(f"unsupported progress state: {state}")

        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise SelectionConstraintError("track does not belong to profile")
        pack_version_id = track.get("pack_version_id")
        if not isinstance(pack_version_id, str) or not pack_version_id:
            raise SelectionConstraintError("track has no pinned PackVersion")

        context = await self._tracks.async_selection_constraints(
            profile_id=profile_id,
            track_id=track_id,
            pack_version_id=pack_version_id,
            learning_item_id=learning_item_id,
            card_key=card_key,
        )
        if not bool(context.get("selected", False)):
            raise SelectionConstraintError("card is not enabled in track selection")
        reasons: list[str] = []
        blocked_until: list[datetime] = []

        if state == "new":
            reasons.extend(self._prerequisite_failures(context))
            confusable_reasons, confusable_until = self._confusable_blocks(context)
            reasons.extend(confusable_reasons)
            blocked_until.extend(confusable_until)

        sibling_reason, sibling_until = self._sibling_block(
            context,
            state=state,
            settings=dict(track["settings"]),
        )
        if sibling_reason is not None:
            reasons.append(sibling_reason)
        if sibling_until is not None:
            blocked_until.append(sibling_until)

        latest = max(blocked_until) if blocked_until else None
        return SelectionDecision(
            eligible=not reasons,
            reasons=tuple(reasons),
            blocked_until_utc=None if latest is None else latest.isoformat(),
        )

    @staticmethod
    def confusable_distractors_allowed(state: str) -> bool:
        """Confusable distractors are reserved for stabilized long-review cards."""
        if state not in {"new", "learning", "review", "relearning", "leech"}:
            raise SelectionConstraintError(f"unsupported progress state: {state}")
        return state == "review"

    def _prerequisite_failures(self, context: dict[str, Any]) -> list[str]:
        prerequisite_keys = tuple(context["prerequisite_card_keys"])
        if not prerequisite_keys:
            return []
        progress_by_card = dict(context["prerequisite_progress"])
        conditions = tuple(context["unlock_conditions"])
        failures: list[str] = []
        for prerequisite_card_key in prerequisite_keys:
            progress = progress_by_card.get(prerequisite_card_key)
            if progress is None:
                failures.append(f"prerequisite_missing:{prerequisite_card_key}")
                continue
            if not conditions:
                if int(progress.get("seen_count", 0)) < 1:
                    failures.append(f"prerequisite_unseen:{prerequisite_card_key}")
                continue
            for condition in conditions:
                metric = str(condition["metric"])
                minimum = float(condition["minimum"])
                actual = self._metric_value(progress, metric)
                if actual < minimum:
                    failures.append(f"prerequisite_threshold:{prerequisite_card_key}:{metric}")
        return failures

    def _confusable_blocks(
        self,
        context: dict[str, Any],
    ) -> tuple[list[str], list[datetime]]:
        now = self._clock.now()
        reasons: list[str] = []
        blocked_until: list[datetime] = []
        for group in context["confusable_groups"]:
            last_raw = group["other_item_last_introduced_at_utc"]
            if last_raw is None:
                continue
            last = self._parse_timestamp(str(last_raw))
            gap_days = int(group["min_intro_gap_days"])
            until = last + timedelta(days=gap_days)
            if now < until:
                reasons.append(f"confusable_intro_gap:{group['confusable_group_id']}")
                blocked_until.append(until)
        return reasons, blocked_until

    def _sibling_block(
        self,
        context: dict[str, Any],
        *,
        state: str,
        settings: dict[str, Any],
    ) -> tuple[str | None, datetime | None]:
        if state not in {"new", "review", "leech"}:
            return None, None
        last_raw = context["sibling_last_interaction_at_utc"]
        if last_raw is None:
            return None, None

        if state == "new":
            minutes = self._configured_gap(
                settings,
                "sibling_gap_new_minutes",
                self._default_new_gap,
            )
        else:
            minutes = self._configured_gap(
                settings,
                "sibling_gap_review_minutes",
                self._default_review_gap,
            )
        until = self._parse_timestamp(str(last_raw)) + timedelta(minutes=minutes)
        if self._clock.now() >= until:
            return None, None
        return f"sibling_buried:{state}", until

    @staticmethod
    def _metric_value(progress: dict[str, Any], metric: str) -> float:
        if metric == "verified_correct_count":
            return float(progress["verified_correct_count"])
        if metric == "mastery":
            return float(progress["mastery"])
        if metric == "box":
            return float(progress["box"])
        raise SelectionConstraintError(f"unsupported unlock metric: {metric}")

    @classmethod
    def _configured_gap(
        cls,
        settings: dict[str, Any],
        key: str,
        default: int,
    ) -> int:
        raw = settings.get(key, default)
        if isinstance(raw, bool) or not isinstance(raw, int):
            raise SelectionConstraintError(f"{key} must be an integer")
        return cls._validate_gap(key, raw)

    @staticmethod
    def _validate_gap(name: str, value: int) -> int:
        if value < 0:
            raise SelectionConstraintError(f"{name} must be >= 0")
        return value

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise SelectionConstraintError("selection timestamps must be timezone-aware")
        return parsed
