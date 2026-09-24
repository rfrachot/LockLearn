"""Apply consumed Companion actions through canonical P3 learning state."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..core.clock import Clock, SystemClock
from ..core.learning import LearningStateMachine
from ..core.review_policy import ReviewPolicyV1, ReviewTransition
from ..core.reviews import ReviewEventService
from ..core.scheduler import SchedulerService, SchedulerValidationError
from ..core.signals import SignalMode, SignalPolicy
from ..core.stats import StatsService
from ..storage.repositories import (
    NotificationTargetsRepository,
    ProgressRepository,
    ProfilesRepository,
    ReviewEventsRepository,
    TracksRepository,
)
from .interactions import (
    NotificationActionDisposition,
    NotificationInteractionService,
)
from .renderers import decode_action_id

EventEmitter = Callable[[str, dict[str, Any]], None]

_POSITIVE_RESULTS = frozenset({"correct", "known", "knew", "easy", "hard"})
_NEGATIVE_RESULTS = frozenset({"wrong", "idk", "review", "again"})


class NotificationActionError(ValueError):
    """Raised when a consumed interaction cannot safely become learning state."""


@dataclass(frozen=True, slots=True)
class NotificationActionOutcome:
    """Result of one Companion action after replay/ACL and state processing."""

    disposition: NotificationActionDisposition
    interaction_id: str | None = None
    review_event_id: str | None = None
    pedagogical_applied: bool = False


class NotificationActionProcessor:
    """Bridge P4.6 action claims to canonical P3 ReviewEvent/Progress state."""

    def __init__(
        self,
        interactions: NotificationInteractionService,
        profiles: ProfilesRepository,
        tracks: TracksRepository,
        progress: ProgressRepository,
        targets: NotificationTargetsRepository,
        scheduler: SchedulerService,
        reviews: ReviewEventService,
        review_events: ReviewEventsRepository,
        signal_policy: SignalPolicy,
        review_policy: ReviewPolicyV1,
        stats: StatsService,
        *,
        dataset_generation: Callable[[], str],
        event_emitter: EventEmitter,
        clock: Clock | None = None,
        mastery_threshold: float = 0.75,
    ) -> None:
        self._interactions = interactions
        self._profiles = profiles
        self._tracks = tracks
        self._progress = progress
        self._targets = targets
        self._scheduler = scheduler
        self._reviews = reviews
        self._review_events = review_events
        self._signal_policy = signal_policy
        self._review_policy = review_policy
        self._stats = stats
        self._dataset_generation = dataset_generation
        self._event_emitter = event_emitter
        self._clock = clock or SystemClock()
        self._learning = LearningStateMachine(clock=self._clock)
        self._mastery_threshold = mastery_threshold

    async def async_handle_mobile_action(
        self,
        *,
        action_id: str,
        actor_user_id: str | None,
    ) -> NotificationActionOutcome | None:
        """Consume a LockLearn action and apply at most one canonical outcome."""
        decoded = decode_action_id(action_id)
        if decoded is None:
            return None
        token, semantic = decoded
        claim = await self._interactions.async_consume_action(
            token=token,
            action_id=semantic,
            actor_user_id=actor_user_id,
        )
        if not claim.may_apply_pedagogical_result or claim.interaction is None:
            return NotificationActionOutcome(claim.disposition)

        interaction = claim.interaction
        interaction_id = str(interaction["interaction_id"])
        payload = dict(interaction.get("payload") or {})
        await self._record_receptivity(payload)

        if semantic == "reveal" or (
            semantic == "idk" and payload.get("selection_reason") == "teaser_new"
        ):
            event = await self._apply_introduction_if_needed(interaction, payload)
            return NotificationActionOutcome(
                claim.disposition,
                interaction_id=interaction_id,
                review_event_id=None if event is None else event.id,
                pedagogical_applied=event is not None,
            )

        event = await self._apply_answer(
            interaction=interaction,
            payload=payload,
            semantic=semantic,
        )
        return NotificationActionOutcome(
            claim.disposition,
            interaction_id=interaction_id,
            review_event_id=event.id,
            pedagogical_applied=True,
        )

    async def _record_receptivity(self, payload: dict[str, Any]) -> None:
        slot_id = payload.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id:
            return
        try:
            await self._scheduler.async_record_receptivity_action(
                slot_id=slot_id,
                action="answered",
            )
        except SchedulerValidationError:
            # Receptivity is observational only and must never veto a valid
            # single-use pedagogical claim.
            return

    async def _apply_introduction_if_needed(
        self,
        interaction: dict[str, Any],
        payload: dict[str, Any],
    ) -> Any | None:
        if payload.get("selection_reason") != "teaser_new":
            return None
        identity = await self._identity(interaction)
        current = await self._progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        if current is not None and str(current["state"]) != "new":
            return None
        pre = current or self._new_snapshot(identity)
        transition = self._learning.introduce(pre)
        return await self._reviews.async_record(
            **identity,
            mode="introduction",
            question_type="learning",
            result="exposure",
            signal_quality="none",
            policy_version=self._review_policy.policy_version,
            dataset_generation=str(pre["dataset_generation"]),
            normalization_version=int(pre["normalization_version"]),
            pre_state_snapshot=pre,
            post_state_snapshot=transition.post_state,
            retrieval_occurred=False,
            notification_id=str(interaction["interaction_id"]),
        )

    async def _apply_answer(
        self,
        *,
        interaction: dict[str, Any],
        payload: dict[str, Any],
        semantic: str,
    ) -> Any:
        identity = await self._identity(interaction)
        pre = await self._progress.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            card_key=identity["card_key"],
        )
        if pre is None or str(pre["state"]) == "new":
            raise NotificationActionError(
                "notification answer requires an introduced card"
            )

        kind = str(payload.get("kind", "learning"))
        if kind == "quiz":
            result, answer_id, expected_answer_id = self._quiz_result(payload, semantic)
            mode = SignalMode.VERIFIED_MCQ
            question_type = "mcq"
        elif kind == "learning":
            if semantic == "known":
                result = "known"
            elif semantic in {"review", "idk"}:
                result = semantic
            else:
                raise NotificationActionError("unsupported learning action semantic")
            answer_id = None
            expected_answer_id = None
            mode = SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL
            question_type = "learning"
        else:
            raise NotificationActionError("unsupported notification interaction kind")

        profile = await self._profiles.async_get(identity["profile_id"])
        target = await self._targets.async_get(str(interaction["target_id"]))
        if profile is None or target is None:
            raise NotificationActionError("notification identity disappeared")
        profile_settings = dict(profile.get("settings") or {})
        shared_device = bool(target.get("shared_device", False))
        shared_trusted = bool(
            profile_settings.get("trust_shared_device_responses", False)
        )

        before_stats = await self._stats.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        before_profile_stats = await self._stats.async_get(
            profile_id=identity["profile_id"],
        )
        post, signal_quality, verified, short_step, scheduled_interval, elapsed = self._transition(
            pre=pre,
            mode=mode,
            result=result,
            shared_device=shared_device,
            shared_trusted=shared_trusted,
        )
        self._increment_mode_counters(
            post,
            mode=mode,
            result=result,
            verified=verified,
            short_step=short_step,
        )

        event = await self._reviews.async_record(
            **identity,
            mode=mode.value,
            question_type=question_type,
            result=result,
            answer_id=answer_id,
            expected_answer_id=expected_answer_id,
            signal_quality=signal_quality,
            policy_version=self._review_policy.policy_version,
            dataset_generation=str(pre["dataset_generation"]),
            normalization_version=int(pre["normalization_version"]),
            pre_state_snapshot=pre,
            post_state_snapshot=post,
            retrieval_occurred=True,
            scheduled_interval_days=scheduled_interval,
            elapsed_days=elapsed,
            notification_id=str(interaction["interaction_id"]),
        )
        after_stats = await self._stats.async_get(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        after_profile_stats = await self._stats.async_get(
            profile_id=identity["profile_id"],
        )
        await self._emit_committed_events(
            interaction=interaction,
            identity=identity,
            event=event,
            before_stats=before_stats,
            after_stats=after_stats,
            before_profile_stats=before_profile_stats,
            after_profile_stats=after_profile_stats,
            answer_id=answer_id,
            expected_answer_id=expected_answer_id,
        )
        return event

    def _transition(
        self,
        *,
        pre: dict[str, Any],
        mode: SignalMode,
        result: str,
        shared_device: bool,
        shared_trusted: bool,
    ) -> tuple[dict[str, Any], str, bool, bool, float | None, float | None]:
        state = str(pre["state"])
        if mode is SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL:
            decision = self._signal_policy.evaluate(
                mode=mode,
                result=result,
                retrieval_occurred=True,
                shared_device=shared_device,
                shared_device_trusted=shared_trusted,
            )
            success = result in _POSITIVE_RESULTS
        else:
            decision = self._signal_policy.evaluate(
                mode=mode,
                result=result,
                retrieval_occurred=True,
                shared_device=shared_device,
                shared_device_trusted=shared_trusted,
            )
            success = result == "correct"

        if state in {"learning", "relearning"}:
            transition = (
                self._learning.learning_result(pre, success=success)
                if state == "learning"
                else self._learning.relearning_result(pre, success=success)
            )
            if transition.ready_for_long_review and success:
                graduated = self._review_policy.graduate_short_steps(transition)
                return (
                    dict(graduated.post_state),
                    decision.signal_quality.value,
                    decision.verified,
                    True,
                    graduated.scheduled_interval_days,
                    graduated.elapsed_days,
                )
            return (
                dict(transition.post_state),
                decision.signal_quality.value,
                decision.verified,
                True,
                None,
                None,
            )

        if state not in {"review", "leech"}:
            raise NotificationActionError(f"unsupported progress state: {state}")
        applied = self._signal_policy.apply_review_signal(pre, decision=decision)
        if applied.transition is None:
            raise NotificationActionError("notification answer produced no schedulable transition")
        transition: ReviewTransition = applied.transition
        return (
            dict(transition.post_state),
            decision.signal_quality.value,
            decision.verified,
            False,
            transition.scheduled_interval_days,
            transition.elapsed_days,
        )

    @staticmethod
    def _increment_mode_counters(
        post: dict[str, Any],
        *,
        mode: SignalMode,
        result: str,
        verified: bool,
        short_step: bool,
    ) -> None:
        if mode is SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL:
            field = "self_known_count" if result in _POSITIVE_RESULTS else "self_review_count"
            post[field] = int(post.get(field, 0)) + 1
            return
        if not verified or not short_step:
            return
        if result == "correct":
            post["verified_correct_count"] = int(post.get("verified_correct_count", 0)) + 1
        elif result in {"wrong", "idk"}:
            post["verified_wrong_count"] = int(post.get("verified_wrong_count", 0)) + 1
        post["last_verified_at_utc"] = post.get("updated_at_utc")

    @staticmethod
    def _quiz_result(
        payload: dict[str, Any],
        semantic: str,
    ) -> tuple[str, str | None, str | None]:
        expected = payload.get("expected_answer_id")
        expected_answer_id = str(expected) if isinstance(expected, str) and expected else None
        if semantic == "idk":
            return "idk", None, expected_answer_id
        if not semantic.startswith("choice_"):
            raise NotificationActionError("unsupported quiz action semantic")
        try:
            index = int(semantic.removeprefix("choice_"))
        except ValueError as err:
            raise NotificationActionError("invalid quiz choice index") from err
        options = payload.get("option_ids")
        if not isinstance(options, list) or not all(
            isinstance(value, str) and value for value in options
        ):
            raise NotificationActionError("quiz interaction has no option identity list")
        if index < 0 or index >= len(options):
            raise NotificationActionError("quiz choice index is out of range")
        answer_id = str(options[index])
        if expected_answer_id is None:
            raise NotificationActionError("quiz interaction has no expected answer identity")
        return (
            "correct" if answer_id == expected_answer_id else "wrong",
            answer_id,
            expected_answer_id,
        )

    async def _identity(self, interaction: dict[str, Any]) -> dict[str, str]:
        profile_id = str(interaction["profile_id"])
        track_raw = interaction.get("track_id")
        card_raw = interaction.get("card_key")
        if not isinstance(track_raw, str) or not track_raw:
            raise NotificationActionError("interaction has no track identity")
        if not isinstance(card_raw, str) or not card_raw:
            raise NotificationActionError("interaction has no card identity")
        card = await self._tracks.async_card_reference(
            track_id=track_raw,
            card_key=card_raw,
        )
        if card is None:
            raise NotificationActionError("interaction card is not enabled in track")
        track = await self._tracks.async_get(track_raw)
        if track is None or str(track["profile_id"]) != profile_id:
            raise NotificationActionError("interaction track does not belong to profile")
        return {
            "profile_id": profile_id,
            "track_id": track_raw,
            "card_key": card.card_key,
            "learning_item_id": card.learning_item_id,
            "prompt_facet_id": card.prompt_facet_id,
            "answer_facet_id": card.answer_facet_id,
        }

    def _new_snapshot(self, identity: dict[str, str]) -> dict[str, Any]:
        now = self._clock.now().isoformat()
        return {
            **identity,
            "state": "new",
            "mastery": 0.0,
            "box": 0,
            "seen_count": 0,
            "verified_correct_count": 0,
            "verified_wrong_count": 0,
            "self_known_count": 0,
            "self_review_count": 0,
            "first_seen_at_utc": None,
            "last_seen_at_utc": None,
            "last_result": None,
            "next_due_at_utc": None,
            "streak_correct": 0,
            "leech_score": 0.0,
            "difficulty_factor": 1.0,
            "last_verified_at_utc": None,
            "verified_success_since_box": 0,
            "user_state": "active",
            "suspend_until_utc": None,
            "example_rotation_index": 0,
            "content_status": "active",
            "policy_version": self._review_policy.policy_version,
            "dataset_generation": self._dataset_generation(),
            "normalization_version": 1,
            "updated_at_utc": now,
        }

    async def _emit_committed_events(
        self,
        *,
        interaction: dict[str, Any],
        identity: dict[str, str],
        event: Any,
        before_stats: dict[str, Any],
        after_stats: dict[str, Any],
        before_profile_stats: dict[str, Any],
        after_profile_stats: dict[str, Any],
        answer_id: str | None,
        expected_answer_id: str | None,
    ) -> None:
        counters = await self._result_counters(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            session_id=event.session_id,
            stats=after_stats,
        )
        track = await self._tracks.async_get(identity["track_id"])
        candidates = await self._tracks.async_session_candidates(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
        )
        content_type = next(
            (
                str(item["content_type"])
                for item in candidates
                if str(item["card_key"]) == identity["card_key"]
            ),
            "unknown",
        )
        payload = {
            "event_id": event.id,
            "interaction_id": str(interaction["interaction_id"]),
            "profile_id": identity["profile_id"],
            "track_id": identity["track_id"],
            "card_key": identity["card_key"],
            "session_id": event.session_id,
            "mode": event.mode,
            "result": event.result,
            "streak_correct": int(event.post_state_snapshot.get("streak_correct", 0)),
            "consecutive_correct": counters["consecutive_correct"],
            "consecutive_wrong": counters["consecutive_wrong"],
            "session_accuracy": counters["session_accuracy"],
            "daily_goal_progress": counters["daily_goal_progress"],
            "content_type": content_type,
            "source_language": None if track is None else track.get("source_language"),
            "target_language": None if track is None else track.get("target_language"),
        }
        self._event_emitter("locklearn_answered", payload)

        if event.mode == SignalMode.VERIFIED_MCQ.value:
            event_name = {
                "correct": "locklearn_quiz_correct",
                "wrong": "locklearn_quiz_wrong",
                "idk": "locklearn_quiz_idk",
            }.get(event.result)
            if event_name is not None:
                self._event_emitter(event_name, payload)

        pre_state = str(event.pre_state_snapshot.get("state"))
        post_state = str(event.post_state_snapshot.get("state"))
        if pre_state != "relearning" and post_state == "relearning":
            self._event_emitter("locklearn_card_entered_relearning", payload)
        if pre_state != "leech" and post_state == "leech":
            self._event_emitter("locklearn_leech_detected", payload)

        pre_mastery = float(event.pre_state_snapshot.get("mastery", 0.0))
        post_mastery = float(event.post_state_snapshot.get("mastery", 0.0))
        if pre_mastery < self._mastery_threshold <= post_mastery:
            self._event_emitter("locklearn_card_mastery_threshold_reached", payload)

        if (
            event.mode == SignalMode.VERIFIED_MCQ.value
            and event.result == "wrong"
            and answer_id is not None
            and expected_answer_id is not None
            and answer_id != expected_answer_id
        ):
            self._event_emitter("locklearn_confusion_detected", payload)

        before_status = str(before_stats["streak"]["today"]["status"])
        after_status = str(after_stats["streak"]["today"]["status"])
        if before_status != "success" and after_status == "success":
            self._event_emitter("locklearn_track_goal_reached", payload)
        before_profile_status = str(before_profile_stats["streak"]["today"]["status"])
        after_profile_status = str(after_profile_stats["streak"]["today"]["status"])
        if before_profile_status != "success" and after_profile_status == "success":
            self._event_emitter("locklearn_daily_goal_reached", payload)

    async def _result_counters(
        self,
        *,
        profile_id: str,
        track_id: str,
        session_id: str | None,
        stats: dict[str, Any],
    ) -> dict[str, Any]:
        events = await self._review_events.async_list_scope_events(
            profile_id=profile_id,
            track_id=track_id,
        )
        consecutive_correct = 0
        consecutive_wrong = 0
        for item in reversed(events):
            result = str(item["result"])
            if result in _POSITIVE_RESULTS:
                if consecutive_wrong:
                    break
                consecutive_correct += 1
                continue
            if result in _NEGATIVE_RESULTS:
                if consecutive_correct:
                    break
                consecutive_wrong += 1
                continue
            if consecutive_correct or consecutive_wrong:
                break

        session_accuracy: float | None = None
        if session_id is not None:
            session_events = [
                item
                for item in events
                if item.get("session_id") == session_id
                and str(item["result"]) in {"correct", "wrong", "idk"}
            ]
            if session_events:
                correct = sum(str(item["result"]) == "correct" for item in session_events)
                session_accuracy = round(correct / len(session_events), 6)

        today = stats["streak"]["today"]
        target = int(today["target"])
        daily_goal_progress = (
            0.0
            if target <= 0
            else round(min(1.0, int(today["treated_due"]) / target), 6)
        )
        return {
            "consecutive_correct": consecutive_correct,
            "consecutive_wrong": consecutive_wrong,
            "session_accuracy": session_accuracy,
            "daily_goal_progress": daily_goal_progress,
        }
