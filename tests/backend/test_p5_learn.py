"""P5.3 direction-aware Learn presentation and atomic session signal tests."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
from custom_components.locklearn.core.content import derive_card_definition_id, derive_card_key
from custom_components.locklearn.core.sessions import SessionQuestion
from custom_components.locklearn.storage.database import StaleSessionError
from tests.backend.content_db_helpers import (
    CONCEPT_ID,
    DATASET_ID,
    ITEM_A,
    TERM_ID,
    card_identity,
    create_package,
    facet_ids,
)


async def _activate_package(hass: HomeAssistant, tmp_path: Path) -> tuple[str, str]:
    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    package = create_package(
        tmp_path / "p5-3.db",
        "p5-3",
        active_item_ids=(ITEM_A,),
    )
    prompt_id, answer_id = facet_ids(ITEM_A)
    reverse_key = derive_card_key(ITEM_A, answer_id, prompt_id)
    reverse_id = derive_card_definition_id(ITEM_A, answer_id, prompt_id)
    with sqlite3.connect(package) as connection:
        connection.execute(
            """UPDATE facets SET language_tag = 'en', script = 'Latn'
               WHERE facet_id = ?""",
            (prompt_id,),
        )
        connection.execute(
            """UPDATE facets SET language_tag = 'fr', script = 'Latn'
               WHERE facet_id = ?""",
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
               ) VALUES ('locklearn:term:answer', ?, 'fr', 'Latn',
                         'réponse', 'réponse', 1)""",
            (DATASET_ID,),
        )
        connection.execute(
            "INSERT INTO concept_terms(concept_id, term_id) VALUES (?, 'locklearn:term:answer')",
            (CONCEPT_ID,),
        )
        connection.execute(
            """INSERT INTO content_blocks(
                   content_block_id, learning_item_id, position, kind, role,
                   reveals_answer, mask_strategy, payload_json
               ) VALUES (
                   'locklearn:block:a:answer', ?, 1, 'text', 'answer',
                   1, 'none', ?
               )""",
            (ITEM_A, json.dumps({"text": "réponse"}, ensure_ascii=False)),
        )
        connection.execute(
            """INSERT INTO card_definitions(
                   card_definition_id, card_key, learning_item_id,
                   prompt_facet_id, answer_facet_id, answer_semantics,
                   grading_policy_kind, grading_policy_version,
                   lifecycle_status, superseded_by_card_definition_id
               ) VALUES (?, ?, ?, ?, ?, 'single_value', 'exact', 1, 'active', NULL)""",
            (reverse_id, reverse_key, ITEM_A, answer_id, prompt_id),
        )
        connection.commit()

    candidate = runtime.storage.paths.content_staging_dir / "generation-p5-3.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p5-3",
    )
    await runtime.storage.async_activate_content_generation(candidate)
    return card_identity(ITEM_A)[1], reverse_key


async def _create_profile(
    hass: HomeAssistant,
    hass_ws_client: Any,
) -> tuple[Any, str]:
    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "P5.3",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    result = await owner.receive_json()
    assert result["success"] is True
    return owner, result["result"]["profile_id"]


async def _create_track(
    owner: Any,
    *,
    profile_id: str,
    name: str,
    source_language: str,
    target_language: str,
    card_key: str,
) -> str:
    await owner.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": name,
            "pack_version_id": "locklearn:pack-version:p5-3",
            "source_language": source_language,
            "target_language": target_language,
            "explicit_card_keys": [card_key],
        }
    )
    result = await owner.receive_json()
    assert result["success"] is True
    return str(result["result"]["track_id"])


async def test_presentation_respects_card_direction(
    hass: HomeAssistant,
    hass_ws_client: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    forward_key, reverse_key = await _activate_package(hass, tmp_path)
    owner, profile_id = await _create_profile(hass, hass_ws_client)
    forward_track = await _create_track(
        owner,
        profile_id=profile_id,
        name="EN-FR",
        source_language="en",
        target_language="fr",
        card_key=forward_key,
    )
    reverse_track = await _create_track(
        owner,
        profile_id=profile_id,
        name="FR-EN",
        source_language="fr",
        target_language="en",
        card_key=reverse_key,
    )
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    forward = await runtime.presentation.async_for_card(
        track_id=forward_track,
        card_key=forward_key,
    )
    reverse = await runtime.presentation.async_for_card(
        track_id=reverse_track,
        card_key=reverse_key,
    )
    assert forward["prompt"]["blocks"][0]["payload"]["text"] == "prompt"
    assert forward["answer"]["blocks"][0]["payload"]["text"] == "réponse"
    assert reverse["prompt"]["blocks"][0]["payload"]["text"] == "réponse"
    assert reverse["answer"]["blocks"][0]["payload"]["text"] == "prompt"

    await hass.config_entries.async_unload(entry.entry_id)


async def test_learning_answer_commits_event_progress_and_session_atomically(
    hass: HomeAssistant,
    hass_ws_client: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    forward_key, _reverse_key = await _activate_package(hass, tmp_path)
    owner, profile_id = await _create_profile(hass, hass_ws_client)
    track_id = await _create_track(
        owner,
        profile_id=profile_id,
        name="EN-FR",
        source_language="en",
        target_language="fr",
        card_key=forward_key,
    )
    runtime = hass.data[DOMAIN][DATA_RUNTIME]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "track_id": track_id,
            "session_type": "learn",
            "strategy": "default",
            "settings": {"requested_cards": 1},
        }
    )
    started = await owner.receive_json()
    assert started["success"] is True
    state = started["result"]
    question = state["current_question"]
    assert question is not None
    assert (
        question["payload"]["presentation"]["answer"]["blocks"][0]["payload"]["text"] == "réponse"
    )

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/answer",
            "session_id": state["id"],
            "expected_version": state["version"],
            "question_id": question["question_id"],
            "answer": {
                "kind": "learning",
                "action": "introduce",
                "hint_used": False,
                "presentation_to_answer_ms": 1200,
            },
        }
    )
    introduced = await owner.receive_json()
    assert introduced["success"] is True
    progress = await runtime.storage.repositories.progress.async_get(
        profile_id=profile_id,
        track_id=track_id,
        card_key=forward_key,
    )
    assert progress is not None
    assert progress["state"] == "learning"
    assert progress["seen_count"] == 1

    events = await runtime.storage.repositories.review_events.async_list_scope_events(
        profile_id=profile_id,
        track_id=track_id,
    )
    assert len(events) == 1
    assert events[0]["mode"] == "introduction"
    assert events[0]["retrieval_occurred"] is False
    assert events[0]["presentation_to_answer_ms"] == 1200
    assert events[0]["session_id"] == state["id"]

    manual = await runtime.sessions.async_start(
        profile_id,
        track_id,
        questions=(
            SessionQuestion(
                question_id="hint-test",
                card_key=forward_key,
                learning_item_id=ITEM_A,
                prompt_facet_id=facet_ids(ITEM_A)[0],
                answer_facet_id=facet_ids(ITEM_A)[1],
                payload=question["payload"],
            ),
        ),
    )
    await runtime.learning_sessions.async_answer(
        manual["id"],
        manual["version"],
        "hint-test",
        {
            "kind": "learning",
            "action": "known",
            "hint_used": True,
            "presentation_to_answer_ms": 800,
        },
    )
    events = await runtime.storage.repositories.review_events.async_list_scope_events(
        profile_id=profile_id,
        track_id=track_id,
    )
    assert len(events) == 2
    assert events[-1]["mode"] == "self_assessment_after_retrieval"
    assert events[-1]["hint_used"] is True
    assert events[-1]["result"] == "known"

    race = await runtime.sessions.async_start(
        profile_id,
        track_id,
        questions=(
            SessionQuestion(
                question_id="race-test",
                card_key=forward_key,
                learning_item_id=ITEM_A,
                prompt_facet_id=facet_ids(ITEM_A)[0],
                answer_facet_id=facet_ids(ITEM_A)[1],
                payload=question["payload"],
            ),
        ),
    )
    before = len(
        await runtime.storage.repositories.review_events.async_list_scope_events(
            profile_id=profile_id,
            track_id=track_id,
        )
    )
    results = await asyncio.gather(
        runtime.learning_sessions.async_answer(
            race["id"],
            race["version"],
            "race-test",
            {"kind": "learning", "action": "review", "hint_used": False},
        ),
        runtime.learning_sessions.async_answer(
            race["id"],
            race["version"],
            "race-test",
            {"kind": "learning", "action": "review", "hint_used": False},
        ),
        return_exceptions=True,
    )
    assert sum(isinstance(result, StaleSessionError) for result in results) == 1
    after = len(
        await runtime.storage.repositories.review_events.async_list_scope_events(
            profile_id=profile_id,
            track_id=track_id,
        )
    )
    assert after == before + 1

    await owner.send_json_auto_id(
        {
            "type": "locklearn/content/report_question",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": forward_key,
            "learning_item_id": ITEM_A,
            "prompt_facet_id": facet_ids(ITEM_A)[0],
            "answer_facet_id": facet_ids(ITEM_A)[1],
            "reason": "user_reported_question",
        }
    )
    reported = await owner.receive_json()
    assert reported["success"] is True
    stored = await runtime.storage.repositories.content_reports.async_get(
        reported["result"]["report_id"]
    )
    assert stored is not None
    assert stored["payload"]["report_kind"] == "question"
    assert reported["result"]["srs_penalized"] is False

    await hass.config_entries.async_unload(entry.entry_id)
