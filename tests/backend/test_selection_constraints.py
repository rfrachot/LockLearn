"""P3.5 prerequisite, sibling-burial and confusable-spacing tests."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.selection import (
    SelectionConstraintError,
    SelectionConstraintService,
)
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import CardReference, SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import (
    ITEM_A,
    ITEM_B,
    card_identity,
    create_package,
    facet_ids,
)


@dataclass
class _FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class _FakeSelectionRepository:
    def __init__(
        self,
        *,
        settings: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._settings = settings or {}
        self._context = context or _context()

    async def async_get(self, track_id: str) -> dict[str, Any] | None:
        if track_id != "track-1":
            return None
        return {
            "track_id": "track-1",
            "profile_id": "profile-1",
            "pack_version_id": "pack-version-1",
            "settings": dict(self._settings),
        }

    async def async_selection_constraints(
        self,
        *,
        profile_id: str,
        track_id: str,
        pack_version_id: str,
        learning_item_id: str,
        card_key: str,
    ) -> dict[str, Any]:
        assert profile_id == "profile-1"
        assert track_id == "track-1"
        assert pack_version_id == "pack-version-1"
        assert learning_item_id == "item-1"
        assert card_key == "card-1"
        return self._context


def _context() -> dict[str, Any]:
    return {
        "selected": True,
        "prerequisite_card_keys": (),
        "unlock_conditions": (),
        "prerequisite_progress": {},
        "sibling_last_interaction_at_utc": None,
        "confusable_groups": (),
    }


def _service(
    context: dict[str, Any],
    *,
    settings: dict[str, Any] | None = None,
) -> SelectionConstraintService:
    return SelectionConstraintService(
        _FakeSelectionRepository(settings=settings, context=context),
        clock=_FixedClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC)),
    )


@pytest.mark.asyncio
async def test_prerequisites_block_new_card_until_all_thresholds_pass() -> None:
    context = _context()
    context.update(
        {
            "prerequisite_card_keys": ("pre-a", "pre-b"),
            "unlock_conditions": (
                {"metric": "verified_correct_count", "minimum": 2.0},
                {"metric": "mastery", "minimum": 0.7},
            ),
            "prerequisite_progress": {
                "pre-a": {
                    "state": "review",
                    "mastery": 0.8,
                    "box": 3,
                    "verified_correct_count": 2,
                    "seen_count": 4,
                },
                "pre-b": {
                    "state": "learning",
                    "mastery": 0.4,
                    "box": 1,
                    "verified_correct_count": 1,
                    "seen_count": 2,
                },
            },
        }
    )
    service = _service(context)

    decision = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )

    assert decision.eligible is False
    assert decision.reasons == (
        "prerequisite_threshold:pre-b:verified_correct_count",
        "prerequisite_threshold:pre-b:mastery",
    )

    context["prerequisite_progress"]["pre-b"].update({"mastery": 0.75, "verified_correct_count": 2})
    passed = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )
    assert passed.eligible is True


@pytest.mark.asyncio
async def test_prerequisite_without_unlock_threshold_requires_prior_exposure() -> None:
    context = _context()
    context.update(
        {
            "prerequisite_card_keys": ("pre-a",),
            "prerequisite_progress": {
                "pre-a": {
                    "state": "new",
                    "mastery": 0.0,
                    "box": 0,
                    "verified_correct_count": 0,
                    "seen_count": 0,
                }
            },
        }
    )
    service = _service(context)

    blocked = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )
    assert blocked.reasons == ("prerequisite_unseen:pre-a",)

    context["prerequisite_progress"]["pre-a"]["seen_count"] = 1
    allowed = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )
    assert allowed.eligible is True


@pytest.mark.asyncio
async def test_new_and_review_siblings_use_distinct_burial_gaps() -> None:
    context = _context()
    context["sibling_last_interaction_at_utc"] = "2026-09-22T19:00:00+00:00"
    service = _service(context)

    new_decision = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )
    review_decision = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="review",
    )

    assert new_decision.reasons == ("sibling_buried:new",)
    assert new_decision.blocked_until_utc == "2026-09-23T19:00:00+00:00"
    assert review_decision.reasons == ("sibling_buried:review",)
    assert review_decision.blocked_until_utc == "2026-09-22T23:00:00+00:00"


@pytest.mark.asyncio
async def test_learning_and_relearning_are_not_delayed_by_sibling_burial() -> None:
    context = _context()
    context["sibling_last_interaction_at_utc"] = "2026-09-22T19:59:00+00:00"
    service = _service(context)

    for state in ("learning", "relearning"):
        decision = await service.async_evaluate(
            profile_id="profile-1",
            track_id="track-1",
            card_key="card-1",
            learning_item_id="item-1",
            state=state,
        )
        assert decision.eligible is True


@pytest.mark.asyncio
async def test_track_can_override_sibling_gap_without_changing_global_policy() -> None:
    context = _context()
    context["sibling_last_interaction_at_utc"] = "2026-09-22T19:59:00+00:00"
    service = _service(
        context,
        settings={
            "sibling_gap_new_minutes": 0,
            "sibling_gap_review_minutes": 0,
        },
    )

    decision = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )
    assert decision.eligible is True


@pytest.mark.asyncio
async def test_confusable_group_blocks_only_new_introduction_until_gap_expires() -> None:
    context = _context()
    context["confusable_groups"] = (
        {
            "confusable_group_id": "group-1",
            "min_intro_gap_days": 2,
            "other_item_last_introduced_at_utc": "2026-09-21T12:00:00+00:00",
        },
    )
    service = _service(context)

    new_decision = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="new",
    )
    review_decision = await service.async_evaluate(
        profile_id="profile-1",
        track_id="track-1",
        card_key="card-1",
        learning_item_id="item-1",
        state="review",
    )

    assert new_decision.reasons == ("confusable_intro_gap:group-1",)
    assert new_decision.blocked_until_utc == "2026-09-23T12:00:00+00:00"
    assert review_decision.eligible is True


def test_confusable_distractors_are_reserved_for_review_state() -> None:
    assert SelectionConstraintService.confusable_distractors_allowed("review") is True
    for state in ("new", "learning", "relearning", "leech"):
        assert SelectionConstraintService.confusable_distractors_allowed(state) is False


@pytest.mark.asyncio
async def test_selection_constraint_validation_is_explicit() -> None:
    service = _service(_context())

    with pytest.raises(SelectionConstraintError, match="unsupported progress state"):
        await service.async_evaluate(
            profile_id="profile-1",
            track_id="track-1",
            card_key="card-1",
            learning_item_id="item-1",
            state="invalid",
        )

    with pytest.raises(SelectionConstraintError, match="does not belong"):
        await service.async_evaluate(
            profile_id="other-profile",
            track_id="track-1",
            card_key="card-1",
            learning_item_id="item-1",
            state="new",
        )

    with pytest.raises(SelectionConstraintError, match="must be >= 0"):
        SelectionConstraintService(
            _FakeSelectionRepository(),
            sibling_gap_new_minutes=-1,
        )

    not_selected = _context()
    not_selected["selected"] = False
    with pytest.raises(SelectionConstraintError, match="not enabled"):
        await _service(not_selected).async_evaluate(
            profile_id="profile-1",
            track_id="track-1",
            card_key="card-1",
            learning_item_id="item-1",
            state="new",
        )


@pytest.mark.asyncio
async def test_repository_reads_pack_prerequisites_and_confusable_progress(
    tmp_path: Path,
) -> None:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    try:
        package = create_package(
            tmp_path / "selection-package.db",
            "selection",
            active_item_ids=(ITEM_A, ITEM_B),
        )
        pack_version_id = "locklearn:pack-version:selection"
        prerequisite_card_key = card_identity(ITEM_A)[1]
        with sqlite3.connect(package) as connection:
            connection.execute(
                """INSERT INTO pack_item_prerequisites(
                       pack_version_id, learning_item_id, prerequisite_card_key
                   ) VALUES (?, ?, ?)""",
                (pack_version_id, ITEM_B, prerequisite_card_key),
            )
            connection.execute(
                """INSERT INTO pack_item_unlock_conditions(
                       pack_version_id, learning_item_id, position, metric, minimum
                   ) VALUES (?, ?, 0, 'verified_correct_count', 2)""",
                (pack_version_id, ITEM_B),
            )
            connection.execute(
                """INSERT INTO confusable_groups(
                       confusable_group_id, pack_version_id, min_intro_gap_days
                   ) VALUES ('locklearn:confusable:test', ?, 2)""",
                (pack_version_id,),
            )
            connection.executemany(
                """INSERT INTO confusable_group_items(
                       confusable_group_id, learning_item_id
                   ) VALUES ('locklearn:confusable:test', ?)""",
                ((ITEM_A,), (ITEM_B,)),
            )
            connection.commit()

        candidate = storage.paths.content_staging_dir / "generation-selection.db"
        await storage.async_build_content_generation(
            (package,),
            candidate,
            generation_id="generation-selection",
        )
        await storage.async_activate_content_generation(candidate)

        clock = _FixedClock(datetime(2026, 9, 22, 20, 0, tzinfo=UTC))
        profiles = ProfileService(
            storage.repositories.profiles,
            clock=clock,
            id_factory=lambda: "profile-selection",
        )
        await profiles.async_create_profile(
            name="Selection",
            preset="standard",
            timezone="Europe/Paris",
            owner_ha_user_ids=("owner",),
        )
        tracks = TrackService(
            storage.repositories.tracks,
            clock=clock,
            id_factory=lambda: "track-selection",
        )
        await tracks.async_create_track(
            profile_id="profile-selection",
            name="Selection Track",
            pack_version_id=pack_version_id,
            source_language="en",
            target_language="fr",
            explicit_card_keys=(card_identity(ITEM_A)[1], card_identity(ITEM_B)[1]),
        )

        prompt_id, answer_id = facet_ids(ITEM_A)
        await storage.repositories.progress.async_create_if_absent(
            profile_id="profile-selection",
            track_id="track-selection",
            card=CardReference(
                card_key=prerequisite_card_key,
                learning_item_id=ITEM_A,
                prompt_facet_id=prompt_id,
                answer_facet_id=answer_id,
            ),
            dataset_generation="generation-selection",
            normalization_version=1,
            updated_at_utc="2026-09-20T10:00:00+00:00",
        )

        def seed_progress(connection: sqlite3.Connection) -> None:
            connection.execute(
                """UPDATE progress
                   SET state = 'review', seen_count = 3, verified_correct_count = 2,
                       mastery = 0.75, box = 2,
                       first_seen_at_utc = '2026-09-20T10:00:00+00:00',
                       last_seen_at_utc = '2026-09-22T18:00:00+00:00'
                   WHERE profile_id = 'profile-selection'
                     AND track_id = 'track-selection' AND card_key = ?""",
                (prerequisite_card_key,),
            )
            connection.commit()

        await storage._async_writer(seed_progress)
        context = await storage.repositories.tracks.async_selection_constraints(
            profile_id="profile-selection",
            track_id="track-selection",
            pack_version_id=pack_version_id,
            learning_item_id=ITEM_B,
            card_key=card_identity(ITEM_B)[1],
        )

        assert context["selected"] is True
        assert context["prerequisite_card_keys"] == (prerequisite_card_key,)
        assert context["unlock_conditions"] == (
            {"metric": "verified_correct_count", "minimum": 2.0},
        )
        assert (
            context["prerequisite_progress"][prerequisite_card_key]["verified_correct_count"] == 2
        )
        assert context["confusable_groups"] == (
            {
                "confusable_group_id": "locklearn:confusable:test",
                "min_intro_gap_days": 2,
                "other_item_last_introduced_at_utc": "2026-09-20T10:00:00+00:00",
            },
        )
    finally:
        await storage.async_close()
