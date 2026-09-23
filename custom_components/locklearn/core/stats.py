"""P3.13 pedagogically honest statistics and metacognitive calibration."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from .clock import Clock, SystemClock
from .review_policy import ReviewPolicyV1

_VERIFIED_MODES = frozenset(
    {"verified_mcq", "verified_free_text", "verified_cloze", "exam_retrieval"}
)
_TRUSTED_QUALITIES = frozenset({"verified", "weak", "medium", "strong"})
_FAILURE_RESULTS = frozenset({"wrong", "idk"})
_SELF_KNOWN_RESULTS = frozenset({"correct", "known", "knew", "easy", "hard"})


class StatsServiceError(ValueError):
    """Raised when a statistics request is invalid."""


class StatsProfilesRepository(Protocol):
    async def async_get(self, profile_id: str) -> dict[str, Any] | None: ...


class StatsTracksRepository(Protocol):
    async def async_get(self, track_id: str) -> dict[str, Any] | None: ...
    async def async_list_for_profile(self, profile_id: str) -> tuple[dict[str, Any], ...]: ...
    async def async_session_candidates(
        self, *, profile_id: str, track_id: str
    ) -> tuple[dict[str, Any], ...]: ...


class StatsProgressRepository(Protocol):
    async def async_list_scope(
        self, *, profile_id: str, track_id: str | None = None
    ) -> tuple[dict[str, Any], ...]: ...


class StatsReviewRepository(Protocol):
    async def async_list_scope_events(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...
    async def async_undone_event_ids(
        self, *, profile_id: str | None = None
    ) -> frozenset[str]: ...
    async def async_stats_daily(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        since_local_date: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...
    async def async_progress_user_state_audit(
        self,
        *,
        profile_id: str,
        since_utc: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...
    async def async_confusions(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
        limit: int = 50,
    ) -> tuple[dict[str, Any], ...]: ...


class StatsService:
    """Build private dashboard statistics from canonical/rebuildable state."""

    def __init__(
        self,
        profiles: StatsProfilesRepository,
        tracks: StatsTracksRepository,
        progress: StatsProgressRepository,
        events: StatsReviewRepository,
        *,
        review_policy: ReviewPolicyV1,
        clock: Clock | None = None,
    ) -> None:
        self._profiles = profiles
        self._tracks = tracks
        self._progress = progress
        self._events = events
        self._review_policy = review_policy
        self._clock = clock or SystemClock()

    async def async_get(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        recent_verified_limit: int = 30,
        calibration_days: int = 7,
        confusion_limit: int = 10,
    ) -> dict[str, Any]:
        """Return the P3.13 dashboard backend payload."""
        if not 1 <= recent_verified_limit <= 200:
            raise StatsServiceError("recent_verified_limit must be within [1, 200]")
        if not 1 <= calibration_days <= 90:
            raise StatsServiceError("calibration_days must be within [1, 90]")
        if not 1 <= confusion_limit <= 100:
            raise StatsServiceError("confusion_limit must be within [1, 100]")

        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise StatsServiceError("profile does not exist")
        if track_id is not None:
            track = await self._tracks.async_get(track_id)
            if track is None or str(track["profile_id"]) != profile_id:
                raise StatsServiceError("track does not belong to profile")
            tracks = (track,)
        else:
            tracks = tuple(
                track
                for track in await self._tracks.async_list_for_profile(profile_id)
                if str(track["status"]) == "active"
            )

        now = self._clock.now()
        timezone_name = str(profile["timezone"])
        local_now = now.astimezone(ZoneInfo(timezone_name))
        settings = dict(profile["settings"])
        goal_fraction = self._setting_fraction(settings, "daily_due_goal_fraction", 0.8)
        goal_minimum = self._setting_int(settings, "daily_due_goal_min_cards", 1, minimum=0)
        grace_days = self._setting_int(settings, "streak_grace_days", 1, minimum=0)

        candidates: list[dict[str, Any]] = []
        for track in tracks:
            candidates.extend(
                await self._tracks.async_session_candidates(
                    profile_id=profile_id,
                    track_id=str(track["track_id"]),
                )
            )
        progress = await self._progress.async_list_scope(
            profile_id=profile_id,
            track_id=track_id,
        )
        events = await self._events.async_list_scope_events(
            profile_id=profile_id,
            track_id=track_id,
        )
        undone = await self._events.async_undone_event_ids(profile_id=profile_id)
        effective_events = tuple(
            event
            for event in events
            if str(event["id"]) not in undone and str(event["mode"]) != "undo_compensation"
        )
        verified = tuple(event for event in effective_events if self._trusted_verified(event))
        recent_verified = verified[-recent_verified_limit:]

        state_counts = {
            "new": 0,
            "learning": 0,
            "review": 0,
            "relearning": 0,
            "leech": 0,
        }
        tomorrow_local = local_now.date() + timedelta(days=1)
        due_deadline = datetime.combine(
            tomorrow_local,
            time.min,
            tzinfo=ZoneInfo(timezone_name),
        ).astimezone(UTC)
        due_today = 0
        for candidate in candidates:
            state = str(candidate["state"])
            if state in state_counts:
                state_counts[state] += 1
            if self._candidate_due(candidate, now=now, due_before=due_deadline):
                due_today += 1

        recent_correct = sum(str(event["result"]) == "correct" for event in recent_verified)
        latest_verified = verified[-1] if verified else None
        mastery_values = [
            self._review_policy.mastery(dict(snapshot), at=now)
            for snapshot in progress
            if str(snapshot["content_status"]) == "active"
            and self._effective_user_active(snapshot, now=now)
        ]
        mastery = None if not mastery_values else round(sum(mastery_values) / len(mastery_values), 6)

        calibration = await self._calibration(
            profile_id=profile_id,
            events=effective_events,
            timezone_name=timezone_name,
            local_today=local_now.date(),
            days=calibration_days,
        )
        daily = await self._events.async_stats_daily(
            profile_id=profile_id,
            track_id=track_id,
        )
        streak = self._streak(
            events=effective_events,
            daily=daily,
            local_today=local_now.date(),
            current_timezone=timezone_name,
            goal_fraction=goal_fraction,
            goal_minimum=goal_minimum,
            grace_days=grace_days,
        )
        confusions = await self._events.async_confusions(
            profile_id=profile_id,
            track_id=track_id,
            limit=confusion_limit,
        )

        return {
            "profile_id": profile_id,
            "track_id": track_id,
            "generated_at_utc": now.isoformat(),
            "local_date": local_now.date().isoformat(),
            "due_today": due_today,
            "states": state_counts,
            "latest_verified_retention": (
                None
                if latest_verified is None
                else {
                    "result": str(latest_verified["result"]),
                    "retained": str(latest_verified["result"]) == "correct",
                    "card_key": str(latest_verified["card_key"]),
                    "created_at_utc": str(latest_verified["created_at_utc"]),
                    "local_date": str(latest_verified["local_date"]),
                }
            ),
            "recent_verified_accuracy": {
                "correct": recent_correct,
                "total": len(recent_verified),
                "accuracy": (
                    None
                    if not recent_verified
                    else round(recent_correct / len(recent_verified), 6)
                ),
                "window_limit": recent_verified_limit,
            },
            "mastery": {
                "value": mastery,
                "card_count": len(mastery_values),
                "secondary_indicator": True,
            },
            "calibration": calibration,
            "streak": streak,
            "confusions": list(confusions),
            "daily": [dict(row) for row in daily],
        }

    async def _calibration(
        self,
        *,
        profile_id: str,
        events: tuple[dict[str, Any], ...],
        timezone_name: str,
        local_today: date,
        days: int,
    ) -> dict[str, Any]:
        zone = ZoneInfo(timezone_name)
        start_local = local_today - timedelta(days=days - 1)
        start_utc = datetime.combine(start_local, time.min, tzinfo=zone).astimezone(UTC)
        declarations: dict[str, datetime] = {}

        audits = await self._events.async_progress_user_state_audit(
            profile_id=profile_id,
            since_utc=start_utc.isoformat(),
        )
        for audit in audits:
            if str(audit.get("user_state")) != "known_already":
                continue
            card_key = audit.get("card_key")
            created = audit.get("created_at_utc")
            if not isinstance(card_key, str) or not isinstance(created, str):
                continue
            moment = self._parse_time(created)
            previous = declarations.get(card_key)
            if previous is None or moment < previous:
                declarations[card_key] = moment

        for event in events:
            if str(event["mode"]) != "self_assessment_after_retrieval":
                continue
            if str(event["result"]) not in _SELF_KNOWN_RESULTS:
                continue
            moment = self._parse_time(str(event["created_at_utc"]))
            if moment < start_utc:
                continue
            card_key = str(event["card_key"])
            previous = declarations.get(card_key)
            if previous is None or moment < previous:
                declarations[card_key] = moment

        verified_by_card: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            if self._trusted_verified(event):
                verified_by_card.setdefault(str(event["card_key"]), []).append(event)

        verified_later = 0
        later_correct = 0
        later_wrong = 0
        for card_key, declared_at in declarations.items():
            next_verified = next(
                (
                    event
                    for event in verified_by_card.get(card_key, [])
                    if self._parse_time(str(event["created_at_utc"])) > declared_at
                ),
                None,
            )
            if next_verified is None:
                continue
            verified_later += 1
            if str(next_verified["result"]) == "correct":
                later_correct += 1
            else:
                later_wrong += 1

        return {
            "window_days": days,
            "declared_known_cards": len(declarations),
            "later_verified_cards": verified_later,
            "later_verified_correct": later_correct,
            "later_verified_wrong": later_wrong,
            "later_verified_accuracy": (
                None if verified_later == 0 else round(later_correct / verified_later, 6)
            ),
            "awaiting_verified_followup": len(declarations) - verified_later,
        }

    def _streak(
        self,
        *,
        events: tuple[dict[str, Any], ...],
        daily: tuple[dict[str, Any], ...],
        local_today: date,
        current_timezone: str,
        goal_fraction: float,
        goal_minimum: int,
        grace_days: int,
    ) -> dict[str, Any]:
        if not events:
            return {
                "days": 0,
                "grace_days": grace_days,
                "grace_days_used": 0,
                "goal_fraction": goal_fraction,
                "goal_minimum_cards": goal_minimum,
                "today": {
                    "due_opening": 0,
                    "treated_due": 0,
                    "target": 0,
                    "status": "neutral",
                },
            }

        first_date = min(self._event_local_date(event) for event in events)
        timezone_by_date = {
            date.fromisoformat(str(row["local_date"])): str(row["timezone_name"])
            for row in daily
        }
        event_timezone_by_date = {
            self._event_local_date(event): str(event["timezone_name"]) for event in events
        }
        timezone_by_date.update(event_timezone_by_date)

        histories: dict[tuple[str, str], list[dict[str, Any]]] = {}
        events_by_date: dict[date, list[dict[str, Any]]] = {}
        for event in events:
            histories.setdefault(
                (str(event["track_id"]), str(event["card_key"])),
                [],
            ).append(event)
            events_by_date.setdefault(self._event_local_date(event), []).append(event)

        statuses: dict[date, dict[str, Any]] = {}
        day = first_date
        last_timezone = current_timezone
        while day <= local_today:
            last_timezone = timezone_by_date.get(day, last_timezone)
            zone = ZoneInfo(last_timezone)
            start = datetime.combine(day, time.min, tzinfo=zone).astimezone(UTC)
            end = datetime.combine(
                day + timedelta(days=1),
                time.min,
                tzinfo=zone,
            ).astimezone(UTC)
            due_keys: set[tuple[str, str]] = set()
            for key, history in histories.items():
                snapshot = self._snapshot_before(history, start)
                if snapshot is not None and self._snapshot_due(
                    snapshot,
                    active_at=start,
                    due_before=end,
                ):
                    due_keys.add(key)
            treated = {
                (str(event["track_id"]), str(event["card_key"]))
                for event in events_by_date.get(day, [])
                if (str(event["track_id"]), str(event["card_key"])) in due_keys
                and str(event["mode"]) not in {"undo_compensation", "leech_reactivation"}
            }
            due_count = len(due_keys)
            target = 0 if due_count == 0 else min(
                due_count,
                max(goal_minimum, math.ceil(due_count * goal_fraction)),
            )
            status = (
                "neutral"
                if due_count == 0
                else "success"
                if len(treated) >= target
                else "missed"
            )
            statuses[day] = {
                "due_opening": due_count,
                "treated_due": len(treated),
                "target": target,
                "status": status,
                "timezone_name": last_timezone,
            }
            day += timedelta(days=1)

        streak = 0
        grace_used = 0
        remaining_grace = grace_days
        day = local_today
        while day >= first_date:
            status = statuses[day]["status"]
            if status == "neutral":
                day -= timedelta(days=1)
                continue
            if status == "success":
                streak += 1
                day -= timedelta(days=1)
                continue
            if remaining_grace > 0:
                remaining_grace -= 1
                grace_used += 1
                day -= timedelta(days=1)
                continue
            break

        return {
            "days": streak,
            "grace_days": grace_days,
            "grace_days_used": grace_used,
            "goal_fraction": goal_fraction,
            "goal_minimum_cards": goal_minimum,
            "today": statuses.get(
                local_today,
                {
                    "due_opening": 0,
                    "treated_due": 0,
                    "target": 0,
                    "status": "neutral",
                    "timezone_name": current_timezone,
                },
            ),
        }

    @staticmethod
    def _snapshot_before(
        history: Sequence[dict[str, Any]],
        moment: datetime,
    ) -> dict[str, Any] | None:
        latest: dict[str, Any] | None = None
        for event in history:
            event_time = StatsService._parse_time(str(event["created_at_utc"]))
            if event_time < moment:
                latest = dict(event["post_state_snapshot"])
                continue
            pre = dict(event["pre_state_snapshot"])
            first_seen = pre.get("first_seen_at_utc")
            if latest is None and isinstance(first_seen, str) and first_seen:
                if StatsService._parse_time(first_seen) < moment:
                    latest = pre
            break
        return latest

    @staticmethod
    def _snapshot_due(
        snapshot: dict[str, Any],
        *,
        active_at: datetime,
        due_before: datetime,
    ) -> bool:
        if str(snapshot.get("state")) not in {"learning", "review", "relearning", "leech"}:
            return False
        if str(snapshot.get("content_status", "active")) != "active":
            return False
        if not StatsService._effective_user_active(snapshot, now=active_at):
            return False
        due = snapshot.get("next_due_at_utc")
        if not isinstance(due, str) or not due:
            return False
        return StatsService._parse_time(due) < due_before

    @staticmethod
    def _candidate_due(
        candidate: dict[str, Any],
        *,
        now: datetime,
        due_before: datetime,
    ) -> bool:
        if str(candidate.get("state")) not in {"learning", "review", "relearning", "leech"}:
            return False
        if not StatsService._effective_user_active(candidate, now=now):
            return False
        due = candidate.get("next_due_at_utc")
        if not isinstance(due, str) or not due:
            return False
        return StatsService._parse_time(due) < due_before

    @staticmethod
    def _effective_user_active(row: dict[str, Any], *, now: datetime) -> bool:
        state = str(row.get("user_state", "active"))
        if state == "active":
            return True
        if state != "buried":
            return False
        until = row.get("suspend_until_utc")
        return isinstance(until, str) and bool(until) and StatsService._parse_time(until) <= now

    @staticmethod
    def _trusted_verified(event: dict[str, Any]) -> bool:
        return (
            bool(event.get("retrieval_occurred"))
            and str(event.get("mode")) in _VERIFIED_MODES
            and str(event.get("signal_quality")) in _TRUSTED_QUALITIES
            and str(event.get("result")) in {"correct", "wrong", "idk"}
        )

    @staticmethod
    def _event_local_date(event: dict[str, Any]) -> date:
        return date.fromisoformat(str(event["local_date"]))

    @staticmethod
    def _parse_time(raw: str) -> datetime:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            raise StatsServiceError("statistics timestamp must be timezone-aware")
        return parsed

    @staticmethod
    def _setting_fraction(settings: dict[str, Any], key: str, default: float) -> float:
        raw = settings.get(key, default)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return default
        value = float(raw)
        return value if 0 < value <= 1 else default

    @staticmethod
    def _setting_int(
        settings: dict[str, Any],
        key: str,
        default: int,
        *,
        minimum: int,
    ) -> int:
        raw = settings.get(key, default)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < minimum:
            return default
        return raw
