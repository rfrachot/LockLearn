"""P3.9 fatigue-aware session selection and content-type interleaving."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from hashlib import sha256
from math import ceil
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from .clock import Clock, SystemClock
from .selection import SelectionConstraintError, SelectionDecision

FATIGUE_WINDOW_SIZE = 10
DEFAULT_FATIGUE_ACCURACY_THRESHOLD = 0.6
_NEW_SESSION_TYPES = frozenset({"learn", "learning", "bounded"})
_CALIBRATION_SESSION_TYPES = frozenset({"calibration"})


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
    last_result: str | None
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
            last_result=None if row.get("last_result") is None else str(row["last_result"]),
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
        raw_allow_early = settings.get("allow_early_learning", False)
        if not isinstance(raw_allow_early, bool):
            raise SessionSelectionError("allow_early_learning must be boolean")

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

        normalized_type = session_type.strip().lower()
        effective_settings = dict(settings)
        if (
            normalized_type in _CALIBRATION_SESSION_TYPES
            and "requested_cards" not in effective_settings
        ):
            effective_settings["requested_cards"] = 20
        requested_cards = self._requested_cards(effective_settings, profile)
        if normalized_type in _CALIBRATION_SESSION_TYPES and not 20 <= requested_cards <= 40:
            raise SessionSelectionError("calibration requested_cards must be within [20, 40]")
        allowed_types = self._allowed_content_types(effective_settings)
        leeches_only = bool(settings.get("leeches_only", False))
        allow_early_learning = bool(settings.get("allow_early_learning", False))
        weights = await self._tracks.async_get_content_weights(track_id)
        now = self._clock.now()
        candidate_pool = await self._async_candidate_pool(
            profile_id=profile_id,
            track_id=track_id,
            track=track,
            weights=weights,
            now=now,
            allowed_types=allowed_types,
            leeches_only=leeches_only,
            session_type=session_type,
        )
        candidates = [
            candidate
            for candidate in candidate_pool
            if (normalized_type not in _CALIBRATION_SESSION_TYPES or candidate.state == "new")
            and self._state_available(
                candidate,
                now=now,
                session_type=session_type,
                allow_early_learning=allow_early_learning,
            )
        ]

        if not candidates:
            return ()

        if normalized_type in _CALIBRATION_SESSION_TYPES:
            ordered = self._calibration_sequence(candidates, requested_cards=requested_cards)
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
                            "reason": "calibration",
                            "pack_position": c.pack_position,
                            "content_weight": self._weight(c.content_type, weights),
                        }
                    },
                )
                for c in ordered
            )

        new_quota = await self._remaining_new_quota(
            profile=profile,
            track=track,
            profile_id=profile_id,
            track_id=track_id,
            session_type=session_type,
        )
        if allow_early_learning and session_type.strip().lower() in _NEW_SESSION_TYPES:
            # An explicit user override may exceed the daily introduction target,
            # but it never changes _state_available(): failed/relearning cooldowns
            # remain authoritative.
            new_quota = max(new_quota, requested_cards)
        raw_selection_seed = effective_settings.get("selection_seed")
        selection_seed = (
            raw_selection_seed
            if isinstance(raw_selection_seed, str) and raw_selection_seed
            else None
        )
        ordered = self._build_sequence(
            candidates,
            requested_cards=requested_cards,
            new_quota=new_quota,
            weights=weights,
            selection_seed=selection_seed,
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
                        "early_learning": (
                            allow_early_learning
                            and c.state == "learning"
                            and c.next_due_at_utc is not None
                            and datetime.fromisoformat(c.next_due_at_utc) > now
                        ),
                    }
                },
            )
            for c in ordered
        )

    async def async_availability(
        self,
        *,
        profile_id: str,
        track_id: str,
        session_type: str,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Describe effective selectability using the same gates as session/start."""
        settings = {} if settings is None else dict(settings)
        self.validate_session_settings(settings)
        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise SessionSelectionError("track does not belong to profile")
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise SessionSelectionError("profile does not exist")

        normalized_type = session_type.strip().lower()
        effective_settings = dict(settings)
        if (
            normalized_type in _CALIBRATION_SESSION_TYPES
            and "requested_cards" not in effective_settings
        ):
            effective_settings["requested_cards"] = 20
        requested_cards = self._requested_cards(effective_settings, profile)
        if normalized_type in _CALIBRATION_SESSION_TYPES and not 20 <= requested_cards <= 40:
            raise SessionSelectionError("calibration requested_cards must be within [20, 40]")
        allowed_types = self._allowed_content_types(effective_settings)
        leeches_only = bool(effective_settings.get("leeches_only", False))
        allow_early_learning = bool(effective_settings.get("allow_early_learning", False))
        weights = await self._tracks.async_get_content_weights(track_id)
        now = self._clock.now()

        raw_rows = await self._tracks.async_session_candidates(
            profile_id=profile_id,
            track_id=track_id,
        )
        raw_candidates = [
            _Candidate.from_row(row)
            for row in raw_rows
            if (not leeches_only or str(row["state"]) == "leech")
            and (allowed_types is None or str(row["content_type"]) in allowed_types)
            and self._weight(str(row["content_type"]), weights) > 0
        ]

        planning_snapshot = getattr(self._tracks, "async_planning_snapshot", None)
        selected_cards = len(raw_candidates)
        introduced = sum(candidate.state != "new" for candidate in raw_candidates)
        new_cards = sum(candidate.state == "new" for candidate in raw_candidates)
        if callable(planning_snapshot):
            snapshot = await planning_snapshot(track_id=track_id, now_utc=now.isoformat())
            selected_cards = int(snapshot.get("selected_cards", selected_cards))
            introduced = int(snapshot.get("introduced_cards", introduced))
            new_cards = max(0, selected_cards - introduced)

        remaining_new_quota = await self._remaining_new_quota(
            profile=profile,
            track=track,
            profile_id=profile_id,
            track_id=track_id,
            session_type=session_type,
        )
        timezone = ZoneInfo(str(profile["timezone"]))
        local_now = now.astimezone(timezone)
        quota_reset = datetime.combine(
            local_now.date() + timedelta(days=1),
            time.min,
            tzinfo=timezone,
        )

        blocker_cards: dict[str, set[str]] = {}
        blocker_until: dict[str, datetime | None] = {}
        blocker_forceable: dict[str, bool] = {}
        temporary_cards: set[str] = set()
        prerequisite_cards: set[str] = set()
        future_opportunities: list[tuple[datetime, str]] = []
        due_now_total = 0

        def add_blocker(
            code: str,
            candidate: _Candidate,
            *,
            until: datetime | None = None,
            forceable: bool = False,
        ) -> None:
            blocker_cards.setdefault(code, set()).add(candidate.card_key)
            blocker_forceable[code] = blocker_forceable.get(code, False) or forceable
            if until is not None:
                temporary_cards.add(candidate.card_key)
                current = blocker_until.get(code)
                blocker_until[code] = until if current is None else min(current, until)
            elif code not in blocker_until:
                blocker_until[code] = None
            if code == "prerequisite":
                prerequisite_cards.add(candidate.card_key)

        normalized_type = session_type.strip().lower()
        constraints_required = normalized_type not in _CALIBRATION_SESSION_TYPES
        probe = getattr(self._tracks, "async_has_selection_constraints", None)
        pack_version_id = track.get("pack_version_id")
        if (
            constraints_required
            and callable(probe)
            and isinstance(pack_version_id, str)
            and pack_version_id
        ):
            constraints_required = bool(await probe(pack_version_id))

        for candidate in raw_candidates:
            due: datetime | None = None
            if candidate.next_due_at_utc is not None:
                due = datetime.fromisoformat(candidate.next_due_at_utc)
                if due.tzinfo is None:
                    raise SessionSelectionError("candidate due timestamp must be timezone-aware")
                if candidate.state != "new" and due <= now:
                    due_now_total += 1

            effective = now
            permanent = False
            if candidate.user_state == "suspended":
                add_blocker("suspended", candidate)
                permanent = True
            elif candidate.user_state == "buried":
                if candidate.suspend_until_utc is None:
                    add_blocker("buried", candidate)
                    permanent = True
                else:
                    buried_until = datetime.fromisoformat(candidate.suspend_until_utc)
                    if buried_until.tzinfo is None:
                        raise SessionSelectionError(
                            "candidate suspend timestamp must be timezone-aware"
                        )
                    if buried_until > now:
                        add_blocker("buried", candidate, until=buried_until)
                        effective = max(effective, buried_until)
            elif candidate.user_state == "known_already":
                if due is not None and due > now:
                    add_blocker("known_already_verification", candidate, until=due)
                elif due is None:
                    add_blocker("known_already_verification", candidate)
                if normalized_type != "quiz":
                    permanent = True
                elif due is not None:
                    effective = max(effective, due)

            if constraints_required and not permanent:
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
                if not decision.eligible:
                    blocked_until = (
                        None
                        if decision.blocked_until_utc is None
                        else datetime.fromisoformat(decision.blocked_until_utc)
                    )
                    for reason in decision.reasons:
                        if reason.startswith("prerequisite_"):
                            add_blocker("prerequisite", candidate)
                            permanent = True
                        elif reason.startswith("sibling_buried:"):
                            add_blocker("sibling_gap", candidate, until=blocked_until)
                            if blocked_until is not None:
                                effective = max(effective, blocked_until)
                        elif reason.startswith("confusable_intro_gap:"):
                            add_blocker("confusable_gap", candidate, until=blocked_until)
                            if blocked_until is not None:
                                effective = max(effective, blocked_until)
                        else:
                            permanent = True

            if candidate.state == "new":
                if normalized_type in _CALIBRATION_SESSION_TYPES:
                    pass
                elif normalized_type in _NEW_SESSION_TYPES:
                    if remaining_new_quota <= 0:
                        add_blocker("new_quota", candidate, until=quota_reset, forceable=True)
                        effective = max(effective, quota_reset)
                else:
                    permanent = True
            elif due is None:
                permanent = True
            elif candidate.user_state != "known_already" and due > now:
                forceable = (
                    normalized_type in _NEW_SESSION_TYPES
                    and candidate.state == "learning"
                    and candidate.last_result != "wrong"
                )
                add_blocker("scheduled_step", candidate, until=due, forceable=forceable)
                effective = max(effective, due)

            if not permanent and effective > now:
                reason = (
                    "known_already_verification"
                    if candidate.user_state == "known_already"
                    else "new_quota"
                    if candidate.state == "new" and remaining_new_quota <= 0
                    else "scheduled_step"
                )
                future_opportunities.append((effective, reason))

        candidate_pool = await self._async_candidate_pool(
            profile_id=profile_id,
            track_id=track_id,
            track=track,
            weights=weights,
            now=now,
            allowed_types=allowed_types,
            leeches_only=leeches_only,
            session_type=session_type,
        )
        candidates = [
            candidate
            for candidate in candidate_pool
            if (normalized_type not in _CALIBRATION_SESSION_TYPES or candidate.state == "new")
            and self._state_available(
                candidate,
                now=now,
                session_type=session_type,
                allow_early_learning=allow_early_learning,
            )
        ]
        if normalized_type in _CALIBRATION_SESSION_TYPES:
            normal_selected = self._calibration_sequence(
                candidates,
                requested_cards=requested_cards,
            )
            forced_selected = normal_selected
        else:
            normal_new_quota = remaining_new_quota
            if allow_early_learning and normalized_type in _NEW_SESSION_TYPES:
                normal_new_quota = max(normal_new_quota, requested_cards)
            normal_selected = self._build_sequence(
                candidates,
                requested_cards=requested_cards,
                new_quota=normal_new_quota,
                weights=weights,
            )
            forced_candidates = [
                candidate
                for candidate in candidate_pool
                if self._state_available(
                    candidate,
                    now=now,
                    session_type=session_type,
                    allow_early_learning=True,
                )
            ]
            forced_new_quota = remaining_new_quota
            if normalized_type in _NEW_SESSION_TYPES:
                forced_new_quota = max(forced_new_quota, requested_cards)
            forced_selected = self._build_sequence(
                forced_candidates,
                requested_cards=requested_cards,
                new_quota=forced_new_quota,
                weights=weights,
            )

        normal_new = sum(candidate.state == "new" for candidate in normal_selected)
        forced_new = sum(candidate.state == "new" for candidate in forced_selected)
        next_available: datetime | None = None
        next_available_reason: str | None = None
        if future_opportunities:
            next_available, next_available_reason = min(
                future_opportunities,
                key=lambda value: (value[0], value[1]),
            )

        blocker_order = (
            "scheduled_step",
            "known_already_verification",
            "new_quota",
            "sibling_gap",
            "confusable_gap",
            "buried",
            "prerequisite",
            "suspended",
        )
        blockers = [
            {
                "code": code,
                "count": len(blocker_cards[code]),
                "until_utc": (
                    None if (until := blocker_until.get(code)) is None else until.isoformat()
                ),
                "forceable": bool(blocker_forceable.get(code, False)),
            }
            for code in blocker_order
            if blocker_cards.get(code)
        ]
        known_count = sum(candidate.user_state == "known_already" for candidate in raw_candidates)
        suspended_count = sum(candidate.user_state == "suspended" for candidate in raw_candidates)
        buried_count = sum(candidate.user_state == "buried" for candidate in raw_candidates)

        return {
            "profile_id": profile_id,
            "track_id": track_id,
            "session_type": session_type,
            "available_now": len(normal_selected),
            "selected_cards": selected_cards,
            "introduced_cards": introduced,
            "new_cards": new_cards,
            "due_now_total": due_now_total,
            "known_already_cards": known_count,
            "known_already_pending_verification": known_count,
            "suspended_cards": suspended_count,
            "buried_cards": buried_count,
            "temporarily_blocked_cards": len(temporary_cards),
            "prerequisite_blocked_cards": len(prerequisite_cards),
            "session_capacity": requested_cards,
            "remaining_new_quota": remaining_new_quota,
            "forceable_new": max(0, forced_new - normal_new),
            "forceable_early": max(0, len(forced_selected) - len(normal_selected)),
            "next_due_at_utc": (
                None
                if not future_opportunities
                else min(value[0] for value in future_opportunities).isoformat()
            ),
            "next_available_at_utc": (
                None if next_available is None else next_available.isoformat()
            ),
            "next_available_reason": next_available_reason,
            "blockers": blockers,
        }

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

    async def _async_candidate_pool(
        self,
        *,
        profile_id: str,
        track_id: str,
        track: dict[str, Any],
        weights: dict[str, float],
        now: datetime,
        allowed_types: frozenset[str] | None = None,
        leeches_only: bool = False,
        session_type: str = "learn",
    ) -> list[_Candidate]:
        """Build the shared per-card eligibility pool for start and availability."""
        raw_candidates = await self._tracks.async_session_candidates(
            profile_id=profile_id,
            track_id=track_id,
        )
        constraints_required = session_type.strip().lower() not in _CALIBRATION_SESSION_TYPES
        probe = getattr(self._tracks, "async_has_selection_constraints", None)
        pack_version_id = track.get("pack_version_id")
        if (
            constraints_required
            and callable(probe)
            and isinstance(pack_version_id, str)
            and pack_version_id
        ):
            constraints_required = bool(await probe(pack_version_id))

        candidates: list[_Candidate] = []
        for row in raw_candidates:
            candidate = _Candidate.from_row(row)
            if not self._user_state_available(
                candidate,
                now=now,
                session_type=session_type,
            ):
                continue
            if leeches_only and candidate.state != "leech":
                continue
            if allowed_types is not None and candidate.content_type not in allowed_types:
                continue
            if self._weight(candidate.content_type, weights) <= 0:
                continue
            if constraints_required:
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
                if not decision.eligible:
                    continue
            candidates.append(candidate)
        return candidates

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

    @staticmethod
    def _calibration_sequence(
        candidates: list[_Candidate],
        *,
        requested_cards: int,
    ) -> list[_Candidate]:
        """Return a deterministic spread of new cards for the quick calibration."""
        ordered = sorted(candidates, key=lambda c: (c.pack_position, c.card_key))
        if len(ordered) <= requested_cards:
            return ordered
        return [
            ordered[((2 * index + 1) * len(ordered)) // (2 * requested_cards)]
            for index in range(requested_cards)
        ]

    def _build_sequence(
        self,
        candidates: list[_Candidate],
        *,
        requested_cards: int,
        new_quota: int,
        weights: dict[str, float],
        selection_seed: str | None = None,
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
                    *self._candidate_order_key(c, selection_seed=selection_seed),
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
    def _candidate_order_key(
        candidate: _Candidate,
        *,
        selection_seed: str | None = None,
    ) -> tuple[int, str, str, int, str]:
        priority = {
            "relearning": 0,
            "learning": 1,
            "review": 2,
            "leech": 3,
            "new": 4,
        }[candidate.state]
        seeded_rank = ""
        if selection_seed is not None and candidate.state == "new":
            seeded_rank = sha256(f"{selection_seed}\0{candidate.card_key}".encode()).hexdigest()
        return (
            priority,
            candidate.next_due_at_utc or "",
            seeded_rank,
            candidate.pack_position,
            candidate.card_key,
        )

    @staticmethod
    def _user_state_available(
        candidate: _Candidate,
        *,
        now: datetime,
        session_type: str,
    ) -> bool:
        if candidate.user_state == "active":
            return True
        if candidate.user_state == "known_already":
            if session_type.strip().lower() != "quiz" or candidate.next_due_at_utc is None:
                return False
            due = datetime.fromisoformat(candidate.next_due_at_utc)
            if due.tzinfo is None:
                raise SessionSelectionError("candidate due timestamp must be timezone-aware")
            return due <= now
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
        allow_early_learning: bool = False,
    ) -> bool:
        if candidate.state == "new":
            normalized = session_type.strip().lower()
            return normalized in _NEW_SESSION_TYPES or normalized in _CALIBRATION_SESSION_TYPES
        if candidate.state not in {"learning", "review", "relearning", "leech"}:
            return False
        if candidate.next_due_at_utc is None:
            return False
        due = datetime.fromisoformat(candidate.next_due_at_utc)
        if due.tzinfo is None:
            raise SessionSelectionError("candidate due timestamp must be timezone-aware")
        if due <= now:
            return True
        return (
            allow_early_learning
            and session_type.strip().lower() in _NEW_SESSION_TYPES
            and candidate.state == "learning"
            and candidate.last_result != "wrong"
        )

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
