"""P3.6 deterministic quiz-engine tests."""

from __future__ import annotations

from custom_components.locklearn.core.quiz import (
    DistractorStrategy,
    QuizCandidate,
    QuizConstructionError,
    QuizEngine,
    QuizFormat,
    QuizPrompt,
    QuizResult,
)


def _candidate(
    answer_id: str,
    text: str,
    *,
    item: str,
    content_type: str = "vocabulary",
    normalized: str | None = None,
    concepts: tuple[str, ...] = (),
    synonyms: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    strategies: tuple[DistractorStrategy, ...] = (DistractorStrategy.SAME_TYPE,),
    contrastive_feedback: str | None = None,
) -> QuizCandidate:
    return QuizCandidate(
        answer_id=answer_id,
        display_text=text,
        normalized_answer=text.lower() if normalized is None else normalized,
        learning_item_id=item,
        content_type=content_type,
        concept_ids=frozenset(concepts),
        synonym_ids=frozenset(synonyms),
        tag_ids=frozenset(tags),
        strategies=frozenset(strategies),
        contrastive_feedback=contrastive_feedback,
    )


def _prompt(*, state: str = "review", content_type: str = "vocabulary") -> QuizPrompt:
    correct = _candidate(
        "answer-correct",
        "Correct",
        item="item-correct",
        content_type=content_type,
        normalized="correct",
        concepts=("concept-native",),
        synonyms=("synonym-known",),
    )
    return QuizPrompt(
        card_key="card-1",
        learning_item_id="item-correct",
        content_type=content_type,
        state=state,
        prompt_text="Prompt",
        correct=correct,
        accepted_normalized_answers=frozenset({"correct", "accepted-alt"}),
        native_concept_ids=frozenset({"concept-native"}),
        explicit_synonym_ids=frozenset({"synonym-known"}),
        sibling_answer_ids=frozenset({"answer-sibling"}),
        context_hint="context",
        cloze_prompt="Sentence ____.",
        example_ids=("example-a", "example-b"),
    )


def _safe_pool() -> tuple[QuizCandidate, ...]:
    return tuple(
        _candidate(
            f"answer-{index}",
            f"Option {index}",
            item=f"item-{index}",
            strategies=(DistractorStrategy.SAME_TYPE,),
        )
        for index in range(1, 10)
    )


def test_mcq_uses_four_to_six_options_and_explicit_idk() -> None:
    engine = QuizEngine()
    question = engine.build_question(
        _prompt(),
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
    )

    assert question.format is QuizFormat.MCQ
    assert len(question.options) == 4
    assert question.options[question.correct_index].answer_id == "answer-correct"
    assert question.idk_available is True
    assert question.reportable is True
    assert question.context_hint == "context"


def test_unsafe_distractors_are_removed_before_sampling() -> None:
    engine = QuizEngine()
    prompt = _prompt(state="review")
    candidates = (
        _candidate(
            "same-concept",
            "Other",
            item="item-a",
            concepts=("concept-native",),
        ),
        _candidate(
            "same-normalized",
            "Accepted",
            item="item-b",
            normalized="accepted-alt",
        ),
        _candidate(
            "same-synonym",
            "Synonym",
            item="item-c",
            synonyms=("synonym-known",),
        ),
        _candidate("answer-sibling", "Sibling", item="item-d"),
        _candidate("same-item", "Sibling 2", item="item-correct"),
        *_safe_pool(),
    )
    question = engine.build_question(
        prompt,
        candidates=candidates,
        option_count=4,
        presentation_index=1,
        answer_position_balance=1,
        example_rotation_index=0,
    )
    answer_ids = {option.answer_id for option in question.options}

    assert "same-concept" not in answer_ids
    assert "same-normalized" not in answer_ids
    assert "same-synonym" not in answer_ids
    assert "answer-sibling" not in answer_ids
    assert "same-item" not in answer_ids


def test_confusable_distractors_are_blocked_until_review() -> None:
    engine = QuizEngine()
    confusable = _candidate(
        "confusable",
        "Confusable",
        item="item-confusable",
        strategies=(DistractorStrategy.CONFUSABLE,),
    )
    pool = (confusable, *_safe_pool())

    learning = engine.build_question(
        _prompt(state="learning"),
        candidates=pool,
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
    )
    review = engine.build_question(
        _prompt(state="review"),
        candidates=pool,
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
    )

    assert "confusable" not in {option.answer_id for option in learning.options}
    assert "confusable" in {option.answer_id for option in review.options}


def test_answer_position_and_example_rotation_are_balanced_deterministically() -> None:
    engine = QuizEngine()
    prompt = _prompt()

    first = engine.build_question(
        prompt,
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=3,
        answer_position_balance=0,
        example_rotation_index=0,
    )
    second = engine.build_question(
        prompt,
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=3,
        answer_position_balance=1,
        example_rotation_index=1,
    )

    assert first.correct_index == 0
    assert first.next_answer_position_balance == 1
    assert second.correct_index == 1
    assert second.next_answer_position_balance == 2
    assert first.example_id == "example-a"
    assert first.next_example_rotation_index == 1
    assert second.example_id == "example-b"
    assert second.next_example_rotation_index == 0


def test_same_presentation_is_reproducible_and_new_presentation_resamples() -> None:
    engine = QuizEngine()
    prompt = _prompt()

    first = engine.build_question(
        prompt,
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=7,
        answer_position_balance=2,
        example_rotation_index=0,
    )
    repeat = engine.build_question(
        prompt,
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=7,
        answer_position_balance=2,
        example_rotation_index=0,
    )
    resampled = engine.build_question(
        prompt,
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=8,
        answer_position_balance=2,
        example_rotation_index=0,
    )

    assert first.options == repeat.options
    assert first.options != resampled.options


def test_grammar_cloze_uses_only_grammar_distractors() -> None:
    engine = QuizEngine()
    pool = (
        _candidate("g1", "いる", item="grammar-1", content_type="grammar"),
        _candidate("g2", "ある", item="grammar-2", content_type="grammar"),
        _candidate("g3", "なる", item="grammar-3", content_type="grammar"),
        _candidate("g4", "する", item="grammar-4", content_type="grammar"),
        _candidate("v1", "読む", item="vocab-1", content_type="vocabulary"),
    )
    question = engine.build_question(
        _prompt(content_type="grammar"),
        candidates=pool,
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
        quiz_format=QuizFormat.CLOZE_MCQ,
    )

    assert question.format is QuizFormat.CLOZE_MCQ
    assert question.prompt_text == "Sentence ____."
    assert all(option.content_type == "grammar" for option in question.options)


def test_wrong_feedback_reveals_correct_answer_and_contrastive_hint() -> None:
    engine = QuizEngine()
    contrastive = _candidate(
        "wrong-contrastive",
        "Wrong",
        item="item-wrong",
        strategies=(DistractorStrategy.CONFUSABLE,),
        contrastive_feedback="Key distinction",
    )
    question = engine.build_question(
        _prompt(state="review"),
        candidates=(contrastive, *_safe_pool()),
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
    )
    selected = next(
        option for option in question.options if option.answer_id == "wrong-contrastive"
    )
    feedback = engine.feedback(question, selected_answer_id=selected.answer_id)

    assert feedback.result is QuizResult.WRONG
    assert feedback.immediate is True
    assert feedback.reveal_correct_answer is True
    assert feedback.correct_answer == "Correct"
    assert feedback.contrastive_feedback == "Key distinction"


def test_idk_is_explicit_and_never_treated_as_guess() -> None:
    engine = QuizEngine()
    question = engine.build_question(
        _prompt(),
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
    )

    feedback = engine.feedback(question, selected_answer_id=None)

    assert feedback.result is QuizResult.IDK
    assert feedback.reveal_correct_answer is True
    assert feedback.message == "idk"


def test_exam_mode_suppresses_immediate_feedback() -> None:
    engine = QuizEngine()
    question = engine.build_question(
        _prompt(),
        candidates=_safe_pool(),
        option_count=4,
        presentation_index=0,
        answer_position_balance=0,
        example_rotation_index=0,
    )
    wrong = next(
        option for index, option in enumerate(question.options) if index != question.correct_index
    )

    feedback = engine.feedback(
        question,
        selected_answer_id=wrong.answer_id,
        exam_mode=True,
    )

    assert feedback.result is QuizResult.WRONG
    assert feedback.immediate is False
    assert feedback.reveal_correct_answer is False
    assert feedback.correct_answer is None


def test_invalid_option_count_and_unsafe_cloze_are_rejected() -> None:
    engine = QuizEngine()

    for count in (3, 7):
        try:
            engine.build_question(
                _prompt(),
                candidates=_safe_pool(),
                option_count=count,
                presentation_index=0,
                answer_position_balance=0,
                example_rotation_index=0,
            )
        except QuizConstructionError:
            pass
        else:
            raise AssertionError("invalid option count was accepted")

    try:
        engine.build_question(
            _prompt(content_type="vocabulary"),
            candidates=_safe_pool(),
            option_count=4,
            presentation_index=0,
            answer_position_balance=0,
            example_rotation_index=0,
            quiz_format=QuizFormat.CLOZE_MCQ,
        )
    except QuizConstructionError:
        pass
    else:
        raise AssertionError("non-grammar cloze was accepted")
