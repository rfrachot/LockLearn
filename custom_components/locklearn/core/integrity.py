"""P3.12 undo, integrity rebuild and explicit algorithmic recompute."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo

from ..storage.repositories import ReviewEventRecord
from .clock import Clock, SystemClock
from .learning import LearningStateMachine
from .leeches import LeechPolicyV1
from .review_policy import POLICY_VERSION_V1, ReviewPolicyV1
from .signals import SignalDecision, SignalMode, SignalOutcome, SignalPolicy, SignalQuality


class IntegrityServiceError(ValueError):
    """Raised when undo/rebuild/recompute cannot be performed safely."""


class IntegrityEventsRepository(Protocol):
    async def async_latest_undo_candidate(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
    ) -> dict[str, Any] | None: ...

    async def async_append_undo_compensation(
        self,
        event: ReviewEventRecord,
        *,
        target_event_id: str,
        actor_user_id: str,
    ) -> None: ...

    async def async_rebuild_progress(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int: ...

    async def async_rebuild_stats(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int: ...

    async def async_list_scope_events(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...

    async def async_replace_progress(
        self,
        snapshots: tuple[dict[str, Any], ...],
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int: ...


class IntegrityProgressRepository(Protocol):
    async def async_get(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
    ) -> dict[str, Any] | None: ...


class IntegrityProfilesRepository(Protocol):
    async def async_get(self, profile_id: str) -> dict[str, Any] | None: ...


@dataclass
class _ReplayClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


@dataclass(frozen=True, slots=True)
class RecomputeReport:
    """Explicit report for a deliberate policy recomputation."""

    target_policy_version: int
    event_count: int
    replayed_event_count: int
    control_event_count: int
    fallback_event_count: int
    card_count: int
    divergence_count: int
    applied: bool
    divergences: tuple[dict[str, Any], ...]
    fallback_events: tuple[dict[str, str], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_policy_version": self.target_policy_version,
            "event_count": self.event_count,
            "replayed_event_count": self.replayed_event_count,
            "control_event_count": self.control_event_count,
            "fallback_event_count": self.fallback_event_count,
            "card_count": self.card_count,
            "divergence_count": self.divergence_count,
            "applied": self.applied,
            "divergences": [dict(item) for item in self.divergences],
            "fallback_events": [dict(item) for item in self.fallback_events],
        }


class IntegrityService:
    """Own safe progress undo, snapshot rebuild and deliberate recompute."""

    _COMPARE_FIELDS = (
        "state",
        "mastery",
        "box",
        "seen_count",
        "verified_correct_count",
        "verified_wrong_count",
        "self_known_count",
        "self_review_count",
        "first_seen_at_utc",
        "last_seen_at_utc",
        "last_result",
        "next_due_at_utc",
        "streak_correct",
        "leech_score",
        "difficulty_factor",
        "last_verified_at_utc",
        "verified_success_since_box",
        "policy_version",
        "normalization_version",
    )

    def __init__(
        self,
        events: IntegrityEventsRepository,
        progress: IntegrityProgressRepository,
        profiles: IntegrityProfilesRepository,
        *,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._events = events
        self._progress = progress
        self._profiles = profiles
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))

    async def async_undo_last(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
    ) -> dict[str, Any]:
        """Undo the latest admissible progress mutation by compensation."""
        if card_key is not None and track_id is None:
            raise IntegrityServiceError("card-scoped undo requires track_id")
        target = await self._events.async_latest_undo_candidate(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
        )
        if target is None:
            raise IntegrityServiceError("no admissible progress mutation to undo")

        current = await self._progress.async_get(
            profile_id=profile_id,
            track_id=str(target["track_id"]),
            card_key=str(target["card_key"]),
        )
        if current is None:
            raise IntegrityServiceError("undo target has no current progress")
        if not self._same_progress(current, dict(target["post_state_snapshot"])):
            raise IntegrityServiceError("progress changed after the undo target")

        restored = dict(target["pre_state_snapshot"])
        for overlay in ("user_state", "suspend_until_utc", "content_status"):
            restored[overlay] = current[overlay]
        now = self._clock.now()
        profile = await self._profiles.async_get(profile_id)
        if profile is None:
            raise IntegrityServiceError("profile does not exist")
        timezone_name = str(profile["timezone"])
        local = now.astimezone(ZoneInfo(timezone_name))
        offset = local.utcoffset()

        event = ReviewEventRecord(
            id=self._id_factory(),
            profile_id=profile_id,
            track_id=str(target["track_id"]),
            learning_item_id=str(target["learning_item_id"]),
            prompt_facet_id=str(target["prompt_facet_id"]),
            answer_facet_id=str(target["answer_facet_id"]),
            card_key=str(target["card_key"]),
            mode="undo_compensation",
            question_type="manual",
            result="undone",
            hint_used=False,
            retrieval_occurred=False,
            signal_quality="none",
            policy_version=int(target["policy_version"]),
            dataset_generation=str(target["dataset_generation"]),
            normalization_version=(
                None
                if target["normalization_version"] is None
                else int(target["normalization_version"])
            ),
            pre_state_snapshot=current,
            post_state_snapshot=restored,
            created_at_utc=now.isoformat(),
            local_date=local.date().isoformat(),
            timezone_name=timezone_name,
            utc_offset_minutes=0 if offset is None else int(offset.total_seconds() // 60),
        )
        await self._events.async_append_undo_compensation(
            event,
            target_event_id=str(target["id"]),
            actor_user_id=actor_user_id,
        )
        return {
            "target_event_id": str(target["id"]),
            "compensation_event_id": event.id,
            "progress": restored,
        }

    async def async_rebuild_progress(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> dict[str, Any]:
        rebuilt = await self._events.async_rebuild_progress(
            profile_id=profile_id,
            track_id=track_id,
        )
        return {"rebuilt_cards": rebuilt}

    async def async_rebuild_stats(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> dict[str, Any]:
        rebuilt = await self._events.async_rebuild_stats(
            profile_id=profile_id,
            track_id=track_id,
        )
        return {"rebuilt_days": rebuilt}

    async def async_recompute_progress(
        self,
        *,
        target_policy_version: int,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> RecomputeReport:
        """Recompute supported history under an explicit target policy."""
        if target_policy_version != POLICY_VERSION_V1:
            raise IntegrityServiceError(
                f"unsupported target policy_version: {target_policy_version}"
            )
        events = await self._events.async_list_scope_events(
            profile_id=profile_id,
            track_id=track_id,
        )
        if not events:
            return RecomputeReport(
                target_policy_version=target_policy_version,
                event_count=0,
                replayed_event_count=0,
                control_event_count=0,
                fallback_event_count=0,
                card_count=0,
                divergence_count=0,
                applied=True,
                divergences=(),
                fallback_events=(),
            )

        first_time = self._parse_time(str(events[0]["created_at_utc"]))
        replay_clock = _ReplayClock(first_time)
        learning = LearningStateMachine(clock=replay_clock)
        review_policy = ReviewPolicyV1(clock=replay_clock)
        signals = SignalPolicy(review_policy)

        states: dict[tuple[str, str, str], dict[str, Any]] = {}
        historical_latest: dict[tuple[str, str, str], dict[str, Any]] = {}
        verified_history: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        fallback_events: list[dict[str, str]] = []
        replayed = 0
        controls = 0

        for event in events:
            key = (
                str(event["profile_id"]),
                str(event["track_id"]),
                str(event["card_key"]),
            )
            replay_clock.current = self._parse_time(str(event["created_at_utc"]))
            historical_latest[key] = dict(event["post_state_snapshot"])
            current = states.get(key)
            if current is None:
                current = dict(event["pre_state_snapshot"])

            mode = str(event["mode"])
            if mode == "undo_compensation":
                states[key] = dict(event["post_state_snapshot"])
                controls += 1
                continue
            if mode == "leech_reactivation":
                post = dict(current)
                post["state"] = "review"
                post["updated_at_utc"] = replay_clock.current.isoformat()
                states[key] = post
                controls += 1
                continue

            try:
                post = self._replay_event(
                    current,
                    event=event,
                    learning=learning,
                    signals=signals,
                    target_policy_version=target_policy_version,
                )
            except (ValueError, KeyError):
                post = dict(event["post_state_snapshot"])
                fallback_events.append(
                    {
                        "event_id": str(event["id"]),
                        "mode": mode,
                        "reason": "insufficient_replay_semantics",
                    }
                )
            else:
                replayed += 1
                history = verified_history.setdefault(key, [])
                leech_event = {
                    "mode": mode,
                    "result": str(event["result"]),
                    "retrieval_occurred": bool(event["retrieval_occurred"]),
                    "signal_quality": str(event["signal_quality"]),
                    "pre_state_snapshot": current,
                    "post_state_snapshot": post,
                    "created_at_utc": str(event["created_at_utc"]),
                }
                leech_policy = LeechPolicyV1()
                if leech_policy.is_trusted_verified(leech_event):
                    decision = leech_policy.evaluate(
                        tuple(history),
                        current=leech_event,
                        now=replay_clock.current,
                    )
                    if decision.detected:
                        post["state"] = "leech"
                        post["leech_score"] = max(
                            float(post.get("leech_score", 0.0)),
                            decision.score,
                        )
                    history.append(leech_event)
            states[key] = post

        divergences: list[dict[str, Any]] = []
        for key, recomputed in sorted(states.items()):
            historical = historical_latest[key]
            changed = [
                field
                for field in self._COMPARE_FIELDS
                if recomputed.get(field) != historical.get(field)
            ]
            if changed:
                divergences.append(
                    {
                        "profile_id": key[0],
                        "track_id": key[1],
                        "card_key": key[2],
                        "changed_fields": changed,
                    }
                )

        applied = not fallback_events
        if applied:
            await self._events.async_replace_progress(
                tuple(states.values()),
                profile_id=profile_id,
                track_id=track_id,
            )

        return RecomputeReport(
            target_policy_version=target_policy_version,
            event_count=len(events),
            replayed_event_count=replayed,
            control_event_count=controls,
            fallback_event_count=len(fallback_events),
            card_count=len(states),
            divergence_count=len(divergences),
            applied=applied,
            divergences=tuple(divergences),
            fallback_events=tuple(fallback_events),
        )

    @staticmethod
    def _replay_event(
        snapshot: dict[str, Any],
        *,
        event: dict[str, Any],
        learning: LearningStateMachine,
        signals: SignalPolicy,
        target_policy_version: int,
    ) -> dict[str, Any]:
        mode = str(event["mode"])
        result = str(event["result"]).strip().lower()
        if mode == "introduction":
            post = learning.introduce(snapshot).post_state
        elif mode == "learning_step":
            post = learning.learning_result(
                snapshot,
                success=result in {"correct", "known", "knew"},
            ).post_state
        elif mode == "relearning_step":
            post = learning.relearning_result(
                snapshot,
                success=result in {"correct", "known", "knew"},
            ).post_state
        elif mode in {
            "verified_mcq",
            "verified_free_text",
            "verified_cloze",
            "exam_retrieval",
            "self_assessment_after_retrieval",
        }:
            decision = IntegrityService._decision_from_event(event)
            applied = signals.apply_review_signal(
                snapshot,
                decision=decision,
                hint_used=bool(event["hint_used"]),
            )
            if applied.transition is None:
                post = dict(snapshot)
            else:
                post = dict(applied.transition.post_state)
        else:
            raise ValueError(f"unsupported replay mode: {mode}")

        post["policy_version"] = target_policy_version
        post["dataset_generation"] = str(event["dataset_generation"])
        post["normalization_version"] = event["normalization_version"]
        return post

    @staticmethod
    def _decision_from_event(event: dict[str, Any]) -> SignalDecision:
        mode = SignalMode(str(event["mode"]))
        result = str(event["result"]).strip().lower()
        quality_raw = str(event["signal_quality"])
        quality = (
            SignalQuality.STRONG
            if quality_raw == "verified"
            else SignalQuality(quality_raw)
        )
        positive = result in {"correct", "known", "knew", "easy", "hard"}
        negative = result in {"wrong", "review", "again", "idk"}
        outcome = (
            SignalOutcome.POSITIVE
            if positive
            else SignalOutcome.NEGATIVE
            if negative
            else SignalOutcome.NEUTRAL
        )
        verified_mode = mode in {
            SignalMode.VERIFIED_MCQ,
            SignalMode.VERIFIED_FREE_TEXT,
            SignalMode.VERIFIED_CLOZE,
            SignalMode.EXAM_RETRIEVAL,
        }
        trusted = (
            verified_mode
            and bool(event["retrieval_occurred"])
            and quality in {
                SignalQuality.WEAK,
                SignalQuality.MEDIUM,
                SignalQuality.STRONG,
            }
        )
        return SignalDecision(
            mode=mode,
            outcome=outcome,
            signal_quality=quality,
            retrieval_occurred=bool(event["retrieval_occurred"]),
            verified=trusted,
            gate_eligible=trusted,
            reward_difficulty=positive and trusted and not bool(event["hint_used"]),
            reason="historical_recompute",
        )

    @classmethod
    def _same_progress(cls, left: dict[str, Any], right: dict[str, Any]) -> bool:
        return all(left.get(field) == right.get(field) for field in cls._COMPARE_FIELDS)

    @staticmethod
    def _parse_time(raw: str) -> datetime:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            raise IntegrityServiceError("historical event timestamp must be timezone-aware")
        return parsed
