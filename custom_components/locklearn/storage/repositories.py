"""Application repositories over persistent LockLearn state."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class StateRepositoryError(RuntimeError):
    """Base repository error."""


class ContentReferenceError(StateRepositoryError):
    """Raised when state points at content absent from the active generation."""


class RepositoryStorage(Protocol):
    async def _async_writer(self, operation: Callable[[sqlite3.Connection], T]) -> T: ...
    async def _async_reader(self, operation: Callable[[sqlite3.Connection], T]) -> T: ...
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
class ProfileMemberRecord:
    profile_id: str
    ha_user_id: str
    role: str
    created_at_utc: str


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


def _profile_dict(row: tuple[Any, ...], *, role: str | None = None) -> dict[str, Any]:
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
    if role is not None:
        result["role"] = role
    return result


class ProfilesRepository:
    """Persistence primitives for profiles; ACL policy belongs to P2.3."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    @staticmethod
    def _serialized_settings(profile: ProfileRecord) -> str:
        return json.dumps(
            profile.settings or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    @classmethod
    def _insert_profile(cls, connection: sqlite3.Connection, profile: ProfileRecord) -> None:
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
                cls._serialized_settings(profile),
                profile.created_at_utc,
                profile.updated_at_utc,
            ),
        )

    async def async_insert(self, profile: ProfileRecord) -> None:
        def insert(connection: sqlite3.Connection) -> None:
            self._insert_profile(connection, profile)
            connection.commit()

        await self._storage._async_writer(insert)

    async def async_insert_with_members(
        self,
        profile: ProfileRecord,
        members: Iterable[ProfileMemberRecord],
    ) -> None:
        materialized_members = tuple(members)
        if any(member.profile_id != profile.profile_id for member in materialized_members):
            raise ValueError("profile member belongs to another profile")

        def insert(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_profile(connection, profile)
                connection.executemany(
                    """INSERT INTO profile_members(
                           profile_id, ha_user_id, role, created_at_utc
                       ) VALUES (?, ?, ?, ?)""",
                    (
                        (
                            member.profile_id,
                            member.ha_user_id,
                            member.role,
                            member.created_at_utc,
                        )
                        for member in materialized_members
                    ),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(insert)

    async def async_get(self, profile_id: str) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT profile_id, name, preset, timezone, status, settings_json,
                          created_at_utc, updated_at_utc
                   FROM profiles WHERE profile_id = ?""",
                (profile_id,),
            ).fetchone()
            return None if row is None else _profile_dict(row)

        return await self._storage._async_reader(read)

    async def async_list_for_ha_user(self, ha_user_id: str) -> tuple[dict[str, Any], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT p.profile_id, p.name, p.preset, p.timezone, p.status,
                          p.settings_json, p.created_at_utc, p.updated_at_utc, m.role
                   FROM profile_members AS m
                   JOIN profiles AS p ON p.profile_id = m.profile_id
                   WHERE m.ha_user_id = ?
                   ORDER BY p.name COLLATE NOCASE, p.profile_id""",
                (ha_user_id,),
            ).fetchall()
            return tuple(_profile_dict(row[:-1], role=str(row[-1])) for row in rows)

        return await self._storage._async_reader(read)

    async def async_list_members(self, profile_id: str) -> tuple[dict[str, str], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, str], ...]:
            rows = connection.execute(
                """SELECT ha_user_id, role, created_at_utc
                   FROM profile_members
                   WHERE profile_id = ?
                   ORDER BY ha_user_id""",
                (profile_id,),
            ).fetchall()
            return tuple(
                {
                    "ha_user_id": str(row[0]),
                    "role": str(row[1]),
                    "created_at_utc": str(row[2]),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_get_role(self, profile_id: str, ha_user_id: str) -> str | None:
        def read(connection: sqlite3.Connection) -> str | None:
            row = connection.execute(
                """SELECT role
                   FROM profile_members
                   WHERE profile_id = ? AND ha_user_id = ?""",
                (profile_id, ha_user_id),
            ).fetchone()
            return None if row is None else str(row[0])

        return await self._storage._async_reader(read)

    async def async_get_visible(self, profile_id: str, ha_user_id: str) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT p.profile_id, p.name, p.preset, p.timezone, p.status,
                          p.settings_json, p.created_at_utc, p.updated_at_utc, m.role
                   FROM profile_members AS m
                   JOIN profiles AS p ON p.profile_id = m.profile_id
                   WHERE p.profile_id = ? AND m.ha_user_id = ?""",
                (profile_id, ha_user_id),
            ).fetchone()
            if row is None:
                return None
            return _profile_dict(row[:-1], role=str(row[-1]))

        return await self._storage._async_reader(read)

    async def async_set_member_role_preserving_owner(self, member: ProfileMemberRecord) -> bool:
        """Upsert a member and atomically refuse demotion of the final owner."""

        def write(connection: sqlite3.Connection) -> bool:
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = connection.execute(
                    """SELECT role FROM profile_members
                       WHERE profile_id = ? AND ha_user_id = ?""",
                    (member.profile_id, member.ha_user_id),
                ).fetchone()
                if current is not None and str(current[0]) == "owner" and member.role != "owner":
                    owner_row = connection.execute(
                        """SELECT COUNT(*) FROM profile_members
                           WHERE profile_id = ? AND role = 'owner'""",
                        (member.profile_id,),
                    ).fetchone()
                    owner_count = 0 if owner_row is None else int(owner_row[0])
                    if owner_count <= 1:
                        connection.rollback()
                        return False
                connection.execute(
                    """INSERT INTO profile_members(profile_id, ha_user_id, role, created_at_utc)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(profile_id, ha_user_id) DO UPDATE SET
                           role = excluded.role""",
                    (
                        member.profile_id,
                        member.ha_user_id,
                        member.role,
                        member.created_at_utc,
                    ),
                )
                connection.commit()
                return True
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

    async def async_delete_member_preserving_owner(self, profile_id: str, ha_user_id: str) -> str:
        """Delete a member atomically, returning deleted/missing/last_owner."""

        def write(connection: sqlite3.Connection) -> str:
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = connection.execute(
                    """SELECT role FROM profile_members
                       WHERE profile_id = ? AND ha_user_id = ?""",
                    (profile_id, ha_user_id),
                ).fetchone()
                if current is None:
                    connection.rollback()
                    return "missing"
                if str(current[0]) == "owner":
                    owner_row = connection.execute(
                        """SELECT COUNT(*) FROM profile_members
                           WHERE profile_id = ? AND role = 'owner'""",
                        (profile_id,),
                    ).fetchone()
                    owner_count = 0 if owner_row is None else int(owner_row[0])
                    if owner_count <= 1:
                        connection.rollback()
                        return "last_owner"
                connection.execute(
                    "DELETE FROM profile_members WHERE profile_id = ? AND ha_user_id = ?",
                    (profile_id, ha_user_id),
                )
                connection.commit()
                return "deleted"
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)


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
