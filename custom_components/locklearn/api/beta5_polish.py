"""Additive beta.5 field-polish WebSocket commands.

These commands keep protocol v3 backwards compatible while tightening the
session start/retry and calibration-follow-up behavior discovered during field
qualification.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import HomeAssistant

from ..core.acl import ProfilePermission
from ..core.learning_sessions import LearningSessionError
from ..core.presentation import PresentationError
from ..core.quiz_sessions import QuizSessionError
from ..core.session_selection import PreparedSessionSelection, SessionSelectionError
from ..core.sessions import SessionQuestion, SessionValidationError
from ..runtime import LockLearnRuntime
from ..storage.database import SessionNotFoundError, StaleSessionError
from .websocket import (
    ERR_INVALID_REQUEST,
    ERR_NOT_FOUND,
    ERR_STALE_SESSION,
    _authorized_session,
    _require_profile_permission,
    _require_runtime,
    _with_fatigue_advice,
)


def _stable_rank(seed: str, card_key: str) -> bytes:
    """Return a deterministic rank without process-global randomness."""
    return sha256(f"{seed}\0{card_key}".encode()).digest()


def _selection_bucket(candidate: PreparedSessionSelection) -> tuple[str, str]:
    selection = candidate.payload.get("selection")
    if not isinstance(selection, dict):
        return ("", "")
    return (str(selection.get("progress_state", "")), str(selection.get("reason", "")))


def _vary_equivalent_order(
    selected: tuple[PreparedSessionSelection, ...],
    *,
    seed: str,
) -> tuple[PreparedSessionSelection, ...]:
    """Vary only contiguous equally-prioritized candidates.

    SessionSelectionService has already enforced prerequisites, SRS priority,
    quotas and sibling/confusable eligibility.  We therefore preserve bucket
    order and only vary cards inside contiguous equal-state/reason runs.
    """
    if len(selected) < 2:
        return selected
    output: list[PreparedSessionSelection] = []
    start = 0
    while start < len(selected):
        bucket = _selection_bucket(selected[start])
        end = start + 1
        while end < len(selected) and _selection_bucket(selected[end]) == bucket:
            end += 1
        run = list(selected[start:end])
        run.sort(key=lambda item: _stable_rank(seed, item.card_key))
        output.extend(run)
        start = end
    return tuple(output)


async def _latest_calibration_id(
    runtime: LockLearnRuntime,
    *,
    profile_id: str,
    track_id: str,
) -> str | None:
    def read(connection: Any) -> str | None:
        row = connection.execute(
            """SELECT id FROM sessions
               WHERE profile_id = ? AND track_id = ? AND type = 'calibration'
                 AND status = 'completed'
               ORDER BY completed_at_utc DESC, last_activity_at_utc DESC
               LIMIT 1""",
            (profile_id, track_id),
        ).fetchone()
        return None if row is None else str(row[0])

    return await runtime.storage._async_reader(read)


async def _calibration_results(
    runtime: LockLearnRuntime,
    *,
    session_id: str,
) -> tuple[tuple[str, str], ...]:
    """Return one latest verified result per sampled card in sample order."""

    def read(connection: Any) -> tuple[tuple[str, str], ...]:
        rows = connection.execute(
            """SELECT re.card_key, re.result, si.position,
                      re.created_at_utc, re.id
               FROM review_events AS re
               JOIN session_items AS si
                 ON si.session_id = re.session_id
                AND si.card_key = re.card_key
               WHERE re.session_id = ?
                 AND re.retrieval_occurred = 1
                 AND re.mode IN (
                     'verified_mcq', 'verified_free_text', 'verified_cloze'
                 )
                 AND re.result IN ('correct', 'wrong', 'idk', 'unrecognized')
               ORDER BY si.position ASC, re.created_at_utc DESC, re.id DESC""",
            (session_id,),
        ).fetchall()
        seen: set[str] = set()
        result: list[tuple[str, str]] = []
        for card_key, outcome, _position, _created_at, _event_id in rows:
            key = str(card_key)
            if key in seen:
                continue
            seen.add(key)
            result.append((key, str(outcome)))
        return tuple(result)

    return await runtime.storage._async_reader(read)


async def _followup_payload(
    runtime: LockLearnRuntime,
    *,
    profile_id: str,
    track_id: str,
    calibration_session_id: str | None,
) -> dict[str, Any]:
    source_id = calibration_session_id or await _latest_calibration_id(
        runtime,
        profile_id=profile_id,
        track_id=track_id,
    )
    if source_id is None:
        return {"source_session_id": None, "pending_count": 0, "card_keys": []}
    session = await runtime.sessions.async_get(source_id)
    if (
        session is None
        or str(session.get("profile_id")) != profile_id
        or str(session.get("track_id")) != track_id
        or str(session.get("type")) != "calibration"
    ):
        raise SessionValidationError("calibration session does not belong to Track/Profile")

    failed = {
        card_key
        for card_key, result in await _calibration_results(runtime, session_id=source_id)
        if result in {"wrong", "idk", "unrecognized"}
    }
    pending: list[str] = []
    for item in session.get("items", []):
        card_key = str(item.get("card_key", ""))
        if card_key not in failed:
            continue
        progress = await runtime.storage.repositories.progress.async_get(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
        )
        if progress is None:
            continue
        if (
            str(progress.get("state")) == "new"
            and str(progress.get("user_state", "active")) == "active"
            and str(progress.get("content_status", "active")) == "active"
        ):
            pending.append(card_key)
    return {
        "source_session_id": source_id,
        "pending_count": len(pending),
        "card_keys": pending,
    }


async def _prepared_followup_questions(
    runtime: LockLearnRuntime,
    *,
    calibration: dict[str, Any],
    track_id: str,
    card_keys: list[str],
) -> tuple[SessionQuestion, ...]:
    wanted = set(card_keys)
    prepared: list[SessionQuestion] = []
    for item in calibration.get("items", []):
        card_key = str(item.get("card_key", ""))
        if card_key not in wanted:
            continue
        payload = {
            "selection": {
                "content_type": str(
                    (item.get("payload") or {}).get("selection", {}).get("content_type", "")
                ),
                "progress_state": "new",
                "reason": "calibration_followup",
                "pack_position": (item.get("payload") or {})
                .get("selection", {})
                .get("pack_position"),
            },
            "presentation": await runtime.presentation.async_for_card(
                track_id=track_id,
                card_key=card_key,
            ),
        }
        prepared.append(
            SessionQuestion(
                question_id=f"q-{len(prepared) + 1}-{card_key}",
                card_key=card_key,
                learning_item_id=str(item["learning_item_id"]),
                prompt_facet_id=str(item["prompt_facet_id"]),
                answer_facet_id=str(item["answer_facet_id"]),
                payload=payload,
            )
        )
    return tuple(prepared)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/start_v04",
        vol.Required("profile_id"): str,
        vol.Required("track_id"): str,
        vol.Required("session_type"): vol.In(("learn", "quiz", "calibration")),
        vol.Optional("strategy", default="default"): str,
        vol.Optional("settings", default={}): dict,
    }
)
@websocket_api.async_response
async def ws_session_start_v04(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Start a session with a persisted deterministic ordering seed."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    profile_id = msg["profile_id"]
    if not await _require_profile_permission(
        runtime, connection, msg["id"], profile_id, ProfilePermission.ANSWER
    ):
        return
    track_id = msg["track_id"]
    track = await runtime.storage.repositories.tracks.async_get(track_id)
    if track is None or str(track["profile_id"]) != profile_id:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Track not found")
        return

    settings = dict(msg["settings"])
    seed = str(settings.get("selection_seed") or uuid4().hex)
    settings["selection_seed"] = seed
    try:
        selected = await runtime.session_selection.async_prepare(
            profile_id=profile_id,
            track_id=track_id,
            session_type=msg["session_type"],
            settings=settings,
        )
        selected = _vary_equivalent_order(selected, seed=seed)
        if msg["session_type"] in {"quiz", "calibration"}:
            questions = await runtime.quiz_sessions.async_prepare_questions(
                track_id=track_id,
                selected=selected,
                settings=settings,
                session_type=msg["session_type"],
            )
        else:
            questions_list: list[SessionQuestion] = []
            for position, candidate in enumerate(selected):
                payload = dict(candidate.payload)
                payload["presentation"] = await runtime.presentation.async_for_card(
                    track_id=track_id,
                    card_key=candidate.card_key,
                )
                questions_list.append(
                    SessionQuestion(
                        question_id=f"q-{position + 1}-{candidate.card_key}",
                        card_key=candidate.card_key,
                        learning_item_id=candidate.learning_item_id,
                        prompt_facet_id=candidate.prompt_facet_id,
                        answer_facet_id=candidate.answer_facet_id,
                        payload=payload,
                    )
                )
            questions = tuple(questions_list)
        state = await runtime.sessions.async_start(
            profile_id,
            track_id,
            session_type=msg["session_type"],
            strategy=msg["strategy"],
            settings=settings,
            questions=questions,
        )
        state = await _with_fatigue_advice(runtime, state)
    except (
        PresentationError,
        QuizSessionError,
        SessionSelectionError,
        SessionValidationError,
    ) as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], state)


async def _answer_learning_once(
    runtime: LockLearnRuntime,
    *,
    session_id: str,
    expected_version: int,
    question_id: str,
    answer: object,
) -> dict[str, Any]:
    if isinstance(answer, dict) and answer.get("kind") == "learning":
        return await runtime.learning_sessions.async_answer(
            session_id,
            expected_version,
            question_id,
            answer,
        )
    return await runtime.sessions.async_answer(
        session_id,
        expected_version,
        question_id,
        answer,
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/session/answer_v04",
        vol.Required("session_id"): str,
        vol.Required("expected_version"): vol.All(int, vol.Range(min=1)),
        vol.Required("question_id"): str,
        vol.Required("answer"): object,
    }
)
@websocket_api.async_response
async def ws_session_answer_v04(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Apply Learn answer and reconcile one benign same-question stale CAS."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await _authorized_session(
        runtime, connection, msg["id"], msg["session_id"], ProfilePermission.ANSWER
    )
    if state is None:
        return
    if str(state.get("type")) in {"quiz", "calibration"}:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, "Use quiz answer for this session")
        return
    try:
        result = await _answer_learning_once(
            runtime,
            session_id=msg["session_id"],
            expected_version=msg["expected_version"],
            question_id=msg["question_id"],
            answer=msg["answer"],
        )
    except StaleSessionError:
        canonical = await runtime.sessions.async_get(msg["session_id"])
        if (
            canonical is None
            or canonical.get("current_question") is None
            or str(canonical["current_question"].get("question_id")) != msg["question_id"]
        ):
            connection.send_error(
                msg["id"],
                ERR_STALE_SESSION,
                "Session refreshed; load the latest recorded state",
            )
            return
        try:
            result = await _answer_learning_once(
                runtime,
                session_id=msg["session_id"],
                expected_version=int(canonical["version"]),
                question_id=msg["question_id"],
                answer=msg["answer"],
            )
        except StaleSessionError:
            connection.send_error(
                msg["id"], ERR_STALE_SESSION, "Session refreshed; load the latest recorded state"
            )
            return
    except (LearningSessionError, QuizSessionError) as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    except SessionNotFoundError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Session not found")
        return
    connection.send_result(msg["id"], await _with_fatigue_advice(runtime, result))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/quiz/answer_v04",
        vol.Required("session_id"): str,
        vol.Required("expected_version"): vol.All(int, vol.Range(min=1)),
        vol.Required("question_id"): str,
        vol.Required("answer"): object,
    }
)
@websocket_api.async_response
async def ws_quiz_answer_v04(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Quiz answer with the same one-time stale reconciliation policy."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    state = await _authorized_session(
        runtime, connection, msg["id"], msg["session_id"], ProfilePermission.ANSWER
    )
    if state is None:
        return
    if str(state.get("type")) not in {"quiz", "calibration"}:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, "Session is not quiz/calibration")
        return
    try:
        result = await runtime.quiz_sessions.async_answer(
            msg["session_id"], msg["expected_version"], msg["question_id"], msg["answer"]
        )
    except StaleSessionError:
        canonical = await runtime.sessions.async_get(msg["session_id"])
        if (
            canonical is None
            or canonical.get("current_question") is None
            or str(canonical["current_question"].get("question_id")) != msg["question_id"]
        ):
            connection.send_error(
                msg["id"], ERR_STALE_SESSION, "Session refreshed; load the latest recorded state"
            )
            return
        try:
            result = await runtime.quiz_sessions.async_answer(
                msg["session_id"],
                int(canonical["version"]),
                msg["question_id"],
                msg["answer"],
            )
        except StaleSessionError:
            connection.send_error(
                msg["id"], ERR_STALE_SESSION, "Session refreshed; load the latest recorded state"
            )
            return
    except QuizSessionError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    except SessionNotFoundError:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Session not found")
        return
    result["session"] = await _with_fatigue_advice(runtime, result["session"])
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/calibration/followup/status",
        vol.Required("profile_id"): str,
        vol.Required("track_id"): str,
        vol.Optional("calibration_session_id"): str,
    }
)
@websocket_api.async_response
async def ws_calibration_followup_status(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if not await _require_profile_permission(
        runtime, connection, msg["id"], msg["profile_id"], ProfilePermission.READ
    ):
        return
    try:
        payload = await _followup_payload(
            runtime,
            profile_id=msg["profile_id"],
            track_id=msg["track_id"],
            calibration_session_id=msg.get("calibration_session_id"),
        )
    except SessionValidationError as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], payload)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "locklearn/calibration/followup/start",
        vol.Required("profile_id"): str,
        vol.Required("track_id"): str,
        vol.Required("calibration_session_id"): str,
    }
)
@websocket_api.async_response
async def ws_calibration_followup_start(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Start Learn from exactly the unresolved failed/IDK calibration cards."""
    runtime = _require_runtime(hass, connection, msg["id"])
    if runtime is None:
        return
    if not await _require_profile_permission(
        runtime, connection, msg["id"], msg["profile_id"], ProfilePermission.ANSWER
    ):
        return
    try:
        payload = await _followup_payload(
            runtime,
            profile_id=msg["profile_id"],
            track_id=msg["track_id"],
            calibration_session_id=msg["calibration_session_id"],
        )
        card_keys = list(payload["card_keys"])
        if not card_keys:
            raise SessionValidationError("calibration has no unresolved cards to learn")
        calibration = await runtime.sessions.async_get(str(payload["source_session_id"]))
        if calibration is None:
            raise SessionValidationError("calibration session not found")
        questions = await _prepared_followup_questions(
            runtime,
            calibration=calibration,
            track_id=msg["track_id"],
            card_keys=card_keys,
        )
        if not questions:
            raise SessionValidationError("calibration follow-up has no active cards")
        state = await runtime.sessions.async_start(
            msg["profile_id"],
            msg["track_id"],
            session_type="learn",
            strategy="calibration_followup",
            settings={
                "source_calibration_session_id": payload["source_session_id"],
                "requested_cards": len(questions),
            },
            questions=questions,
        )
        state = await _with_fatigue_advice(runtime, state)
    except (PresentationError, SessionValidationError) as err:
        connection.send_error(msg["id"], ERR_INVALID_REQUEST, str(err))
        return
    connection.send_result(msg["id"], state)


COMMANDS = (
    ws_session_start_v04,
    ws_session_answer_v04,
    ws_quiz_answer_v04,
    ws_calibration_followup_status,
    ws_calibration_followup_start,
)


def async_register_beta5_polish_commands(hass: HomeAssistant) -> None:
    """Register additive beta.5 polish commands once per HA process."""
    for command in COMMANDS:
        websocket_api.async_register_command(hass, command)
