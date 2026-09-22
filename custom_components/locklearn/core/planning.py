"""Learning quotas, goals, and deterministic load forecasts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from math import ceil
from typing import Any
from zoneinfo import ZoneInfo

from ..storage.repositories import ProfilesRepository, TracksRepository
from .clock import Clock, SystemClock

_BASE_REVIEW_OFFSETS_DAYS = (1, 3, 7, 14, 30, 60)


class LearningPlanValidationError(ValueError):
    """Raised when quotas or goals are invalid."""


@dataclass(frozen=True, slots=True)
class LearningPlan:
    """Track-level quotas and optional completion goal."""

    max_new_per_day_cards: int
    max_reviews_per_day_cards: int
    max_notification_new_teasers: int = 2
    target_date: date | None = None
    target_coverage: float = 1.0
    target_retention: float = 0.9

    def __post_init__(self) -> None:
        if self.max_new_per_day_cards < 0:
            raise LearningPlanValidationError("max_new_per_day_cards must be >= 0")
        if self.max_reviews_per_day_cards < 1:
            raise LearningPlanValidationError("max_reviews_per_day_cards must be >= 1")
        if self.max_notification_new_teasers < 0:
            raise LearningPlanValidationError("max_notification_new_teasers must be >= 0")
        if self.max_notification_new_teasers > self.max_new_per_day_cards:
            raise LearningPlanValidationError(
                "max_notification_new_teasers cannot exceed max_new_per_day_cards"
            )
        if not 0 < self.target_coverage <= 1:
            raise LearningPlanValidationError("target_coverage must be within (0, 1]")
        if not 0 < self.target_retention <= 1:
            raise LearningPlanValidationError("target_retention must be within (0, 1]")


@dataclass(frozen=True, slots=True)
class LoadForecast:
    """Explainable planning estimate for one Track."""

    selected_cards: int
    introduced_cards: int
    target_cards: int
    remaining_target_cards: int
    required_new_per_day: int
    planned_new_per_day: int
    reviews_per_day_in_3_weeks: int
    reviews_per_day_in_3_months: int
    due_now: int
    notification_deliverable_in_3_weeks: int
    active_session_cards_in_3_weeks: int
    notification_deliverable_in_3_months: int
    active_session_cards_in_3_months: int
    target_date_feasible: bool
    review_capacity_feasible_in_3_weeks: bool
    review_capacity_feasible_in_3_months: bool
    warnings: tuple[str, ...]
    assumptions: tuple[str, ...]


class LearningPlanService:
    """Persist quotas/goals and estimate their future card workload."""

    def __init__(
        self,
        tracks: TracksRepository,
        profiles: ProfilesRepository,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._tracks = tracks
        self._profiles = profiles
        self._clock = clock or SystemClock()

    async def async_set_plan_from_profile_defaults(
        self,
        *,
        track_id: str,
        max_reviews_per_day_cards: int,
        target_date: date | None = None,
        target_coverage: float = 1.0,
        target_retention: float = 0.9,
    ) -> LoadForecast:
        """Apply profile preset defaults while requiring an explicit review ceiling."""
        track = await self._tracks.async_get(track_id)
        if track is None:
            raise LearningPlanValidationError("track does not exist")
        profile = await self._profiles.async_get(str(track["profile_id"]))
        if profile is None:
            raise LearningPlanValidationError("track profile does not exist")
        max_new = int(profile["settings"].get("max_new_per_day_cards", 0))
        return await self.async_set_plan(
            track_id=track_id,
            plan=LearningPlan(
                max_new_per_day_cards=max_new,
                max_reviews_per_day_cards=max_reviews_per_day_cards,
                max_notification_new_teasers=min(2, max_new),
                target_date=target_date,
                target_coverage=target_coverage,
                target_retention=target_retention,
            ),
        )

    async def async_set_plan(
        self,
        *,
        track_id: str,
        plan: LearningPlan,
    ) -> LoadForecast:
        """Persist a Track plan and return its current deterministic forecast."""
        track = await self._tracks.async_get(track_id)
        if track is None:
            raise LearningPlanValidationError("track does not exist")
        profile = await self._profiles.async_get(str(track["profile_id"]))
        if profile is None:
            raise LearningPlanValidationError("track profile does not exist")

        self._validate_target_date(plan, str(profile["timezone"]))
        settings = dict(track["settings"])
        settings["learning_plan"] = {
            **asdict(plan),
            "target_date": None if plan.target_date is None else plan.target_date.isoformat(),
        }
        now = self._clock.now().isoformat()
        await self._tracks.async_update_settings(
            track_id=track_id,
            settings=settings,
            updated_at_utc=now,
        )
        return await self.async_forecast(track_id=track_id)

    async def async_forecast(self, *, track_id: str) -> LoadForecast:
        """Estimate future review load from V1 base intervals and configured quotas."""
        track = await self._tracks.async_get(track_id)
        if track is None:
            raise LearningPlanValidationError("track does not exist")
        profile = await self._profiles.async_get(str(track["profile_id"]))
        if profile is None:
            raise LearningPlanValidationError("track profile does not exist")

        plan = self._plan_from_track(track)
        self._validate_target_date(plan, str(profile["timezone"]))
        now = self._clock.now()
        snapshot = await self._tracks.async_planning_snapshot(
            track_id=track_id,
            now_utc=now.isoformat(),
        )
        selected_cards = snapshot["selected_cards"]
        introduced_cards = min(snapshot["introduced_cards"], selected_cards)
        target_cards = ceil(selected_cards * plan.target_coverage)
        remaining_target_cards = max(0, target_cards - introduced_cards)

        local_today = now.astimezone(ZoneInfo(str(profile["timezone"]))).date()
        if plan.target_date is None:
            required_new_per_day = min(plan.max_new_per_day_cards, remaining_target_cards)
            target_date_feasible = True
        else:
            days_remaining = max(1, (plan.target_date - local_today).days)
            required_new_per_day = ceil(remaining_target_cards / days_remaining)
            target_date_feasible = required_new_per_day <= plan.max_new_per_day_cards

        planned_new_per_day = min(
            plan.max_new_per_day_cards,
            remaining_target_cards,
        )
        reviews_21 = self._projected_review_load(
            remaining_target_cards=remaining_target_cards,
            max_new_per_day=plan.max_new_per_day_cards,
            horizon_days=21,
        )
        reviews_90 = self._projected_review_load(
            remaining_target_cards=remaining_target_cards,
            max_new_per_day=plan.max_new_per_day_cards,
            horizon_days=90,
        )
        daily_push_budget = int(profile["settings"].get("daily_push_budget", 0))
        new_21 = self._projected_new_load(
            remaining_target_cards=remaining_target_cards,
            max_new_per_day=plan.max_new_per_day_cards,
            horizon_days=21,
        )
        new_90 = self._projected_new_load(
            remaining_target_cards=remaining_target_cards,
            max_new_per_day=plan.max_new_per_day_cards,
            horizon_days=90,
        )
        notif_21, active_21 = self._delivery_split(
            new_cards=new_21,
            reviews=reviews_21,
            daily_push_budget=daily_push_budget,
            max_notification_new_teasers=plan.max_notification_new_teasers,
        )
        notif_90, active_90 = self._delivery_split(
            new_cards=new_90,
            reviews=reviews_90,
            daily_push_budget=daily_push_budget,
            max_notification_new_teasers=plan.max_notification_new_teasers,
        )
        warnings: list[str] = []
        if not target_date_feasible:
            warnings.append("target_date_requires_more_new_cards_than_daily_quota")
        if reviews_21 > plan.max_reviews_per_day_cards:
            warnings.append("review_load_exceeds_quota_in_3_weeks")
        if reviews_90 > plan.max_reviews_per_day_cards:
            warnings.append("review_load_exceeds_quota_in_3_months")
        if snapshot["due_now"] > plan.max_reviews_per_day_cards:
            warnings.append("current_due_backlog_exceeds_review_quota")

        return LoadForecast(
            selected_cards=selected_cards,
            introduced_cards=introduced_cards,
            target_cards=target_cards,
            remaining_target_cards=remaining_target_cards,
            required_new_per_day=required_new_per_day,
            planned_new_per_day=planned_new_per_day,
            reviews_per_day_in_3_weeks=reviews_21,
            reviews_per_day_in_3_months=reviews_90,
            due_now=snapshot["due_now"],
            notification_deliverable_in_3_weeks=notif_21,
            active_session_cards_in_3_weeks=active_21,
            notification_deliverable_in_3_months=notif_90,
            active_session_cards_in_3_months=active_90,
            target_date_feasible=target_date_feasible,
            review_capacity_feasible_in_3_weeks=reviews_21 <= plan.max_reviews_per_day_cards,
            review_capacity_feasible_in_3_months=reviews_90 <= plan.max_reviews_per_day_cards,
            warnings=tuple(warnings),
            assumptions=(
                "Forecast counts CardDefinitions, never LearningItems.",
                "Future reviews use the V1 base intervals 1/3/7/14/30/60 days.",
                "3-week and 3-month values are 7-day average daily loads ending at the horizon.",
                "The estimate assumes successful reviews and excludes future lapses/leeches.",
                "Existing due backlog is reported separately as due_now.",
            ),
        )

    def _plan_from_track(self, track: dict[str, Any]) -> LearningPlan:
        raw = track["settings"].get("learning_plan")
        if not isinstance(raw, dict):
            raise LearningPlanValidationError("track has no learning plan")
        raw_target_date = raw.get("target_date")
        target_date = None if raw_target_date is None else date.fromisoformat(str(raw_target_date))
        return LearningPlan(
            max_new_per_day_cards=int(raw["max_new_per_day_cards"]),
            max_reviews_per_day_cards=int(raw["max_reviews_per_day_cards"]),
            max_notification_new_teasers=int(raw.get("max_notification_new_teasers", 2)),
            target_date=target_date,
            target_coverage=float(raw.get("target_coverage", 1.0)),
            target_retention=float(raw.get("target_retention", 0.9)),
        )

    def _validate_target_date(self, plan: LearningPlan, timezone: str) -> None:
        if plan.target_date is None:
            return
        local_today = self._clock.now().astimezone(ZoneInfo(timezone)).date()
        if plan.target_date <= local_today:
            raise LearningPlanValidationError("target_date must be in the future")

    @staticmethod
    def _projected_new_load(
        *,
        remaining_target_cards: int,
        max_new_per_day: int,
        horizon_days: int,
    ) -> int:
        if remaining_target_cards == 0 or max_new_per_day == 0:
            return 0
        introduced_before_horizon = max_new_per_day * max(0, horizon_days - 1)
        remaining = max(0, remaining_target_cards - introduced_before_horizon)
        return min(max_new_per_day, remaining)

    @staticmethod
    def _projected_review_load(
        *,
        remaining_target_cards: int,
        max_new_per_day: int,
        horizon_days: int,
    ) -> int:
        if remaining_target_cards == 0 or max_new_per_day == 0:
            return 0
        introduced_by_day: dict[int, int] = {}
        remaining = remaining_target_cards
        for day_index in range(1, horizon_days + 1):
            introduced = min(max_new_per_day, remaining)
            introduced_by_day[day_index] = introduced
            remaining -= introduced
            if remaining == 0:
                break

        cumulative_offsets: list[int] = []
        elapsed = 0
        for interval in _BASE_REVIEW_OFFSETS_DAYS:
            elapsed += interval
            cumulative_offsets.append(elapsed)

        window_start = max(1, horizon_days - 6)
        window_reviews = 0
        for review_day in range(window_start, horizon_days + 1):
            window_reviews += sum(
                introduced_by_day.get(review_day - offset, 0)
                for offset in cumulative_offsets
                if review_day - offset >= 1
            )
        window_days = horizon_days - window_start + 1
        return ceil(window_reviews / window_days)

    @staticmethod
    def _delivery_split(
        *,
        new_cards: int,
        reviews: int,
        daily_push_budget: int,
        max_notification_new_teasers: int,
    ) -> tuple[int, int]:
        if daily_push_budget <= 0:
            return 0, new_cards + reviews
        notification_new = min(
            new_cards,
            max_notification_new_teasers,
            daily_push_budget,
        )
        remaining_push = max(0, daily_push_budget - notification_new)
        notification_reviews = min(reviews, remaining_push)
        delivered = notification_new + notification_reviews
        return delivered, max(0, new_cards + reviews - delivered)
