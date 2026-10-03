"""Regression tests for beta.5 field-polish behavior."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.locklearn.api import beta5_polish
from custom_components.locklearn.core.session_selection import PreparedSessionSelection


def _prepared(
    card_key: str, *, state: str = "new", reason: str = "new"
) -> PreparedSessionSelection:
    return PreparedSessionSelection(
        card_key=card_key,
        learning_item_id=f"item-{card_key}",
        prompt_facet_id=f"prompt-{card_key}",
        answer_facet_id=f"answer-{card_key}",
        payload={
            "selection": {
                "content_type": "vocabulary",
                "progress_state": state,
                "reason": reason,
                "pack_position": int(card_key.removeprefix("card-")),
            }
        },
    )


def test_equivalent_order_is_seeded_and_replay_stable() -> None:
    selected = tuple(_prepared(f"card-{index}") for index in range(1, 10))

    first = beta5_polish._vary_equivalent_order(selected, seed="session-a")
    replay = beta5_polish._vary_equivalent_order(selected, seed="session-a")
    second = beta5_polish._vary_equivalent_order(selected, seed="session-b")

    assert tuple(item.card_key for item in first) == tuple(item.card_key for item in replay)
    assert tuple(item.card_key for item in first) != tuple(item.card_key for item in second)
    assert {item.card_key for item in first} == {item.card_key for item in selected}


def test_order_never_crosses_selection_priority_buckets() -> None:
    selected = (
        _prepared("card-1", state="learning", reason="learning_due"),
        _prepared("card-2", state="learning", reason="learning_due"),
        _prepared("card-3", state="review", reason="review_due"),
        _prepared("card-4", state="review", reason="review_due"),
        _prepared("card-5", state="new", reason="new"),
        _prepared("card-6", state="new", reason="new"),
    )

    varied = beta5_polish._vary_equivalent_order(selected, seed="different-session")

    assert [item.payload["selection"]["progress_state"] for item in varied] == [
        "learning",
        "learning",
        "review",
        "review",
        "new",
        "new",
    ]


class _Sessions:
    def __init__(self, calibration: dict[str, Any]) -> None:
        self.calibration = calibration

    async def async_get(self, session_id: str) -> dict[str, Any] | None:
        return self.calibration if session_id == self.calibration["id"] else None


class _Progress:
    def __init__(self, states: dict[str, dict[str, Any]]) -> None:
        self.states = states

    async def async_get(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
    ) -> dict[str, Any] | None:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        return self.states.get(card_key)


class _Presentation:
    async def async_for_card(self, *, track_id: str, card_key: str) -> dict[str, Any]:
        assert track_id == "track-1"
        return {"card_key": card_key, "prompt": {"blocks": []}, "answer": {"blocks": []}}


@pytest.mark.asyncio
async def test_calibration_followup_contains_exact_unresolved_failed_cards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calibration = {
        "id": "cal-1",
        "profile_id": "profile-1",
        "track_id": "track-1",
        "type": "calibration",
        "items": [
            {
                "card_key": key,
                "learning_item_id": f"item-{key}",
                "prompt_facet_id": f"prompt-{key}",
                "answer_facet_id": f"answer-{key}",
                "payload": {"selection": {"content_type": "vocabulary", "pack_position": pos}},
            }
            for pos, key in enumerate(("a", "i", "ru", "u", "e"), start=1)
        ],
    }
    states = {
        "a": {"state": "review", "user_state": "active", "content_status": "active"},
        "i": {"state": "review", "user_state": "active", "content_status": "active"},
        "ru": {"state": "new", "user_state": "active", "content_status": "active"},
        "u": {"state": "new", "user_state": "suspended", "content_status": "active"},
        "e": {"state": "new", "user_state": "active", "content_status": "active"},
    }
    runtime = SimpleNamespace(
        sessions=_Sessions(calibration),
        storage=SimpleNamespace(repositories=SimpleNamespace(progress=_Progress(states))),
        presentation=_Presentation(),
    )

    async def fake_results(_runtime: Any, *, session_id: str) -> tuple[tuple[str, str], ...]:
        assert session_id == "cal-1"
        return (
            ("a", "correct"),
            ("i", "correct"),
            ("ru", "wrong"),
            ("u", "idk"),
            ("e", "unrecognized"),
        )

    monkeypatch.setattr(beta5_polish, "_calibration_results", fake_results)

    payload = await beta5_polish._followup_payload(
        runtime,  # type: ignore[arg-type]
        profile_id="profile-1",
        track_id="track-1",
        calibration_session_id="cal-1",
    )
    questions = await beta5_polish._prepared_followup_questions(
        runtime,  # type: ignore[arg-type]
        calibration=calibration,
        track_id="track-1",
        card_keys=list(payload["card_keys"]),
    )

    assert payload == {
        "source_session_id": "cal-1",
        "pending_count": 2,
        "card_keys": ["ru", "e"],
    }
    assert [question.card_key for question in questions] == ["ru", "e"]
    assert "a" not in payload["card_keys"]
    assert "i" not in payload["card_keys"]
    assert "u" not in payload["card_keys"]
