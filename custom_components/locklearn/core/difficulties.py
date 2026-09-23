"""P3.11 difficulties, leech remediation and private annotations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol
from uuid import uuid4

from .clock import Clock, SystemClock
from .reviews import ReviewEventService


class DifficultyServiceError(ValueError):
    """Raised when a difficulty/remediation request is invalid."""


class DifficultiesProgressRepository(Protocol):
    async def async_list_leeches(
        self, *, profile_id: str, track_id: str | None = None
    ) -> tuple[dict[str, Any], ...]: ...
    async def async_get(
        self, *, profile_id: str, track_id: str, card_key: str
    ) -> dict[str, Any] | None: ...


class DifficultiesReviewRepository(Protocol):
    async def async_confusions(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
        limit: int = 50,
    ) -> tuple[dict[str, Any], ...]: ...


class DifficultiesAnnotationRepository(Protocol):
    async def async_upsert(
        self,
        *,
        annotation_id: str,
        profile_id: str,
        learning_item_id: str | None,
        card_key: str | None,
        note: str,
        created_at_utc: str,
        updated_at_utc: str,
    ) -> dict[str, Any]: ...
    async def async_get(
        self, *, annotation_id: str, profile_id: str
    ) -> dict[str, Any] | None: ...
    async def async_list(
        self,
        *,
        profile_id: str,
        learning_item_id: str | None = None,
        card_key: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...
    async def async_delete(self, *, annotation_id: str, profile_id: str) -> bool: ...


class DifficultyService:
    """Expose leeches/confusions and prioritize personal mnemonic remediation."""

    def __init__(
        self,
        progress: DifficultiesProgressRepository,
        review_events: DifficultiesReviewRepository,
        annotations: DifficultiesAnnotationRepository,
        reviews: ReviewEventService,
        *,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._progress = progress
        self._review_events = review_events
        self._annotations = annotations
        self._reviews = reviews
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))

    async def async_list(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Return explainable leeches with confusion and mnemonic context."""
        leeches = await self._progress.async_list_leeches(
            profile_id=profile_id,
            track_id=track_id,
        )
        result: list[dict[str, Any]] = []
        for leech in leeches:
            card_key = str(leech["card_key"])
            learning_item_id = str(leech["learning_item_id"])
            annotations = await self._annotations.async_list(
                profile_id=profile_id,
                card_key=card_key,
            )
            if not annotations:
                annotations = await self._annotations.async_list(
                    profile_id=profile_id,
                    learning_item_id=learning_item_id,
                )
            confusions = await self._review_events.async_confusions(
                profile_id=profile_id,
                track_id=str(leech["track_id"]),
                card_key=card_key,
                limit=10,
            )
            item = dict(leech)
            item.update(
                {
                    "confusions": list(confusions),
                    "annotations": list(annotations),
                    "recommended_remediation": (
                        "create_personal_mnemonic" if not annotations else "edit_personal_mnemonic"
                    ),
                }
            )
            result.append(item)
        return tuple(result)

    async def async_list_confusions(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
        limit: int = 50,
    ) -> tuple[dict[str, Any], ...]:
        """Return the profile-private confusion matrix derived from ReviewEvents."""
        return await self._review_events.async_confusions(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
            limit=limit,
        )

    async def async_create_annotation(
        self,
        *,
        profile_id: str,
        note: str,
        learning_item_id: str | None = None,
        card_key: str | None = None,
    ) -> dict[str, Any]:
        """Create one private exportable note/mnemonic."""
        if (learning_item_id is None) == (card_key is None):
            raise DifficultyServiceError("annotation must target exactly one item or card")
        if not note.strip():
            raise DifficultyServiceError("annotation note must not be empty")
        now = self._clock.now().isoformat()
        return await self._annotations.async_upsert(
            annotation_id=self._id_factory(),
            profile_id=profile_id,
            learning_item_id=learning_item_id,
            card_key=card_key,
            note=note,
            created_at_utc=now,
            updated_at_utc=now,
        )

    async def async_update_annotation(
        self,
        *,
        profile_id: str,
        annotation_id: str,
        note: str,
    ) -> dict[str, Any]:
        """Update note text without changing its target identity."""
        if not note.strip():
            raise DifficultyServiceError("annotation note must not be empty")
        existing = await self._annotations.async_get(
            annotation_id=annotation_id,
            profile_id=profile_id,
        )
        if existing is None:
            raise DifficultyServiceError("annotation not found")
        return await self._annotations.async_upsert(
            annotation_id=annotation_id,
            profile_id=profile_id,
            learning_item_id=(
                None
                if existing["learning_item_id"] is None
                else str(existing["learning_item_id"])
            ),
            card_key=None if existing["card_key"] is None else str(existing["card_key"]),
            note=note,
            created_at_utc=str(existing["created_at_utc"]),
            updated_at_utc=self._clock.now().isoformat(),
        )

    async def async_delete_annotation(
        self,
        *,
        profile_id: str,
        annotation_id: str,
    ) -> None:
        """Delete one private annotation."""
        if not await self._annotations.async_delete(
            annotation_id=annotation_id,
            profile_id=profile_id,
        ):
            raise DifficultyServiceError("annotation not found")

    async def async_list_annotations(
        self,
        *,
        profile_id: str,
        learning_item_id: str | None = None,
        card_key: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """List annotations for export/dashboard use."""
        return await self._annotations.async_list(
            profile_id=profile_id,
            learning_item_id=learning_item_id,
            card_key=card_key,
        )

    async def async_reactivate_leech(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
    ) -> dict[str, Any]:
        """Move a leech back to review through a canonical non-retrieval event."""
        pre = await self._progress.async_get(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
        )
        if pre is None:
            raise DifficultyServiceError("card progress not found")
        if str(pre["state"]) != "leech":
            raise DifficultyServiceError("card is not a leech")
        for field in (
            "learning_item_id",
            "prompt_facet_id",
            "answer_facet_id",
            "dataset_generation",
        ):
            if pre.get(field) is None:
                raise DifficultyServiceError("leech progress identity is incomplete")

        post = dict(pre)
        post.update(
            {
                "state": "review",
                "updated_at_utc": self._clock.now().isoformat(),
            }
        )
        event = await self._reviews.async_record(
            profile_id=profile_id,
            track_id=track_id,
            learning_item_id=str(pre["learning_item_id"]),
            prompt_facet_id=str(pre["prompt_facet_id"]),
            answer_facet_id=str(pre["answer_facet_id"]),
            card_key=card_key,
            mode="leech_reactivation",
            question_type="manual",
            result="reactivated",
            signal_quality="none",
            policy_version=int(pre["policy_version"]),
            dataset_generation=str(pre["dataset_generation"]),
            normalization_version=(
                None
                if pre["normalization_version"] is None
                else int(pre["normalization_version"])
            ),
            pre_state_snapshot=pre,
            post_state_snapshot=post,
            retrieval_occurred=False,
        )
        return dict(event.post_state_snapshot)
