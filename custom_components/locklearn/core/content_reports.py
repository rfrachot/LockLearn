"""P3.7 recoverable content-quality feedback service."""

from __future__ import annotations

from dataclasses import dataclass

from ..storage.repositories import (
    CardReference,
    ContentReportsRepository,
    StateRepositoryError,
    TracksRepository,
)
from .clock import Clock, SystemClock
from .content import GradingOutcome
from .grading import FreeTextGradingResult


class ContentReportError(ValueError):
    """Raised when a content-quality report is invalid."""


@dataclass(frozen=True, slots=True)
class ContentReportReceipt:
    """Stable receipt returned after persisting content feedback."""

    report_id: int
    grading_result: str = GradingOutcome.UNRECOGNIZED.value
    srs_penalized: bool = False


class ContentReportService:
    """Persist user-claimed valid answers without creating false SRS failures."""

    def __init__(
        self,
        reports: ContentReportsRepository,
        tracks: TracksRepository,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._reports = reports
        self._tracks = tracks
        self._clock = clock or SystemClock()

    async def async_report_should_be_accepted(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str,
        card: CardReference,
        grade: FreeTextGradingResult,
        dataset_generation: str,
    ) -> ContentReportReceipt:
        """Persist one unrecognized-answer report after track/card validation."""
        if grade.outcome is not GradingOutcome.UNRECOGNIZED or not grade.reportable:
            raise ContentReportError("content report requires a reportable unrecognized grade")
        if not dataset_generation.strip():
            raise ContentReportError("dataset_generation must not be empty")

        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise ContentReportError("track does not belong to profile")

        try:
            report_id = await self._reports.async_create_unrecognized_answer_report(
                actor_user_id=actor_user_id,
                profile_id=profile_id,
                track_id=track_id,
                card=card,
                submitted_text=grade.submitted_text,
                normalized_submission=grade.normalized_submission,
                grading_policy_kind=grade.grading_policy_kind.value,
                grading_policy_version=grade.grading_policy_version,
                normalization_version=grade.normalization_version,
                dataset_generation=dataset_generation,
                created_at_utc=self._clock.now().isoformat(),
            )
        except StateRepositoryError as err:
            raise ContentReportError(str(err)) from err
        return ContentReportReceipt(report_id=report_id)

    async def async_report_question(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str,
        card: CardReference,
        dataset_generation: str,
        reason: str = "user_reported_question",
        message: str | None = None,
    ) -> ContentReportReceipt:
        """Persist generic question-quality feedback without touching SRS."""
        if not dataset_generation.strip():
            raise ContentReportError("dataset_generation must not be empty")
        if not reason.strip():
            raise ContentReportError("reason must not be empty")
        if message is not None and len(message) > 1000:
            raise ContentReportError("report message is too long")

        track = await self._tracks.async_get(track_id)
        if track is None or str(track["profile_id"]) != profile_id:
            raise ContentReportError("track does not belong to profile")
        try:
            report_id = await self._reports.async_create_question_report(
                actor_user_id=actor_user_id,
                profile_id=profile_id,
                track_id=track_id,
                card=card,
                dataset_generation=dataset_generation,
                reason=reason,
                message=message,
                created_at_utc=self._clock.now().isoformat(),
            )
        except StateRepositoryError as err:
            raise ContentReportError(str(err)) from err
        return ContentReportReceipt(report_id=report_id, grading_result="not_applicable")
