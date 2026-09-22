"""P3.6 deterministic quiz construction, distractors and corrective feedback."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from .selection import SelectionConstraintService


class QuizFormat(StrEnum):
    MCQ = "mcq"
    CLOZE_MCQ = "cloze_mcq"


class DistractorStrategy(StrEnum):
    SAME_LEVEL = "same_level"
    SAME_TYPE = "same_type"
    SIMILAR_SEMANTICS = "similar_semantics"
    SAME_TAG = "same_tag"
    CONFUSABLE = "confusable"
    RANDOM_FALLBACK = "random_fallback"


class QuizResult(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    IDK = "idk"


@dataclass(frozen=True, slots=True)
class QuizCandidate:
    """One possible answer candidate supplied by an indexed content pool."""

    answer_id: str
    display_text: str
    normalized_answer: str
    learning_item_id: str
    content_type: str
    concept_ids: frozenset[str] = frozenset()
    synonym_ids: frozenset[str] = frozenset()
    tag_ids: frozenset[str] = frozenset()
    strategies: frozenset[DistractorStrategy] = frozenset()
    level: str | None = None
    contrastive_feedback: str | None = None


@dataclass(frozen=True, slots=True)
class QuizPrompt:
    """Question material independent from renderer/UI."""

    card_key: str
    learning_item_id: str
    content_type: str
    state: str
    prompt_text: str
    correct: QuizCandidate
    accepted_normalized_answers: frozenset[str]
    native_concept_ids: frozenset[str]
    explicit_synonym_ids: frozenset[str] = frozenset()
    sibling_answer_ids: frozenset[str] = frozenset()
    context_hint: str | None = None
    cloze_prompt: str | None = None
    example_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class QuizQuestion:
    """Deterministic quiz question payload."""

    format: QuizFormat
    card_key: str
    prompt_text: str
    context_hint: str | None
    options: tuple[QuizCandidate, ...]
    correct_index: int
    idk_available: bool
    reportable: bool
    example_id: str | None
    next_example_rotation_index: int
    next_answer_position_balance: int
    presentation_index: int


@dataclass(frozen=True, slots=True)
class QuizFeedback:
    """Immediate feedback for non-exam quiz/learning surfaces."""

    result: QuizResult
    immediate: bool
    reveal_correct_answer: bool
    correct_answer: str | None
    contrastive_feedback: str | None
    message: str


class QuizConstructionError(ValueError):
    """Raised when a quiz cannot be built safely."""


class QuizEngine:
    """Build deterministic MCQ/cloze questions from pre-indexed candidates."""

    _STRATEGY_PRIORITY: ClassVar[dict[DistractorStrategy, int]] = {
        DistractorStrategy.CONFUSABLE: 0,
        DistractorStrategy.SIMILAR_SEMANTICS: 1,
        DistractorStrategy.SAME_TYPE: 2,
        DistractorStrategy.SAME_TAG: 3,
        DistractorStrategy.SAME_LEVEL: 4,
        DistractorStrategy.RANDOM_FALLBACK: 5,
    }

    def build_question(
        self,
        prompt: QuizPrompt,
        *,
        candidates: Iterable[QuizCandidate],
        option_count: int,
        presentation_index: int,
        answer_position_balance: int,
        example_rotation_index: int,
        quiz_format: QuizFormat = QuizFormat.MCQ,
    ) -> QuizQuestion:
        """Create one 4-6 option panel question with deterministic resampling."""
        if option_count < 4 or option_count > 6:
            raise QuizConstructionError("panel MCQ must contain 4 to 6 answer options")
        if presentation_index < 0:
            raise QuizConstructionError("presentation_index must be >= 0")
        if answer_position_balance < 0:
            raise QuizConstructionError("answer_position_balance must be >= 0")
        if example_rotation_index < 0:
            raise QuizConstructionError("example_rotation_index must be >= 0")
        if quiz_format is QuizFormat.CLOZE_MCQ:
            if prompt.content_type != "grammar":
                raise QuizConstructionError("cloze-MCQ is reserved for grammar cards")
            if not prompt.cloze_prompt:
                raise QuizConstructionError("grammar cloze-MCQ requires cloze_prompt")

        candidate_pool = tuple(candidates)
        if quiz_format is QuizFormat.CLOZE_MCQ:
            candidate_pool = tuple(
                candidate for candidate in candidate_pool if candidate.content_type == "grammar"
            )
        filtered = self._eligible_distractors(prompt, candidate_pool)
        if len(filtered) < option_count - 1:
            raise QuizConstructionError(
                f"not enough safe distractors: need {option_count - 1}, got {len(filtered)}"
            )

        selected = tuple(
            sorted(
                filtered,
                key=lambda candidate: self._candidate_rank(
                    prompt,
                    candidate,
                    presentation_index=presentation_index,
                ),
            )[: option_count - 1]
        )

        correct_index = answer_position_balance % option_count
        options = list(selected)
        options.insert(correct_index, prompt.correct)

        example_id, next_example = self._rotate_example(
            prompt.example_ids,
            example_rotation_index,
        )
        rendered_prompt = (
            prompt.cloze_prompt
            if quiz_format is QuizFormat.CLOZE_MCQ and prompt.cloze_prompt is not None
            else prompt.prompt_text
        )
        return QuizQuestion(
            format=quiz_format,
            card_key=prompt.card_key,
            prompt_text=rendered_prompt,
            context_hint=prompt.context_hint,
            options=tuple(options),
            correct_index=correct_index,
            idk_available=True,
            reportable=True,
            example_id=example_id,
            next_example_rotation_index=next_example,
            next_answer_position_balance=(correct_index + 1) % option_count,
            presentation_index=presentation_index,
        )

    def feedback(
        self,
        question: QuizQuestion,
        *,
        selected_answer_id: str | None,
        exam_mode: bool = False,
    ) -> QuizFeedback:
        """Return corrective feedback while preserving explicit IDK semantics."""
        if exam_mode:
            result = self._result(question, selected_answer_id)
            return QuizFeedback(
                result=result,
                immediate=False,
                reveal_correct_answer=False,
                correct_answer=None,
                contrastive_feedback=None,
                message="answer_recorded",
            )

        result = self._result(question, selected_answer_id)
        correct = question.options[question.correct_index]
        if result is QuizResult.CORRECT:
            return QuizFeedback(
                result=result,
                immediate=True,
                reveal_correct_answer=False,
                correct_answer=correct.display_text,
                contrastive_feedback=None,
                message="correct",
            )
        if result is QuizResult.IDK:
            return QuizFeedback(
                result=result,
                immediate=True,
                reveal_correct_answer=True,
                correct_answer=correct.display_text,
                contrastive_feedback=None,
                message="idk",
            )

        selected = next(
            option for option in question.options if option.answer_id == selected_answer_id
        )
        return QuizFeedback(
            result=result,
            immediate=True,
            reveal_correct_answer=True,
            correct_answer=correct.display_text,
            contrastive_feedback=selected.contrastive_feedback,
            message="wrong",
        )

    @classmethod
    def _eligible_distractors(
        cls,
        prompt: QuizPrompt,
        candidates: tuple[QuizCandidate, ...],
    ) -> tuple[QuizCandidate, ...]:
        allowed: list[QuizCandidate] = []
        seen_answer_ids: set[str] = set()
        seen_normalized: set[str] = set()
        for candidate in candidates:
            if candidate.answer_id == prompt.correct.answer_id:
                continue
            if candidate.answer_id in seen_answer_ids:
                continue
            if candidate.learning_item_id == prompt.learning_item_id:
                continue
            if candidate.answer_id in prompt.sibling_answer_ids:
                continue
            if candidate.normalized_answer in prompt.accepted_normalized_answers:
                continue
            if candidate.normalized_answer in seen_normalized:
                continue
            if candidate.concept_ids & prompt.native_concept_ids:
                continue
            if candidate.synonym_ids & prompt.explicit_synonym_ids:
                continue
            if (
                DistractorStrategy.CONFUSABLE in candidate.strategies
                and not SelectionConstraintService.confusable_distractors_allowed(prompt.state)
            ):
                continue
            allowed.append(candidate)
            seen_answer_ids.add(candidate.answer_id)
            seen_normalized.add(candidate.normalized_answer)
        return tuple(allowed)

    @classmethod
    def _candidate_rank(
        cls,
        prompt: QuizPrompt,
        candidate: QuizCandidate,
        *,
        presentation_index: int,
    ) -> tuple[int, int]:
        priority = min(
            (
                cls._STRATEGY_PRIORITY[strategy]
                for strategy in candidate.strategies
                if strategy in cls._STRATEGY_PRIORITY
            ),
            default=cls._STRATEGY_PRIORITY[DistractorStrategy.RANDOM_FALLBACK],
        )
        seed = f"{prompt.card_key}|{presentation_index}|{candidate.answer_id}".encode()
        stable = int.from_bytes(hashlib.sha256(seed).digest()[:8], "big")
        return priority, stable

    @staticmethod
    def _rotate_example(
        examples: tuple[str, ...],
        rotation_index: int,
    ) -> tuple[str | None, int]:
        if not examples:
            return None, rotation_index
        current = rotation_index % len(examples)
        return examples[current], (current + 1) % len(examples)

    @staticmethod
    def _result(question: QuizQuestion, selected_answer_id: str | None) -> QuizResult:
        if selected_answer_id is None:
            return QuizResult.IDK
        if not any(option.answer_id == selected_answer_id for option in question.options):
            raise QuizConstructionError("selected answer is not one of the question options")
        correct = question.options[question.correct_index]
        return QuizResult.CORRECT if selected_answer_id == correct.answer_id else QuizResult.WRONG
