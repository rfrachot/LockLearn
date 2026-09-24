"""Deterministic materialized scheduler for profile-level notification slots."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..storage.repositories import (
    NotificationTargetsRepository,
    ProfilesRepository,
    SchedulerRepository,
    SettingsRepository,
    TracksRepository,
)
from .clock import Clock, SystemClock
from .notification_selection import (
    NotificationSelectionError,
    NotificationSelectionService,
)

_DEFAULT_ACTIVE_DAYS = tuple(range(7))
_DEFAULT_ACTIVE_WINDOWS = (("08:00", "20:00"),)
_DEFAULT_MINIMUM_GAP_SECONDS = 3600
_DEFAULT_MAXIMUM_NOTIFICATIONS_PER_HOUR = 1
_DEFAULT_QUIET_HOURS = ("22:00", "08:00")
_SCHEDULER_TIME_STATE_KEY = "scheduler_time_state_v1"
_CAPACITY_STATE_PREFIX = "scheduler_capacity_state_v1:"
_CAPACITY_REPAIR_DAYS = 3
_ROUTINE_SLOT_TYPES = frozenset({"pre_sleep_consolidation", "morning_first_review"})


class SchedulerValidationError(ValueError):
    """Raised when profile scheduler configuration is invalid."""


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    """Normalized profile-level scheduler configuration."""

    profile_id: str
    version: int
    timezone: str
    active_days: tuple[int, ...]
    active_windows: tuple[tuple[str, str], ...]
    minimum_gap_seconds: int
    maximum_notifications_per_hour: int
    quiet_hours: tuple[str, str]
    receptive_when: str | None = None
    defer_window_minutes: int = 0


@dataclass(frozen=True, slots=True)
class SchedulerSlotDraft:
    """One deterministic generic notification slot before persistence."""

    slot_id: str
    profile_id: str
    slot_type: str
    scheduled_for_utc: str
    scheduler_config_version: int
    seed: str
    track_id: str | None = None
    target_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return the storage/API representation without pedagogical content."""
        return {
            "slot_id": self.slot_id,
            "profile_id": self.profile_id,
            "track_id": self.track_id,
            "target_id": self.target_id,
            "slot_type": self.slot_type,
            "scheduled_for_utc": self.scheduled_for_utc,
            "scheduler_config_version": self.scheduler_config_version,
            "seed": self.seed,
        }


@dataclass(frozen=True, slots=True)
class SchedulerReconciliation:
    """Clock high-watermark used to make restart/jump handling monotonic."""

    observed_now_utc: datetime
    effective_now_utc: datetime
    previous_high_watermark_utc: datetime | None
    expired_slots: int
    kind: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable reconciliation diagnostic."""
        return {
            "observed_now_utc": self.observed_now_utc.isoformat(),
            "effective_now_utc": self.effective_now_utc.isoformat(),
            "previous_high_watermark_utc": (
                None
                if self.previous_high_watermark_utc is None
                else self.previous_high_watermark_utc.isoformat()
            ),
            "expired_slots": self.expired_slots,
            "kind": self.kind,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class TrackDemand:
    """One Track's requested scheduler work for a local day."""

    track_id: str
    priority: int
    learning_count: int
    quiz_count: int
    target_ids: tuple[str, ...]

    @property
    def total(self) -> int:
        return self.learning_count + self.quiz_count


@dataclass(frozen=True, slots=True)
class SchedulerAllocation:
    """One Track/target/type assignment for a concrete future slot."""

    track_id: str
    target_id: str
    slot_type: str


def _parse_hhmm(value: Any, field: str) -> time:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise SchedulerValidationError(f"{field} must use HH:MM")
    try:
        parsed = time.fromisoformat(value)
    except ValueError as err:
        raise SchedulerValidationError(f"{field} must use HH:MM") from err
    if parsed.second or parsed.microsecond:
        raise SchedulerValidationError(f"{field} must use minute precision")
    return parsed


def _normalize_active_days(raw: Any) -> tuple[int, ...]:
    if raw is None:
        return _DEFAULT_ACTIVE_DAYS
    if not isinstance(raw, (list, tuple)):
        raise SchedulerValidationError("active_days must be a list of weekday integers")
    days: list[int] = []
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 6:
            raise SchedulerValidationError("active_days entries must be integers from 0 to 6")
        if value not in days:
            days.append(value)
    return tuple(sorted(days))


def _normalize_active_windows(raw: Any) -> tuple[tuple[str, str], ...]:
    if raw is None:
        return _DEFAULT_ACTIVE_WINDOWS
    if not isinstance(raw, (list, tuple)):
        raise SchedulerValidationError("active_windows must be a list")
    windows: list[tuple[str, str]] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise SchedulerValidationError(f"active_windows[{index}] must be an object")
        start_value = entry.get("start")
        end_value = entry.get("end")
        start = _parse_hhmm(start_value, f"active_windows[{index}].start")
        end = _parse_hhmm(end_value, f"active_windows[{index}].end")
        if start == end:
            raise SchedulerValidationError("active window start and end must differ")
        window = (str(start_value), str(end_value))
        if window not in windows:
            windows.append(window)
    return tuple(sorted(windows))


def _normalize_quiet_hours(raw: Any) -> tuple[str, str]:
    if raw is None:
        return _DEFAULT_QUIET_HOURS
    if not isinstance(raw, Mapping):
        raise SchedulerValidationError("quiet_hours must be an object")
    start_value = raw.get("start")
    end_value = raw.get("end")
    _parse_hhmm(start_value, "quiet_hours.start")
    _parse_hhmm(end_value, "quiet_hours.end")
    return str(start_value), str(end_value)


def _semantic_config(config: SchedulerConfig) -> tuple[Any, ...]:
    return (
        config.timezone,
        config.active_days,
        config.active_windows,
        config.minimum_gap_seconds,
        config.maximum_notifications_per_hour,
        config.quiet_hours,
        config.receptive_when,
        config.defer_window_minutes,
    )


def _persisted_semantics(config: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(config["timezone"]),
        tuple(int(day) for day in config["active_days"]),
        tuple((str(window["start"]), str(window["end"])) for window in config["active_windows"]),
        int(config["minimum_gap_seconds"]),
        int(config["maximum_notifications_per_hour"]),
        (
            str(config["quiet_hours"]["start"]),
            str(config["quiet_hours"]["end"]),
        ),
        None if config["receptive_when"] is None else str(config["receptive_when"]),
        int(config["defer_window_minutes"]),
    )


def _active_at_local_minute(config: SchedulerConfig, local_naive: datetime) -> bool:
    local_date = local_naive.date()
    local_time = local_naive.time()
    for start_value, end_value in config.active_windows:
        start = _parse_hhmm(start_value, "active_window.start")
        end = _parse_hhmm(end_value, "active_window.end")
        if start < end:
            if local_date.weekday() in config.active_days and start <= local_time < end:
                return True
            continue
        if local_time >= start:
            window_start_date = local_date
        elif local_time < end:
            window_start_date = local_date - timedelta(days=1)
        else:
            continue
        if window_start_date.weekday() in config.active_days:
            return True
    return False


def _quiet_at_local_minute(config: SchedulerConfig, local_naive: datetime) -> bool:
    local_time = local_naive.time()
    start = _parse_hhmm(config.quiet_hours[0], "quiet_hours.start")
    end = _parse_hhmm(config.quiet_hours[1], "quiet_hours.end")
    if start == end:
        return False
    if start < end:
        return start <= local_time < end
    return local_time >= start or local_time < end


def _resolve_local_minute(local_naive: datetime, timezone: ZoneInfo) -> tuple[datetime, ...]:
    """Map one wall-clock minute to zero, one, or two real UTC instants.

    A spring-forward minute has no round-tripping representation and is skipped.
    A fall-back minute has two valid folds and both are returned; downstream
    local-hour capacity applies across both folds, preventing duplicate floods.
    """
    resolved: list[datetime] = []
    for fold in (0, 1):
        aware = local_naive.replace(tzinfo=timezone, fold=fold)
        candidate = aware.astimezone(UTC)
        round_trip = candidate.astimezone(timezone)
        if round_trip.replace(tzinfo=None) != local_naive or round_trip.fold != fold:
            continue
        if candidate not in resolved:
            resolved.append(candidate)
    return tuple(sorted(resolved))


def _minute_candidates(
    config: SchedulerConfig,
    local_date: date,
    *,
    not_before_utc: datetime | None,
) -> tuple[datetime, ...]:
    timezone = ZoneInfo(config.timezone)
    local_midnight = datetime.combine(local_date, time.min)
    candidates: list[datetime] = []
    for minute_offset in range(24 * 60):
        local_naive = local_midnight + timedelta(minutes=minute_offset)
        if not _active_at_local_minute(config, local_naive):
            continue
        if _quiet_at_local_minute(config, local_naive):
            continue
        for candidate in _resolve_local_minute(local_naive, timezone):
            if not_before_utc is None or candidate >= not_before_utc:
                candidates.append(candidate)
    return tuple(sorted(dict.fromkeys(candidates)))


def _hour_bucket(candidate_utc: datetime, timezone: ZoneInfo) -> tuple[date, int]:
    local = candidate_utc.astimezone(timezone)
    return local.date(), local.hour


def _valid_after(
    candidate: datetime,
    selected: list[datetime],
    *,
    occupied: tuple[datetime, ...],
    timezone: ZoneInfo,
    minimum_gap_seconds: int,
    maximum_notifications_per_hour: int,
) -> bool:
    all_existing = (*occupied, *selected)
    if any(abs((candidate - item).total_seconds()) < minimum_gap_seconds for item in all_existing):
        return False
    bucket = _hour_bucket(candidate, timezone)
    return (
        sum(1 for item in all_existing if _hour_bucket(item, timezone) == bucket)
        < maximum_notifications_per_hour
    )


def _greedy_capacity(
    candidates: tuple[datetime, ...],
    *,
    requested: int,
    occupied: tuple[datetime, ...],
    timezone: ZoneInfo,
    minimum_gap_seconds: int,
    maximum_notifications_per_hour: int,
) -> tuple[datetime, ...]:
    selected: list[datetime] = []
    for candidate in candidates:
        if not _valid_after(
            candidate,
            selected,
            occupied=occupied,
            timezone=timezone,
            minimum_gap_seconds=minimum_gap_seconds,
            maximum_notifications_per_hour=maximum_notifications_per_hour,
        ):
            continue
        selected.append(candidate)
        if len(selected) == requested:
            break
    return tuple(selected)


def _score(seed: str, slot_index: int, candidate: datetime) -> bytes:
    payload = f"{seed}|{slot_index}|{candidate.isoformat()}".encode()
    return hashlib.sha256(payload).digest()


def _stratified_schedule(
    candidates: tuple[datetime, ...],
    *,
    target_count: int,
    seed: str,
    occupied: tuple[datetime, ...],
    timezone: ZoneInfo,
    minimum_gap_seconds: int,
    maximum_notifications_per_hour: int,
) -> tuple[datetime, ...] | None:
    if target_count == 0:
        return ()
    selected: list[datetime] = []
    total = len(candidates)
    for slot_index in range(target_count):
        start_index = slot_index * total // target_count
        end_index = (slot_index + 1) * total // target_count
        bucket_candidates = candidates[start_index:end_index]
        chosen = next(
            (
                candidate
                for candidate in sorted(
                    bucket_candidates,
                    key=lambda item: _score(seed, slot_index, item),
                )
                if _valid_after(
                    candidate,
                    selected,
                    occupied=occupied,
                    timezone=timezone,
                    minimum_gap_seconds=minimum_gap_seconds,
                    maximum_notifications_per_hour=maximum_notifications_per_hour,
                )
            ),
            None,
        )
        if chosen is None:
            return None
        selected.append(chosen)
    return tuple(selected)


def _track_unit_queue(demand: TrackDemand) -> list[str]:
    """Interleave one Track's learning and quiz demand deterministically."""
    learning = demand.learning_count
    quiz = demand.quiz_count
    queue: list[str] = []
    while learning or quiz:
        if learning:
            queue.append("learning")
            learning -= 1
        if quiz:
            queue.append("quiz")
            quiz -= 1
    return queue


def _weighted_round_robin(
    demands: tuple[TrackDemand, ...],
) -> tuple[tuple[TrackDemand, str], ...]:
    """Return a finite smooth weighted round-robin sequence without starvation."""
    queues = {demand.track_id: _track_unit_queue(demand) for demand in demands}
    current = {demand.track_id: 0 for demand in demands}
    active = [demand for demand in demands if queues[demand.track_id]]
    sequence: list[tuple[TrackDemand, str]] = []

    while active:
        total_weight = sum(demand.priority for demand in active)
        for demand in active:
            current[demand.track_id] += demand.priority
        chosen = max(
            active,
            key=lambda demand: (
                current[demand.track_id],
                demand.priority,
                demand.track_id,
            ),
        )
        current[chosen.track_id] -= total_weight
        sequence.append((chosen, queues[chosen.track_id].pop(0)))
        active = [demand for demand in active if queues[demand.track_id]]
    return tuple(sequence)


def _slot_id(
    profile_id: str,
    local_date: date,
    config_version: int,
    scheduled_for_utc: datetime,
) -> str:
    payload = (
        f"locklearn|scheduler|{profile_id}|{local_date.isoformat()}|"
        f"{config_version}|{scheduled_for_utc.isoformat()}"
    )
    return "locklearn:slot:" + hashlib.sha256(payload.encode()).hexdigest()[:32]


class SchedulerService:
    """Generate and materialize generic profile notification slots.

    P4.1 intentionally stops before content, Track, target, context, missed-slot
    and notification-interaction selection. A persisted slot is only a time
    opportunity; pedagogical content is selected later at send time.
    """

    def __init__(
        self,
        profiles: ProfilesRepository,
        tracks: TracksRepository,
        notification_targets: NotificationTargetsRepository,
        scheduler: SchedulerRepository,
        settings: SettingsRepository,
        notification_selection: NotificationSelectionService | None = None,
        *,
        clock: Clock | None = None,
        issue_callback: Callable[[str, str, Mapping[str, str]], Awaitable[None]] | None = None,
        issue_clear_callback: Callable[[str], Awaitable[None]] | None = None,
        receptive_evaluator: Callable[[str], Awaitable[bool]] | None = None,
    ) -> None:
        self._profiles = profiles
        self._tracks = tracks
        self._notification_targets = notification_targets
        self._scheduler = scheduler
        self._settings = settings
        self._notification_selection = notification_selection
        self._clock = clock or SystemClock()
        self._issue_callback = issue_callback
        self._issue_clear_callback = issue_clear_callback
        self._receptive_evaluator = receptive_evaluator

    async def async_preview(
        self,
        *,
        profile_id: str,
        local_date: date | None = None,
    ) -> dict[str, Any]:
        """Return deterministic future slots without persisting config or slots."""
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise SchedulerValidationError("profile does not exist")
        persisted = await self._scheduler.async_get_config(profile_id)
        config, daily_push_budget = self._resolve_config(profile, persisted)

        now = await self.async_effective_now()
        timezone = ZoneInfo(config.timezone)
        resolved_date = local_date or now.astimezone(timezone).date()
        not_before = now if resolved_date == now.astimezone(timezone).date() else None
        start_utc, end_utc = self._local_day_bounds(config.timezone, resolved_date)
        existing = await self._scheduler.async_list_slots(
            profile_id=profile_id,
            start_utc=start_utc.isoformat(),
            end_utc=end_utc.isoformat(),
        )
        current_version = tuple(
            slot for slot in existing if int(slot["scheduler_config_version"]) == config.version
        )
        remaining_budget = max(0, daily_push_budget - len(current_version))
        occupied = tuple(
            datetime.fromisoformat(str(slot["scheduled_for_utc"])).astimezone(UTC)
            for slot in current_version
        )
        drafts = self._generate(
            config,
            local_date=resolved_date,
            daily_push_budget=remaining_budget,
            not_before_utc=not_before,
            occupied=occupied,
        )
        drafts, allocation = await self._async_allocate(
            profile_id=profile_id,
            config=config,
            local_date=resolved_date,
            drafts=drafts,
            existing_slots=current_version,
            profile_daily_budget=daily_push_budget,
        )
        payload = self._preview_payload(
            config=config,
            local_date=resolved_date,
            daily_push_budget=daily_push_budget,
            drafts=drafts,
        )
        payload["allocation"] = allocation
        return payload

    async def async_generate(
        self,
        *,
        profile_id: str,
        local_date: date | None = None,
    ) -> dict[str, Any]:
        """Persist one deterministic day while preserving materialized history."""
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise SchedulerValidationError("profile does not exist")
        persisted = await self._scheduler.async_get_config(profile_id)
        prospective, daily_push_budget = self._resolve_config(profile, persisted)

        reconciliation = await self.async_reconcile(reason="generate")
        now = reconciliation.effective_now_utc
        timezone_changed = (
            persisted is not None and str(persisted["timezone"]) != prospective.timezone
        )
        config_row = await self._scheduler.async_sync_config(
            profile_id=profile_id,
            timezone=prospective.timezone,
            active_days=prospective.active_days,
            active_windows=prospective.active_windows,
            minimum_gap_seconds=prospective.minimum_gap_seconds,
            maximum_notifications_per_hour=prospective.maximum_notifications_per_hour,
            quiet_hours=prospective.quiet_hours,
            receptive_when=prospective.receptive_when,
            defer_window_minutes=prospective.defer_window_minutes,
            updated_at_utc=now.isoformat(),
        )
        config = self._config_from_row(config_row)
        if timezone_changed:
            await self._scheduler.async_cancel_superseded_future_slots(
                profile_id=profile_id,
                active_config_version=config.version,
                not_before_utc=now.isoformat(),
                updated_at_utc=now.isoformat(),
            )

        timezone = ZoneInfo(config.timezone)
        resolved_date = local_date or now.astimezone(timezone).date()
        local_today = now.astimezone(timezone).date()
        not_before = now if resolved_date == local_today else None
        start_utc, end_utc = self._local_day_bounds(config.timezone, resolved_date)
        existing = await self._scheduler.async_list_slots(
            profile_id=profile_id,
            start_utc=start_utc.isoformat(),
            end_utc=end_utc.isoformat(),
        )
        current_version = tuple(
            slot for slot in existing if int(slot["scheduler_config_version"]) == config.version
        )
        remaining_budget = max(0, daily_push_budget - len(current_version))
        occupied = tuple(
            datetime.fromisoformat(str(slot["scheduled_for_utc"])).astimezone(UTC)
            for slot in current_version
        )
        drafts = self._generate(
            config,
            local_date=resolved_date,
            daily_push_budget=remaining_budget,
            not_before_utc=not_before,
            occupied=occupied,
        )
        drafts, allocation = await self._async_allocate(
            profile_id=profile_id,
            config=config,
            local_date=resolved_date,
            drafts=drafts,
            existing_slots=current_version,
            profile_daily_budget=daily_push_budget,
        )
        await self._async_update_capacity_repair(
            profile_id=profile_id,
            local_date=resolved_date,
            unmet_demand=int(allocation["unmet_demand"]),
            requested_demand=int(allocation["requested_demand"]),
            allocatable_slots=int(allocation["allocated_demand"]),
            now_utc=now,
        )
        materialized = await self._scheduler.async_materialize_day(
            profile_id=profile_id,
            scheduler_config_version=config.version,
            seed=self._seed(profile_id, resolved_date, config.version),
            start_utc=start_utc.isoformat(),
            end_utc=end_utc.isoformat(),
            now_utc=now.isoformat(),
            slots=tuple(draft.as_dict() for draft in drafts),
            updated_at_utc=now.isoformat(),
        )
        payload = self._preview_payload(
            config=config,
            local_date=resolved_date,
            daily_push_budget=daily_push_budget,
            drafts=drafts,
        )
        payload["materialized"] = True
        payload["materialized_slots"] = list(materialized)
        payload["reconciliation"] = reconciliation.as_dict()
        payload["allocation"] = allocation
        return payload

    async def async_prepare_delivery(self, slot_id: str) -> dict[str, Any]:
        """Apply pending, receptivity and send-time content-selection policy."""
        slot = await self._scheduler.async_get_slot(slot_id)
        if slot is None:
            raise SchedulerValidationError("slot does not exist")
        if str(slot["status"]) not in {"scheduled", "deferred"}:
            return {
                "slot_id": slot_id,
                "ready": False,
                "status": str(slot["status"]),
                "reason": "not_pending",
            }

        profile_id = str(slot["profile_id"])
        target_id = slot.get("target_id")
        now = await self.async_effective_now()
        if isinstance(target_id, str) and target_id:
            if await self._scheduler.async_has_pending_for_target(
                profile_id=profile_id,
                target_id=target_id,
                exclude_slot_id=slot_id,
            ):
                await self._scheduler.async_expire_slot(
                    slot_id=slot_id,
                    reason="pending_existing",
                    updated_at_utc=now.isoformat(),
                )
                return {
                    "slot_id": slot_id,
                    "ready": False,
                    "status": "expired",
                    "reason": "pending_existing",
                }

        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise SchedulerValidationError("slot profile does not exist")
        persisted = await self._scheduler.async_get_config(profile_id)
        config, _daily_budget = self._resolve_config(profile, persisted)

        deferred_until_raw = slot.get("deferred_until_utc")
        if isinstance(deferred_until_raw, str):
            deferred_until = datetime.fromisoformat(deferred_until_raw).astimezone(UTC)
            if now < deferred_until:
                return {
                    "slot_id": slot_id,
                    "ready": False,
                    "status": "deferred",
                    "reason": str(slot.get("defer_reason") or "deferred"),
                    "deferred_until_utc": deferred_until.isoformat(),
                }

        if config.receptive_when is not None:
            if self._receptive_evaluator is None:
                raise SchedulerValidationError("receptive_when evaluator is unavailable")
            receptive = await self._receptive_evaluator(config.receptive_when)
            if not receptive:
                scheduled_for = datetime.fromisoformat(
                    str(slot["scheduled_for_utc"])
                ).astimezone(UTC)
                deadline = scheduled_for + timedelta(minutes=config.defer_window_minutes)
                if config.defer_window_minutes <= 0 or now >= deadline:
                    await self._scheduler.async_expire_slot(
                        slot_id=slot_id,
                        reason="missed_not_receptive",
                        updated_at_utc=now.isoformat(),
                    )
                    return {
                        "slot_id": slot_id,
                        "ready": False,
                        "status": "expired",
                        "reason": "missed_not_receptive",
                        "defer_exhausted": True,
                    }

                await self._scheduler.async_defer_slot(
                    slot_id=slot_id,
                    deferred_until_utc=deadline.isoformat(),
                    reason="receptive_when_false",
                    updated_at_utc=now.isoformat(),
                )
                return {
                    "slot_id": slot_id,
                    "ready": False,
                    "status": "deferred",
                    "reason": "receptive_when_false",
                    "deferred_until_utc": deadline.isoformat(),
                    "defer_exhausted": False,
                }

        selection: dict[str, str] | None = None
        if self._notification_selection is not None:
            try:
                selected = await self._notification_selection.async_select_for_slot(slot_id)
            except NotificationSelectionError as err:
                raise SchedulerValidationError(str(err)) from err
            if selected is None:
                await self._scheduler.async_expire_slot(
                    slot_id=slot_id,
                    reason="no_candidate",
                    updated_at_utc=now.isoformat(),
                )
                return {
                    "slot_id": slot_id,
                    "ready": False,
                    "status": "expired",
                    "reason": "no_candidate",
                }
            selection = selected.as_dict()

        return {
            "slot_id": slot_id,
            "ready": True,
            "status": str(slot["status"]),
            "reason": (
                "receptive_condition_absent"
                if config.receptive_when is None
                else "receptive"
            ),
            "selection": selection,
        }

    async def async_record_delivery(
        self,
        *,
        slot_id: str,
        delivered_at_utc: datetime | None = None,
    ) -> dict[str, Any]:
        """Record delivery-only receptivity features, never an SRS result."""
        decision = await self.async_prepare_delivery(slot_id)
        if not bool(decision["ready"]):
            raise SchedulerValidationError(
                f"slot is not receptive for delivery: {decision['reason']}"
            )
        slot = await self._scheduler.async_get_slot(slot_id)
        if slot is None:
            raise SchedulerValidationError("slot does not exist")
        profile = await self._profiles.async_get(str(slot["profile_id"]))
        if profile is None:
            raise SchedulerValidationError("slot profile does not exist")
        delivered = (delivered_at_utc or self._aware_utc_now()).astimezone(UTC)
        timezone_name = str(profile["timezone"])
        local = delivered.astimezone(ZoneInfo(timezone_name))
        changed = await self._scheduler.async_mark_slot_sent(
            slot_id=slot_id,
            delivered_at_utc=delivered.isoformat(),
            timezone_name=timezone_name,
            weekday=local.weekday(),
            local_hour=local.hour,
        )
        if not changed:
            raise SchedulerValidationError("slot is not deliverable")
        sample = await self._scheduler.async_get_receptivity_sample(slot_id)
        if sample is None:
            raise SchedulerValidationError("receptivity sample was not created")
        return sample

    async def async_record_receptivity_action(
        self,
        *,
        slot_id: str,
        action: str,
        action_at_utc: datetime | None = None,
    ) -> dict[str, Any]:
        """Record observational cleared/answered features without SRS mutation."""
        sample = await self._scheduler.async_get_receptivity_sample(slot_id)
        if sample is None:
            raise SchedulerValidationError("slot has no delivery sample")
        action_at = (action_at_utc or self._aware_utc_now()).astimezone(UTC)
        delivered_at = datetime.fromisoformat(str(sample["delivered_at_utc"])).astimezone(UTC)
        latency_ms = max(0, int((action_at - delivered_at).total_seconds() * 1000))
        changed = await self._scheduler.async_record_receptivity_action(
            slot_id=slot_id,
            action=action,
            action_at_utc=action_at.isoformat(),
            delivery_to_action_ms=latency_ms,
        )
        if not changed:
            raise SchedulerValidationError("receptivity sample could not be updated")
        updated = await self._scheduler.async_get_receptivity_sample(slot_id)
        if updated is None:
            raise SchedulerValidationError("receptivity sample disappeared")
        return updated

    async def async_trigger_routine(
        self,
        *,
        profile_id: str,
        routine_type: str,
        track_id: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        """Materialize one routine hook slot for an HA entity/automation adapter."""
        if routine_type not in _ROUTINE_SLOT_TYPES:
            raise SchedulerValidationError("unsupported routine slot type")
        profile = await self._profiles.async_get(profile_id)
        if profile is None or str(profile["status"]) != "active":
            raise SchedulerValidationError("active profile does not exist")
        persisted = await self._scheduler.async_get_config(profile_id)
        config, daily_push_budget = self._resolve_config(profile, persisted)
        now = await self.async_effective_now()
        timezone = ZoneInfo(config.timezone)
        local_date = now.astimezone(timezone).date()
        start_utc, end_utc = self._local_day_bounds(config.timezone, local_date)
        existing = await self._scheduler.async_list_slots(
            profile_id=profile_id,
            start_utc=start_utc.isoformat(),
            end_utc=end_utc.isoformat(),
        )
        active_slots = tuple(
            slot for slot in existing if str(slot["status"]) not in {"cancelled", "expired"}
        )
        if len(active_slots) >= daily_push_budget:
            raise SchedulerValidationError("profile daily push budget is exhausted")

        active_session_tracks = await self._scheduler.async_active_session_track_ids(profile_id)
        tracks = tuple(
            track
            for track in await self._tracks.async_list_for_profile(profile_id)
            if str(track["status"]) == "active"
            and str(track["track_id"]) not in active_session_tracks
        )
        if track_id is None:
            if not tracks:
                raise SchedulerValidationError("routine has no eligible active track")
            selected_track_id = str(
                sorted(tracks, key=lambda item: str(item["track_id"]))[0]["track_id"]
            )
        else:
            matching = next(
                (track for track in tracks if str(track["track_id"]) == track_id),
                None,
            )
            if matching is None:
                raise SchedulerValidationError(
                    "routine track is unavailable or has an active session"
                )
            selected_track_id = track_id

        raw_targets = await self._notification_targets.async_list_for_profile(profile_id)
        targets = await self._async_targets_with_backoff(
            profile_id=profile_id,
            targets=raw_targets,
            profile_daily_budget=profile_daily_budget,
        )
        targets_by_id = {str(target["target_id"]): target for target in targets}
        if target_id is None:
            candidate_target_ids = tuple(sorted(targets_by_id))
        else:
            if target_id not in targets_by_id:
                raise SchedulerValidationError("routine target is not enabled in profile")
            candidate_target_ids = (target_id,)
        if not candidate_target_ids:
            raise SchedulerValidationError("routine has no enabled notification target")

        existing_by_target: dict[str, list[datetime]] = {}
        for existing_slot in active_slots:
            existing_target_id = existing_slot.get("target_id")
            if isinstance(existing_target_id, str):
                existing_by_target.setdefault(existing_target_id, []).append(
                    datetime.fromisoformat(str(existing_slot["scheduled_for_utc"])).astimezone(UTC)
                )
        device_usage: dict[str, tuple[datetime, ...]] = {}
        for target in targets:
            device_registry_id = str(target["device_registry_id"])
            if device_registry_id in device_usage:
                continue
            device_usage[device_registry_id] = tuple(
                datetime.fromisoformat(str(item["scheduled_for_utc"])).astimezone(UTC)
                for item in await self._scheduler.async_list_device_slots(
                    device_registry_id=device_registry_id,
                    start_utc=start_utc.isoformat(),
                    end_utc=end_utc.isoformat(),
                )
                if str(item["status"]) not in {"cancelled", "expired"}
            )
        routine_demand = TrackDemand(
            track_id=selected_track_id,
            priority=1,
            learning_count=1,
            quiz_count=0,
            target_ids=candidate_target_ids,
        )
        selected_target_id = self._select_target(
            demand=routine_demand,
            scheduled_for_utc=now,
            targets_by_id=targets_by_id,
            target_existing_usage=existing_by_target,
            target_new_usage={target: [] for target in targets_by_id},
            device_existing_usage=device_usage,
            device_new_usage={str(target["device_registry_id"]): [] for target in targets},
            config=config,
        )
        if selected_target_id is None:
            raise SchedulerValidationError("routine target capacity is unavailable")

        slot_id = self._routine_slot_id(
            profile_id=profile_id,
            routine_type=routine_type,
            scheduled_for_utc=now,
            config_version=config.version,
        )
        slot = SchedulerSlotDraft(
            slot_id=slot_id,
            profile_id=profile_id,
            track_id=selected_track_id,
            target_id=selected_target_id,
            slot_type=routine_type,
            scheduled_for_utc=now.isoformat(),
            scheduler_config_version=config.version,
            seed=self._seed(profile_id, local_date, config.version),
        )
        materialized = await self._scheduler.async_materialize_day(
            profile_id=profile_id,
            scheduler_config_version=config.version,
            seed=slot.seed,
            start_utc=start_utc.isoformat(),
            end_utc=end_utc.isoformat(),
            now_utc=now.isoformat(),
            slots=(slot.as_dict(),),
            updated_at_utc=now.isoformat(),
        )
        created = next(
            (item for item in materialized if str(item["slot_id"]) == slot_id),
            None,
        )
        if created is None:
            raise SchedulerValidationError("routine slot could not be materialized")
        return created

    @staticmethod
    def _routine_slot_id(
        *,
        profile_id: str,
        routine_type: str,
        scheduled_for_utc: datetime,
        config_version: int,
    ) -> str:
        payload = (
            f"locklearn|routine|{profile_id}|{routine_type}|"
            f"{config_version}|{scheduled_for_utc.isoformat()}"
        )
        return "locklearn:routine-slot:" + hashlib.sha256(payload.encode()).hexdigest()[:32]

    async def _async_allocate(
        self,
        *,
        profile_id: str,
        config: SchedulerConfig,
        local_date: date,
        drafts: tuple[SchedulerSlotDraft, ...],
        existing_slots: tuple[dict[str, Any], ...],
        profile_daily_budget: int,
    ) -> tuple[tuple[SchedulerSlotDraft, ...], dict[str, Any]]:
        """Allocate future Profile slots across Tracks and stable targets."""
        tracks = tuple(
            track
            for track in await self._tracks.async_list_for_profile(profile_id)
            if str(track["status"]) == "active"
        )
        active_session_tracks = await self._scheduler.async_active_session_track_ids(profile_id)
        targets = await self._notification_targets.async_list_for_profile(profile_id)
        targets_by_id = {str(target["target_id"]): target for target in targets}

        demands: list[TrackDemand] = []
        suppressed: list[str] = []
        for track in tracks:
            settings = track.get("settings")
            scheduler_settings = (
                settings.get("scheduler") if isinstance(settings, Mapping) else None
            )
            if not isinstance(scheduler_settings, Mapping):
                continue
            learning_count = self._nonnegative_count(
                scheduler_settings.get("learning_count", 0),
                "learning_count",
            )
            quiz_count = self._nonnegative_count(
                scheduler_settings.get("quiz_count", 0),
                "quiz_count",
            )
            if learning_count + quiz_count == 0:
                continue
            track_id = str(track["track_id"])
            if track_id in active_session_tracks:
                suppressed.append(track_id)
                continue
            raw_target_ids = scheduler_settings.get("target_ids")
            if raw_target_ids is None:
                target_ids = tuple(sorted(targets_by_id))
            elif isinstance(raw_target_ids, (list, tuple)):
                target_ids = tuple(
                    target_id
                    for target_id in dict.fromkeys(str(value) for value in raw_target_ids)
                    if target_id in targets_by_id
                )
            else:
                raise SchedulerValidationError("track scheduler target_ids must be a list")
            demands.append(
                TrackDemand(
                    track_id=track_id,
                    priority=int(track["priority"]),
                    learning_count=learning_count,
                    quiz_count=quiz_count,
                    target_ids=target_ids,
                )
            )

        requested_demand = sum(demand.total for demand in demands)
        if requested_demand == 0:
            return drafts, {
                "mode": "profile_only",
                "requested_demand": 0,
                "allocated_demand": 0,
                "unmet_demand": 0,
                "allocatable_slots": len(drafts),
                "suppressed_active_session_tracks": sorted(suppressed),
            }

        sequence = _weighted_round_robin(tuple(demands))
        existing_by_target: dict[str, list[datetime]] = {}
        for slot in existing_slots:
            target_id = slot.get("target_id")
            if not isinstance(target_id, str):
                continue
            existing_by_target.setdefault(target_id, []).append(
                datetime.fromisoformat(str(slot["scheduled_for_utc"])).astimezone(UTC)
            )

        device_usage: dict[str, tuple[datetime, ...]] = {}
        start_utc, end_utc = self._local_day_bounds(config.timezone, local_date)
        for target in targets:
            device_registry_id = str(target["device_registry_id"])
            if device_registry_id in device_usage:
                continue
            device_usage[device_registry_id] = tuple(
                datetime.fromisoformat(str(slot["scheduled_for_utc"])).astimezone(UTC)
                for slot in await self._scheduler.async_list_device_slots(
                    device_registry_id=device_registry_id,
                    start_utc=start_utc.isoformat(),
                    end_utc=end_utc.isoformat(),
                )
                if str(slot["status"]) not in {"cancelled", "expired"}
            )

        allocated: list[SchedulerSlotDraft] = []
        target_new_usage: dict[str, list[datetime]] = {target_id: [] for target_id in targets_by_id}
        device_new_usage: dict[str, list[datetime]] = {
            str(target["device_registry_id"]): [] for target in targets
        }
        pending = list(sequence)
        for draft in drafts:
            chosen_index: int | None = None
            chosen_target_id: str | None = None
            when = datetime.fromisoformat(draft.scheduled_for_utc).astimezone(UTC)
            for index, (demand, _slot_type) in enumerate(pending):
                target_id = self._select_target(
                    demand=demand,
                    scheduled_for_utc=when,
                    targets_by_id=targets_by_id,
                    target_existing_usage=existing_by_target,
                    target_new_usage=target_new_usage,
                    device_existing_usage=device_usage,
                    device_new_usage=device_new_usage,
                    config=config,
                )
                if target_id is not None:
                    chosen_index = index
                    chosen_target_id = target_id
                    break
            if chosen_index is None or chosen_target_id is None:
                continue

            demand, slot_type = pending.pop(chosen_index)
            target = targets_by_id[chosen_target_id]
            target_new_usage[chosen_target_id].append(when)
            device_new_usage[str(target["device_registry_id"])].append(when)
            allocated.append(
                SchedulerSlotDraft(
                    slot_id=draft.slot_id,
                    profile_id=draft.profile_id,
                    track_id=demand.track_id,
                    target_id=chosen_target_id,
                    slot_type=slot_type,
                    scheduled_for_utc=draft.scheduled_for_utc,
                    scheduler_config_version=draft.scheduler_config_version,
                    seed=draft.seed,
                )
            )
            if not pending:
                break

        allocated_demand = len(allocated)
        return tuple(allocated), {
            "mode": "track_target",
            "requested_demand": requested_demand,
            "allocated_demand": allocated_demand,
            "unmet_demand": max(0, requested_demand - allocated_demand),
            "allocatable_slots": len(drafts),
            "suppressed_active_session_tracks": sorted(suppressed),
            "target_backoff": {
                str(target["target_id"]): float(target["backoff_factor"])
                for target in targets
            },
        }

    @staticmethod
    def _nonnegative_count(value: Any, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SchedulerValidationError(f"{field} must be an integer >= 0")
        return value

    @staticmethod
    def _select_target(
        *,
        demand: TrackDemand,
        scheduled_for_utc: datetime,
        targets_by_id: Mapping[str, Mapping[str, Any]],
        target_existing_usage: Mapping[str, list[datetime]],
        target_new_usage: Mapping[str, list[datetime]],
        device_existing_usage: Mapping[str, tuple[datetime, ...]],
        device_new_usage: Mapping[str, list[datetime]],
        config: SchedulerConfig,
    ) -> str | None:
        """Choose the first stable target satisfying target/device budgets."""
        for target_id in demand.target_ids:
            target = targets_by_id.get(target_id)
            if target is None:
                continue
            target_existing = tuple(target_existing_usage.get(target_id, ()))
            target_new = tuple(target_new_usage.get(target_id, ()))
            target_usage = (*target_existing, *target_new)
            daily_budget_raw = target.get("effective_daily_push_budget")
            daily_budget = 10**9 if daily_budget_raw is None else int(daily_budget_raw)
            if len(target_usage) >= daily_budget:
                continue

            minimum_gap_raw = target.get("minimum_gap_seconds")
            minimum_gap = (
                config.minimum_gap_seconds if minimum_gap_raw is None else int(minimum_gap_raw)
            )
            if any(
                abs((scheduled_for_utc - item).total_seconds()) < minimum_gap
                for item in target_usage
            ):
                continue

            max_hour_raw = target.get("maximum_notifications_per_hour")
            max_hour = (
                config.maximum_notifications_per_hour if max_hour_raw is None else int(max_hour_raw)
            )
            timezone = ZoneInfo(config.timezone)
            bucket = _hour_bucket(scheduled_for_utc, timezone)
            if (
                sum(1 for item in target_usage if _hour_bucket(item, timezone) == bucket)
                >= max_hour
            ):
                continue

            device_registry_id = str(target["device_registry_id"])
            device_usage = (
                *device_existing_usage.get(device_registry_id, ()),
                *device_new_usage.get(device_registry_id, ()),
            )
            if len(device_usage) >= daily_budget:
                continue
            if (
                sum(1 for item in device_usage if _hour_bucket(item, timezone) == bucket)
                >= max_hour
            ):
                continue
            if any(
                abs((scheduled_for_utc - item).total_seconds()) < minimum_gap
                for item in device_usage
            ):
                continue
            return target_id
        return None

    async def _async_targets_with_backoff(
        self,
        *,
        profile_id: str,
        targets: tuple[dict[str, Any], ...],
        profile_daily_budget: int,
    ) -> tuple[dict[str, Any], ...]:
        """Apply channel-only adaptive backoff without touching SRS state."""
        adjusted: list[dict[str, Any]] = []
        for target in targets:
            target_id = str(target["target_id"])
            outcomes = await self._scheduler.async_channel_outcomes(
                profile_id=profile_id,
                target_id=target_id,
            )
            factor = self._backoff_factor(outcomes)
            base_raw = target.get("daily_push_budget")
            base_budget = profile_daily_budget if base_raw is None else int(base_raw)
            effective = 0 if base_budget <= 0 else max(1, int(base_budget * factor))
            item = dict(target)
            item["backoff_factor"] = factor
            item["effective_daily_push_budget"] = effective
            adjusted.append(item)
        return tuple(adjusted)

    @staticmethod
    def _backoff_factor(outcomes: tuple[str, ...]) -> float:
        """Map recent expiry/clear streaks to a V1 channel budget multiplier."""
        filtered = tuple(
            outcome
            for outcome in outcomes
            if outcome in {"expired", "cleared", "answered", "consumed"}
        )
        if not filtered:
            return 1.0

        recovery = 0
        index = 0
        while index < len(filtered) and filtered[index] in {"answered", "consumed"}:
            recovery += 1
            index += 1

        failures = 0
        while index < len(filtered) and filtered[index] in {"expired", "cleared"}:
            failures += 1
            index += 1

        if failures >= 6:
            base = 0.5
        elif failures >= 3:
            base = 0.75
        else:
            base = 1.0
        return min(1.0, base + recovery * 0.25)

    async def _async_update_capacity_repair(
        self,
        *,
        profile_id: str,
        local_date: date,
        unmet_demand: int,
        requested_demand: int,
        allocatable_slots: int,
        now_utc: datetime,
    ) -> None:
        """Raise/clear the HA Repair only after distinct sustained infeasible days."""
        key = f"{_CAPACITY_STATE_PREFIX}{profile_id}"
        issue_id = f"scheduler_configuration_infeasible_{profile_id}"
        raw = await self._settings.async_get(key)
        state = dict(raw) if isinstance(raw, Mapping) else {}
        last_raw = state.get("last_local_date")
        last_date = date.fromisoformat(str(last_raw)) if isinstance(last_raw, str) else None
        count = int(state.get("consecutive_infeasible_days", 0))

        if unmet_demand <= 0:
            count = 0
            if self._issue_clear_callback is not None:
                await self._issue_clear_callback(issue_id)
        elif last_date != local_date:
            count = count + 1 if last_date == local_date - timedelta(days=1) else 1

        await self._settings.async_set(
            key,
            {
                "last_local_date": local_date.isoformat(),
                "consecutive_infeasible_days": count,
                "last_unmet_demand": unmet_demand,
                "last_requested_demand": requested_demand,
                "last_allocatable_slots": allocatable_slots,
            },
            updated_at_utc=now_utc.isoformat(),
        )

        if unmet_demand > 0 and count >= _CAPACITY_REPAIR_DAYS and self._issue_callback is not None:
            await self._issue_callback(
                issue_id,
                "scheduler_configuration_infeasible",
                {
                    "profile_id": profile_id,
                    "requested": str(requested_demand),
                    "capacity": str(allocatable_slots),
                },
            )

    def _resolve_config(
        self,
        profile: Mapping[str, Any],
        persisted: Mapping[str, Any] | None,
    ) -> tuple[SchedulerConfig, int]:
        settings = profile.get("settings")
        if not isinstance(settings, Mapping):
            settings = {}
        raw_scheduler = settings.get("scheduler")
        if raw_scheduler is None:
            scheduler_settings: Mapping[str, Any] = {}
        elif isinstance(raw_scheduler, Mapping):
            scheduler_settings = raw_scheduler
        else:
            raise SchedulerValidationError("profile scheduler setting must be an object")

        timezone_name = str(profile["timezone"])
        try:
            ZoneInfo(timezone_name)
        except (ValueError, ZoneInfoNotFoundError) as err:
            raise SchedulerValidationError(f"invalid timezone: {timezone_name}") from err

        active_days = _normalize_active_days(scheduler_settings.get("active_days"))
        active_windows = _normalize_active_windows(scheduler_settings.get("active_windows"))
        minimum_gap = scheduler_settings.get(
            "minimum_gap_seconds",
            _DEFAULT_MINIMUM_GAP_SECONDS,
        )
        max_per_hour = scheduler_settings.get(
            "maximum_notifications_per_hour",
            _DEFAULT_MAXIMUM_NOTIFICATIONS_PER_HOUR,
        )
        if isinstance(minimum_gap, bool) or not isinstance(minimum_gap, int) or minimum_gap < 0:
            raise SchedulerValidationError("minimum_gap_seconds must be an integer >= 0")
        if isinstance(max_per_hour, bool) or not isinstance(max_per_hour, int) or max_per_hour < 1:
            raise SchedulerValidationError("maximum_notifications_per_hour must be an integer >= 1")

        quiet_source = scheduler_settings.get("quiet_hours", settings.get("quiet_hours"))
        quiet_hours = _normalize_quiet_hours(quiet_source)
        daily_budget_raw = settings.get("daily_push_budget", 0)
        if (
            isinstance(daily_budget_raw, bool)
            or not isinstance(daily_budget_raw, int)
            or daily_budget_raw < 0
        ):
            raise SchedulerValidationError("daily_push_budget must be an integer >= 0")
        daily_push_budget = 0 if profile.get("status") != "active" else daily_budget_raw

        receptive_when_raw = scheduler_settings.get("receptive_when")
        receptive_when = (
            None if receptive_when_raw is None else str(receptive_when_raw).strip() or None
        )
        defer_window_raw = scheduler_settings.get("defer_window_minutes", 0)
        if (
            isinstance(defer_window_raw, bool)
            or not isinstance(defer_window_raw, int)
            or defer_window_raw < 0
        ):
            raise SchedulerValidationError("defer_window_minutes must be an integer >= 0")

        provisional = SchedulerConfig(
            profile_id=str(profile["profile_id"]),
            version=1 if persisted is None else int(persisted["version"]),
            timezone=timezone_name,
            active_days=active_days,
            active_windows=active_windows,
            minimum_gap_seconds=minimum_gap,
            maximum_notifications_per_hour=max_per_hour,
            quiet_hours=quiet_hours,
            receptive_when=receptive_when,
            defer_window_minutes=defer_window_raw,
        )
        if persisted is not None and _persisted_semantics(persisted) != _semantic_config(
            provisional
        ):
            provisional = SchedulerConfig(
                profile_id=provisional.profile_id,
                version=int(persisted["version"]) + 1,
                timezone=provisional.timezone,
                active_days=provisional.active_days,
                active_windows=provisional.active_windows,
                minimum_gap_seconds=provisional.minimum_gap_seconds,
                maximum_notifications_per_hour=provisional.maximum_notifications_per_hour,
                quiet_hours=provisional.quiet_hours,
                receptive_when=provisional.receptive_when,
                defer_window_minutes=provisional.defer_window_minutes,
            )
        return provisional, daily_push_budget

    @staticmethod
    def _config_from_row(row: Mapping[str, Any]) -> SchedulerConfig:
        return SchedulerConfig(
            profile_id=str(row["profile_id"]),
            version=int(row["version"]),
            timezone=str(row["timezone"]),
            active_days=tuple(int(day) for day in row["active_days"]),
            active_windows=tuple(
                (str(window["start"]), str(window["end"])) for window in row["active_windows"]
            ),
            minimum_gap_seconds=int(row["minimum_gap_seconds"]),
            maximum_notifications_per_hour=int(row["maximum_notifications_per_hour"]),
            quiet_hours=(
                str(row["quiet_hours"]["start"]),
                str(row["quiet_hours"]["end"]),
            ),
            receptive_when=(None if row["receptive_when"] is None else str(row["receptive_when"])),
            defer_window_minutes=int(row["defer_window_minutes"]),
        )

    def _generate(
        self,
        config: SchedulerConfig,
        *,
        local_date: date,
        daily_push_budget: int,
        not_before_utc: datetime | None,
        occupied: tuple[datetime, ...] = (),
    ) -> tuple[SchedulerSlotDraft, ...]:
        seed = self._seed(config.profile_id, local_date, config.version)
        candidates = _minute_candidates(
            config,
            local_date,
            not_before_utc=not_before_utc,
        )
        timezone = ZoneInfo(config.timezone)
        capacity = _greedy_capacity(
            candidates,
            requested=daily_push_budget,
            occupied=occupied,
            timezone=timezone,
            minimum_gap_seconds=config.minimum_gap_seconds,
            maximum_notifications_per_hour=config.maximum_notifications_per_hour,
        )
        selected = _stratified_schedule(
            candidates,
            target_count=len(capacity),
            seed=seed,
            occupied=occupied,
            timezone=timezone,
            minimum_gap_seconds=config.minimum_gap_seconds,
            maximum_notifications_per_hour=config.maximum_notifications_per_hour,
        )
        if selected is None:
            selected = capacity

        return tuple(
            SchedulerSlotDraft(
                slot_id=_slot_id(
                    config.profile_id,
                    local_date,
                    config.version,
                    scheduled_for_utc,
                ),
                profile_id=config.profile_id,
                slot_type="notification",
                scheduled_for_utc=scheduled_for_utc.isoformat(),
                scheduler_config_version=config.version,
                seed=seed,
            )
            for scheduled_for_utc in selected
        )

    @staticmethod
    def _seed(profile_id: str, local_date: date, config_version: int) -> str:
        payload = f"{profile_id}|{local_date.isoformat()}|{config_version}".encode()
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _local_day_bounds(timezone_name: str, local_date: date) -> tuple[datetime, datetime]:
        timezone = ZoneInfo(timezone_name)

        def boundary(day: date) -> datetime:
            local_midnight = datetime.combine(day, time.min)
            for minute_offset in range(48 * 60):
                resolved = _resolve_local_minute(
                    local_midnight + timedelta(minutes=minute_offset),
                    timezone,
                )
                if resolved:
                    return resolved[0]
            raise SchedulerValidationError(
                f"could not resolve a local-day boundary for {day.isoformat()}"
            )

        return boundary(local_date), boundary(local_date + timedelta(days=1))

    async def async_effective_now(self) -> datetime:
        """Return a read-only monotonic wall-clock cutoff for preview/generation."""
        observed = self._aware_utc_now()
        state = await self._settings.async_get(_SCHEDULER_TIME_STATE_KEY)
        if not isinstance(state, Mapping):
            return observed
        raw = state.get("high_watermark_utc")
        if not isinstance(raw, str):
            return observed
        previous = datetime.fromisoformat(raw).astimezone(UTC)
        return max(observed, previous)

    async def async_reconcile(self, *, reason: str) -> SchedulerReconciliation:
        """Persist a monotonic scheduler time watermark across restart/clock jumps."""
        observed = self._aware_utc_now()
        state = await self._settings.async_get(_SCHEDULER_TIME_STATE_KEY)
        previous: datetime | None = None
        if isinstance(state, Mapping):
            raw = state.get("high_watermark_utc")
            if isinstance(raw, str):
                previous = datetime.fromisoformat(raw).astimezone(UTC)

        effective = observed if previous is None else max(observed, previous)
        if previous is None:
            kind = "initial"
        elif observed < previous:
            kind = "clock_backward"
        elif reason == "startup":
            kind = "restart"
        elif reason == "timer" and observed - previous > timedelta(minutes=5):
            kind = "clock_forward"
        else:
            kind = "advance"

        expired_slots = await self._scheduler.async_expire_before(
            before_utc=effective.isoformat(),
            updated_at_utc=effective.isoformat(),
        )
        await self._settings.async_set(
            _SCHEDULER_TIME_STATE_KEY,
            {
                "high_watermark_utc": effective.isoformat(),
                "last_observed_utc": observed.isoformat(),
                "last_reason": reason,
                "kind": kind,
            },
            updated_at_utc=observed.isoformat(),
        )
        return SchedulerReconciliation(
            observed_now_utc=observed,
            effective_now_utc=effective,
            previous_high_watermark_utc=previous,
            expired_slots=expired_slots,
            kind=kind,
            reason=reason,
        )

    def _aware_utc_now(self) -> datetime:
        now = self._clock.now()
        if now.tzinfo is None:
            raise SchedulerValidationError("scheduler clock must return an aware datetime")
        return now.astimezone(UTC)

    @staticmethod
    def _preview_payload(
        *,
        config: SchedulerConfig,
        local_date: date,
        daily_push_budget: int,
        drafts: tuple[SchedulerSlotDraft, ...],
    ) -> dict[str, Any]:
        return {
            "profile_id": config.profile_id,
            "local_date": local_date.isoformat(),
            "timezone": config.timezone,
            "scheduler_config_version": config.version,
            "seed": SchedulerService._seed(
                config.profile_id,
                local_date,
                config.version,
            ),
            "requested_slots": daily_push_budget,
            "generated_slots": len(drafts),
            "capacity_limited": len(drafts) < daily_push_budget,
            "content_selection": "send_time",
            "slots": [draft.as_dict() for draft in drafts],
        }
