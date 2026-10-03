from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, *, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text()
    matches = text.count(old)
    if matches < count:
        raise SystemExit(f"{path}: expected >= {count}, found {matches}: {old[:100]!r}")
    p.write_text(text.replace(old, new, count))


replace(
    "custom_components/locklearn/core/session_selection.py",
    "from dataclasses import dataclass\n",
    "from dataclasses import dataclass\nfrom hashlib import sha256\n",
)
replace(
    "custom_components/locklearn/core/session_selection.py",
    "        ordered = self._build_sequence(\n            candidates,\n            requested_cards=requested_cards,\n            new_quota=new_quota,\n            weights=weights,\n        )",
    "        raw_selection_seed = effective_settings.get(\"selection_seed\")\n        selection_seed = (\n            raw_selection_seed if isinstance(raw_selection_seed, str) and raw_selection_seed else None\n        )\n        ordered = self._build_sequence(\n            candidates,\n            requested_cards=requested_cards,\n            new_quota=new_quota,\n            weights=weights,\n            selection_seed=selection_seed,\n        )",
)
replace(
    "custom_components/locklearn/core/session_selection.py",
    "    def _build_sequence(\n        self,\n        candidates: list[_Candidate],\n        *,\n        requested_cards: int,\n        new_quota: int,\n        weights: dict[str, float],\n    ) -> list[_Candidate]:",
    "    def _build_sequence(\n        self,\n        candidates: list[_Candidate],\n        *,\n        requested_cards: int,\n        new_quota: int,\n        weights: dict[str, float],\n        selection_seed: str | None = None,\n    ) -> list[_Candidate]:",
)
replace(
    "custom_components/locklearn/core/session_selection.py",
    "                    *self._candidate_order_key(c),\n",
    "                    *self._candidate_order_key(c, selection_seed=selection_seed),\n",
)
replace(
    "custom_components/locklearn/core/session_selection.py",
    "    @staticmethod\n    def _candidate_order_key(candidate: _Candidate) -> tuple[int, str, int, str]:\n        priority = {\n            \"relearning\": 0,\n            \"learning\": 1,\n            \"review\": 2,\n            \"leech\": 3,\n            \"new\": 4,\n        }[candidate.state]\n        return (\n            priority,\n            candidate.next_due_at_utc or \"\",\n            candidate.pack_position,\n            candidate.card_key,\n        )",
    "    @staticmethod\n    def _candidate_order_key(\n        candidate: _Candidate,\n        *,\n        selection_seed: str | None = None,\n    ) -> tuple[int, str, str, int, str]:\n        priority = {\n            \"relearning\": 0,\n            \"learning\": 1,\n            \"review\": 2,\n            \"leech\": 3,\n            \"new\": 4,\n        }[candidate.state]\n        seeded_rank = \"\"\n        if selection_seed is not None and candidate.state == \"new\":\n            seeded_rank = sha256(\n                f\"{selection_seed}\\0{candidate.card_key}\".encode()\n            ).hexdigest()\n        return (\n            priority,\n            candidate.next_due_at_utc or \"\",\n            seeded_rank,\n            candidate.pack_position,\n            candidate.card_key,\n        )",
)

path = Path("tests/backend/test_session_selection.py")
text = path.read_text()
marker = "@pytest.mark.asyncio\nasync def test_known_already_is_learn_hidden_until_verified_quiz_due() -> None:\n"
if marker not in text:
    raise SystemExit("test insertion marker missing")
test = '''@pytest.mark.asyncio\nasync def test_selection_seed_varies_new_prefix_and_replays_stably() -> None:\n    candidates = tuple(\n        _candidate(index, state="new", content_type="vocabulary")\n        for index in range(1, 41)\n    )\n    service = _service(\n        candidates,\n        profiles=_Profiles(max_new=40, session_length=8),\n    )\n\n    first = await service.async_prepare(\n        profile_id="profile-1",\n        track_id="track-1",\n        session_type="learn",\n        settings={"requested_cards": 8, "selection_seed": "session-a"},\n    )\n    replay = await service.async_prepare(\n        profile_id="profile-1",\n        track_id="track-1",\n        session_type="learn",\n        settings={"requested_cards": 8, "selection_seed": "session-a"},\n    )\n    second = await service.async_prepare(\n        profile_id="profile-1",\n        track_id="track-1",\n        session_type="learn",\n        settings={"requested_cards": 8, "selection_seed": "session-b"},\n    )\n\n    first_keys = tuple(item.card_key for item in first)\n    replay_keys = tuple(item.card_key for item in replay)\n    second_keys = tuple(item.card_key for item in second)\n    assert first_keys == replay_keys\n    assert first_keys != second_keys\n    assert len(first_keys) == len(second_keys)\n    assert len(first_keys) > 0\n    assert set(first_keys) != {f"card-{index}" for index in range(1, len(first_keys) + 1)}\n\n\n'''
path.write_text(text.replace(marker, test + marker, 1))

print("seeded selection completed")
