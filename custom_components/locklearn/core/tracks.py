"""Track configuration, explicit pack pinning, and card selection."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
from uuid import uuid4

from ..storage.repositories import (
    ContentReferenceError,
    TrackCardRuleRecord,
    TrackRecord,
    TracksRepository,
)
from .clock import Clock, SystemClock
from .packs import PackVersionDiff


class TrackValidationError(ValueError):
    """Raised when a Track configuration is invalid."""


class TrackService:
    """Configure Tracks without making direction part of card identity."""

    def __init__(
        self,
        repository: TracksRepository,
        *,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or SystemClock()
        self._id_factory = id_factory or (lambda: str(uuid4()))

    @staticmethod
    def _validate_weights(weights: Mapping[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for raw_type, raw_weight in weights.items():
            content_type = raw_type.strip()
            weight = float(raw_weight)
            if not content_type:
                raise TrackValidationError("content type must not be empty")
            if weight < 0:
                raise TrackValidationError("content weights must be non-negative")
            normalized[content_type] = weight
        if normalized and not any(weight > 0 for weight in normalized.values()):
            raise TrackValidationError("at least one content weight must be positive")
        return normalized

    @staticmethod
    def _rules_from_cards(
        track_id: str,
        cards: tuple[dict[str, str], ...],
        *,
        rule_kind: str,
    ) -> tuple[TrackCardRuleRecord, ...]:
        return tuple(
            TrackCardRuleRecord(
                track_id=track_id,
                rule_id=f"card:{card['card_key']}",
                rule_kind=rule_kind,
                card_key=card["card_key"],
                prompt_facet_id=card["prompt_facet_id"],
                answer_facet_id=card["answer_facet_id"],
                enabled=True,
            )
            for card in cards
        )

    async def async_create_track(
        self,
        *,
        profile_id: str,
        name: str,
        pack_version_id: str,
        source_language: str,
        target_language: str,
        priority: int = 1,
        content_weights: Mapping[str, float] | None = None,
        explicit_card_keys: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """Create one Track with an explicit immutable PackVersion pin."""
        normalized_name = name.strip()
        if not normalized_name:
            raise TrackValidationError("track name must not be empty")
        source = source_language.strip()
        target = target_language.strip()
        if not source or not target:
            raise TrackValidationError("source and target languages are required")
        if source == target:
            raise TrackValidationError("source and target languages must differ")
        if priority < 1:
            raise TrackValidationError("track priority must be >= 1")

        pack = await self._repository.async_pack_version_info(pack_version_id)
        if pack is None:
            raise ContentReferenceError(f"unknown active pack_version_id: {pack_version_id}")

        track_id = self._id_factory()
        if explicit_card_keys is None:
            cards = await self._repository.async_resolve_direction_cards(
                pack_version_id=pack_version_id,
                source_language=source,
                target_language=target,
            )
            selection_mode = "direction"
            rule_kind = "direction_card"
        else:
            requested = tuple(dict.fromkeys(explicit_card_keys))
            cards = await self._repository.async_cards_in_pack(
                pack_version_id=pack_version_id,
                card_keys=requested,
            )
            found = {card["card_key"] for card in cards}
            missing = tuple(card_key for card_key in requested if card_key not in found)
            if missing:
                raise TrackValidationError(
                    f"explicit cards are not active in pinned pack: {missing!r}"
                )
            selection_mode = "explicit"
            rule_kind = "explicit_card"

        if not cards:
            raise TrackValidationError("track selection resolves to no active cards")

        weights = (
            self._validate_weights(content_weights)
            if content_weights is not None
            else {content_type: 1.0 for content_type in sorted({c["content_type"] for c in cards})}
        )
        rules = self._rules_from_cards(track_id, cards, rule_kind=rule_kind)
        now = self._clock.now().isoformat()
        track = TrackRecord(
            track_id=track_id,
            profile_id=profile_id,
            name=normalized_name,
            source_language=source,
            target_language=target,
            priority=priority,
            settings={"card_selection_mode": selection_mode},
            created_at_utc=now,
            updated_at_utc=now,
        )
        await self._repository.async_insert_configured(
            track=track,
            pack_version_id=pack_version_id,
            dataset_generation=pack["generation_id"],
            integrated_at_utc=now,
            rules=rules,
            weights=weights,
        )
        created = await self._repository.async_get(track_id)
        if created is None:
            raise RuntimeError("created track could not be reloaded")
        return created

    async def async_update_track(
        self,
        *,
        track_id: str,
        name: str | None = None,
        source_language: str | None = None,
        target_language: str | None = None,
        status: str | None = None,
        priority: int | None = None,
        content_weights: Mapping[str, float] | None = None,
        explicit_card_keys: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """Atomically update mutable Track configuration."""
        current = await self._repository.async_get(track_id)
        if current is None:
            raise TrackValidationError("track does not exist")
        next_name = str(current["name"]) if name is None else name.strip()
        if not next_name:
            raise TrackValidationError("track name must not be empty")
        next_source = (
            ""
            if current["source_language"] is None
            else str(current["source_language"])
        ) if source_language is None else source_language.strip()
        next_target = (
            ""
            if current["target_language"] is None
            else str(current["target_language"])
        ) if target_language is None else target_language.strip()
        if not next_source or not next_target:
            raise TrackValidationError("source and target languages are required")
        if next_source == next_target:
            raise TrackValidationError("source and target languages must differ")
        next_status = str(current["status"]) if status is None else status
        if next_status not in {"active", "paused", "archived"}:
            raise TrackValidationError("invalid track status")
        next_priority = int(current["priority"]) if priority is None else priority
        if next_priority < 1:
            raise TrackValidationError("track priority must be >= 1")

        pack_version_id = current.get("pack_version_id")
        if not isinstance(pack_version_id, str):
            raise TrackValidationError("track has no pinned pack version")
        settings = dict(current["settings"])
        current_mode = str(settings.get("card_selection_mode", "direction"))
        if explicit_card_keys is not None:
            requested = tuple(dict.fromkeys(explicit_card_keys))
            cards = await self._repository.async_cards_in_pack(
                pack_version_id=pack_version_id,
                card_keys=requested,
            )
            found = {card["card_key"] for card in cards}
            missing = tuple(card_key for card_key in requested if card_key not in found)
            if missing:
                raise TrackValidationError(
                    f"explicit cards are not active in pinned pack: {missing!r}"
                )
            mode = "explicit"
            rule_kind = "explicit_card"
        elif current_mode == "direction":
            cards = await self._repository.async_resolve_direction_cards(
                pack_version_id=pack_version_id,
                source_language=next_source,
                target_language=next_target,
            )
            mode = "direction"
            rule_kind = "direction_card"
        else:
            existing = await self._repository.async_get_card_rules(track_id)
            keys = tuple(
                str(rule["card_key"])
                for rule in existing
                if rule["card_key"] is not None and bool(rule["enabled"])
            )
            cards = await self._repository.async_cards_in_pack(
                pack_version_id=pack_version_id,
                card_keys=keys,
            )
            mode = "explicit"
            rule_kind = "explicit_card"

        if not cards:
            raise TrackValidationError("track selection resolves to no active cards")
        rules = self._rules_from_cards(track_id, cards, rule_kind=rule_kind)
        weights = (
            await self._repository.async_get_content_weights(track_id)
            if content_weights is None
            else self._validate_weights(content_weights)
        )
        settings["card_selection_mode"] = mode
        now = self._clock.now().isoformat()
        updated = await self._repository.async_update_configured(
            track=TrackRecord(
                track_id=track_id,
                profile_id=str(current["profile_id"]),
                name=next_name,
                source_language=next_source,
                target_language=next_target,
                status=next_status,
                priority=next_priority,
                settings=settings,
                created_at_utc=str(current["created_at_utc"]),
                updated_at_utc=now,
            ),
            rules=rules,
            weights=weights,
        )
        if not updated:
            raise TrackValidationError("track does not exist")
        result = await self._repository.async_get(track_id)
        if result is None:
            raise RuntimeError("updated track could not be reloaded")
        return result

    async def async_delete_track(self, track_id: str) -> bool:
        """Delete one Track and its Track-scoped user state."""
        return await self._repository.async_delete(track_id)

    async def async_preview_pack_update(
        self,
        *,
        track_id: str,
        target_pack_version_id: str,
    ) -> PackVersionDiff:
        """Return the deterministic curriculum diff before explicit integration."""
        track = await self._repository.async_get(track_id)
        if track is None:
            raise TrackValidationError("track does not exist")
        current_id = track.get("pack_version_id")
        if not isinstance(current_id, str):
            raise TrackValidationError("track has no pinned pack version")
        if current_id == target_pack_version_id:
            raise TrackValidationError("target pack version is already integrated")

        current = await self._repository.async_pack_version_info(current_id)
        target = await self._repository.async_pack_version_info(target_pack_version_id)
        if current is None or target is None:
            raise ContentReferenceError("pack update references inactive content")
        if current["pack_id"] != target["pack_id"]:
            raise TrackValidationError("pack update must stay within the same Pack")

        before = await self._repository.async_pack_item_signatures(current_id)
        after = await self._repository.async_pack_item_signatures(target_pack_version_id)
        before_ids = set(before)
        after_ids = set(after)
        common = before_ids & after_ids
        return PackVersionDiff(
            from_pack_version_id=current_id,
            to_pack_version_id=target_pack_version_id,
            added_learning_item_ids=tuple(sorted(after_ids - before_ids)),
            removed_learning_item_ids=tuple(sorted(before_ids - after_ids)),
            changed_learning_item_ids=tuple(
                sorted(item_id for item_id in common if before[item_id] != after[item_id])
            ),
        )

    async def async_integrate_pack_update(
        self,
        *,
        track_id: str,
        target_pack_version_id: str,
    ) -> PackVersionDiff:
        """Explicitly integrate a new PackVersion after a previewable diff."""
        diff = await self.async_preview_pack_update(
            track_id=track_id,
            target_pack_version_id=target_pack_version_id,
        )
        track = await self._repository.async_get(track_id)
        target = await self._repository.async_pack_version_info(target_pack_version_id)
        if track is None or target is None:
            raise TrackValidationError("track or target pack disappeared")

        mode = str(track["settings"].get("card_selection_mode", "direction"))
        if mode == "direction":
            cards = await self._repository.async_resolve_direction_cards(
                pack_version_id=target_pack_version_id,
                source_language=str(track["source_language"]),
                target_language=str(track["target_language"]),
            )
            rule_kind = "direction_card"
        elif mode == "explicit":
            existing_rules = await self._repository.async_get_card_rules(track_id)
            explicit_keys = tuple(
                str(rule["card_key"])
                for rule in existing_rules
                if rule["rule_kind"] == "explicit_card" and rule["card_key"] is not None
            )
            cards = await self._repository.async_cards_in_pack(
                pack_version_id=target_pack_version_id,
                card_keys=explicit_keys,
            )
            found = {card["card_key"] for card in cards}
            missing = tuple(card_key for card_key in explicit_keys if card_key not in found)
            if missing:
                raise TrackValidationError(
                    "explicit card selection must be updated before integrating "
                    f"removed cards: {missing!r}"
                )
            rule_kind = "explicit_card"
        else:
            raise TrackValidationError(f"unknown card selection mode: {mode}")

        if not cards:
            raise TrackValidationError("updated pack resolves to no active cards")
        rules = self._rules_from_cards(track_id, cards, rule_kind=rule_kind)
        now = self._clock.now().isoformat()
        await self._repository.async_integrate_pack_version(
            track_id=track_id,
            pack_version_id=target_pack_version_id,
            dataset_generation=target["generation_id"],
            integrated_at_utc=now,
            rules=rules,
        )
        return diff

    async def async_set_content_weights(
        self,
        *,
        track_id: str,
        weights: Mapping[str, float],
    ) -> None:
        """Replace relative content-volume targets for one Track."""
        if await self._repository.async_get(track_id) is None:
            raise TrackValidationError("track does not exist")
        await self._repository.async_replace_content_weights(
            track_id,
            self._validate_weights(weights),
        )
