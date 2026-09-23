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


@dataclass(frozen=True, slots=True)
class TrackCardRuleRecord:
    track_id: str
    rule_id: str
    rule_kind: str
    enabled: bool = True
    card_key: str | None = None
    prompt_facet_id: str | None = None
    answer_facet_id: str | None = None
    rule: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ReviewEventRecord:
    """Canonical immutable learning interaction audit record."""

    id: str
    profile_id: str
    track_id: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    card_key: str
    mode: str
    question_type: str
    result: str
    hint_used: bool
    retrieval_occurred: bool
    signal_quality: str
    policy_version: int
    dataset_generation: str
    pre_state_snapshot: dict[str, Any]
    post_state_snapshot: dict[str, Any]
    created_at_utc: str
    local_date: str
    timezone_name: str
    utc_offset_minutes: int
    answer_id: str | None = None
    expected_answer_id: str | None = None
    scheduled_interval_days: float | None = None
    elapsed_days: float | None = None
    grading_result: str | None = None
    normalization_version: int | None = None
    presentation_to_answer_ms: int | None = None
    delivery_to_action_ms: int | None = None
    session_id: str | None = None
    notification_id: str | None = None


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

    async def async_update(
        self,
        *,
        profile_id: str,
        name: str,
        timezone: str,
        status: str,
        settings: dict[str, Any],
        updated_at_utc: str,
    ) -> bool:
        serialized = json.dumps(
            settings,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> bool:
            cursor = connection.execute(
                """UPDATE profiles
                   SET name = ?, timezone = ?, status = ?, settings_json = ?,
                       updated_at_utc = ?
                   WHERE profile_id = ?""",
                (name, timezone, status, serialized, updated_at_utc, profile_id),
            )
            connection.commit()
            return cursor.rowcount == 1

        return await self._storage._async_writer(write)

    async def async_delete(self, profile_id: str) -> bool:
        """Delete one profile and profile-scoped private state."""

        def write(connection: sqlite3.Connection) -> bool:
            try:
                connection.execute("BEGIN IMMEDIATE")
                exists = connection.execute(
                    "SELECT 1 FROM profiles WHERE profile_id = ?",
                    (profile_id,),
                ).fetchone()
                if exists is None:
                    connection.rollback()
                    return False
                for table in (
                    "notification_interactions",
                    "scheduled_slots",
                    "stats_daily",
                    "exam_attempts",
                    "review_events",
                    "progress",
                    "sessions",
                    "audit_events",
                ):
                    connection.execute(
                        f"DELETE FROM {table} WHERE profile_id = ?",
                        (profile_id,),
                    )
                connection.execute(
                    "DELETE FROM profiles WHERE profile_id = ?",
                    (profile_id,),
                )
                connection.commit()
                return True
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

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

    async def async_insert_configured(
        self,
        *,
        track: TrackRecord,
        pack_version_id: str,
        dataset_generation: str,
        integrated_at_utc: str,
        rules: tuple[TrackCardRuleRecord, ...],
        weights: dict[str, float],
    ) -> None:
        if any(rule.track_id != track.track_id for rule in rules):
            raise ValueError("track card rule belongs to another track")
        settings_json = json.dumps(
            track.settings or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
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
                connection.execute(
                    """INSERT INTO track_pack_versions(
                           track_id, pack_version_id, dataset_generation, integrated_at_utc
                       ) VALUES (?, ?, ?, ?)""",
                    (
                        track.track_id,
                        pack_version_id,
                        dataset_generation,
                        integrated_at_utc,
                    ),
                )
                connection.executemany(
                    """INSERT INTO track_card_rules(
                           track_id, rule_id, rule_kind, card_key, prompt_facet_id,
                           answer_facet_id, rule_json, enabled
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        (
                            rule.track_id,
                            rule.rule_id,
                            rule.rule_kind,
                            rule.card_key,
                            rule.prompt_facet_id,
                            rule.answer_facet_id,
                            json.dumps(
                                rule.rule or {},
                                ensure_ascii=False,
                                separators=(",", ":"),
                                sort_keys=True,
                            ),
                            int(rule.enabled),
                        )
                        for rule in rules
                    ),
                )
                connection.executemany(
                    """INSERT INTO track_content_weights(track_id, content_type, weight)
                       VALUES (?, ?, ?)""",
                    (
                        (track.track_id, content_type, weight)
                        for content_type, weight in sorted(weights.items())
                    ),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

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

    async def async_get(self, track_id: str) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT track.track_id, track.profile_id, track.name,
                          track.source_language, track.target_language, track.status,
                          track.priority, track.settings_json, track.created_at_utc,
                          track.updated_at_utc, pin.pack_version_id,
                          pin.dataset_generation, pin.integrated_at_utc
                   FROM tracks AS track
                   LEFT JOIN track_pack_versions AS pin ON pin.track_id = track.track_id
                   WHERE track.track_id = ?""",
                (track_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "track_id",
                "profile_id",
                "name",
                "source_language",
                "target_language",
                "status",
                "priority",
                "settings_json",
                "created_at_utc",
                "updated_at_utc",
                "pack_version_id",
                "dataset_generation",
                "integrated_at_utc",
            )
            result = dict(zip(keys, row, strict=True))
            result["settings"] = json.loads(result.pop("settings_json"))
            return result

        return await self._storage._async_reader(read)

    async def async_list_for_profile(self, profile_id: str) -> tuple[dict[str, Any], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT track.track_id, track.profile_id, track.name,
                          track.source_language, track.target_language, track.status,
                          track.priority, track.settings_json, track.created_at_utc,
                          track.updated_at_utc, pin.pack_version_id,
                          pin.dataset_generation, pin.integrated_at_utc
                   FROM tracks AS track
                   LEFT JOIN track_pack_versions AS pin ON pin.track_id = track.track_id
                   WHERE track.profile_id = ?
                   ORDER BY track.name COLLATE NOCASE, track.track_id""",
                (profile_id,),
            ).fetchall()
            keys = (
                "track_id",
                "profile_id",
                "name",
                "source_language",
                "target_language",
                "status",
                "priority",
                "settings_json",
                "created_at_utc",
                "updated_at_utc",
                "pack_version_id",
                "dataset_generation",
                "integrated_at_utc",
            )
            result: list[dict[str, Any]] = []
            for row in rows:
                item = dict(zip(keys, row, strict=True))
                item["settings"] = json.loads(item.pop("settings_json"))
                result.append(item)
            return tuple(result)

        return await self._storage._async_reader(read)

    async def async_update_configured(
        self,
        *,
        track: TrackRecord,
        rules: tuple[TrackCardRuleRecord, ...],
        weights: dict[str, float],
    ) -> bool:
        """Atomically replace mutable Track configuration."""
        if any(rule.track_id != track.track_id for rule in rules):
            raise ValueError("track card rule belongs to another track")
        serialized = json.dumps(
            track.settings or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> bool:
            try:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    """UPDATE tracks
                       SET name = ?, source_language = ?, target_language = ?,
                           status = ?, priority = ?, settings_json = ?,
                           updated_at_utc = ?
                       WHERE track_id = ?""",
                    (
                        track.name,
                        track.source_language,
                        track.target_language,
                        track.status,
                        track.priority,
                        serialized,
                        track.updated_at_utc,
                        track.track_id,
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return False
                connection.execute(
                    "DELETE FROM track_card_rules WHERE track_id = ?",
                    (track.track_id,),
                )
                connection.executemany(
                    """INSERT INTO track_card_rules(
                           track_id, rule_id, rule_kind, card_key, prompt_facet_id,
                           answer_facet_id, rule_json, enabled
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        (
                            rule.track_id,
                            rule.rule_id,
                            rule.rule_kind,
                            rule.card_key,
                            rule.prompt_facet_id,
                            rule.answer_facet_id,
                            json.dumps(
                                rule.rule or {},
                                ensure_ascii=False,
                                separators=(",", ":"),
                                sort_keys=True,
                            ),
                            int(rule.enabled),
                        )
                        for rule in rules
                    ),
                )
                connection.execute(
                    "DELETE FROM track_content_weights WHERE track_id = ?",
                    (track.track_id,),
                )
                connection.executemany(
                    """INSERT INTO track_content_weights(track_id, content_type, weight)
                       VALUES (?, ?, ?)""",
                    (
                        (track.track_id, content_type, weight)
                        for content_type, weight in sorted(weights.items())
                    ),
                )
                connection.commit()
                return True
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

    async def async_update_metadata(
        self,
        *,
        track_id: str,
        name: str,
        status: str,
        priority: int,
        updated_at_utc: str,
    ) -> bool:
        def write(connection: sqlite3.Connection) -> bool:
            cursor = connection.execute(
                """UPDATE tracks
                   SET name = ?, status = ?, priority = ?, updated_at_utc = ?
                   WHERE track_id = ?""",
                (name, status, priority, updated_at_utc, track_id),
            )
            connection.commit()
            return cursor.rowcount == 1

        return await self._storage._async_writer(write)

    async def async_delete(self, track_id: str) -> bool:
        """Delete one Track and its Track-scoped private state."""

        def write(connection: sqlite3.Connection) -> bool:
            try:
                connection.execute("BEGIN IMMEDIATE")
                exists = connection.execute(
                    "SELECT 1 FROM tracks WHERE track_id = ?",
                    (track_id,),
                ).fetchone()
                if exists is None:
                    connection.rollback()
                    return False
                for table in (
                    "notification_interactions",
                    "scheduled_slots",
                    "stats_daily",
                    "exam_attempts",
                    "review_events",
                    "progress",
                    "sessions",
                ):
                    connection.execute(
                        f"DELETE FROM {table} WHERE track_id = ?",
                        (track_id,),
                    )
                connection.execute("DELETE FROM tracks WHERE track_id = ?", (track_id,))
                connection.commit()
                return True
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

    async def async_pack_version_info(self, pack_version_id: str) -> dict[str, str] | None:
        def read(connection: sqlite3.Connection) -> dict[str, str] | None:
            row = connection.execute(
                """SELECT version.pack_version_id, version.pack_id, version.version,
                          metadata.generation_id
                   FROM content.pack_versions AS version
                   JOIN content.generation_metadata AS metadata
                   WHERE version.pack_version_id = ?""",
                (pack_version_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "pack_version_id": str(row[0]),
                "pack_id": str(row[1]),
                "version": str(row[2]),
                "generation_id": str(row[3]),
            }

        return await self._storage._async_reader(read)

    async def async_resolve_direction_cards(
        self,
        *,
        pack_version_id: str,
        source_language: str,
        target_language: str,
    ) -> tuple[dict[str, str], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, str], ...]:
            rows = connection.execute(
                """SELECT card.card_key, card.learning_item_id,
                          card.prompt_facet_id, card.answer_facet_id,
                          item.content_type
                   FROM content.pack_items AS member
                   JOIN content.learning_items AS item
                     ON item.learning_item_id = member.learning_item_id
                    AND item.lifecycle_status = 'active'
                   JOIN content.card_definitions AS card
                     ON card.learning_item_id = item.learning_item_id
                    AND card.lifecycle_status = 'active'
                   JOIN content.facets AS prompt
                     ON prompt.facet_id = card.prompt_facet_id
                    AND prompt.lifecycle_status = 'active'
                   JOIN content.facets AS answer
                     ON answer.facet_id = card.answer_facet_id
                    AND answer.lifecycle_status = 'active'
                   LEFT JOIN content.pack_item_card_defaults AS default_rule
                     ON default_rule.pack_version_id = member.pack_version_id
                    AND default_rule.learning_item_id = member.learning_item_id
                    AND default_rule.card_key = card.card_key
                   WHERE member.pack_version_id = ?
                     AND prompt.language_tag = ?
                     AND answer.language_tag = ?
                     AND COALESCE(default_rule.enabled_by_default, 1) = 1
                   ORDER BY member.position, card.card_key""",
                (pack_version_id, source_language, target_language),
            ).fetchall()
            return tuple(
                {
                    "card_key": str(row[0]),
                    "learning_item_id": str(row[1]),
                    "prompt_facet_id": str(row[2]),
                    "answer_facet_id": str(row[3]),
                    "content_type": str(row[4]),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_cards_in_pack(
        self,
        *,
        pack_version_id: str,
        card_keys: tuple[str, ...],
    ) -> tuple[dict[str, str], ...]:
        if not card_keys:
            return ()
        placeholders = ",".join("?" for _ in card_keys)

        def read(connection: sqlite3.Connection) -> tuple[dict[str, str], ...]:
            rows = connection.execute(
                f"""SELECT card.card_key, card.learning_item_id,
                           card.prompt_facet_id, card.answer_facet_id,
                           item.content_type
                    FROM content.pack_items AS member
                    JOIN content.learning_items AS item
                      ON item.learning_item_id = member.learning_item_id
                     AND item.lifecycle_status = 'active'
                    JOIN content.card_definitions AS card
                      ON card.learning_item_id = item.learning_item_id
                     AND card.lifecycle_status = 'active'
                    WHERE member.pack_version_id = ?
                      AND card.card_key IN ({placeholders})
                    ORDER BY card.card_key""",
                (pack_version_id, *card_keys),
            ).fetchall()
            return tuple(
                {
                    "card_key": str(row[0]),
                    "learning_item_id": str(row[1]),
                    "prompt_facet_id": str(row[2]),
                    "answer_facet_id": str(row[3]),
                    "content_type": str(row[4]),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_integrate_pack_version(
        self,
        *,
        track_id: str,
        pack_version_id: str,
        dataset_generation: str,
        integrated_at_utc: str,
        rules: tuple[TrackCardRuleRecord, ...],
    ) -> None:
        if any(rule.track_id != track_id for rule in rules):
            raise ValueError("track card rule belongs to another track")

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """UPDATE track_pack_versions
                       SET pack_version_id = ?, dataset_generation = ?, integrated_at_utc = ?
                       WHERE track_id = ?""",
                    (
                        pack_version_id,
                        dataset_generation,
                        integrated_at_utc,
                        track_id,
                    ),
                )
                connection.execute("DELETE FROM track_card_rules WHERE track_id = ?", (track_id,))
                connection.executemany(
                    """INSERT INTO track_card_rules(
                           track_id, rule_id, rule_kind, card_key, prompt_facet_id,
                           answer_facet_id, rule_json, enabled
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        (
                            rule.track_id,
                            rule.rule_id,
                            rule.rule_kind,
                            rule.card_key,
                            rule.prompt_facet_id,
                            rule.answer_facet_id,
                            json.dumps(
                                rule.rule or {},
                                ensure_ascii=False,
                                separators=(",", ":"),
                                sort_keys=True,
                            ),
                            int(rule.enabled),
                        )
                        for rule in rules
                    ),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

    async def async_get_card_rules(self, track_id: str) -> tuple[dict[str, Any], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT rule_id, rule_kind, card_key, prompt_facet_id,
                          answer_facet_id, rule_json, enabled
                   FROM track_card_rules
                   WHERE track_id = ?
                   ORDER BY rule_id""",
                (track_id,),
            ).fetchall()
            return tuple(
                {
                    "rule_id": str(row[0]),
                    "rule_kind": str(row[1]),
                    "card_key": None if row[2] is None else str(row[2]),
                    "prompt_facet_id": None if row[3] is None else str(row[3]),
                    "answer_facet_id": None if row[4] is None else str(row[4]),
                    "rule": json.loads(str(row[5])),
                    "enabled": bool(row[6]),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_get_content_weights(self, track_id: str) -> dict[str, float]:
        def read(connection: sqlite3.Connection) -> dict[str, float]:
            return {
                str(content_type): float(weight)
                for content_type, weight in connection.execute(
                    """SELECT content_type, weight
                       FROM track_content_weights
                       WHERE track_id = ?
                       ORDER BY content_type""",
                    (track_id,),
                ).fetchall()
            }

        return await self._storage._async_reader(read)

    async def async_planning_snapshot(
        self,
        *,
        track_id: str,
        now_utc: str,
    ) -> dict[str, int]:
        def read(connection: sqlite3.Connection) -> dict[str, int]:
            selected = connection.execute(
                """SELECT COUNT(DISTINCT card_key)
                   FROM track_card_rules
                   WHERE track_id = ? AND enabled = 1 AND card_key IS NOT NULL""",
                (track_id,),
            ).fetchone()
            introduced = connection.execute(
                """SELECT COUNT(DISTINCT progress.card_key)
                   FROM progress
                   JOIN track_card_rules AS rule
                     ON rule.track_id = progress.track_id
                    AND rule.card_key = progress.card_key
                    AND rule.enabled = 1
                   WHERE progress.track_id = ?""",
                (track_id,),
            ).fetchone()
            due = connection.execute(
                """SELECT COUNT(*)
                   FROM progress
                   JOIN track_card_rules AS rule
                     ON rule.track_id = progress.track_id
                    AND rule.card_key = progress.card_key
                    AND rule.enabled = 1
                   WHERE progress.track_id = ?
                     AND progress.state IN ('review', 'relearning')
                     AND progress.next_due_at_utc IS NOT NULL
                     AND progress.next_due_at_utc <= ?""",
                (track_id, now_utc),
            ).fetchone()
            return {
                "selected_cards": 0 if selected is None else int(selected[0]),
                "introduced_cards": 0 if introduced is None else int(introduced[0]),
                "due_now": 0 if due is None else int(due[0]),
            }

        return await self._storage._async_reader(read)

    async def async_update_settings(
        self,
        *,
        track_id: str,
        settings: dict[str, Any],
        updated_at_utc: str,
    ) -> None:
        serialized = json.dumps(
            settings,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """UPDATE tracks
                   SET settings_json = ?, updated_at_utc = ?
                   WHERE track_id = ?""",
                (serialized, updated_at_utc, track_id),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise StateRepositoryError(f"unknown track_id: {track_id}")
            connection.commit()

        await self._storage._async_writer(write)

    async def async_replace_card_rules(
        self,
        track_id: str,
        rules: tuple[TrackCardRuleRecord, ...],
    ) -> None:
        if any(rule.track_id != track_id for rule in rules):
            raise ValueError("track card rule belongs to another track")

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("DELETE FROM track_card_rules WHERE track_id = ?", (track_id,))
                connection.executemany(
                    """INSERT INTO track_card_rules(
                           track_id, rule_id, rule_kind, card_key, prompt_facet_id,
                           answer_facet_id, rule_json, enabled
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        (
                            rule.track_id,
                            rule.rule_id,
                            rule.rule_kind,
                            rule.card_key,
                            rule.prompt_facet_id,
                            rule.answer_facet_id,
                            json.dumps(
                                rule.rule or {},
                                ensure_ascii=False,
                                separators=(",", ":"),
                                sort_keys=True,
                            ),
                            int(rule.enabled),
                        )
                        for rule in rules
                    ),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

    async def async_replace_content_weights(
        self,
        track_id: str,
        weights: dict[str, float],
    ) -> None:
        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "DELETE FROM track_content_weights WHERE track_id = ?",
                    (track_id,),
                )
                connection.executemany(
                    """INSERT INTO track_content_weights(track_id, content_type, weight)
                       VALUES (?, ?, ?)""",
                    (
                        (track_id, content_type, weight)
                        for content_type, weight in sorted(weights.items())
                    ),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

    async def async_session_candidates(
        self,
        *,
        profile_id: str,
        track_id: str,
    ) -> tuple[dict[str, Any], ...]:
        """Load P3.9 session candidates from the pinned active PackVersion."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            pin = connection.execute(
                """SELECT pin.pack_version_id
                   FROM tracks AS track
                   JOIN track_pack_versions AS pin ON pin.track_id = track.track_id
                   WHERE track.track_id = ? AND track.profile_id = ?
                     AND track.status = 'active'""",
                (track_id, profile_id),
            ).fetchone()
            if pin is None:
                return ()
            pack_version_id = str(pin[0])

            rows = connection.execute(
                """SELECT rule.card_key, card.learning_item_id,
                          card.prompt_facet_id, card.answer_facet_id,
                          item.content_type,
                          COALESCE(progress.state, 'new') AS progress_state,
                          progress.next_due_at_utc, pack_item.position
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card
                     ON card.card_key = rule.card_key
                    AND card.lifecycle_status = 'active'
                   JOIN content.learning_items AS item
                     ON item.learning_item_id = card.learning_item_id
                    AND item.lifecycle_status = 'active'
                   JOIN content.pack_items AS pack_item
                     ON pack_item.pack_version_id = ?
                    AND pack_item.learning_item_id = item.learning_item_id
                   LEFT JOIN progress
                     ON progress.profile_id = ?
                    AND progress.track_id = rule.track_id
                    AND progress.card_key = rule.card_key
                   WHERE rule.track_id = ? AND rule.enabled = 1
                     AND rule.card_key IS NOT NULL
                     AND COALESCE(progress.user_state, 'active') = 'active'
                     AND COALESCE(progress.content_status, 'active') = 'active'
                   ORDER BY pack_item.position, rule.card_key""",
                (pack_version_id, profile_id, track_id),
            ).fetchall()

            confusable_by_item: dict[str, list[str]] = {}
            for learning_item_id, group_id in connection.execute(
                """SELECT member.learning_item_id, member.confusable_group_id
                   FROM content.confusable_group_items AS member
                   JOIN content.confusable_groups AS group_row
                     ON group_row.confusable_group_id = member.confusable_group_id
                   WHERE group_row.pack_version_id = ?
                   ORDER BY member.learning_item_id, member.confusable_group_id""",
                (pack_version_id,),
            ).fetchall():
                confusable_by_item.setdefault(str(learning_item_id), []).append(
                    str(group_id)
                )

            return tuple(
                {
                    "card_key": str(row[0]),
                    "learning_item_id": str(row[1]),
                    "prompt_facet_id": str(row[2]),
                    "answer_facet_id": str(row[3]),
                    "content_type": str(row[4]),
                    "state": str(row[5]),
                    "next_due_at_utc": None if row[6] is None else str(row[6]),
                    "pack_position": int(row[7]),
                    "confusable_group_ids": tuple(
                        confusable_by_item.get(str(row[1]), ())
                    ),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_selection_constraints(
        self,
        *,
        profile_id: str,
        track_id: str,
        pack_version_id: str,
        learning_item_id: str,
        card_key: str,
    ) -> dict[str, Any]:
        """Load deterministic P3.5 selection constraints for one candidate card."""

        def read(connection: sqlite3.Connection) -> dict[str, Any]:
            selected_row = connection.execute(
                """SELECT 1
                   FROM track_card_rules
                   WHERE track_id = ? AND card_key = ? AND enabled = 1
                   LIMIT 1""",
                (track_id, card_key),
            ).fetchone()
            prerequisite_rows = connection.execute(
                """SELECT prerequisite_card_key
                   FROM content.pack_item_prerequisites
                   WHERE pack_version_id = ? AND learning_item_id = ?
                   ORDER BY prerequisite_card_key""",
                (pack_version_id, learning_item_id),
            ).fetchall()
            unlock_rows = connection.execute(
                """SELECT metric, minimum
                   FROM content.pack_item_unlock_conditions
                   WHERE pack_version_id = ? AND learning_item_id = ?
                   ORDER BY position""",
                (pack_version_id, learning_item_id),
            ).fetchall()
            prerequisite_progress = {
                str(row[0]): {
                    "state": str(row[1]),
                    "mastery": float(row[2]),
                    "box": int(row[3]),
                    "verified_correct_count": int(row[4]),
                    "seen_count": int(row[5]),
                }
                for row in connection.execute(
                    """SELECT card_key, state, mastery, box, verified_correct_count, seen_count
                       FROM progress
                       WHERE profile_id = ? AND track_id = ?
                         AND card_key IN (
                             SELECT prerequisite_card_key
                             FROM content.pack_item_prerequisites
                             WHERE pack_version_id = ? AND learning_item_id = ?
                         )""",
                    (profile_id, track_id, pack_version_id, learning_item_id),
                ).fetchall()
            }
            sibling_row = connection.execute(
                """SELECT MAX(created_at_utc)
                   FROM review_events
                   WHERE profile_id = ? AND track_id = ?
                     AND learning_item_id = ? AND card_key <> ?""",
                (profile_id, track_id, learning_item_id, card_key),
            ).fetchone()
            confusable_rows = connection.execute(
                """SELECT group_row.confusable_group_id, group_row.min_intro_gap_days
                   FROM content.confusable_groups AS group_row
                   JOIN content.confusable_group_items AS member
                     ON member.confusable_group_id = group_row.confusable_group_id
                   WHERE group_row.pack_version_id = ?
                     AND member.learning_item_id = ?
                   ORDER BY group_row.confusable_group_id""",
                (pack_version_id, learning_item_id),
            ).fetchall()
            confusable_last_seen: dict[str, str | None] = {}
            for group_id, _gap in confusable_rows:
                row = connection.execute(
                    """SELECT MAX(progress.first_seen_at_utc)
                       FROM progress
                       JOIN content.confusable_group_items AS member
                         ON member.learning_item_id = progress.learning_item_id
                       WHERE progress.profile_id = ? AND progress.track_id = ?
                         AND member.confusable_group_id = ?
                         AND progress.learning_item_id <> ?""",
                    (profile_id, track_id, str(group_id), learning_item_id),
                ).fetchone()
                confusable_last_seen[str(group_id)] = (
                    None if row is None or row[0] is None else str(row[0])
                )
            return {
                "selected": selected_row is not None,
                "prerequisite_card_keys": tuple(str(row[0]) for row in prerequisite_rows),
                "unlock_conditions": tuple(
                    {"metric": str(row[0]), "minimum": float(row[1])} for row in unlock_rows
                ),
                "prerequisite_progress": prerequisite_progress,
                "sibling_last_interaction_at_utc": (
                    None if sibling_row is None or sibling_row[0] is None else str(sibling_row[0])
                ),
                "confusable_groups": tuple(
                    {
                        "confusable_group_id": str(group_id),
                        "min_intro_gap_days": int(gap),
                        "other_item_last_introduced_at_utc": confusable_last_seen[str(group_id)],
                    }
                    for group_id, gap in confusable_rows
                ),
            }

        return await self._storage._async_reader(read)

    async def async_pack_item_signatures(
        self, pack_version_id: str
    ) -> dict[str, tuple[tuple[str, int], ...]]:
        def read(connection: sqlite3.Connection) -> dict[str, tuple[tuple[str, int], ...]]:
            rows = connection.execute(
                """SELECT member.learning_item_id, card.card_key,
                          COALESCE(default_rule.enabled_by_default, 1)
                   FROM content.pack_items AS member
                   LEFT JOIN content.card_definitions AS card
                     ON card.learning_item_id = member.learning_item_id
                    AND card.lifecycle_status = 'active'
                   LEFT JOIN content.pack_item_card_defaults AS default_rule
                     ON default_rule.pack_version_id = member.pack_version_id
                    AND default_rule.learning_item_id = member.learning_item_id
                    AND default_rule.card_key = card.card_key
                   WHERE member.pack_version_id = ?
                   ORDER BY member.learning_item_id, card.card_key""",
                (pack_version_id,),
            ).fetchall()
            signatures: dict[str, list[tuple[str, int]]] = {}
            for item_id, card_key, enabled in rows:
                signatures.setdefault(str(item_id), []).append(
                    ("" if card_key is None else str(card_key), int(enabled))
                )
            return {key: tuple(value) for key, value in signatures.items()}

        return await self._storage._async_reader(read)


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


class ReviewEventsRepository:
    """Append-only audit log plus rebuildable progress projection."""

    _PROGRESS_COLUMNS = (
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
        "first_seen_at_utc",
        "last_seen_at_utc",
        "last_result",
        "next_due_at_utc",
        "streak_correct",
        "leech_score",
        "difficulty_factor",
        "last_verified_at_utc",
        "verified_success_since_box",
        "user_state",
        "suspend_until_utc",
        "example_rotation_index",
        "content_status",
        "policy_version",
        "dataset_generation",
        "normalization_version",
        "updated_at_utc",
    )

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    @classmethod
    def _validate_projection_identity(
        cls,
        event: ReviewEventRecord,
        snapshot: dict[str, Any],
    ) -> None:
        missing = tuple(column for column in cls._PROGRESS_COLUMNS if column not in snapshot)
        if missing:
            raise StateRepositoryError(f"incomplete progress snapshot: {missing!r}")
        expected = {
            "profile_id": event.profile_id,
            "track_id": event.track_id,
            "card_key": event.card_key,
            "learning_item_id": event.learning_item_id,
            "prompt_facet_id": event.prompt_facet_id,
            "answer_facet_id": event.answer_facet_id,
        }
        mismatched = tuple(key for key, value in expected.items() if snapshot.get(key) != value)
        if mismatched:
            raise StateRepositoryError(f"progress snapshot identity mismatch: {mismatched!r}")

    @classmethod
    def _upsert_progress(
        cls,
        connection: sqlite3.Connection,
        snapshot: dict[str, Any],
    ) -> None:
        placeholders = ",".join("?" for _ in cls._PROGRESS_COLUMNS)
        update_columns = cls._PROGRESS_COLUMNS[3:]
        assignments = ",".join(f"{column}=excluded.{column}" for column in update_columns)
        connection.execute(
            f"""INSERT INTO progress({",".join(cls._PROGRESS_COLUMNS)})
                VALUES ({placeholders})
                ON CONFLICT(profile_id, track_id, card_key) DO UPDATE SET
                {assignments}""",
            tuple(snapshot[column] for column in cls._PROGRESS_COLUMNS),
        )

    async def async_append_with_projection(self, event: ReviewEventRecord) -> None:
        """Append one event and materialize its post-state in one transaction."""
        valid = await self._storage.async_validate_card_reference(
            card_key=event.card_key,
            learning_item_id=event.learning_item_id,
            prompt_facet_id=event.prompt_facet_id,
            answer_facet_id=event.answer_facet_id,
        )
        if not valid:
            raise ContentReferenceError(f"unknown active card reference: {event.card_key}")
        self._validate_projection_identity(event, event.post_state_snapshot)

        pre_json = json.dumps(
            event.pre_state_snapshot,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        post_json = json.dumps(
            event.post_state_snapshot,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO review_events(
                           id, profile_id, track_id, learning_item_id,
                           prompt_facet_id, answer_facet_id, card_key, mode,
                           question_type, result, answer_id, expected_answer_id,
                           hint_used, retrieval_occurred, scheduled_interval_days,
                           elapsed_days, grading_result, signal_quality,
                           policy_version, dataset_generation, normalization_version,
                           pre_state_snapshot, post_state_snapshot,
                           presentation_to_answer_ms, delivery_to_action_ms,
                           session_id, notification_id, created_at_utc, local_date,
                           timezone_name, utc_offset_minutes
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                 ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.id,
                        event.profile_id,
                        event.track_id,
                        event.learning_item_id,
                        event.prompt_facet_id,
                        event.answer_facet_id,
                        event.card_key,
                        event.mode,
                        event.question_type,
                        event.result,
                        event.answer_id,
                        event.expected_answer_id,
                        int(event.hint_used),
                        int(event.retrieval_occurred),
                        event.scheduled_interval_days,
                        event.elapsed_days,
                        event.grading_result,
                        event.signal_quality,
                        event.policy_version,
                        event.dataset_generation,
                        event.normalization_version,
                        pre_json,
                        post_json,
                        event.presentation_to_answer_ms,
                        event.delivery_to_action_ms,
                        event.session_id,
                        event.notification_id,
                        event.created_at_utc,
                        event.local_date,
                        event.timezone_name,
                        event.utc_offset_minutes,
                    ),
                )
                self._upsert_progress(connection, event.post_state_snapshot)
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

    async def async_count_introductions(
        self,
        *,
        profile_id: str,
        track_id: str,
        local_date: str,
    ) -> int:
        """Count distinct cards introduced today for P3.9 new-card quota."""

        def read(connection: sqlite3.Connection) -> int:
            row = connection.execute(
                """SELECT COUNT(DISTINCT card_key)
                   FROM review_events
                   WHERE profile_id = ? AND track_id = ?
                     AND local_date = ? AND mode = 'introduction'""",
                (profile_id, track_id, local_date),
            ).fetchone()
            return 0 if row is None else int(row[0])

        return await self._storage._async_reader(read)

    async def async_recent_session_verified_results(
        self,
        session_id: str,
        *,
        limit: int,
    ) -> tuple[str, ...]:
        """Return recent trusted verified outcomes for fatigue detection."""
        if limit < 1:
            raise ValueError("limit must be >= 1")

        def read(connection: sqlite3.Connection) -> tuple[str, ...]:
            rows = connection.execute(
                """SELECT result
                   FROM review_events
                   WHERE session_id = ?
                     AND retrieval_occurred = 1
                     AND mode IN (
                         'verified_mcq',
                         'verified_free_text',
                         'verified_cloze',
                         'exam_retrieval'
                     )
                     AND signal_quality IN ('weak', 'medium', 'strong')
                     AND result IN ('correct', 'wrong', 'idk')
                   ORDER BY created_at_utc DESC, id DESC
                   LIMIT ?""",
                (session_id, limit),
            ).fetchall()
            return tuple(str(row[0]) for row in rows)

        return await self._storage._async_reader(read)

    async def async_list_for_card(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
    ) -> tuple[dict[str, Any], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT id, mode, question_type, result, hint_used,
                          retrieval_occurred, signal_quality, policy_version,
                          dataset_generation, normalization_version,
                          pre_state_snapshot, post_state_snapshot,
                          presentation_to_answer_ms, delivery_to_action_ms,
                          created_at_utc, local_date, timezone_name,
                          utc_offset_minutes
                   FROM review_events
                   WHERE profile_id = ? AND track_id = ? AND card_key = ?
                   ORDER BY created_at_utc, id""",
                (profile_id, track_id, card_key),
            ).fetchall()
            return tuple(
                {
                    "id": str(row[0]),
                    "mode": str(row[1]),
                    "question_type": str(row[2]),
                    "result": str(row[3]),
                    "hint_used": bool(row[4]),
                    "retrieval_occurred": bool(row[5]),
                    "signal_quality": str(row[6]),
                    "policy_version": int(row[7]),
                    "dataset_generation": str(row[8]),
                    "normalization_version": None if row[9] is None else int(row[9]),
                    "pre_state_snapshot": json.loads(str(row[10])),
                    "post_state_snapshot": json.loads(str(row[11])),
                    "presentation_to_answer_ms": None if row[12] is None else int(row[12]),
                    "delivery_to_action_ms": None if row[13] is None else int(row[13]),
                    "created_at_utc": str(row[14]),
                    "local_date": str(row[15]),
                    "timezone_name": str(row[16]),
                    "utc_offset_minutes": int(row[17]),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_rebuild_progress(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int:
        """Rebuild progress from the latest event snapshot under historical policy."""
        if track_id is not None and profile_id is None:
            raise ValueError("track-scoped rebuild requires profile_id")

        def write(connection: sqlite3.Connection) -> int:
            try:
                connection.execute("BEGIN IMMEDIATE")
                clauses: list[str] = []
                params: list[str] = []
                if profile_id is not None:
                    clauses.append("profile_id = ?")
                    params.append(profile_id)
                if track_id is not None:
                    clauses.append("track_id = ?")
                    params.append(track_id)
                where = "" if not clauses else " WHERE " + " AND ".join(clauses)
                connection.execute(f"DELETE FROM progress{where}", tuple(params))
                rows = connection.execute(
                    f"""SELECT post_state_snapshot
                        FROM review_events
                        {where}
                        ORDER BY created_at_utc, id""",
                    tuple(params),
                ).fetchall()
                latest: dict[tuple[str, str, str], dict[str, Any]] = {}
                for (payload,) in rows:
                    snapshot = json.loads(str(payload))
                    key = (
                        str(snapshot["profile_id"]),
                        str(snapshot["track_id"]),
                        str(snapshot["card_key"]),
                    )
                    latest[key] = snapshot
                for snapshot in latest.values():
                    self._upsert_progress(connection, snapshot)
                connection.commit()
                return len(latest)
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)


class ContentReportsRepository:
    """Persist recoverable content-quality feedback in the private state audit log."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    async def async_create_unrecognized_answer_report(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str,
        card: CardReference,
        submitted_text: str,
        normalized_submission: str | None,
        grading_policy_kind: str,
        grading_policy_version: int,
        normalization_version: int,
        dataset_generation: str,
        created_at_utc: str,
    ) -> int:
        valid = await self._storage.async_validate_card_reference(
            card_key=card.card_key,
            learning_item_id=card.learning_item_id,
            prompt_facet_id=card.prompt_facet_id,
            answer_facet_id=card.answer_facet_id,
        )
        if not valid:
            raise ContentReferenceError(f"unknown active card reference: {card.card_key}")

        payload = json.dumps(
            {
                "report_kind": "answer_should_be_accepted",
                "track_id": track_id,
                "card_key": card.card_key,
                "learning_item_id": card.learning_item_id,
                "prompt_facet_id": card.prompt_facet_id,
                "answer_facet_id": card.answer_facet_id,
                "submitted_text": submitted_text,
                "normalized_submission": normalized_submission,
                "grading_result": "unrecognized",
                "grading_policy_kind": grading_policy_kind,
                "grading_policy_version": grading_policy_version,
                "normalization_version": normalization_version,
                "dataset_generation": dataset_generation,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> int:
            track = connection.execute(
                """SELECT profile_id FROM tracks WHERE track_id = ?""",
                (track_id,),
            ).fetchone()
            if track is None or str(track[0]) != profile_id:
                raise StateRepositoryError("track does not belong to profile")
            selected = connection.execute(
                """SELECT 1 FROM track_card_rules
                   WHERE track_id = ? AND card_key = ? AND enabled = 1
                   LIMIT 1""",
                (track_id, card.card_key),
            ).fetchone()
            if selected is None:
                raise StateRepositoryError("card is not enabled in track")
            cursor = connection.execute(
                """INSERT INTO audit_events(
                       event_type, actor_user_id, profile_id, payload_json, created_at_utc
                   ) VALUES ('content_report', ?, ?, ?, ?)""",
                (actor_user_id, profile_id, payload, created_at_utc),
            )
            report_id = cursor.lastrowid
            if report_id is None:
                raise StateRepositoryError("content report insert returned no row id")
            connection.commit()
            return report_id

        return await self._storage._async_writer(write)

    async def async_get(self, report_id: int) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT id, actor_user_id, profile_id, payload_json, created_at_utc
                   FROM audit_events
                   WHERE id = ? AND event_type = 'content_report'""",
                (report_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "report_id": int(row[0]),
                "actor_user_id": None if row[1] is None else str(row[1]),
                "profile_id": None if row[2] is None else str(row[2]),
                "payload": json.loads(str(row[3])),
                "created_at_utc": str(row[4]),
            }

        return await self._storage._async_reader(read)


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
    review_events: ReviewEventsRepository
    content_reports: ContentReportsRepository
    settings: SettingsRepository

    @classmethod
    def for_storage(cls, storage: RepositoryStorage) -> StateRepositories:
        return cls(
            profiles=ProfilesRepository(storage),
            tracks=TracksRepository(storage),
            progress=ProgressRepository(storage),
            review_events=ReviewEventsRepository(storage),
            content_reports=ContentReportsRepository(storage),
            settings=SettingsRepository(storage),
        )
