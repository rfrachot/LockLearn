"""P5.4 quiz orchestration contract tests."""

from __future__ import annotations

from typing import Any, cast

import pytest

from custom_components.locklearn.core.grading import FreeTextGrader
from custom_components.locklearn.core.quiz import QuizEngine
from custom_components.locklearn.core.quiz_sessions import (
    QuizSessionError,
    QuizSessionService,
    _AnswerTerm,
    _QuizCardMeta,
)
from custom_components.locklearn.core.review_policy import ReviewPolicyV1
from custom_components.locklearn.core.session_selection import PreparedSessionSelection
from custom_components.locklearn.core.signals import SignalPolicy


def _meta(index: int, *, content_type: str = "vocabulary") -> _QuizCardMeta:
    return _QuizCardMeta(
        card_key=f"card-{index}",
        learning_item_id=f"item-{index}",
        prompt_facet_id=f"prompt-{index}",
        answer_facet_id=f"answer-{index}",
        content_type=content_type,
        grading_policy_kind="exact",
        grading_policy_version=1,
        answer_terms=(
            _AnswerTerm(
                term_id=f"term-{index}",
                text=f"Answer {index}",
                normalized_text=f"Answer {index}",
                normalization_version=1,
                script="Latn",
            ),
        ),
        concept_ids=frozenset({f"concept-{index}"}),
        tag_ids=frozenset({"level-1"}),
        confusable_group_ids=frozenset(),
    )


class _Presentation:
    async def async_for_card(self, *, track_id: str, card_key: str) -> dict[str, Any]:
        assert track_id == "track-1"
        index = int(card_key.rsplit("-", 1)[-1])
        return {
            "prompt": {
                "blocks": [{"payload": {"text": f"Prompt {index}"}}],
            },
            "answer": {
                "blocks": [{"payload": {"text": f"Answer {index}"}}],
            },
            "context": [],
            "hint_blocks": [],
            "mnemonic_blocks": [],
            "example_blocks": [],
            "introduction_blocks": [
                {
                    "content_block_id": f"block-{index}",
                    "mask_strategy": "none",
                    "payload": {"text": f"Prompt {index}"},
                }
            ],
        }


class _Sessions:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state

    async def async_get(self, session_id: str) -> dict[str, Any] | None:
        assert session_id == self.state["id"]
        return self.state


def _service(
    *,
    sessions: Any | None = None,
    presentation: Any | None = None,
) -> QuizSessionService:
    review_policy = ReviewPolicyV1()
    return QuizSessionService(
        cast(Any, None),
        cast(Any, sessions),
        cast(Any, presentation),
        cast(Any, None),
        review_policy,
        SignalPolicy(review_policy),
        QuizEngine(),
        FreeTextGrader(),
        dataset_generation=lambda: "generation-1",
    )


@pytest.mark.asyncio
async def test_quiz_preparation_keeps_correct_marker_backend_only() -> None:
    service = _service(presentation=_Presentation())
    catalog = {f"card-{index}": _meta(index) for index in range(1, 7)}

    async def load_catalog(track_id: str) -> dict[str, _QuizCardMeta]:
        assert track_id == "track-1"
        return catalog

    service._load_catalog = load_catalog  # type: ignore[method-assign]
    selected = (
        PreparedSessionSelection(
            card_key="card-1",
            learning_item_id="item-1",
            prompt_facet_id="prompt-1",
            answer_facet_id="answer-1",
            payload={
                "selection": {
                    "content_type": "vocabulary",
                    "progress_state": "review",
                    "reason": "review_due",
                }
            },
        ),
    )

    questions = await service.async_prepare_questions(
        track_id="track-1",
        selected=selected,
        settings={"quiz_format": "mcq", "option_count": 4},
    )

    assert len(questions) == 1
    payload = questions[0].payload["quiz"]
    assert payload["format"] == "mcq"
    assert len(payload["options"]) == 4
    assert payload["idk_available"] is True
    assert "correct_index" not in payload
    assert "correct_answer" not in payload


@pytest.mark.asyncio
async def test_free_text_wrong_can_be_recovered_as_unrecognized() -> None:
    meta = _meta(1)
    question = {
        "question_id": "q1",
        "card_key": meta.card_key,
        "payload": {
            "quiz": {
                "format": "free_text",
                "prompt_text": "Prompt",
                "context_hint": None,
                "options": [],
                "idk_available": True,
                "reportable": True,
                "hint_blocks": [],
                "content_type": "vocabulary",
            }
        },
    }
    session = {
        "id": "session-1",
        "type": "quiz",
        "track_id": "track-1",
        "current_question": question,
    }
    service = _service(sessions=_Sessions(session))

    async def load_catalog(track_id: str) -> dict[str, _QuizCardMeta]:
        assert track_id == "track-1"
        return {meta.card_key: meta}

    service._load_catalog = load_catalog  # type: ignore[method-assign]

    wrong = await service.async_evaluate(
        "session-1",
        "q1",
        {"kind": "quiz", "submitted_text": "wrong"},
    )
    assert wrong["result"] == "wrong"
    assert wrong["reportable"] is True
    assert wrong["correct_answer"] is None
    assert wrong["reveal_correct_answer"] is False

    recovered = await service.async_evaluate(
        "session-1",
        "q1",
        {
            "kind": "quiz",
            "submitted_text": "wrong",
            "should_be_accepted": True,
        },
    )
    assert recovered["result"] == "unrecognized"
    assert recovered["reportable"] is True


@pytest.mark.asyncio
async def test_provisional_free_text_cannot_change_after_grading() -> None:
    meta = _meta(1)
    session = {
        "id": "session-1",
        "type": "quiz",
        "track_id": "track-1",
        "current_question": {
            "question_id": "q1",
            "card_key": meta.card_key,
            "payload": {
                "quiz": {
                    "format": "free_text",
                    "prompt_text": "Prompt",
                    "context_hint": None,
                    "options": [],
                    "idk_available": True,
                    "reportable": True,
                    "hint_blocks": [],
                    "content_type": "vocabulary",
                }
            },
        },
    }
    service = _service(sessions=_Sessions(session))

    async def load_catalog(track_id: str) -> dict[str, _QuizCardMeta]:
        return {meta.card_key: meta}

    service._load_catalog = load_catalog  # type: ignore[method-assign]
    await service.async_evaluate(
        "session-1",
        "q1",
        {"kind": "quiz", "submitted_text": "wrong"},
    )

    with pytest.raises(QuizSessionError, match="already evaluated"):
        await service.async_evaluate(
            "session-1",
            "q1",
            {"kind": "quiz", "submitted_text": "Answer 1"},
        )


@pytest.mark.asyncio
async def test_choice_evaluation_requires_atomic_submission() -> None:
    meta = _meta(1)
    session = {
        "id": "session-1",
        "type": "quiz",
        "track_id": "track-1",
        "current_question": {
            "question_id": "q1",
            "card_key": meta.card_key,
            "payload": {
                "quiz": {
                    "format": "mcq",
                    "prompt_text": "Prompt",
                    "context_hint": None,
                    "options": [
                        {"answer_id": "term-1", "text": "Answer 1"},
                    ],
                    "idk_available": True,
                    "reportable": True,
                    "hint_blocks": [],
                    "content_type": "vocabulary",
                }
            },
        },
    }
    service = _service(sessions=_Sessions(session))

    async def load_catalog(track_id: str) -> dict[str, _QuizCardMeta]:
        return {meta.card_key: meta}

    service._load_catalog = load_catalog  # type: ignore[method-assign]

    with pytest.raises(QuizSessionError, match="atomic quiz submission"):
        await service.async_evaluate(
            "session-1",
            "q1",
            {"kind": "quiz", "selected_answer_id": "term-1"},
        )


@pytest.mark.asyncio
async def test_free_text_idk_is_explicit_without_fake_submission() -> None:
    meta = _meta(1)
    session = {
        "id": "session-1",
        "type": "quiz",
        "track_id": "track-1",
        "current_question": {
            "question_id": "q1",
            "card_key": meta.card_key,
            "payload": {
                "quiz": {
                    "format": "free_text",
                    "prompt_text": "Prompt",
                    "context_hint": None,
                    "options": [],
                    "idk_available": True,
                    "reportable": True,
                    "hint_blocks": [],
                    "content_type": "vocabulary",
                }
            },
        },
    }
    service = _service(sessions=_Sessions(session))

    async def load_catalog(track_id: str) -> dict[str, _QuizCardMeta]:
        return {meta.card_key: meta}

    service._load_catalog = load_catalog  # type: ignore[method-assign]
    feedback = await service.async_evaluate(
        "session-1",
        "q1",
        {"kind": "quiz", "action": "idk"},
    )
    assert feedback["result"] == "idk"
    assert feedback["reveal_correct_answer"] is True
    assert feedback["submitted_text"] is None


def test_cloze_requires_explicit_maskable_content() -> None:
    service = _service()
    accepted = (_meta(1).canonical_answer,)
    plain = {
        "introduction_blocks": [{"mask_strategy": "none", "payload": {"text": "Answer 1 is here."}}]
    }
    masked = {
        "introduction_blocks": [
            {
                "mask_strategy": "blank_term",
                "payload": {"text": "Answer 1 is here."},
            }
        ]
    }

    assert service._cloze_prompt(plain, accepted) is None
    assert service._cloze_prompt(masked, accepted) == "＿＿ is here."
