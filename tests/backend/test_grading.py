"""P3.7 free-text grading and recoverable content-report tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from custom_components.locklearn.core.content import GradingOutcome, GradingPolicyKind
from custom_components.locklearn.core.content_reports import ContentReportService
from custom_components.locklearn.core.grading import FreeTextGrader, GradingError
from custom_components.locklearn.core.localization import (
    CaseMode,
    NormalizationPolicy,
    PunctuationMode,
    UnicodeNormalization,
    WhitespaceMode,
)
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.storage import CardReference, SQLiteStorage, StoragePaths
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 22, 22, 0, tzinfo=UTC)


def _latin_policy(*, version: int = 3) -> NormalizationPolicy:
    return NormalizationPolicy(
        policy_id="latin_panel",
        normalization_version=version,
        unicode_normalization=UnicodeNormalization.NFC,
        case_mode=CaseMode.CASEFOLD,
        whitespace_mode=WhitespaceMode.COLLAPSE,
        punctuation_mode=PunctuationMode.PRESERVE,
        allowed_scripts=("Latn",),
    )


def test_exact_and_any_of_are_explicit_membership_policies() -> None:
    grader = FreeTextGrader()
    policy = _latin_policy()

    exact = grader.grade(
        "Hello",
        accepted_answers=("Hello",),
        grading_policy_kind=GradingPolicyKind.EXACT,
        grading_policy_version=2,
        normalization_policy=policy,
        script="Latn",
    )
    any_of = grader.grade(
        "Hi",
        accepted_answers=("Hello", "Hi"),
        grading_policy_kind=GradingPolicyKind.ANY_OF,
        grading_policy_version=4,
        normalization_policy=policy,
        script="Latn",
    )

    assert exact.outcome is GradingOutcome.CORRECT
    assert exact.grading_policy_version == 2
    assert exact.normalization_version == 3
    assert any_of.outcome is GradingOutcome.CORRECT
    assert any_of.matched_answer == "Hi"


def test_fuzzy_normalized_is_script_gated_versioned_and_conservative() -> None:
    grader = FreeTextGrader()
    policy = _latin_policy(version=7)

    normalized = grader.grade(
        "  HELLO ",
        accepted_answers=("hello",),
        grading_policy_kind=GradingPolicyKind.FUZZY_NORMALIZED,
        grading_policy_version=1,
        normalization_policy=policy,
        script="Latn",
    )
    typo = grader.grade(
        "hellp",
        accepted_answers=("hello",),
        grading_policy_kind=GradingPolicyKind.FUZZY_NORMALIZED,
        grading_policy_version=1,
        normalization_policy=policy,
        script="Latn",
    )
    semantic_accent = grader.grade(
        "cafe",
        accepted_answers=("café",),
        grading_policy_kind=GradingPolicyKind.FUZZY_NORMALIZED,
        grading_policy_version=1,
        normalization_policy=policy,
        script="Latn",
    )

    assert normalized.outcome is GradingOutcome.CORRECT
    assert normalized.normalized_submission == "hello"
    assert normalized.normalization_version == 7
    assert typo.outcome is GradingOutcome.CORRECT
    assert typo.reason == "fuzzy_single_edit_match"
    assert semantic_accent.outcome is GradingOutcome.WRONG

    with pytest.raises(Exception, match="not allowed"):
        grader.grade(
            "かな",
            accepted_answers=("カナ",),
            grading_policy_kind=GradingPolicyKind.FUZZY_NORMALIZED,
            grading_policy_version=1,
            normalization_policy=policy,
            script="Kana",
        )


def test_disputed_wrong_answer_becomes_unrecognized_not_srs_failure() -> None:
    grader = FreeTextGrader()
    grade = grader.grade(
        "colour",
        accepted_answers=("color",),
        grading_policy_kind=GradingPolicyKind.EXACT,
        grading_policy_version=1,
        normalization_policy=_latin_policy(version=5),
        script="Latn",
    )
    recovered = grader.mark_should_be_accepted(grade)

    assert grade.outcome is GradingOutcome.WRONG
    assert grade.is_definitive_failure is True
    assert recovered.outcome is GradingOutcome.UNRECOGNIZED
    assert recovered.is_definitive_failure is False
    assert recovered.reportable is True
    assert recovered.normalization_version == 5

    with pytest.raises(GradingError, match="correct answer"):
        grader.mark_should_be_accepted(
            grader.grade(
                "color",
                accepted_answers=("color",),
                grading_policy_kind=GradingPolicyKind.EXACT,
                grading_policy_version=1,
                normalization_policy=_latin_policy(),
                script="Latn",
            )
        )


async def test_content_report_is_private_audit_feedback_without_progress_mutation(
    tmp_path: Path,
) -> None:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    try:
        package = create_package(
            tmp_path / "grading-package.db",
            "grading",
            active_item_ids=(ITEM_A,),
        )
        candidate = storage.paths.content_staging_dir / "generation-grading.db"
        await storage.async_build_content_generation(
            (package,),
            candidate,
            generation_id="generation-grading",
        )
        await storage.async_activate_content_generation(candidate)

        clock = _FixedClock()
        profiles = ProfileService(
            storage.repositories.profiles,
            clock=clock,
            id_factory=lambda: "profile-grading",
        )
        await profiles.async_create_profile(
            name="Grading",
            preset="standard",
            timezone="Europe/Paris",
            owner_ha_user_ids=("owner",),
        )
        tracks = TrackService(
            storage.repositories.tracks,
            clock=clock,
            id_factory=lambda: "track-grading",
        )
        card_key = card_identity(ITEM_A)[1]
        await tracks.async_create_track(
            profile_id="profile-grading",
            name="Grading Track",
            pack_version_id="locklearn:pack-version:grading",
            source_language="en",
            target_language="fr",
            explicit_card_keys=(card_key,),
        )

        grader = FreeTextGrader()
        wrong = grader.grade(
            "colour",
            accepted_answers=("color",),
            grading_policy_kind=GradingPolicyKind.EXACT,
            grading_policy_version=1,
            normalization_policy=_latin_policy(version=9),
            script="Latn",
        )
        unrecognized = grader.mark_should_be_accepted(wrong)
        prompt_id, answer_id = facet_ids(ITEM_A)
        service = ContentReportService(
            storage.repositories.content_reports,
            storage.repositories.tracks,
            clock=clock,
        )
        receipt = await service.async_report_should_be_accepted(
            actor_user_id="owner",
            profile_id="profile-grading",
            track_id="track-grading",
            card=CardReference(
                card_key=card_key,
                learning_item_id=ITEM_A,
                prompt_facet_id=prompt_id,
                answer_facet_id=answer_id,
            ),
            grade=unrecognized,
            dataset_generation="generation-grading",
        )

        report = await storage.repositories.content_reports.async_get(receipt.report_id)
        assert report is not None
        assert receipt.grading_result == "unrecognized"
        assert receipt.srs_penalized is False
        assert report["profile_id"] == "profile-grading"
        assert report["payload"]["submitted_text"] == "colour"
        assert report["payload"]["normalization_version"] == 9
        assert report["payload"]["grading_result"] == "unrecognized"

        progress = await storage.repositories.progress.async_get(
            profile_id="profile-grading",
            track_id="track-grading",
            card_key=card_key,
        )
        assert progress is None
    finally:
        await storage.async_close()
