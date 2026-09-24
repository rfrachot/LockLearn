"""P4.5 send-time notification content selection policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from ..storage.repositories import CardReference
from .clock import Clock, SystemClock
from .selection import SelectionConstraintError, SelectionDecision


DEFAULT_NEW_TEASER_BUDGET = 2


class NotificationSelectionError(ValueError):
    """Raised when a notification slot cannot be selected safely."""


class NotificationTracksRepository(Protocol):
    async def async_get(self, track_id: str) -> dict[str, Any] | None: ...
    async def async_session_candidates(
        self,
        *,
        profile_id: str,
        track_id: str,
    ) -> tuple[dict[str, Any], ...]: ...


class NotificationProfilesRepository(Protocol):
    async def async_get(self, profile_id: str) -> dict[str, Any] | None: ...


class NotificationReviewRepository(Protocol):
    async def async_introduced_card_keys(
        self,
        *,
        profile_id: str,
        track_id: str,
        local_date: str,
    ) -> frozenset[str]: ...


class NotificationSchedulerRepository(Protocol):
    async def async_get_slot(self, slot_id: str) -> dict[str, Any] | None: ...
    async def async_bind_content_selection(
        self,
        *,
        slot_id: str,
        card: CardReference,
        selection_reason: str,
        updated_at_utc: str,
    ) -> bool: ...
    async def async_count_selected_teasers(
        self,
        *,
        profile_id: str,
        start_utc: str,
        end_utc: str,
    ) -> int: ...


class NotificationConstraintEvaluator(Protocol):
    async def async_evaluate(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        learning_item_id: str,
        state: str,
    ) -> SelectionDecision: ...


@dataclass(frozen=True, slots=True)
class NotificationSelection:
    """Persisted send-time CardDefinition decision."""

    card: CardReference
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "card_key": self.card.card_key,
            "learning_item_id": self.card.learning_item_id,
            "prompt_facet_id": self.card.prompt_facet_id,
            "answer_facet_id": self.card.answer_facet_id,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class _Candidate:
    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    state: str
    next_due_at_utc: str | None
    pack_position: int
    user_state: str
    suspend_until_utc: str | None
    difficulty_factor: float
    last_verified_at_utc: str | None
    last_seen_at_utc: str | None
    self_known_count: int

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> _Candidate:
        return cls(
            card_key=str(row["card_key"]),
            learning_item_id=str(row["learning_item_id"]),
            prompt_facet_id=str(row["prompt_facet_id"]),
            answer_facet_id=str(row["answer_facet_id"]),
            state=str(row["state"]),
            next_due_at_utc=(
                None if row.get("next_due_at_utc") is None else str(row["next_due_at_utc"])
            ),
            pack_position=int(row["pack_position"]),
            user_state=str(row.get("user_state", "active")),
            suspend_until_utc=(
                None if row.get("suspend_until_utc") is None else str(row["suspend_until_utc"])
            ),
            difficulty_factor=float(row.get("difficulty_factor", 1.0)),
            last_verified_at_utc=(
                None
                if row.get("last_verified_at_utc") is None
                else str(row["last_verified_at_utc"])
            ),
            last_seen_at_utc=(
                None if row.get("last_seen_at_utc") is None else str(row["last_seen_at_utc"])
            ),
            self_known_count=int(row.get("self_known_count", 0)),
        )

    @property
    def card(self) -> CardReference:
        return CardReference(
            card_key=self.card_key,
            learning_item_id=self.learning_item_id,
            prompt_facet_id=self.prompt_facet_id,
            answer_facet_id=self.answer_facet_id,
        )


class NotificationSelectionService:
    """Choose one content CardDefinition only when a slot is ready to send."""

    def __init__(
        self,
        tracks: NotificationTracksRepository,
        profiles: NotificationProfilesRepository,
        reviews: NotificationReviewRepository,
        scheduler: NotificationSchedulerRepository,
        constraints: NotificationConstraintEvaluator,
        *,
        clock: Clock | None = None,
        teaser_budget: int = DEFAULT_NEW_TEASER_BUDGET,
    ) -> None:
        if teaser_budget < 0:
            raise NotificationSelectionError("teaser_budget must be >= 0")
        self._tracks = tracks
        self._profiles = profiles
        self._reviews = reviews
        self._scheduler = scheduler
        self._constraints = constraints
        self._clock = clock or SystemClock()
        self._teaser_budget = teaser_budget

    async def async_select_for_slot(self, slot_id: str) -> NotificationSelection | None:
        """Select and persist one CardDefinition, or return None if no candidate exists."""
        slot = await self._scheduler.async_get_slot(slot_id)
        if slot is None:
            raise NotificationSelectionError("slot does not exist")

        existing = self._selection_from_slot(slot)
        if existing is not None:
            return existing

        profile_id = str(slot["profile_id"])
        track_id_raw = slot.get("track_id")
        if not isinstance(track_id_raw, str) or not track_id_raw:
            return None
        track_id = track_id_raw

        profile = await self._profiles.async_get(profile_id)
        track = await self._tracks.async_get(track_id)
        if profile is None or str(profile["status"]) != "active":
            return None
        if (
            track is None
            or str(track["profile_id"]) != profile_id
            or str(track["status"]) != "active"
        ):
            return None

        now = self._clock.now()
        raw_candidates = await self._tracks.async_session_candidates(
            profile_id=profile_id,
            track_id=track_id,
        )
        candidates: list[_Candidate] = []
        for row in raw_candidates:
            candidate = _Candidate.from_row(row)
            if self._user_state_available(candidate, now=now):
                candidates.append(candidate)
        candidates = await self._eligible_candidates(
            profile_id=profile_id,
            track_id=track_id,
            candidates=candidates,
        )
        if not candidates:
            return None

        routine_type = str(slot["slot_type"])
        if routine_type in {"pre_sleep_consolidation", "morning_first_review"}:
            candidates = await self._routine_candidates(
                profile=profile,
                profile_id=profile_id,
                track_id=track_id,
                routine_type=routine_type,
                candidates=candidates,
                now=now,
            )
            if not candidates:
                return None

        teaser_allowed = (
            str(slot["slot_type"]) == "learning"
            and await self._teaser_available(profile_id=profile_id, profile=profile, now=now)
        )
        ranked = self._rank_candidates(
            candidates,
            now=now,
            teaser_allowed=teaser_allowed,
            routine_type=routine_type,
        )
        if not ranked:
            return None

        chosen, reason = ranked[0]
        changed = await self._scheduler.async_bind_content_selection(
            slot_id=slot_id,
            card=chosen.card,
            selection_reason=reason,
            updated_at_utc=now.isoformat(),
        )
        if not changed:
            reloaded = await self._scheduler.async_get_slot(slot_id)
            if reloaded is None:
                raise NotificationSelectionError("slot disappeared during selection")
            return self._selection_from_slot(reloaded)
        return NotificationSelection(card=chosen.card, reason=reason)

    async def _eligible_candidates(
        self,
        *,
        profile_id: str,
        track_id: str,
        candidates: list[_Candidate],
    ) -> list[_Candidate]:
        eligible: list[_Candidate] = []
        for candidate in candidates:
            try:
                decision = await self._constraints.async_evaluate(
                    profile_id=profile_id,
                    track_id=track_id,
                    card_key=candidate.card_key,
                    learning_item_id=candidate.learning_item_id,
                    state=candidate.state,
                )
            except SelectionConstraintError as err:
                raise NotificationSelectionError(str(err)) from err
            if decision.eligible:
                eligible.append(candidate)
        return eligible

    async def _routine_candidates(
        self,
        *,
        profile: dict[str, Any],
        profile_id: str,
        track_id: str,
        routine_type: str,
        candidates: list[_Candidate],
        now: datetime,
    ) -> list[_Candidate]:
        local_date = now.astimezone(ZoneInfo(str(profile["timezone"]))).date()
        target_date = (
            local_date
            if routine_type == "pre_sleep_consolidation"
            else local_date - timedelta(days=1)
        )
        introduced = await self._reviews.async_introduced_card_keys(
            profile_id=profile_id,
            track_id=track_id,
            local_date=target_date.isoformat(),
        )
        return [candidate for candidate in candidates if candidate.card_key in introduced]

    async def _teaser_available(
        self,
        *,
        profile_id: str,
        profile: dict[str, Any],
        now: datetime,
    ) -> bool:
        if self._teaser_budget <= 0:
            return False
        timezone = ZoneInfo(str(profile["timezone"]))
        local_date = now.astimezone(timezone).date()
        start = datetime.combine(local_date, datetime.min.time(), tzinfo=timezone)
        end = datetime.combine(local_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone)
        used = await self._scheduler.async_count_selected_teasers(
            profile_id=profile_id,
            start_utc=start.astimezone(now.tzinfo).isoformat(),
            end_utc=end.astimezone(now.tzinfo).isoformat(),
        )
        return used < self._teaser_budget

    @classmethod
    def _rank_candidates(
        cls,
        candidates: list[_Candidate],
        *,
        now: datetime,
        teaser_allowed: bool,
        routine_type: str,
    ) -> list[tuple[_Candidate, str]]:
        ranked: list[tuple[tuple[Any, ...], _Candidate, str]] = []
        for candidate in candidates:
            category = cls._category(
                candidate,
                now=now,
                teaser_allowed=teaser_allowed,
                routine_type=routine_type,
            )
            if category is None:
                continue
            priority, reason = category
            due = cls._due_timestamp(candidate)
            ranked.append(
                (
                    (
                        priority,
                        due or datetime.max.replace(tzinfo=now.tzinfo),
                        candidate.difficulty_factor,
                        candidate.pack_position,
                        candidate.card_key,
                    ),
                    candidate,
                    reason,
                )
            )
        ranked.sort(key=lambda item: item[0])
        return [(candidate, reason) for _key, candidate, reason in ranked]

    @classmethod
    def _category(
        cls,
        candidate: _Candidate,
        *,
        now: datetime,
        teaser_allowed: bool,
        routine_type: str,
    ) -> tuple[int, str] | None:
        if routine_type == "pre_sleep_consolidation":
            return (0, "routine_pre_sleep")
        if routine_type == "morning_first_review":
            return (0, "routine_morning")

        due = cls._due_timestamp(candidate)
        is_due = due is not None and due <= now
        if candidate.state == "relearning" and is_due:
            return (0, "relearning_due")
        if candidate.state == "review" and is_due:
            return (1, "review_due")
        if candidate.state == "leech" and is_due:
            return (2, "difficult_recoverable")
        if cls._needs_calibration(candidate):
            return (3, "calibration_needed")
        if candidate.state == "new" and teaser_allowed:
            return (4, "teaser_new")
        return None

    @staticmethod
    def _needs_calibration(candidate: _Candidate) -> bool:
        if candidate.state == "new" or candidate.self_known_count <= 0:
            return False
        if candidate.last_seen_at_utc is None:
            return False
        if candidate.last_verified_at_utc is None:
            return True
        return datetime.fromisoformat(candidate.last_seen_at_utc) > datetime.fromisoformat(
            candidate.last_verified_at_utc
        )

    @staticmethod
    def _due_timestamp(candidate: _Candidate) -> datetime | None:
        if candidate.next_due_at_utc is None:
            return None
        due = datetime.fromisoformat(candidate.next_due_at_utc)
        if due.tzinfo is None:
            raise NotificationSelectionError("candidate due timestamp must be timezone-aware")
        return due

    @staticmethod
    def _user_state_available(candidate: _Candidate, *, now: datetime) -> bool:
        if candidate.user_state == "active":
            return True
        if candidate.user_state != "buried" or candidate.suspend_until_utc is None:
            return False
        until = datetime.fromisoformat(candidate.suspend_until_utc)
        if until.tzinfo is None:
            raise NotificationSelectionError("candidate suspend timestamp must be timezone-aware")
        return until <= now

    @staticmethod
    def _selection_from_slot(slot: dict[str, Any]) -> NotificationSelection | None:
        card_key = slot.get("card_key")
        if not isinstance(card_key, str) or not card_key:
            return None
        fields = (
            slot.get("learning_item_id"),
            slot.get("prompt_facet_id"),
            slot.get("answer_facet_id"),
            slot.get("selection_reason"),
        )
        if not all(isinstance(value, str) and value for value in fields):
            raise NotificationSelectionError("slot has incomplete content selection")
        return NotificationSelection(
            card=CardReference(
                card_key=card_key,
                learning_item_id=str(fields[0]),
                prompt_facet_id=str(fields[1]),
                answer_facet_id=str(fields[2]),
            ),
            reason=str(fields[3]),
        )
