"""P5.4 quiz orchestration contract tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, cast

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
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
from tests.backend.content_db_helpers import (
    CONCEPT_ID,
    DATASET_ID,
    ITEM_A,
    TERM_ID,
    card_identity,
    create_package,
    facet_ids,
)


async def _activate_quiz_package(hass: HomeAssistant, tmp_path: Path) -> str:
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    package = create_package(
        tmp_path / "p5-4.db",
        "p5-4",
        active_item_ids=(ITEM_A,),
    )
    prompt_id, answer_id = facet_ids(ITEM_A)
    with sqlite3.connect(package) as connection:
        connection.execute(
            "UPDATE facets SET language_tag = 'en', script = 'Latn' WHERE facet_id = ?",
            (prompt_id,),
        )
        connection.execute(
            "UPDATE facets SET language_tag = 'fr', script = 'Latn' WHERE facet_id = ?",
            (answer_id,),
        )
        connection.execute(
            """UPDATE terms
               SET language_tag = 'en', script = 'Latn',
                   text = 'prompt', normalized_text = 'prompt'
               WHERE term_id = ?""",
            (TERM_ID,),
        )
        connection.execute(
            """INSERT INTO terms(
                   term_id, dataset_id, language_tag, script, text,
                   normalized_text, normalization_version
               ) VALUES (
                   'locklearn:term:p5-4-answer', ?, 'fr', 'Latn',
                   'réponse', 'réponse', 1
               )""",
            (DATASET_ID,),
        )
        connection.execute(
            "INSERT INTO concept_terms(concept_id, term_id) VALUES (?, ?)",
            (CONCEPT_ID, "locklearn:term:p5-4-answer"),
        )
        connection.execute(
            """INSERT INTO content_blocks(
                   content_block_id, learning_item_id, position, kind, role,
                   reveals_answer, mask_strategy, payload_json
               ) VALUES (?, ?, 1, 'text', 'answer', 1, 'none', ?)""",
            (
                "locklearn:block:p5-4-answer",
                ITEM_A,
                json.dumps({"text": "réponse"}, ensure_ascii=False),
            ),
        )
        connection.commit()

    candidate = runtime.storage.paths.content_staging_dir / "generation-p5-4.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p5-4",
    )
    await runtime.storage.async_activate_content_generation(candidate)
    return card_identity(ITEM_A)[1]


async def _seed_review_progress(
    hass: HomeAssistant,
    *,
    profile_id: str,
    track_id: str,
    card_key: str,
) -> None:
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    prompt_id, answer_id = facet_ids(ITEM_A)

    def insert(connection: sqlite3.Connection) -> None:
        connection.execute(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, learning_item_id,
                   prompt_facet_id, answer_facet_id, state,
                   next_due_at_utc, dataset_generation,
                   normalization_version, updated_at_utc
               ) VALUES (?, ?, ?, ?, ?, ?, 'review', ?, ?, 1, ?)""",
            (
                profile_id,
                track_id,
                card_key,
                ITEM_A,
                prompt_id,
                answer_id,
                "2026-01-01T00:00:00+00:00",
                runtime.storage.content_generations.active_metadata.generation_id,
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.commit()

    await runtime.storage._async_writer(insert)


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

    recovered = await service._evaluate_current(
        session,
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
    assert feedback["reveal_correct_answer"] is False
    assert feedback["correct_answer"] is None
    assert feedback["submitted_text"] is None


@pytest.mark.asyncio
async def test_real_ws_quiz_answer_is_atomic_and_generic_session_answer_is_rejected(
    hass: HomeAssistant,
    hass_ws_client: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    card_key = await _activate_quiz_package(hass, tmp_path)
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "P5.4",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile = await owner.receive_json()
    assert profile["success"] is True
    profile_id = str(profile["result"]["profile_id"])

    await owner.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "P5.4 quiz",
            "pack_version_id": "locklearn:pack-version:p5-4",
            "source_language": "en",
            "target_language": "fr",
            "explicit_card_keys": [card_key],
        }
    )
    track = await owner.receive_json()
    assert track["success"] is True
    track_id = str(track["result"]["track_id"])
    await _seed_review_progress(
        hass,
        profile_id=profile_id,
        track_id=track_id,
        card_key=card_key,
    )

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "track_id": track_id,
            "session_type": "quiz",
            "strategy": "default",
            "settings": {
                "requested_cards": 1,
                "quiz_format": "free_text",
                "option_count": 4,
            },
        }
    )
    started = await owner.receive_json()
    assert started["success"] is True
    state = started["result"]
    question = state["current_question"]
    assert question is not None
    assert question["payload"]["quiz"]["format"] == "free_text"
    assert "correct_answer" not in question["payload"]["quiz"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/answer",
            "session_id": state["id"],
            "expected_version": state["version"],
            "question_id": question["question_id"],
            "answer": {"kind": "quiz", "submitted_text": "wrong"},
        }
    )
    bypass = await owner.receive_json()
    assert bypass["success"] is False
    assert bypass["error"]["code"] == "locklearn/invalid_request"

    await owner.send_json_auto_id(
        {
            "type": "locklearn/quiz/answer",
            "session_id": state["id"],
            "expected_version": state["version"],
            "question_id": question["question_id"],
            "answer": {
                "kind": "quiz",
                "submitted_text": "wrong",
                "hint_used": False,
            },
        }
    )
    answered = await owner.receive_json()
    assert answered["success"] is True
    assert answered["result"]["feedback"]["result"] == "wrong"
    assert answered["result"]["feedback"]["correct_answer"] == "réponse"
    assert answered["result"]["session"]["current_question"] is None

    events = await runtime.storage.repositories.review_events.async_list_scope_events(
        profile_id=profile_id,
        track_id=track_id,
    )
    assert len(events) == 1
    assert events[0]["mode"] == "verified_free_text"
    assert events[0]["retrieval_occurred"] is True
    assert events[0]["result"] == "wrong"

    progress = await runtime.storage.repositories.progress.async_get(
        profile_id=profile_id,
        track_id=track_id,
        card_key=card_key,
    )
    assert progress is not None
    assert progress["verified_wrong_count"] == 1

    await hass.config_entries.async_unload(entry.entry_id)


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
    assert service._cloze_prompt(masked, accepted) == "____ is here."
