"""Application repositories over persistent LockLearn state."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Protocol


class StateRepositoryError(RuntimeError):
    """Base repository error."""


class ContentReferenceError(StateRepositoryError):
    """Raised when state points at content absent from the active generation."""


class RepositoryStorage(Protocol):
    async def _async_writer(self, operation): ...
    async def _async_reader(self, operation): ...
    async def async_validate_card_reference(
        self,
        *,
        card_key: str,
        learning_item_id: str,
        prompt_facet_id: str,
        answer_facet_id: str,
    ) -> bool: ...
    async def async_validate_pack_version_reference(self, pack_version_id: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    profile_id: str
    name: str
    preset: str
    timezone: str
    created_at_utc: str
    updated_at_utc: str
    status: str = "active"
    settings: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class TrackRecord:
    track_id: str
    profile_id: str
    name: str
    created_at_utc: str
    updated_at_utc: str
    source_language: str | None = None
    target_language: str | None = None
    status: str = "active"
    priority: int = 1
    settings: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CardReference:
    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str


class ProfilesRepository:
    """Persistence primitives for profiles; policy belongs to P2.2/P2.3."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    async def async_insert(self, profile: ProfileRecord) -> None:
        settings_json = json.dumps(
            profile.settings or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def insert(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO profiles(
                       profile_id, name, preset, timezone, status, settings_json,
                       created_at_utc, updated_at_utc
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.profile_id,
                    profile.name,
                    profile.preset,
                    profile.timezone,
                    profile.status,
                    settings_json,
                    profile.created_at_utc,
                    profile.updated_at_utc,
                ),
            )
            connection.commit()

        await self._storage._async_writer(insert)

    async def async_get(self, profile_id: str) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT profile_id, name, preset, timezone, status, settings_json,
                          created_at_utc, updated_at_utc
                   FROM profiles WHERE profile_id = ?""",
                (profile_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "profile_id",
                "name",
                "preset",
                "timezone",
                "status",
                "settings_json",
                "created_at_utc",
                "updated_at_utc",
            )
            result = dict(zip(keys, row, strict=True))
            result["settings"] = json.loads(result.pop("settings_json"))
            return result

        return await self._storage._async_reader(read)


class TracksRepository:
    """Persistence primitives for tracks and explicit PackVersion pinning."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    async def async_insert(self, track: TrackRecord) -> None:
        settings_json = json.dumps(
            track.settings or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def insert(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO tracks(
                       track_id, profile_id, name, source_language, target_language,
                       status, priority, settings_json, created_at_utc, updated_at_utc
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    track.track_id,
                    track.profile_id,
                    track.name,
                    track.source_language,
                    track.target_language,
                    track.status,
                    track.priority,
                    settings_json,
                    track.created_at_utc,
                    track.updated_at_utc,
                ),
            )
            connection.commit()

        await self._storage._async_writer(insert)

    async def async_pin_pack_version(
        self,
        *,
        track_id: str,
        pack_version_id: str,
        dataset_generation: str,
        integrated_at_utc: str,
    ) -> None:
        if not await self._storage.async_validate_pack_version_reference(pack_version_id):
            raise ContentReferenceError(f"unknown active pack_version_id: {pack_version_id}")

        def pin(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO track_pack_versions(
                       track_id, pack_version_id, dataset_generation, integrated_at_utc
                   ) VALUES (?, ?, ?, ?)
                   ON CONFLICT(track_id) DO UPDATE SET
                       pack_version_id = excluded.pack_version_id,
                       dataset_generation = excluded.dataset_generation,
                       integrated_at_utc = excluded.integrated_at_utc""",
                (track_id, pack_version_id, dataset_generation, integrated_at_utc),
            )
            connection.commit()

        await self._storage._async_writer(pin)


class ProgressRepository:
    """Lazy materialized card progress projection."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    async def async_get(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
    ) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT profile_id, track_id, card_key, learning_item_id,
                          prompt_facet_id, answer_facet_id, state, mastery, box,
                          seen_count, verified_correct_count, verified_wrong_count,
                          self_known_count, self_review_count, next_due_at_utc,
                          user_state, content_status, policy_version,
                          dataset_generation, normalization_version, updated_at_utc
                   FROM progress
                   WHERE profile_id = ? AND track_id = ? AND card_key = ?""",
                (profile_id, track_id, card_key),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "profile_id",
                "track_id",
                "card_key",
                "learning_item_id",
                "prompt_facet_id",
                "answer_facet_id",
                "state",
                "mastery",
                "box",
                "seen_count",
                "verified_correct_count",
                "verified_wrong_count",
                "self_known_count",
                "self_review_count",
                "next_due_at_utc",
                "user_state",
                "content_status",
                "policy_version",
                "dataset_generation",
                "normalization_version",
                "updated_at_utc",
            )
            return dict(zip(keys, row, strict=True))

        return await self._storage._async_reader(read)

    async def async_create_if_absent(
        self,
        *,
        profile_id: str,
        track_id: str,
        card: CardReference,
        dataset_generation: str,
        normalization_version: int,
        updated_at_utc: str,
    ) -> bool:
        valid = await self._storage.async_validate_card_reference(
            card_key=card.card_key,
            learning_item_id=card.learning_item_id,
            prompt_facet_id=card.prompt_facet_id,
            answer_facet_id=card.answer_facet_id,
        )
        if not valid:
            raise ContentReferenceError(f"unknown active card reference: {card.card_key}")

        def create(connection: sqlite3.Connection) -> bool:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO progress(
                       profile_id, track_id, card_key, learning_item_id,
                       prompt_facet_id, answer_facet_id, state, dataset_generation,
                       normalization_version, updated_at_utc
                   ) VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?, ?)""",
                (
                    profile_id,
                    track_id,
                    card.card_key,
                    card.learning_item_id,
                    card.prompt_facet_id,
                    card.answer_facet_id,
                    dataset_generation,
                    normalization_version,
                    updated_at_utc,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

        return await self._storage._async_writer(create)


class SettingsRepository:
    """Small JSON settings store with deterministic serialization."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    async def async_set(self, key: str, value: Any, *, updated_at_utc: str) -> None:
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

        def set_value(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO settings(key, value_json, updated_at_utc)
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                       value_json = excluded.value_json,
                       updated_at_utc = excluded.updated_at_utc""",
                (key, serialized, updated_at_utc),
            )
            connection.commit()

        await self._storage._async_writer(set_value)

    async def async_get(self, key: str) -> Any | None:
        def read(connection: sqlite3.Connection) -> Any | None:
            row = connection.execute(
                "SELECT value_json FROM settings WHERE key = ?",
                (key,),
            ).fetchone()
            return None if row is None else json.loads(str(row[0]))

        return await self._storage._async_reader(read)


@dataclass(frozen=True, slots=True)
class StateRepositories:
    """Application-facing repository bundle."""

    profiles: ProfilesRepository
    tracks: TracksRepository
    progress: ProgressRepository
    settings: SettingsRepository

    @classmethod
    def for_storage(cls, storage: RepositoryStorage) -> StateRepositories:
        return cls(
            profiles=ProfilesRepository(storage),
            tracks=TracksRepository(storage),
            progress=ProgressRepository(storage),
            settings=SettingsRepository(storage),
        )
