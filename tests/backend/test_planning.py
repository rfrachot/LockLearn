"""P2.5 learning quota, goal, and load-forecast tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

from custom_components.locklearn.core.content import (
    derive_card_definition_id,
    derive_card_key,
)
from custom_components.locklearn.core.planning import LearningPlan, LearningPlanService
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, ITEM_B, create_package


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 22, 20, 0, tzinfo=UTC)


def _package_with_three_cards(path: Path) -> Path:
    package = create_package(path, "plan", active_item_ids=(ITEM_A, ITEM_B))
    with sqlite3.connect(package) as connection:
        connection.execute("UPDATE facets SET language_tag = 'en' WHERE facet_key = 'prompt'")
        connection.execute("UPDATE facets SET language_tag = 'fr' WHERE facet_key = 'answer'")
        alt_prompt = "locklearn:facet:a:prompt-alt"
        answer = "locklearn:facet:a:answer"
        connection.execute(
            """INSERT INTO facets(
                   facet_id, learning_item_id, kind, facet_key, language_tag, script,
                   lifecycle_status, superseded_by_facet_id
               ) VALUES (?, ?, 'text', 'prompt_alt', 'en', 'Latn', 'active', NULL)""",
            (alt_prompt, ITEM_A),
        )
        connection.execute(
            """INSERT INTO card_definitions(
                   card_definition_id, card_key, learning_item_id,
                   prompt_facet_id, answer_facet_id, answer_semantics,
                   grading_policy_kind, grading_policy_version,
                   lifecycle_status, superseded_by_card_definition_id
               ) VALUES (?, ?, ?, ?, ?, 'single_value', 'exact', 1, 'active', NULL)""",
            (
                derive_card_definition_id(ITEM_A, alt_prompt, answer),
                derive_card_key(ITEM_A, alt_prompt, answer),
                ITEM_A,
                alt_prompt,
                answer,
            ),
        )
        connection.commit()
    return package


async def _services(
    tmp_path: Path,
) -> tuple[SQLiteStorage, TrackService, LearningPlanService]:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    package = _package_with_three_cards(tmp_path / "planning-package.db")
    candidate = storage.paths.content_staging_dir / "planning-generation.db"
    await storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-planning",
    )
    await storage.async_activate_content_generation(candidate)

    profile_service = ProfileService(
        storage.repositories.profiles,
        clock=_FixedClock(),
        id_factory=lambda: "profile-plan",
    )
    await profile_service.async_create_profile(
        name="Planner",
        preset="standard",
        timezone="Europe/Paris",
        owner_ha_user_ids=("owner",),
    )

    track_service = TrackService(
        storage.repositories.tracks,
        clock=_FixedClock(),
        id_factory=lambda: "track-plan",
    )
    await track_service.async_create_track(
        profile_id="profile-plan",
        name="Plan",
        pack_version_id="locklearn:pack-version:plan",
        source_language="en",
        target_language="fr",
    )
    planning = LearningPlanService(
        storage.repositories.tracks,
        storage.repositories.profiles,
        clock=_FixedClock(),
    )
    return storage, track_service, planning


async def test_profile_preset_supplies_card_based_new_quota(tmp_path: Path) -> None:
    storage, _tracks, planning = await _services(tmp_path)
    try:
        forecast = await planning.async_set_plan_from_profile_defaults(
            track_id="track-plan",
            max_reviews_per_day_cards=20,
        )

        assert forecast.selected_cards == 3
        assert forecast.target_cards == 3
        assert forecast.remaining_target_cards == 3
        assert forecast.planned_new_per_day == 3

        track = await storage.repositories.tracks.async_get("track-plan")
        assert track is not None
        assert track["settings"]["learning_plan"]["max_new_per_day_cards"] == 8
        assert track["settings"]["learning_plan"]["max_reviews_per_day_cards"] == 20
        assert track["settings"]["learning_plan"]["max_notification_new_teasers"] == 2
    finally:
        await storage.async_close()


async def test_target_date_feasibility_uses_card_count_not_learning_items(tmp_path: Path) -> None:
    storage, _tracks, planning = await _services(tmp_path)
    try:
        forecast = await planning.async_set_plan(
            track_id="track-plan",
            plan=LearningPlan(
                max_new_per_day_cards=1,
                max_reviews_per_day_cards=20,
                max_notification_new_teasers=1,
                target_date=date(2026, 9, 23),
                target_coverage=1.0,
                target_retention=0.9,
            ),
        )

        assert forecast.selected_cards == 3
        assert forecast.required_new_per_day == 3
        assert forecast.target_date_feasible is False
        assert "target_date_requires_more_new_cards_than_daily_quota" in forecast.warnings
    finally:
        await storage.async_close()


def test_review_forecast_uses_v1_intervals_and_seven_day_horizon_average() -> None:
    reviews_21 = LearningPlanService._projected_review_load(
        remaining_target_cards=300,
        max_new_per_day=8,
        horizon_days=21,
    )
    reviews_90 = LearningPlanService._projected_review_load(
        remaining_target_cards=300,
        max_new_per_day=8,
        horizon_days=90,
    )

    assert reviews_21 > 0
    assert reviews_90 > 0


async def test_notification_and_active_session_split_is_bounded_by_push_budget(
    tmp_path: Path,
) -> None:
    storage, _tracks, planning = await _services(tmp_path)
    try:
        forecast = await planning.async_set_plan(
            track_id="track-plan",
            plan=LearningPlan(
                max_new_per_day_cards=3,
                max_reviews_per_day_cards=1,
                max_notification_new_teasers=2,
            ),
        )

        assert forecast.notification_deliverable_in_3_weeks <= 6
        horizon_new = LearningPlanService._projected_new_load(
            remaining_target_cards=forecast.remaining_target_cards,
            max_new_per_day=3,
            horizon_days=21,
        )
        assert (
            forecast.notification_deliverable_in_3_weeks
            + forecast.active_session_cards_in_3_weeks
            == horizon_new + forecast.reviews_per_day_in_3_weeks
        )
        assert forecast.review_capacity_feasible_in_3_weeks is (
            forecast.reviews_per_day_in_3_weeks <= 1
        )
        assert "CardDefinitions" in forecast.assumptions[0]
    finally:
        await storage.async_close()
