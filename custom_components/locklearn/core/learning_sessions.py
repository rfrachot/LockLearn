"""Panel Learn interactions committed atomically with persistent session CAS."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..storage.database import SQLiteStorage
from .clock import Clock, SystemClock
from .learning import LearningStateMachine
from .review_policy import ReviewPolicyV1, ReviewTransition
from .reviews import ReviewEventService
from .sessions import SessionService
from .signals import SignalMode, SignalPolicy


class LearningSessionError(ValueError):
    """Raised when a P5.3 Learn answer violates the session learning contract."""


class LearningSessionService:
    """Apply Learn semantics before advancing the persistent session cursor."""

    def __init__(
        self,
        storage: SQLiteStorage,
        sessions: SessionService,
        reviews: ReviewEventService,
        review_policy: ReviewPolicyV1,
        signal_policy: SignalPolicy,
        *,
        dataset_generation: Callable[[], str],
        clock: Clock | None = None,
    ) -> None:
        self._storage = storage
        self._sessions = sessions
        self._reviews = reviews
        self._review_policy = review_policy
        self._signal_policy = signal_policy
        self._dataset_generation = dataset_generation
        self._clock = clock or SystemClock()
        self._learning = LearningStateMachine(clock=self._clock)

    async def async_answer(
        self,
        session_id: str,
        expected_version: int,
        question_id: str,
        answer: object,
    ) -> dict[str, Any]:
        """Commit one Learn mutation and session CAS as one state.db transaction."""
        if not isinstance(answer, dict) or answer.get("kind") != "learning":
            raise LearningSessionError("learning answer must use kind='learning'")
        action_raw = answer.get("action")
        if not isinstance(action_raw, str):
            raise LearningSessionError("learning answer requires an action")
        action = action_raw.strip().lower()
        hint_used = answer.get("hint_used", False)
        if not isinstance(hint_used, bool):
            raise LearningSessionError("hint_used must be boolean")
        latency = answer.get("presentation_to_answer_ms")
        if latency is not None and (
            isinstance(latency, bool) or not isinstance(latency, int) or latency < 0
        ):
            raise LearningSessionError("presentation_to_answer_ms must be a non-negative integer")

        session = await self._sessions.async_get(session_id)
        if session is None:
            raise LearningSessionError("session not found")
        current = session.get("current_question")
        if not isinstance(current, dict) or current.get("question_id") != question_id:
            raise LearningSessionError("question is no longer current")
        self._require_question_available(current)
        profile_id = str(session["profile_id"])
        track_raw = session.get("track_id")
        if not isinstance(track_raw, str) or not track_raw:
            raise LearningSessionError("learning session requires a track")
        identity = {
            "profile_id": profile_id,
            "track_id": track_raw,
            "card_key": str(current["card_key"]),
            "learning_item_id": str(current["learning_item_id"]),
            "prompt_facet_id": str(current["prompt_facet_id"]),
            "answer_facet_id": str(current["answer_facet_id"]),
        }
        pre = await self._storage.repositories.progress.async_get(
            profile_id=profile_id,
            track_id=track_raw,
            card_key=identity["card_key"],
        )
        pre = self._normalized_pre(pre, identity)
        follow_up: dict[str, Any] | None = None

        if action == "introduce":
            if str(pre["state"]) != "new":
                raise LearningSessionError("only a new card can be introduced")
            transition = self._learning.introduce(pre)
            follow_up = self._first_retrieval_question(current, transition.post_state)
            event = await self._reviews.async_record(
                profile_id=profile_id,
                track_id=track_raw,
                learning_item_id=identity["learning_item_id"],
                prompt_facet_id=identity["prompt_facet_id"],
                answer_facet_id=identity["answer_facet_id"],
                card_key=identity["card_key"],
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
                presentation_to_answer_ms=latency,
                session_id=session_id,
                persist=False,
            )
        elif action in {"known", "review", "idk"}:
            if str(pre["state"]) == "new":
                raise LearningSessionError("new card must be introduced before retrieval")
            event = await self._self_assessment_event(
                pre=pre,
                identity=identity,
                session_id=session_id,
                result=action,
                hint_used=hint_used,
                presentation_to_answer_ms=latency,
            )
        else:
            raise LearningSessionError("unsupported learning action")

        state = await self._storage.async_answer_learning_session(
            event,
            expected_version=expected_version,
            question_id=question_id,
            answer=answer,
            follow_up=follow_up,
        )
        self._sessions.publish(session_id, state)
        return state

    def _require_question_available(self, current: dict[str, Any]) -> None:
        """Reject a scheduled learning-step retrieval before its due instant."""
        payload = current.get("payload")
        if not isinstance(payload, dict):
            return
        raw_available_at = payload.get("available_at_utc")
        if raw_available_at is None:
            return
        if not isinstance(raw_available_at, str):
            raise LearningSessionError("available_at_utc must be an ISO timestamp")
        try:
            available_at = datetime.fromisoformat(raw_available_at)
        except ValueError as err:
            raise LearningSessionError("available_at_utc must be an ISO timestamp") from err
        if available_at.tzinfo is None:
            raise LearningSessionError("available_at_utc must be timezone-aware")
        if self._clock.now() < available_at:
            raise LearningSessionError("learning step is not due yet")

    @staticmethod
    def _first_retrieval_question(
        current: dict[str, Any],
        post_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Queue the mandatory first retrieval after an explicit introduction."""
        available_at = post_state.get("next_due_at_utc")
        if not isinstance(available_at, str) or not available_at:
            raise LearningSessionError("introduction must schedule a first retrieval")

        raw_payload = current.get("payload")
        payload = dict(raw_payload) if isinstance(raw_payload, dict) else {}
        raw_selection = payload.get("selection")
        selection = dict(raw_selection) if isinstance(raw_selection, dict) else {}
        selection["progress_state"] = "learning"
        selection["reason"] = "learning_step"
        payload["selection"] = selection
        payload["available_at_utc"] = available_at

        return {
            "question_id": f"{current['question_id']}:learning-step-1",
            "card_key": str(current["card_key"]),
            "learning_item_id": str(current["learning_item_id"]),
            "prompt_facet_id": str(current["prompt_facet_id"]),
            "answer_facet_id": str(current["answer_facet_id"]),
            "payload": payload,
        }

    async def _self_assessment_event(
        self,
        *,
        pre: dict[str, Any],
        identity: dict[str, str],
        session_id: str,
        result: str,
        hint_used: bool,
        presentation_to_answer_ms: int | None,
    ) -> Any:
        decision = self._signal_policy.evaluate(
            mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL,
            result=result,
            retrieval_occurred=True,
            hint_used=hint_used,
        )
        success = result == "known"
        state = str(pre["state"])
        scheduled_interval: float | None = None
        elapsed: float | None = None

        if state in {"learning", "relearning"}:
            transition = (
                self._learning.learning_result(pre, success=success)
                if state == "learning"
                else self._learning.relearning_result(pre, success=success)
            )
            post = dict(transition.post_state)
            if transition.ready_for_long_review and success:
                graduated = self._review_policy.graduate_short_steps(transition)
                post = dict(graduated.post_state)
                scheduled_interval = graduated.scheduled_interval_days
                elapsed = graduated.elapsed_days
        elif state in {"review", "leech"}:
            applied = self._signal_policy.apply_review_signal(
                pre,
                decision=decision,
                hint_used=hint_used,
            )
            review_transition: ReviewTransition | None = applied.transition
            if review_transition is None:
                raise LearningSessionError("learning answer produced no schedulable transition")
            post = dict(review_transition.post_state)
            scheduled_interval = review_transition.scheduled_interval_days
            elapsed = review_transition.elapsed_days
        else:
            raise LearningSessionError(f"unsupported progress state: {state}")

        counter = "self_known_count" if success else "self_review_count"
        post[counter] = int(post.get(counter, 0)) + 1
        return await self._reviews.async_record(
            profile_id=identity["profile_id"],
            track_id=identity["track_id"],
            learning_item_id=identity["learning_item_id"],
            prompt_facet_id=identity["prompt_facet_id"],
            answer_facet_id=identity["answer_facet_id"],
            card_key=identity["card_key"],
            mode=SignalMode.SELF_ASSESSMENT_AFTER_RETRIEVAL.value,
            question_type="learning",
            result=result,
            signal_quality=decision.signal_quality.value,
            policy_version=self._review_policy.policy_version,
            dataset_generation=str(pre["dataset_generation"]),
            normalization_version=int(pre["normalization_version"]),
            pre_state_snapshot=pre,
            post_state_snapshot=post,
            hint_used=hint_used,
            retrieval_occurred=True,
            scheduled_interval_days=scheduled_interval,
            elapsed_days=elapsed,
            presentation_to_answer_ms=presentation_to_answer_ms,
            session_id=session_id,
            persist=False,
        )

    def _normalized_pre(
        self,
        current: dict[str, Any] | None,
        identity: dict[str, str],
    ) -> dict[str, Any]:
        if current is None:
            return self._new_snapshot(identity)
        pre = dict(current)
        pre["dataset_generation"] = pre.get("dataset_generation") or self._dataset_generation()
        pre["normalization_version"] = pre.get("normalization_version") or 1
        return pre

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
