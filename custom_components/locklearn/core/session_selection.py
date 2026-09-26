"""P3.9 fatigue-aware session selection and content-type interleaving."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import ceil
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from .clock import Clock, SystemClock
from .selection import SelectionConstraintError, SelectionDecision

FATIGUE_WINDOW_SIZE = 10
DEFAULT_FATIGUE_ACCURACY_THRESHOLD = 0.6
_NEW_SESSION_TYPES = frozenset({"learn", "learning", "bounded"})


class SessionSelectionError(ValueError):
    """Raised when a session selection request cannot be interpreted safely."""


class SessionConstraintEvaluator(Protocol):
    async def async_evaluate(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        learning_item_id: str,
        state: str,
    ) -> SelectionDecision: ...


class SessionTracksRepository(Protocol):
    async def async_get(self, track_id: str) -> dict[str, Any] | None: ...
    async def async_get_content_weights(self, track_id: str) -> dict[str, float]: ...
    async def async_session_candidates(
        self, *, profile_id: str, track_id: str
    ) -> tuple[dict[str, Any], ...]: ...


class SessionProfilesRepository(Protocol):
    async def async_get(self, profile_id: str) -> dict[str, Any] | None: ...


class SessionReviewRepository(Protocol):
    async def async_count_introductions(
        self, *, profile_id: str, track_id: str, local_date: str
    ) -> int: ...
    async def async_recent_session_verified_results(
        self, session_id: str, *, limit: int
    ) -> tuple[str, ...]: ...


@dataclass(frozen=True, slots=True)
class PreparedSessionSelection:
    """One backend-selected CardDefinition ready for session persistence."""

    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FatigueAdvice:
    """Advisory-only fatigue signal derived from canonical verified retrievals."""

    detected: bool
    sample_size: int
    verified_accuracy: float | None
    threshold: float
    actions: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "sample_size": self.sample_size,
            "verified_accuracy": self.verified_accuracy,
            "threshold": self.threshold,
            "actions": list(self.actions),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class _Candidate:
    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    content_type: str
    state: str
    next_due_at_utc: str | None
    pack_position: int
    user_state: str
    suspend_until_utc: str | None
    confusable_group_ids: tuple[str, ...]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> _Candidate:
        return cls(
            card_key=str(row["card_key"]),
            learning_item_id=str(row["learning_item_id"]),
            prompt_facet_id=str(row["prompt_facet_id"]),
            answer_facet_id=str(row["answer_facet_id"]),
            content_type=str(row["content_type"]),
            state=str(row["state"]),
            next_due_at_utc=(
                None if row.get("next_due_at_utc") is None else str(row["next_due_at_utc"])
            ),
            pack_position=int(row["pack_position"]),
            user_state=str(row.get("user_state", "active")),
            suspend_until_utc=(
                None if row.get("suspend_until_utc") is None else str(row["suspend_until_utc"])
            ),
            confusable_group_ids=tuple(str(v) for v in row.get("confusable_group_ids", ())),
        )

    @property
    def reason(self) -> str:
        return "new" if self.state == "new" else f"{self.state}_due"


class SessionSelectionService:
    """Prepare finite explainable sessions without mutating SRS history."""

    def __init__(
        self,
        tracks: SessionTracksRepository,
        profiles: SessionProfilesRepository,
        reviews: SessionReviewRepository,
        constraints: SessionConstraintEvaluator,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._tracks = tracks
        self._profiles = profiles
        self._reviews = reviews
        self._constraints = constraints
        self._clock = clock or SystemClock()

    def validate_session_settings(self, settings: dict[str, Any]) -> None:
        """Validate settings that apply even before card preparation."""
        self._fatigue_threshold(settings)
        raw_leeches_only = settings.get("leeches_only", False)
        if not isinstance(raw_leeches_only, bool):
            raise SessionSelectionError("leeches_only must be boolean")

    async def async_prepare(
        self,
        *,
        profile_id: str,
        track_id: str,
        session_type: str,
        settings: dict[str, Any],
    ) -> tuple[PreparedSessionSelection, ...]:
        """Select due/new cards, then interleave content types deterministically."""
        self.validate_session_settings(settings)
        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise SessionSelectionError("track does not belong to profile")
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise SessionSelectionError("profile does not exist")

        requested_cards = self._requested_cards(settings, profile)
        allowed_types = self._allowed_content_types(settings)
        leeches_only = bool(settings.get("leeches_only", False))
        weights = await self._tracks.async_get_content_weights(track_id)
        raw_candidates = await self._tracks.async_session_candidates(
            profile_id=profile_id,
            track_id=track_id,
        )
        now = self._clock.now()
        candidates: list[_Candidate] = []
        for row in raw_candidates:
            candidate = _Candidate.from_row(row)
            if not self._user_state_available(candidate, now=now):
                continue
            if leeches_only and candidate.state != "leech":
                continue
            if allowed_types is not None and candidate.content_type not in allowed_types:
                continue
            if self._weight(candidate.content_type, weights) <= 0:
                continue
            if not self._state_available(candidate, now=now, session_type=session_type):
                continue
            try:
                decision = await self._constraints.async_evaluate(
                    profile_id=profile_id,
                    track_id=track_id,
                    card_key=candidate.card_key,
                    learning_item_id=candidate.learning_item_id,
                    state=candidate.state,
                )
            except SelectionConstraintError as err:
                raise SessionSelectionError(str(err)) from err
            if decision.eligible:
                candidates.append(candidate)

        if not candidates:
            return ()

        new_quota = await self._remaining_new_quota(
            profile=profile,
            track=track,
            profile_id=profile_id,
            track_id=track_id,
            session_type=session_type,
        )
        ordered = self._build_sequence(
            candidates,
            requested_cards=requested_cards,
            new_quota=new_quota,
            weights=weights,
        )
        return tuple(
            PreparedSessionSelection(
                card_key=c.card_key,
                learning_item_id=c.learning_item_id,
                prompt_facet_id=c.prompt_facet_id,
                answer_facet_id=c.answer_facet_id,
                payload={
                    "selection": {
                        "content_type": c.content_type,
                        "progress_state": c.state,
                        "reason": c.reason,
                        "pack_position": c.pack_position,
                        "content_weight": self._weight(c.content_type, weights),
                    }
                },
            )
            for c in ordered
        )

    async def async_fatigue_advice(
        self,
        session_id: str,
        *,
        settings: dict[str, Any],
        active: bool = True,
    ) -> FatigueAdvice:
        """Evaluate the last ten trusted verified retrievals without changing SRS."""
        threshold = self._fatigue_threshold(settings)
        results = await self._reviews.async_recent_session_verified_results(
            session_id,
            limit=FATIGUE_WINDOW_SIZE,
        )
        accuracy = (
            None if not results else sum(result == "correct" for result in results) / len(results)
        )
        if len(results) < FATIGUE_WINDOW_SIZE:
            return FatigueAdvice(
                detected=False,
                sample_size=len(results),
                verified_accuracy=accuracy,
                threshold=threshold,
                actions=(),
                reason="insufficient_verified_sample",
            )

        detected = active and accuracy is not None and accuracy < threshold
        return FatigueAdvice(
            detected=detected,
            sample_size=FATIGUE_WINDOW_SIZE,
            verified_accuracy=accuracy,
            threshold=threshold,
            actions=("finish", "recognition_only", "continue") if detected else (),
            reason="verified_accuracy_drop" if detected else "verified_accuracy_ok",
        )

    async def _remaining_new_quota(
        self,
        *,
        profile: dict[str, Any],
        track: dict[str, Any],
        profile_id: str,
        track_id: str,
        session_type: str,
    ) -> int:
        if session_type.strip().lower() not in _NEW_SESSION_TYPES:
            return 0
        profile_settings = dict(profile.get("settings", {}))
        max_new = int(profile_settings.get("max_new_per_day_cards", 0))
        plan = dict(track.get("settings", {})).get("learning_plan")
        if isinstance(plan, dict) and "max_new_per_day_cards" in plan:
            max_new = int(plan["max_new_per_day_cards"])
        if max_new <= 0:
            return 0

        local_date = (
            self._clock.now().astimezone(ZoneInfo(str(profile["timezone"]))).date().isoformat()
        )
        introduced = await self._reviews.async_count_introductions(
            profile_id=profile_id,
            track_id=track_id,
            local_date=local_date,
        )
        return max(0, max_new - introduced)

    def _build_sequence(
        self,
        candidates: list[_Candidate],
        *,
        requested_cards: int,
        new_quota: int,
        weights: dict[str, float],
    ) -> list[_Candidate]:
        due = [c for c in candidates if c.state != "new"]
        scheduled_due = [c for c in due if c.state != "leech"]
        new = [c for c in candidates if c.state == "new"]
        due_target = min(len({c.learning_item_id for c in scheduled_due}), requested_cards)
        new_target = min(
            new_quota,
            len({candidate.learning_item_id for candidate in new}),
            max(0, requested_cards - due_target),
        )
        final_quarter_start = ceil(requested_cards * 0.75)
        strict_due_count = min(
            requested_cards,
            len({c.learning_item_id for c in due if c.state in {"relearning", "learning"}}),
        )
        new_target = min(
            new_target,
            max(0, final_quarter_start - strict_due_count),
        )

        remaining = list(candidates)
        selected: list[_Candidate] = []
        selected_items: set[str] = set()
        selected_new_groups: set[str] = set()
        selected_type_counts: dict[str, int] = {}
        selected_new = 0
        selected_review = 0
        target_review = min(
            len({c.learning_item_id for c in due if c.state == "review"}),
            max(0, requested_cards - strict_due_count - new_target),
        )

        while len(selected) < requested_cards:
            position = len(selected)
            available = [
                c
                for c in remaining
                if self._prospectively_allowed(
                    c,
                    position=position,
                    final_quarter_start=final_quarter_start,
                    selected_items=selected_items,
                    selected_new_groups=selected_new_groups,
                    selected_new=selected_new,
                    new_target=new_target,
                )
            ]
            if not available:
                break
            state_pool = self._state_pool(
                available,
                position=position,
                final_quarter_start=final_quarter_start,
                selected_new=selected_new,
                new_target=new_target,
                selected_review=selected_review,
                target_review=target_review,
            )
            if not state_pool:
                break

            chosen = min(
                state_pool,
                key=lambda c: (
                    selected_type_counts.get(c.content_type, 0)
                    / self._weight(c.content_type, weights),
                    *self._candidate_order_key(c),
                ),
            )
            selected.append(chosen)
            remaining.remove(chosen)
            selected_items.add(chosen.learning_item_id)
            selected_type_counts[chosen.content_type] = (
                selected_type_counts.get(chosen.content_type, 0) + 1
            )
            if chosen.state == "new":
                selected_new += 1
                selected_new_groups.update(chosen.confusable_group_ids)
            elif chosen.state == "review":
                selected_review += 1

        return selected

    @staticmethod
    def _state_pool(
        available: list[_Candidate],
        *,
        position: int,
        final_quarter_start: int,
        selected_new: int,
        new_target: int,
        selected_review: int,
        target_review: int,
    ) -> list[_Candidate]:
        for state in ("relearning", "learning"):
            pool = [c for c in available if c.state == state]
            if pool:
                return pool

        reviews = [c for c in available if c.state == "review"]
        leeches = [c for c in available if c.state == "leech"]
        new = [c for c in available if c.state == "new"]
        if not new or position >= final_quarter_start or selected_new >= new_target:
            return reviews or leeches
        remaining_pre_final_slots = max(0, final_quarter_start - position)
        remaining_new = max(0, new_target - selected_new)
        if remaining_new >= remaining_pre_final_slots:
            return new
        if not reviews or target_review <= 0:
            return new if new else leeches

        new_progress = selected_new / max(1, new_target)
        review_progress = selected_review / target_review
        return new if new_progress <= review_progress else reviews

    @staticmethod
    def _prospectively_allowed(
        candidate: _Candidate,
        *,
        position: int,
        final_quarter_start: int,
        selected_items: set[str],
        selected_new_groups: set[str],
        selected_new: int,
        new_target: int,
    ) -> bool:
        if candidate.state in {"new", "review"} and candidate.learning_item_id in selected_items:
            return False
        if candidate.state != "new":
            return True
        if position >= final_quarter_start or selected_new >= new_target:
            return False
        return not selected_new_groups.intersection(candidate.confusable_group_ids)

    @staticmethod
    def _candidate_order_key(candidate: _Candidate) -> tuple[int, str, int, str]:
        priority = {
            "relearning": 0,
            "learning": 1,
            "review": 2,
            "leech": 3,
            "new": 4,
        }[candidate.state]
        return (
            priority,
            candidate.next_due_at_utc or "",
            candidate.pack_position,
            candidate.card_key,
        )

    @staticmethod
    def _user_state_available(candidate: _Candidate, *, now: datetime) -> bool:
        if candidate.user_state == "active":
            return True
        if candidate.user_state != "buried" or candidate.suspend_until_utc is None:
            return False
        until = datetime.fromisoformat(candidate.suspend_until_utc)
        if until.tzinfo is None:
            raise SessionSelectionError("candidate suspend timestamp must be timezone-aware")
        return until <= now

    @staticmethod
    def _state_available(
        candidate: _Candidate,
        *,
        now: datetime,
        session_type: str,
    ) -> bool:
        if candidate.state == "new":
            return session_type.strip().lower() in _NEW_SESSION_TYPES
        if candidate.state not in {"learning", "review", "relearning", "leech"}:
            return False
        if candidate.next_due_at_utc is None:
            return False
        due = datetime.fromisoformat(candidate.next_due_at_utc)
        if due.tzinfo is None:
            raise SessionSelectionError("candidate due timestamp must be timezone-aware")
        return due <= now

    @staticmethod
    def _requested_cards(settings: dict[str, Any], profile: dict[str, Any]) -> int:
        raw = settings.get("requested_cards")
        if raw is None:
            raw = dict(profile.get("settings", {})).get("session_length_cards", 20)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            raise SessionSelectionError("requested_cards must be a positive integer")
        return raw

    @staticmethod
    def _allowed_content_types(settings: dict[str, Any]) -> frozenset[str] | None:
        raw = settings.get("content_types")
        if raw is None:
            return None
        if not isinstance(raw, (list, tuple)) or not raw:
            raise SessionSelectionError("content_types must be a non-empty list")
        normalized = frozenset(str(value).strip() for value in raw)
        if not normalized or "" in normalized:
            raise SessionSelectionError("content_types must contain non-empty values")
        return normalized

    @staticmethod
    def _weight(content_type: str, weights: dict[str, float]) -> float:
        if not weights:
            return 1.0
        return max(0.0, float(weights.get(content_type, 0.0)))

    @staticmethod
    def _fatigue_threshold(settings: dict[str, Any]) -> float:
        raw = settings.get(
            "fatigue_accuracy_threshold",
            DEFAULT_FATIGUE_ACCURACY_THRESHOLD,
        )
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise SessionSelectionError("fatigue_accuracy_threshold must be numeric")
        threshold = float(raw)
        if not 0.0 <= threshold <= 1.0:
            raise SessionSelectionError("fatigue_accuracy_threshold must be within [0, 1]")
        return threshold
