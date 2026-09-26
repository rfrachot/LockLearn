"""P5.4 persistent quiz orchestration over the P3 quiz/grading primitives."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..storage.database import SQLiteStorage
from .clock import Clock, SystemClock
from .content import GradingOutcome, GradingPolicyKind
from .grading import FreeTextGrader, FreeTextGradingResult, GradingError
from .learning import LearningStateMachine
from .localization import (
    CaseMode,
    NormalizationPolicy,
    PunctuationMode,
    UnicodeNormalization,
    WhitespaceMode,
)
from .presentation import CardPresentationService
from .quiz import (
    DistractorStrategy,
    QuizCandidate,
    QuizConstructionError,
    QuizEngine,
    QuizFormat,
    QuizPrompt,
    QuizQuestion,
)
from .review_policy import ReviewPolicyV1
from .reviews import ReviewEventService
from .session_selection import PreparedSessionSelection
from .sessions import SessionQuestion, SessionService
from .signals import SignalMode, SignalOutcome, SignalPolicy


class QuizSessionError(ValueError):
    """Raised when a P5.4 quiz request violates the backend contract."""


@dataclass(frozen=True, slots=True)
class _AnswerTerm:
    term_id: str
    text: str
    normalized_text: str
    normalization_version: int
    script: str | None


@dataclass(frozen=True, slots=True)
class _QuizCardMeta:
    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    content_type: str
    grading_policy_kind: str
    grading_policy_version: int
    answer_terms: tuple[_AnswerTerm, ...]
    concept_ids: frozenset[str]
    tag_ids: frozenset[str]
    confusable_group_ids: frozenset[str]

    @property
    def canonical_answer(self) -> _AnswerTerm:
        if not self.answer_terms:
            raise QuizSessionError(f"card has no textual accepted answer: {self.card_key}")
        return self.answer_terms[0]


class QuizSessionService:
    """Prepare, evaluate and atomically commit panel quiz questions."""

    def __init__(
        self,
        storage: SQLiteStorage,
        sessions: SessionService,
        presentation: CardPresentationService,
        reviews: ReviewEventService,
        review_policy: ReviewPolicyV1,
        signal_policy: SignalPolicy,
        quiz: QuizEngine,
        grading: FreeTextGrader,
        *,
        dataset_generation: Callable[[], str],
        event_emitter: Callable[[str, dict[str, Any]], None] | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._storage = storage
        self._sessions = sessions
        self._presentation = presentation
        self._reviews = reviews
        self._review_policy = review_policy
        self._signal_policy = signal_policy
        self._quiz = quiz
        self._grading = grading
        self._dataset_generation = dataset_generation
        self._event_emitter = event_emitter
        self._clock = clock or SystemClock()
        self._learning = LearningStateMachine(clock=self._clock)

    async def async_prepare_questions(
        self,
        *,
        track_id: str,
        selected: tuple[PreparedSessionSelection, ...],
        settings: dict[str, Any],
    ) -> tuple[SessionQuestion, ...]:
        """Build safe client payloads without exposing accepted answers."""
        requested_format = self._quiz_format(settings)
        option_count = self._option_count(settings)
        catalog = await self._load_catalog(track_id)
        prepared: list[SessionQuestion] = []

        for selection in selected:
            state = str(selection.payload.get("selection", {}).get("progress_state", ""))
            if state == "new":
                continue
            meta = catalog.get(selection.card_key)
            if meta is None or not meta.answer_terms:
                continue
            presentation = await self._presentation.async_for_card(
                track_id=track_id,
                card_key=selection.card_key,
            )
            cloze_prompt = self._cloze_prompt(presentation, meta.answer_terms)
            resolved_format = self._resolve_format(
                requested_format,
                meta=meta,
                cloze_prompt=cloze_prompt,
                ordinal=len(prepared),
            )
            if resolved_format is None:
                continue

            quiz_payload = self._base_payload(
                resolved_format,
                presentation=presentation,
                meta=meta,
            )
            if resolved_format in {"mcq", "cloze_mcq"}:
                try:
                    question = self._build_choice_question(
                        meta,
                        catalog=catalog,
                        state=state,
                        presentation=presentation,
                        cloze_prompt=cloze_prompt,
                        option_count=option_count,
                        presentation_index=len(prepared),
                    )
                except QuizConstructionError:
                    if requested_format != "mixed" or not self._free_text_supported(meta):
                        continue
                    resolved_format = "free_text"
                    quiz_payload = self._base_payload(
                        resolved_format,
                        presentation=presentation,
                        meta=meta,
                    )
                else:
                    quiz_payload.update(
                        {
                            "format": question.format.value,
                            "prompt_text": question.prompt_text,
                            "context_hint": question.context_hint,
                            "options": [
                                {
                                    "answer_id": option.answer_id,
                                    "text": option.display_text,
                                }
                                for option in question.options
                            ],
                            "idk_available": question.idk_available,
                            "reportable": question.reportable,
                        }
                    )

            payload = dict(selection.payload)
            payload["quiz"] = quiz_payload
            prepared.append(
                SessionQuestion(
                    question_id=f"q-{len(prepared) + 1}-{selection.card_key}",
                    card_key=selection.card_key,
                    learning_item_id=selection.learning_item_id,
                    prompt_facet_id=selection.prompt_facet_id,
                    answer_facet_id=selection.answer_facet_id,
                    payload=payload,
                )
            )
        return tuple(prepared)

    async def async_evaluate(
        self,
        session_id: str,
        question_id: str,
        answer: object,
    ) -> dict[str, Any]:
        """Evaluate the current answer without mutating the session or SRS."""
        session = await self._sessions.async_get(session_id)
        if session is None:
            raise QuizSessionError("session not found")
        return await self._evaluate_current(session, question_id, answer)

    async def async_answer(
        self,
        session_id: str,
        expected_version: int,
        question_id: str,
        answer: object,
    ) -> dict[str, Any]:
        """Re-evaluate and commit one verified quiz signal with session CAS."""
        session = await self._sessions.async_get(session_id)
        if session is None:
            raise QuizSessionError("session not found")
        feedback = await self._evaluate_current(session, question_id, answer)
        current = session.get("current_question")
        assert isinstance(current, dict)
        track_id = session.get("track_id")
        if not isinstance(track_id, str) or not track_id:
            raise QuizSessionError("quiz session requires a track")
        profile_id = str(session["profile_id"])
        catalog = await self._load_catalog(track_id)
        meta = catalog.get(str(current["card_key"]))
        if meta is None:
            raise QuizSessionError("quiz card metadata is unavailable")

        pre = await self._storage.repositories.progress.async_get(
            profile_id=profile_id,
            track_id=track_id,
            card_key=meta.card_key,
        )
        if pre is None or str(pre.get("state")) == "new":
            raise QuizSessionError("quiz requires an introduced card")
        pre = dict(pre)
        pre["dataset_generation"] = pre.get("dataset_generation") or self._dataset_generation()
        pre["normalization_version"] = (
            pre.get("normalization_version") or meta.canonical_answer.normalization_version
        )

        result = str(feedback["result"])
        quiz_format = str(feedback["format"])
        hint_used = bool(feedback["hint_used"])
        mode = {
            "mcq": SignalMode.VERIFIED_MCQ,
            "cloze_mcq": SignalMode.VERIFIED_CLOZE,
            "free_text": SignalMode.VERIFIED_FREE_TEXT,
        }[quiz_format]
        decision = self._signal_policy.evaluate(
            mode=mode,
            result=result,
            retrieval_occurred=True,
            hint_used=hint_used,
        )
        post, scheduled_interval, elapsed_days = self._apply_signal(
            pre,
            decision=decision,
            hint_used=hint_used,
        )

        event = await self._reviews.async_record(
            profile_id=profile_id,
            track_id=track_id,
            learning_item_id=meta.learning_item_id,
            prompt_facet_id=meta.prompt_facet_id,
            answer_facet_id=meta.answer_facet_id,
            card_key=meta.card_key,
            mode=mode.value,
            question_type=quiz_format,
            result=result,
            answer_id=feedback.get("selected_answer_id"),
            expected_answer_id=meta.canonical_answer.term_id,
            hint_used=hint_used,
            retrieval_occurred=True,
            scheduled_interval_days=scheduled_interval,
            elapsed_days=elapsed_days,
            grading_result=(result if quiz_format == "free_text" else None),
            signal_quality=decision.signal_quality.value,
            policy_version=self._review_policy.policy_version,
            dataset_generation=str(pre["dataset_generation"]),
            normalization_version=meta.canonical_answer.normalization_version,
            pre_state_snapshot=pre,
            post_state_snapshot=post,
            presentation_to_answer_ms=feedback.get("presentation_to_answer_ms"),
            session_id=session_id,
            persist=False,
        )
        state = await self._storage.async_answer_learning_session(
            event,
            expected_version=expected_version,
            question_id=question_id,
            answer=answer,
        )
        self._sessions.publish(session_id, state)
        self._emit_event(event.id, profile_id, track_id, meta.card_key, session_id, mode, result)
        return state

    async def _evaluate_current(
        self,
        session: dict[str, Any],
        question_id: str,
        answer: object,
    ) -> dict[str, Any]:
        if str(session.get("type")) != "quiz":
            raise QuizSessionError("session is not a quiz session")
        current = session.get("current_question")
        if not isinstance(current, dict) or current.get("question_id") != question_id:
            raise QuizSessionError("question is no longer current")
        if not isinstance(answer, dict) or answer.get("kind") != "quiz":
            raise QuizSessionError("quiz answer must use kind='quiz'")

        raw_payload = current.get("payload")
        quiz_payload = raw_payload.get("quiz") if isinstance(raw_payload, dict) else None
        if not isinstance(quiz_payload, dict):
            raise QuizSessionError("current question has no quiz payload")
        quiz_format = str(quiz_payload.get("format", ""))
        if quiz_format not in {"mcq", "cloze_mcq", "free_text"}:
            raise QuizSessionError("unsupported quiz format")

        hint_used = answer.get("hint_used", False)
        if not isinstance(hint_used, bool):
            raise QuizSessionError("hint_used must be boolean")
        latency = answer.get("presentation_to_answer_ms")
        if latency is not None and (
            isinstance(latency, bool) or not isinstance(latency, int) or latency < 0
        ):
            raise QuizSessionError("presentation_to_answer_ms must be a non-negative integer")

        track_id = session.get("track_id")
        if not isinstance(track_id, str) or not track_id:
            raise QuizSessionError("quiz session requires a track")
        catalog = await self._load_catalog(track_id)
        meta = catalog.get(str(current["card_key"]))
        if meta is None:
            raise QuizSessionError("quiz card metadata is unavailable")

        if quiz_format == "free_text":
            result = self._evaluate_free_text(meta, answer)
            return {
                **result,
                "format": quiz_format,
                "hint_used": hint_used,
                "presentation_to_answer_ms": latency,
                "selected_answer_id": None,
            }

        selected = answer.get("selected_answer_id")
        if selected is not None and not isinstance(selected, str):
            raise QuizSessionError("selected_answer_id must be a string or null")
        question = self._choice_question_from_payload(
            meta,
            catalog=catalog,
            payload=quiz_payload,
        )
        feedback = self._quiz.feedback(question, selected_answer_id=selected)
        selected_text = next(
            (
                option.display_text
                for option in question.options
                if option.answer_id == selected
            ),
            None,
        )
        return {
            "format": quiz_format,
            "result": feedback.result.value,
            "immediate": feedback.immediate,
            "reveal_correct_answer": feedback.reveal_correct_answer,
            "correct_answer": feedback.correct_answer,
            "contrastive_feedback": feedback.contrastive_feedback,
            "selected_answer_id": selected,
            "selected_answer": selected_text,
            "reportable": True,
            "hint_used": hint_used,
            "presentation_to_answer_ms": latency,
        }

    def _evaluate_free_text(
        self,
        meta: _QuizCardMeta,
        answer: dict[str, Any],
    ) -> dict[str, Any]:
        submitted = answer.get("submitted_text")
        if not isinstance(submitted, str) or not submitted.strip():
            raise QuizSessionError("free_text answer requires submitted_text")
        accepted = tuple(term.text for term in meta.answer_terms)
        canonical = meta.canonical_answer
        policy = self._normalization_policy(canonical)
        try:
            grade = self._grading.grade(
                submitted,
                accepted_answers=accepted,
                grading_policy_kind=meta.grading_policy_kind,
                grading_policy_version=meta.grading_policy_version,
                normalization_policy=policy,
                script=canonical.script,
            )
            should_be_accepted = answer.get("should_be_accepted", False)
            if not isinstance(should_be_accepted, bool):
                raise QuizSessionError("should_be_accepted must be boolean")
            if should_be_accepted:
                grade = self._grading.mark_should_be_accepted(grade)
        except GradingError as err:
            raise QuizSessionError(str(err)) from err

        return {
            "result": grade.outcome.value,
            "immediate": True,
            "reveal_correct_answer": grade.outcome is not GradingOutcome.CORRECT,
            "correct_answer": canonical.text,
            "contrastive_feedback": None,
            "submitted_text": grade.submitted_text,
            "normalized_submission": grade.normalized_submission,
            "reportable": grade.outcome is not GradingOutcome.CORRECT,
            "grading_policy_kind": grade.grading_policy_kind.value,
            "grading_policy_version": grade.grading_policy_version,
            "normalization_version": grade.normalization_version,
            "grading_reason": grade.reason,
        }

    def _apply_signal(
        self,
        pre: dict[str, Any],
        *,
        decision: Any,
        hint_used: bool,
    ) -> tuple[dict[str, Any], float | None, float | None]:
        if decision.outcome is SignalOutcome.NEUTRAL:
            return dict(pre), None, None

        state = str(pre["state"])
        if state in {"learning", "relearning"}:
            success = decision.outcome is SignalOutcome.POSITIVE
            transition = (
                self._learning.learning_result(pre, success=success)
                if state == "learning"
                else self._learning.relearning_result(pre, success=success)
            )
            post = dict(transition.post_state)
            scheduled: float | None = None
            elapsed: float | None = None
            if transition.ready_for_long_review and success:
                graduated = self._review_policy.graduate_short_steps(transition)
                post = dict(graduated.post_state)
                scheduled = graduated.scheduled_interval_days
                elapsed = graduated.elapsed_days
            if decision.verified:
                counter = (
                    "verified_correct_count"
                    if decision.outcome is SignalOutcome.POSITIVE
                    else "verified_wrong_count"
                )
                post[counter] = int(post.get(counter, 0)) + 1
                post["last_verified_at_utc"] = self._clock.now().isoformat()
            return post, scheduled, elapsed

        if state in {"review", "leech"}:
            applied = self._signal_policy.apply_review_signal(
                pre,
                decision=decision,
                hint_used=hint_used,
            )
            if applied.transition is None:
                return dict(pre), None, None
            return (
                dict(applied.transition.post_state),
                applied.transition.scheduled_interval_days,
                applied.transition.elapsed_days,
            )
        raise QuizSessionError(f"unsupported quiz progress state: {state}")

    def _build_choice_question(
        self,
        meta: _QuizCardMeta,
        *,
        catalog: dict[str, _QuizCardMeta],
        state: str,
        presentation: dict[str, Any],
        cloze_prompt: str | None,
        option_count: int,
        presentation_index: int,
    ) -> QuizQuestion:
        prompt = QuizPrompt(
            card_key=meta.card_key,
            learning_item_id=meta.learning_item_id,
            content_type=meta.content_type,
            state=state,
            prompt_text=self._prompt_text(presentation),
            correct=self._candidate(meta, current=meta),
            accepted_normalized_answers=frozenset(
                term.normalized_text for term in meta.answer_terms
            ),
            native_concept_ids=meta.concept_ids,
            sibling_answer_ids=frozenset(
                other.canonical_answer.term_id
                for other in catalog.values()
                if other.learning_item_id == meta.learning_item_id
                and other.card_key != meta.card_key
                and other.answer_terms
            ),
            context_hint=self._context_hint(presentation),
            cloze_prompt=cloze_prompt,
            example_ids=tuple(
                str(block.get("content_block_id"))
                for block in presentation.get("example_blocks", [])
                if isinstance(block, dict) and block.get("content_block_id")
            ),
        )
        candidates = tuple(
            self._candidate(other, current=meta)
            for other in catalog.values()
            if other.card_key != meta.card_key and other.answer_terms
        )
        raw_format = "cloze_mcq" if cloze_prompt is not None and meta.content_type == "grammar" else "mcq"
        return self._quiz.build_question(
            prompt,
            candidates=candidates,
            option_count=option_count,
            presentation_index=presentation_index,
            answer_position_balance=presentation_index,
            example_rotation_index=0,
            quiz_format=QuizFormat(raw_format),
        )

    def _choice_question_from_payload(
        self,
        meta: _QuizCardMeta,
        *,
        catalog: dict[str, _QuizCardMeta],
        payload: dict[str, Any],
    ) -> QuizQuestion:
        raw_options = payload.get("options")
        if not isinstance(raw_options, list) or not raw_options:
            raise QuizSessionError("choice question has no options")
        by_answer_id = {
            card.canonical_answer.term_id: card
            for card in catalog.values()
            if card.answer_terms
        }
        options: list[QuizCandidate] = []
        correct_index: int | None = None
        for index, raw in enumerate(raw_options):
            if not isinstance(raw, dict):
                raise QuizSessionError("invalid quiz option")
            answer_id = raw.get("answer_id")
            text = raw.get("text")
            if not isinstance(answer_id, str) or not isinstance(text, str):
                raise QuizSessionError("invalid quiz option")
            option_meta = by_answer_id.get(answer_id)
            if option_meta is None:
                raise QuizSessionError("quiz option no longer exists")
            candidate = self._candidate(option_meta, current=meta)
            options.append(candidate)
            if answer_id == meta.canonical_answer.term_id:
                correct_index = index
        if correct_index is None:
            raise QuizSessionError("quiz payload does not contain the expected answer")
        return QuizQuestion(
            format=QuizFormat(str(payload["format"])),
            card_key=meta.card_key,
            prompt_text=str(payload.get("prompt_text", "")),
            context_hint=(
                None if payload.get("context_hint") is None else str(payload["context_hint"])
            ),
            options=tuple(options),
            correct_index=correct_index,
            idk_available=True,
            reportable=True,
            example_id=None,
            next_example_rotation_index=0,
            next_answer_position_balance=0,
            presentation_index=0,
        )

    def _candidate(self, meta: _QuizCardMeta, *, current: _QuizCardMeta) -> QuizCandidate:
        answer = meta.canonical_answer
        strategies = {DistractorStrategy.RANDOM_FALLBACK}
        if meta.content_type == current.content_type:
            strategies.add(DistractorStrategy.SAME_TYPE)
        if meta.tag_ids & current.tag_ids:
            strategies.add(DistractorStrategy.SAME_TAG)
        is_confusable = bool(meta.confusable_group_ids & current.confusable_group_ids)
        if is_confusable:
            strategies.add(DistractorStrategy.CONFUSABLE)
        return QuizCandidate(
            answer_id=answer.term_id,
            display_text=answer.text,
            normalized_answer=answer.normalized_text,
            learning_item_id=meta.learning_item_id,
            content_type=meta.content_type,
            concept_ids=meta.concept_ids,
            tag_ids=meta.tag_ids,
            strategies=frozenset(strategies),
            contrastive_feedback="known_confusable" if is_confusable else None,
        )

    @staticmethod
    def _base_payload(
        quiz_format: str,
        *,
        presentation: dict[str, Any],
        meta: _QuizCardMeta,
    ) -> dict[str, Any]:
        return {
            "format": quiz_format,
            "prompt_text": QuizSessionService._prompt_text(presentation),
            "context_hint": QuizSessionService._context_hint(presentation),
            "options": [],
            "idk_available": True,
            "reportable": True,
            "hint_blocks": list(presentation.get("hint_blocks", []))
            + list(presentation.get("mnemonic_blocks", [])),
            "content_type": meta.content_type,
        }

    @staticmethod
    def _prompt_text(presentation: dict[str, Any]) -> str:
        prompt = presentation.get("prompt")
        blocks = prompt.get("blocks") if isinstance(prompt, dict) else None
        if not isinstance(blocks, list):
            raise QuizSessionError("quiz prompt has no renderable content")
        for block in blocks:
            if isinstance(block, dict):
                payload = block.get("payload")
                text = payload.get("text") if isinstance(payload, dict) else None
                if isinstance(text, str) and text:
                    return text
        raise QuizSessionError("quiz prompt has no renderable text")

    @staticmethod
    def _context_hint(presentation: dict[str, Any]) -> str | None:
        texts: list[str] = []
        context = presentation.get("context")
        if not isinstance(context, list):
            return None
        for facet in context:
            blocks = facet.get("blocks") if isinstance(facet, dict) else None
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                payload = block.get("payload") if isinstance(block, dict) else None
                text = payload.get("text") if isinstance(payload, dict) else None
                if isinstance(text, str) and text and text not in texts:
                    texts.append(text)
        return " · ".join(texts) if texts else None

    @staticmethod
    def _cloze_prompt(
        presentation: dict[str, Any],
        accepted: tuple[_AnswerTerm, ...],
    ) -> str | None:
        blocks = presentation.get("introduction_blocks")
        if not isinstance(blocks, list):
            return None
        accepted_texts = tuple(term.text for term in accepted)
        for block in blocks:
            if not isinstance(block, dict):
                continue
            strategy = str(block.get("mask_strategy", "none"))
            if strategy == "none":
                continue
            payload = block.get("payload")
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not text:
                continue
            if strategy == "hide_block":
                return "＿＿"
            targets: list[str] = []
            if strategy == "blank_span" and isinstance(payload, dict):
                for key in ("blank_text", "answer"):
                    value = payload.get(key)
                    if isinstance(value, str) and value:
                        targets.append(value)
            targets.extend(accepted_texts)
            placeholder = "＿＿"
            if strategy == "replace_with_placeholder" and isinstance(payload, dict):
                raw_placeholder = payload.get("placeholder")
                if isinstance(raw_placeholder, str) and raw_placeholder:
                    placeholder = raw_placeholder
            for target in targets:
                if target in text:
                    return text.replace(target, placeholder, 1)
        return None

    @staticmethod
    def _quiz_format(settings: dict[str, Any]) -> str:
        value = str(settings.get("quiz_format", "mixed")).strip().lower()
        if value not in {"mixed", "mcq", "free_text", "cloze_mcq"}:
            raise QuizSessionError("quiz_format must be mixed, mcq, free_text or cloze_mcq")
        return value

    @staticmethod
    def _option_count(settings: dict[str, Any]) -> int:
        value = settings.get("option_count", 4)
        if isinstance(value, bool) or not isinstance(value, int) or not 4 <= value <= 6:
            raise QuizSessionError("option_count must be within [4, 6]")
        return value

    @staticmethod
    def _free_text_supported(meta: _QuizCardMeta) -> bool:
        return meta.grading_policy_kind in {"exact", "any_of", "fuzzy_normalized"}

    def _resolve_format(
        self,
        requested: str,
        *,
        meta: _QuizCardMeta,
        cloze_prompt: str | None,
        ordinal: int,
    ) -> str | None:
        if requested == "mcq":
            return "mcq"
        if requested == "free_text":
            return "free_text" if self._free_text_supported(meta) else None
        if requested == "cloze_mcq":
            return (
                "cloze_mcq"
                if meta.content_type == "grammar" and cloze_prompt is not None
                else None
            )
        if meta.content_type == "grammar" and cloze_prompt is not None:
            return "cloze_mcq"
        return "free_text" if ordinal % 2 and self._free_text_supported(meta) else "mcq"

    @staticmethod
    def _normalization_policy(answer: _AnswerTerm) -> NormalizationPolicy:
        return NormalizationPolicy(
            policy_id="quiz_free_text",
            normalization_version=answer.normalization_version,
            unicode_normalization=UnicodeNormalization.NFKC,
            case_mode=CaseMode.CASEFOLD,
            whitespace_mode=WhitespaceMode.COLLAPSE,
            punctuation_mode=PunctuationMode.PRESERVE,
            allowed_scripts=() if answer.script is None else (answer.script,),
        )

    async def _load_catalog(self, track_id: str) -> dict[str, _QuizCardMeta]:
        def read(connection: sqlite3.Connection) -> dict[str, _QuizCardMeta]:
            rows = connection.execute(
                """SELECT card.card_key, card.learning_item_id,
                          card.prompt_facet_id, card.answer_facet_id,
                          item.content_type, card.grading_policy_kind,
                          card.grading_policy_version, answer.language_tag,
                          answer.script, term.term_id, term.text,
                          term.normalized_text, term.normalization_version
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card
                     ON card.card_key = rule.card_key
                    AND card.lifecycle_status = 'active'
                   JOIN content.learning_items AS item
                     ON item.learning_item_id = card.learning_item_id
                    AND item.lifecycle_status = 'active'
                   JOIN content.facets AS answer
                     ON answer.facet_id = card.answer_facet_id
                    AND answer.lifecycle_status = 'active'
                   JOIN content.learning_item_concepts AS item_concept
                     ON item_concept.learning_item_id = item.learning_item_id
                   JOIN content.concept_terms AS relation
                     ON relation.concept_id = item_concept.concept_id
                   JOIN content.terms AS term ON term.term_id = relation.term_id
                   WHERE rule.track_id = ? AND rule.enabled = 1
                     AND rule.card_key IS NOT NULL
                     AND term.language_tag = answer.language_tag
                     AND (
                         answer.script IS NULL OR term.script IS NULL
                         OR term.script = answer.script
                     )
                   ORDER BY card.card_key, term.term_id""",
                (track_id,),
            ).fetchall()
            concepts: dict[str, set[str]] = {}
            tags: dict[str, set[str]] = {}
            groups: dict[str, set[str]] = {}
            for card_key, concept_id in connection.execute(
                """SELECT DISTINCT card.card_key, item_concept.concept_id
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card ON card.card_key = rule.card_key
                   JOIN content.learning_item_concepts AS item_concept
                     ON item_concept.learning_item_id = card.learning_item_id
                   WHERE rule.track_id = ? AND rule.enabled = 1""",
                (track_id,),
            ):
                concepts.setdefault(str(card_key), set()).add(str(concept_id))
            for card_key, tag_id in connection.execute(
                """SELECT DISTINCT card.card_key, item_tag.tag_id
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card ON card.card_key = rule.card_key
                   JOIN content.learning_item_tags AS item_tag
                     ON item_tag.learning_item_id = card.learning_item_id
                   WHERE rule.track_id = ? AND rule.enabled = 1""",
                (track_id,),
            ):
                tags.setdefault(str(card_key), set()).add(str(tag_id))
            for card_key, group_id in connection.execute(
                """SELECT DISTINCT card.card_key, member.confusable_group_id
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card ON card.card_key = rule.card_key
                   JOIN content.confusable_group_items AS member
                     ON member.learning_item_id = card.learning_item_id
                   WHERE rule.track_id = ? AND rule.enabled = 1""",
                (track_id,),
            ):
                groups.setdefault(str(card_key), set()).add(str(group_id))

            mutable: dict[str, dict[str, Any]] = {}
            for row in rows:
                key = str(row[0])
                entry = mutable.setdefault(
                    key,
                    {
                        "card_key": key,
                        "learning_item_id": str(row[1]),
                        "prompt_facet_id": str(row[2]),
                        "answer_facet_id": str(row[3]),
                        "content_type": str(row[4]),
                        "grading_policy_kind": str(row[5]),
                        "grading_policy_version": int(row[6]),
                        "answer_terms": [],
                    },
                )
                normalized = str(row[11]) if row[11] is not None else str(row[10])
                normalization_version = int(row[12]) if row[12] is not None else 1
                entry["answer_terms"].append(
                    _AnswerTerm(
                        term_id=str(row[9]),
                        text=str(row[10]),
                        normalized_text=normalized,
                        normalization_version=normalization_version,
                        script=None if row[8] is None else str(row[8]),
                    )
                )
            return {
                key: _QuizCardMeta(
                    **entry,
                    answer_terms=tuple(entry["answer_terms"]),
                    concept_ids=frozenset(concepts.get(key, ())),
                    tag_ids=frozenset(tags.get(key, ())),
                    confusable_group_ids=frozenset(groups.get(key, ())),
                )
                for key, entry in mutable.items()
            }

        return await self._storage._async_reader(read)

    def _emit_event(
        self,
        event_id: str,
        profile_id: str,
        track_id: str,
        card_key: str,
        session_id: str,
        mode: SignalMode,
        result: str,
    ) -> None:
        if self._event_emitter is None:
            return
        if result == "unrecognized":
            event_type = "locklearn_free_text_unrecognized"
        elif result == "correct":
            event_type = "locklearn_quiz_correct"
        elif result == "wrong":
            event_type = "locklearn_quiz_wrong"
        else:
            event_type = "locklearn_quiz_idk"
        self._event_emitter(
            event_type,
            {
                "event_id": event_id,
                "profile_id": profile_id,
                "track_id": track_id,
                "card_key": card_key,
                "session_id": session_id,
                "mode": mode.value,
                "result": result,
            },
        )
