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
    async def async_validate_learning_item_reference(self, learning_item_id: str) -> bool: ...


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
class NotificationTargetRecord:
    """Stable notification target state backed by the HA device registry identity."""

    target_id: str
    profile_id: str
    device_registry_id: str
    platform: str
    friendly_name: str
    created_at_utc: str
    updated_at_utc: str
    capabilities: dict[str, Any] | None = None
    last_resolved_notify_service: str | None = None
    shared_device: bool = False
    lockscreen_visibility: str = "private"
    enabled: bool = True
    minimum_gap_seconds: int | None = None
    maximum_notifications_per_hour: int | None = None
    daily_push_budget: int | None = None
    adaptive_backoff: dict[str, Any] | None = None


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

    async def async_list_active(self) -> tuple[dict[str, Any], ...]:
        """List active Profiles for internal scheduler hooks."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT profile_id, name, preset, timezone, status, settings_json,
                          created_at_utc, updated_at_utc
                   FROM profiles
                   WHERE status = 'active'
                   ORDER BY profile_id"""
            ).fetchall()
            return tuple(_profile_dict(row) for row in rows)

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

    async def async_card_reference(
        self,
        *,
        track_id: str,
        card_key: str,
    ) -> CardReference | None:
        """Resolve one enabled active CardDefinition selected by a Track."""

        def read(connection: sqlite3.Connection) -> CardReference | None:
            row = connection.execute(
                """SELECT card.card_key, card.learning_item_id,
                          card.prompt_facet_id, card.answer_facet_id
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card
                     ON card.card_key = rule.card_key
                    AND card.lifecycle_status = 'active'
                   JOIN content.learning_items AS item
                     ON item.learning_item_id = card.learning_item_id
                    AND item.lifecycle_status = 'active'
                   JOIN content.facets AS prompt
                     ON prompt.facet_id = card.prompt_facet_id
                    AND prompt.lifecycle_status = 'active'
                   JOIN content.facets AS answer
                     ON answer.facet_id = card.answer_facet_id
                    AND answer.lifecycle_status = 'active'
                   WHERE rule.track_id = ? AND rule.card_key = ?
                     AND rule.enabled = 1
                   LIMIT 1""",
                (track_id, card_key),
            ).fetchone()
            if row is None:
                return None
            return CardReference(
                card_key=str(row[0]),
                learning_item_id=str(row[1]),
                prompt_facet_id=str(row[2]),
                answer_facet_id=str(row[3]),
            )

        return await self._storage._async_reader(read)

    async def async_session_candidates(
        self,
        *,
        profile_id: str,
        track_id: str,
    ) -> tuple[dict[str, Any], ...]:
        """Load P3.9/P3.10 candidate facts from the pinned active PackVersion."""

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
                """SELECT DISTINCT rule.card_key, card.learning_item_id,
                          card.prompt_facet_id, card.answer_facet_id,
                          item.content_type,
                          COALESCE(progress.state, 'new') AS progress_state,
                          progress.next_due_at_utc, pack_item.position,
                          COALESCE(progress.user_state, 'active') AS user_state,
                          progress.suspend_until_utc
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
                confusable_by_item.setdefault(str(learning_item_id), []).append(str(group_id))

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
                    "user_state": str(row[8]),
                    "suspend_until_utc": None if row[9] is None else str(row[9]),
                    "confusable_group_ids": tuple(confusable_by_item.get(str(row[1]), ())),
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
                          self_known_count, self_review_count, first_seen_at_utc,
                          last_seen_at_utc, last_result, next_due_at_utc,
                          streak_correct, leech_score, difficulty_factor,
                          last_verified_at_utc, verified_success_since_box,
                          user_state, suspend_until_utc, example_rotation_index,
                          content_status, policy_version, dataset_generation,
                          normalization_version, updated_at_utc
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
            return dict(zip(keys, row, strict=True))

        return await self._storage._async_reader(read)

    async def async_list_scope(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """List materialized Progress rows for statistics and integrity views."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            clauses = ["profile_id = ?"]
            params: list[Any] = [profile_id]
            if track_id is not None:
                clauses.append("track_id = ?")
                params.append(track_id)
            rows = connection.execute(
                f"""SELECT {",".join(ReviewEventsRepository._PROGRESS_COLUMNS)}
                    FROM progress
                    WHERE {" AND ".join(clauses)}
                    ORDER BY track_id, card_key""",
                tuple(params),
            ).fetchall()
            return tuple(
                dict(zip(ReviewEventsRepository._PROGRESS_COLUMNS, row, strict=True))
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_set_user_state(
        self,
        *,
        actor_user_id: str,
        profile_id: str,
        track_id: str,
        card: CardReference,
        user_state: str,
        suspend_until_utc: str | None,
        dataset_generation: str,
        updated_at_utc: str,
    ) -> None:
        """Upsert user-owned card state without changing SRS scheduling fields."""
        valid = await self._storage.async_validate_card_reference(
            card_key=card.card_key,
            learning_item_id=card.learning_item_id,
            prompt_facet_id=card.prompt_facet_id,
            answer_facet_id=card.answer_facet_id,
        )
        if not valid:
            raise ContentReferenceError(f"unknown active card reference: {card.card_key}")

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                track = connection.execute(
                    "SELECT profile_id FROM tracks WHERE track_id = ?",
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

                previous = connection.execute(
                    """SELECT user_state, suspend_until_utc
                       FROM progress
                       WHERE profile_id = ? AND track_id = ? AND card_key = ?""",
                    (profile_id, track_id, card.card_key),
                ).fetchone()
                connection.execute(
                    """INSERT INTO progress(
                           profile_id, track_id, card_key, learning_item_id,
                           prompt_facet_id, answer_facet_id, state, user_state,
                           suspend_until_utc, dataset_generation, updated_at_utc
                       ) VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?, ?, ?)
                       ON CONFLICT(profile_id, track_id, card_key) DO UPDATE SET
                           user_state = excluded.user_state,
                           suspend_until_utc = excluded.suspend_until_utc,
                           updated_at_utc = excluded.updated_at_utc""",
                    (
                        profile_id,
                        track_id,
                        card.card_key,
                        card.learning_item_id,
                        card.prompt_facet_id,
                        card.answer_facet_id,
                        user_state,
                        suspend_until_utc,
                        dataset_generation,
                        updated_at_utc,
                    ),
                )
                payload = json.dumps(
                    {
                        "track_id": track_id,
                        "card_key": card.card_key,
                        "learning_item_id": card.learning_item_id,
                        "prompt_facet_id": card.prompt_facet_id,
                        "answer_facet_id": card.answer_facet_id,
                        "previous_user_state": "active" if previous is None else str(previous[0]),
                        "previous_suspend_until_utc": (
                            None if previous is None or previous[1] is None else str(previous[1])
                        ),
                        "user_state": user_state,
                        "suspend_until_utc": suspend_until_utc,
                        "dataset_generation": dataset_generation,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                connection.execute(
                    """INSERT INTO audit_events(
                           event_type, actor_user_id, profile_id, payload_json, created_at_utc
                       ) VALUES ('progress_user_state', ?, ?, ?, ?)""",
                    (actor_user_id, profile_id, payload, updated_at_utc),
                )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

    async def async_list_leeches(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """List materialized leech cards for a profile."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            clauses = ["profile_id = ?", "state = 'leech'"]
            params: list[Any] = [profile_id]
            if track_id is not None:
                clauses.append("track_id = ?")
                params.append(track_id)
            rows = connection.execute(
                f"""SELECT profile_id, track_id, card_key, learning_item_id,
                           prompt_facet_id, answer_facet_id, mastery, box,
                           seen_count, verified_correct_count, verified_wrong_count,
                           next_due_at_utc, leech_score, difficulty_factor,
                           user_state, content_status, policy_version, updated_at_utc
                    FROM progress
                    WHERE {" AND ".join(clauses)}
                    ORDER BY leech_score DESC, updated_at_utc DESC, card_key""",
                tuple(params),
            ).fetchall()
            keys = (
                "profile_id",
                "track_id",
                "card_key",
                "learning_item_id",
                "prompt_facet_id",
                "answer_facet_id",
                "mastery",
                "box",
                "seen_count",
                "verified_correct_count",
                "verified_wrong_count",
                "next_due_at_utc",
                "leech_score",
                "difficulty_factor",
                "user_state",
                "content_status",
                "policy_version",
                "updated_at_utc",
            )
            return tuple(dict(zip(keys, row, strict=True)) for row in rows)

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

    @staticmethod
    def _undone_ids_in_connection(
        connection: sqlite3.Connection,
        *,
        profile_id: str,
    ) -> set[str]:
        undone: set[str] = set()
        rows = connection.execute(
            """SELECT payload_json FROM audit_events
               WHERE event_type = 'progress_undo' AND profile_id = ?""",
            (profile_id,),
        ).fetchall()
        for (payload,) in rows:
            decoded = json.loads(str(payload))
            target = decoded.get("target_event_id")
            if isinstance(target, str):
                undone.add(target)
        return undone

    @classmethod
    def _rebuild_stats_day_in_connection(
        cls,
        connection: sqlite3.Connection,
        *,
        profile_id: str,
        track_id: str,
        local_date: str,
    ) -> bool:
        """Replace one stats_daily row from canonical non-undone ReviewEvents."""
        connection.execute(
            """DELETE FROM stats_daily
               WHERE profile_id = ? AND track_id = ? AND local_date = ?""",
            (profile_id, track_id, local_date),
        )
        undone_ids = cls._undone_ids_in_connection(
            connection,
            profile_id=profile_id,
        )
        rows = connection.execute(
            """SELECT id, timezone_name, utc_offset_minutes, policy_version,
                      mode, result, hint_used, retrieval_occurred, signal_quality,
                      question_type, pre_state_snapshot, post_state_snapshot,
                      presentation_to_answer_ms
               FROM review_events
               WHERE profile_id = ? AND track_id = ? AND local_date = ?
               ORDER BY created_at_utc, id""",
            (profile_id, track_id, local_date),
        ).fetchall()
        if not rows:
            return False

        item: dict[str, Any] | None = None
        for row in rows:
            event_id = str(row[0])
            mode = str(row[4])
            if event_id in undone_ids or mode == "undo_compensation":
                continue
            if item is None:
                item = {
                    "timezone_name": str(row[1]),
                    "utc_offset_minutes": int(row[2]),
                    "policy_version": int(row[3]),
                    "learning_exposures": 0,
                    "verified_retrievals": 0,
                    "self_known": 0,
                    "verified_correct": 0,
                    "verified_wrong": 0,
                    "quiz_total": 0,
                    "free_text_total": 0,
                    "hints_used": 0,
                    "new_cards": set(),
                    "reviewed_cards": set(),
                    "relearning_cards": set(),
                    "leech_cards": set(),
                    "active_seconds": 0,
                }
            item["timezone_name"] = str(row[1])
            item["utc_offset_minutes"] = int(row[2])
            item["policy_version"] = int(row[3])
            result = str(row[5])
            retrieval = bool(row[7])
            quality = str(row[8])
            question_type = str(row[9])
            pre = json.loads(str(row[10]))
            post = json.loads(str(row[11]))
            if mode == "introduction":
                item["learning_exposures"] += 1
                item["new_cards"].add(str(post["card_key"]))
            trusted_verified = (
                retrieval
                and mode
                in {
                    "verified_mcq",
                    "verified_free_text",
                    "verified_cloze",
                    "exam_retrieval",
                }
                and quality in {"verified", "weak", "medium", "strong"}
                and result in {"correct", "wrong", "idk"}
            )
            if trusted_verified:
                item["verified_retrievals"] += 1
                if result == "correct":
                    item["verified_correct"] += 1
                else:
                    item["verified_wrong"] += 1
            if mode == "self_assessment_after_retrieval" and result in {
                "correct",
                "known",
                "knew",
                "easy",
                "hard",
            }:
                item["self_known"] += 1
            if question_type in {"mcq", "cloze", "cloze_mcq"}:
                item["quiz_total"] += 1
            if question_type == "free_text":
                item["free_text_total"] += 1
            if bool(row[6]):
                item["hints_used"] += 1
            if str(pre.get("state")) in {"review", "leech"} and retrieval:
                item["reviewed_cards"].add(str(post["card_key"]))
            if str(pre.get("state")) == "relearning" or str(post.get("state")) == "relearning":
                item["relearning_cards"].add(str(post["card_key"]))
            if str(post.get("state")) == "leech":
                item["leech_cards"].add(str(post["card_key"]))
            if row[12] is not None:
                item["active_seconds"] += max(0, int(row[12]) // 1000)

        if item is None:
            return False
        connection.execute(
            """INSERT INTO stats_daily(
                   profile_id, track_id, local_date, timezone_name,
                   utc_offset_minutes, policy_version, learning_exposures,
                   verified_retrievals, self_known, verified_correct,
                   verified_wrong, quiz_total, free_text_total, hints_used,
                   new_cards, reviewed_cards, relearning_cards, leech_cards,
                   active_seconds
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profile_id,
                track_id,
                local_date,
                item["timezone_name"],
                item["utc_offset_minutes"],
                item["policy_version"],
                item["learning_exposures"],
                item["verified_retrievals"],
                item["self_known"],
                item["verified_correct"],
                item["verified_wrong"],
                item["quiz_total"],
                item["free_text_total"],
                item["hints_used"],
                len(item["new_cards"]),
                len(item["reviewed_cards"]),
                len(item["relearning_cards"]),
                len(item["leech_cards"]),
                item["active_seconds"],
            ),
        )
        return True

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
                self._rebuild_stats_day_in_connection(
                    connection,
                    profile_id=event.profile_id,
                    track_id=event.track_id,
                    local_date=event.local_date,
                )
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

    async def async_recent_verified_card_events(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        since_utc: str,
    ) -> tuple[dict[str, Any], ...]:
        """Return trusted verified card events for versioned leech detection."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT mode, result, retrieval_occurred, signal_quality,
                          pre_state_snapshot, post_state_snapshot, created_at_utc
                   FROM review_events
                   WHERE profile_id = ? AND track_id = ? AND card_key = ?
                     AND created_at_utc >= ?
                     AND retrieval_occurred = 1
                     AND mode IN (
                         'verified_mcq',
                         'verified_free_text',
                         'verified_cloze',
                         'exam_retrieval'
                     )
                     AND signal_quality IN ('weak', 'medium', 'strong')
                     AND result IN ('correct', 'wrong', 'idk')
                   ORDER BY created_at_utc DESC, id DESC""",
                (profile_id, track_id, card_key, since_utc),
            ).fetchall()
            return tuple(
                {
                    "mode": str(row[0]),
                    "result": str(row[1]),
                    "retrieval_occurred": bool(row[2]),
                    "signal_quality": str(row[3]),
                    "pre_state_snapshot": json.loads(str(row[4])),
                    "post_state_snapshot": json.loads(str(row[5])),
                    "created_at_utc": str(row[6]),
                }
                for row in rows
            )

        return await self._storage._async_reader(read)

    async def async_confusions(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
        limit: int = 50,
    ) -> tuple[dict[str, Any], ...]:
        """Aggregate expected/chosen answer confusions from non-undone events."""
        if limit < 1:
            raise ValueError("limit must be >= 1")

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            undone = self._undone_ids_in_connection(connection, profile_id=profile_id)
            clauses = [
                "profile_id = ?",
                "retrieval_occurred = 1",
                "result IN ('wrong', 'idk')",
                "expected_answer_id IS NOT NULL",
                "answer_id IS NOT NULL",
                "expected_answer_id != answer_id",
            ]
            params: list[Any] = [profile_id]
            if track_id is not None:
                clauses.append("track_id = ?")
                params.append(track_id)
            if card_key is not None:
                clauses.append("card_key = ?")
                params.append(card_key)
            rows = connection.execute(
                f"""SELECT id, card_key, expected_answer_id, answer_id
                    FROM review_events
                    WHERE {" AND ".join(clauses)}
                    ORDER BY created_at_utc, id""",
                tuple(params),
            ).fetchall()
            counts: dict[tuple[str, str, str], int] = {}
            for row in rows:
                if str(row[0]) in undone:
                    continue
                key = (str(row[1]), str(row[2]), str(row[3]))
                counts[key] = counts.get(key, 0) + 1
            ordered = sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1], item[0][2]),
            )[:limit]
            return tuple(
                {
                    "card_key": key[0],
                    "expected_answer_id": key[1],
                    "chosen_answer_id": key[2],
                    "count": count,
                }
                for key, count in ordered
            )

        return await self._storage._async_reader(read)

    async def async_stats_daily(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        since_local_date: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Read materialized daily statistics without rewriting historical dates."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            clauses = ["profile_id = ?"]
            params: list[Any] = [profile_id]
            if track_id is not None:
                clauses.append("track_id = ?")
                params.append(track_id)
            if since_local_date is not None:
                clauses.append("local_date >= ?")
                params.append(since_local_date)
            rows = connection.execute(
                f"""SELECT profile_id, track_id, local_date, timezone_name,
                           utc_offset_minutes, policy_version, learning_exposures,
                           verified_retrievals, self_known, verified_correct,
                           verified_wrong, quiz_total, free_text_total, hints_used,
                           new_cards, reviewed_cards, relearning_cards, leech_cards,
                           active_seconds
                    FROM stats_daily
                    WHERE {" AND ".join(clauses)}
                    ORDER BY local_date, track_id""",
                tuple(params),
            ).fetchall()
            keys = (
                "profile_id",
                "track_id",
                "local_date",
                "timezone_name",
                "utc_offset_minutes",
                "policy_version",
                "learning_exposures",
                "verified_retrievals",
                "self_known",
                "verified_correct",
                "verified_wrong",
                "quiz_total",
                "free_text_total",
                "hints_used",
                "new_cards",
                "reviewed_cards",
                "relearning_cards",
                "leech_cards",
                "active_seconds",
            )
            return tuple(dict(zip(keys, row, strict=True)) for row in rows)

        return await self._storage._async_reader(read)

    async def async_progress_user_state_audit(
        self,
        *,
        profile_id: str,
        since_utc: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Return private P3.10 user-state audit events for metacognitive stats."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            clauses = ["event_type = 'progress_user_state'", "profile_id = ?"]
            params: list[Any] = [profile_id]
            if since_utc is not None:
                clauses.append("created_at_utc >= ?")
                params.append(since_utc)
            rows = connection.execute(
                f"""SELECT payload_json, created_at_utc
                    FROM audit_events
                    WHERE {" AND ".join(clauses)}
                    ORDER BY created_at_utc, id""",
                tuple(params),
            ).fetchall()
            result: list[dict[str, Any]] = []
            for payload, created_at in rows:
                item = json.loads(str(payload))
                item["created_at_utc"] = str(created_at)
                result.append(item)
            return tuple(result)

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

    async def async_list_scope_events(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Return canonical events in deterministic replay order."""
        if track_id is not None and profile_id is None:
            raise ValueError("track-scoped event replay requires profile_id")

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            clauses: list[str] = []
            params: list[str] = []
            if profile_id is not None:
                clauses.append("profile_id = ?")
                params.append(profile_id)
            if track_id is not None:
                clauses.append("track_id = ?")
                params.append(track_id)
            where = "" if not clauses else " WHERE " + " AND ".join(clauses)
            rows = connection.execute(
                f"""SELECT id, profile_id, track_id, learning_item_id,
                           prompt_facet_id, answer_facet_id, card_key, mode,
                           question_type, result, answer_id, expected_answer_id,
                           hint_used, retrieval_occurred, scheduled_interval_days,
                           elapsed_days, grading_result, signal_quality,
                           policy_version, dataset_generation, normalization_version,
                           pre_state_snapshot, post_state_snapshot,
                           presentation_to_answer_ms, delivery_to_action_ms,
                           session_id, notification_id, created_at_utc, local_date,
                           timezone_name, utc_offset_minutes
                    FROM review_events{where}
                    ORDER BY created_at_utc, id""",
                tuple(params),
            ).fetchall()
            keys = (
                "id",
                "profile_id",
                "track_id",
                "learning_item_id",
                "prompt_facet_id",
                "answer_facet_id",
                "card_key",
                "mode",
                "question_type",
                "result",
                "answer_id",
                "expected_answer_id",
                "hint_used",
                "retrieval_occurred",
                "scheduled_interval_days",
                "elapsed_days",
                "grading_result",
                "signal_quality",
                "policy_version",
                "dataset_generation",
                "normalization_version",
                "pre_state_snapshot",
                "post_state_snapshot",
                "presentation_to_answer_ms",
                "delivery_to_action_ms",
                "session_id",
                "notification_id",
                "created_at_utc",
                "local_date",
                "timezone_name",
                "utc_offset_minutes",
            )
            result: list[dict[str, Any]] = []
            for row in rows:
                event = dict(zip(keys, row, strict=True))
                event["hint_used"] = bool(event["hint_used"])
                event["retrieval_occurred"] = bool(event["retrieval_occurred"])
                event["policy_version"] = int(event["policy_version"])
                event["normalization_version"] = (
                    None
                    if event["normalization_version"] is None
                    else int(event["normalization_version"])
                )
                event["pre_state_snapshot"] = json.loads(str(event["pre_state_snapshot"]))
                event["post_state_snapshot"] = json.loads(str(event["post_state_snapshot"]))
                result.append(event)
            return tuple(result)

        return await self._storage._async_reader(read)

    async def async_undone_event_ids(
        self,
        *,
        profile_id: str | None = None,
    ) -> frozenset[str]:
        """Return canonical ReviewEvent ids explicitly undone by compensation."""

        def read(connection: sqlite3.Connection) -> frozenset[str]:
            if profile_id is None:
                rows = connection.execute(
                    """SELECT payload_json FROM audit_events
                       WHERE event_type = 'progress_undo'
                       ORDER BY id"""
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT payload_json FROM audit_events
                       WHERE event_type = 'progress_undo' AND profile_id = ?
                       ORDER BY id""",
                    (profile_id,),
                ).fetchall()
            ids: set[str] = set()
            for (payload,) in rows:
                decoded = json.loads(str(payload))
                target = decoded.get("target_event_id")
                if isinstance(target, str):
                    ids.add(target)
            return frozenset(ids)

        return await self._storage._async_reader(read)

    async def async_latest_undo_candidate(
        self,
        *,
        profile_id: str,
        track_id: str | None = None,
        card_key: str | None = None,
    ) -> dict[str, Any] | None:
        """Return the newest not-yet-undone progress mutation in scope."""

        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            undone: set[str] = set()
            rows = connection.execute(
                """SELECT payload_json FROM audit_events
                   WHERE event_type = 'progress_undo' AND profile_id = ?
                   ORDER BY id""",
                (profile_id,),
            ).fetchall()
            for (payload,) in rows:
                decoded = json.loads(str(payload))
                target = decoded.get("target_event_id")
                if isinstance(target, str):
                    undone.add(target)

            clauses = ["profile_id = ?", "mode != 'undo_compensation'"]
            params: list[Any] = [profile_id]
            if track_id is not None:
                clauses.append("track_id = ?")
                params.append(track_id)
            if card_key is not None:
                clauses.append("card_key = ?")
                params.append(card_key)
            rows = connection.execute(
                f"""SELECT id, profile_id, track_id, learning_item_id,
                           prompt_facet_id, answer_facet_id, card_key, mode,
                           question_type, result, signal_quality, policy_version,
                           dataset_generation, normalization_version,
                           pre_state_snapshot, post_state_snapshot, created_at_utc,
                           local_date, timezone_name, utc_offset_minutes
                    FROM review_events
                    WHERE {" AND ".join(clauses)}
                    ORDER BY created_at_utc DESC, id DESC""",
                tuple(params),
            ).fetchall()
            for row in rows:
                event_id = str(row[0])
                if event_id in undone:
                    continue
                return {
                    "id": event_id,
                    "profile_id": str(row[1]),
                    "track_id": str(row[2]),
                    "learning_item_id": str(row[3]),
                    "prompt_facet_id": str(row[4]),
                    "answer_facet_id": str(row[5]),
                    "card_key": str(row[6]),
                    "mode": str(row[7]),
                    "question_type": str(row[8]),
                    "result": str(row[9]),
                    "signal_quality": str(row[10]),
                    "policy_version": int(row[11]),
                    "dataset_generation": str(row[12]),
                    "normalization_version": None if row[13] is None else int(row[13]),
                    "pre_state_snapshot": json.loads(str(row[14])),
                    "post_state_snapshot": json.loads(str(row[15])),
                    "created_at_utc": str(row[16]),
                    "local_date": str(row[17]),
                    "timezone_name": str(row[18]),
                    "utc_offset_minutes": int(row[19]),
                }
            return None

        return await self._storage._async_reader(read)

    async def async_append_undo_compensation(
        self,
        event: ReviewEventRecord,
        *,
        target_event_id: str,
        actor_user_id: str,
    ) -> None:
        """Atomically append an undo compensation and audit its target."""
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
                target = connection.execute(
                    """SELECT local_date FROM review_events
                       WHERE id = ? AND profile_id = ?""",
                    (target_event_id, event.profile_id),
                ).fetchone()
                if target is None:
                    raise StateRepositoryError("undo target no longer exists")
                target_local_date = str(target[0])
                for (payload,) in connection.execute(
                    """SELECT payload_json FROM audit_events
                       WHERE event_type = 'progress_undo' AND profile_id = ?""",
                    (event.profile_id,),
                ).fetchall():
                    decoded = json.loads(str(payload))
                    if decoded.get("target_event_id") == target_event_id:
                        raise StateRepositoryError("progress mutation was already undone")

                current_row = connection.execute(
                    f"""SELECT {",".join(self._PROGRESS_COLUMNS)}
                        FROM progress
                        WHERE profile_id = ? AND track_id = ? AND card_key = ?""",
                    (event.profile_id, event.track_id, event.card_key),
                ).fetchone()
                if current_row is None:
                    raise StateRepositoryError("undo target has no current progress")
                current_progress = dict(zip(self._PROGRESS_COLUMNS, current_row, strict=True))
                if any(
                    current_progress[column] != event.pre_state_snapshot.get(column)
                    for column in self._PROGRESS_COLUMNS
                ):
                    raise StateRepositoryError("progress changed during undo")
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
                audit_payload = json.dumps(
                    {
                        "target_event_id": target_event_id,
                        "compensation_event_id": event.id,
                        "track_id": event.track_id,
                        "card_key": event.card_key,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                connection.execute(
                    """INSERT INTO audit_events(
                           event_type, actor_user_id, profile_id, payload_json, created_at_utc
                       ) VALUES ('progress_undo', ?, ?, ?, ?)""",
                    (actor_user_id, event.profile_id, audit_payload, event.created_at_utc),
                )
                for affected_date in {target_local_date, event.local_date}:
                    self._rebuild_stats_day_in_connection(
                        connection,
                        profile_id=event.profile_id,
                        track_id=event.track_id,
                        local_date=affected_date,
                    )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)

    async def async_replace_progress(
        self,
        snapshots: tuple[dict[str, Any], ...],
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int:
        """Replace Progress while preserving independent user/content overlays."""
        if track_id is not None and profile_id is None:
            raise ValueError("track-scoped replacement requires profile_id")

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

                existing_rows = connection.execute(
                    f"""SELECT {",".join(self._PROGRESS_COLUMNS)}
                        FROM progress{where}""",
                    tuple(params),
                ).fetchall()
                existing: dict[tuple[str, str, str], dict[str, Any]] = {}
                for row in existing_rows:
                    snapshot = dict(zip(self._PROGRESS_COLUMNS, row, strict=True))
                    key = (
                        str(snapshot["profile_id"]),
                        str(snapshot["track_id"]),
                        str(snapshot["card_key"]),
                    )
                    existing[key] = snapshot

                connection.execute(f"DELETE FROM progress{where}", tuple(params))
                inserted: set[tuple[str, str, str]] = set()
                for raw in snapshots:
                    snapshot = dict(raw)
                    key = (
                        str(snapshot["profile_id"]),
                        str(snapshot["track_id"]),
                        str(snapshot["card_key"]),
                    )
                    previous = existing.get(key)
                    if previous is not None:
                        snapshot["user_state"] = previous["user_state"]
                        snapshot["suspend_until_utc"] = previous["suspend_until_utc"]
                        snapshot["content_status"] = previous["content_status"]
                    self._upsert_progress(connection, snapshot)
                    inserted.add(key)

                for key, previous in existing.items():
                    if key in inserted:
                        continue
                    if (
                        previous["user_state"] != "active"
                        or previous["suspend_until_utc"] is not None
                        or previous["content_status"] != "active"
                    ):
                        self._upsert_progress(connection, previous)
                        inserted.add(key)

                connection.commit()
                return len(inserted)
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

    async def async_rebuild_stats(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int:
        """Rebuild stats_daily independently from canonical ReviewEvents."""
        if track_id is not None and profile_id is None:
            raise ValueError("track-scoped stats rebuild requires profile_id")

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
                connection.execute(f"DELETE FROM stats_daily{where}", tuple(params))
                rows = connection.execute(
                    f"""SELECT DISTINCT profile_id, track_id, local_date
                        FROM review_events{where}
                        ORDER BY profile_id, track_id, local_date""",
                    tuple(params),
                ).fetchall()
                rebuilt = 0
                for p_id, t_id, local_date in rows:
                    rebuilt += int(
                        self._rebuild_stats_day_in_connection(
                            connection,
                            profile_id=str(p_id),
                            track_id=str(t_id),
                            local_date=str(local_date),
                        )
                    )
                connection.commit()
                return rebuilt
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

    async def async_rebuild_progress(
        self,
        *,
        profile_id: str | None = None,
        track_id: str | None = None,
    ) -> int:
        """Rebuild Progress from historical post snapshots, preserving overlays."""
        events = await self.async_list_scope_events(
            profile_id=profile_id,
            track_id=track_id,
        )
        latest: dict[tuple[str, str, str], dict[str, Any]] = {}
        for event in events:
            snapshot = dict(event["post_state_snapshot"])
            key = (
                str(snapshot["profile_id"]),
                str(snapshot["track_id"]),
                str(snapshot["card_key"]),
            )
            latest[key] = snapshot
        return await self.async_replace_progress(
            tuple(latest.values()),
            profile_id=profile_id,
            track_id=track_id,
        )


class UserAnnotationsRepository:
    """Private profile-scoped notes and mnemonics."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

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
    ) -> dict[str, Any]:
        if (learning_item_id is None) == (card_key is None):
            raise StateRepositoryError("annotation must target exactly one item or card")
        if not note.strip():
            raise StateRepositoryError("annotation note must not be empty")
        if (
            learning_item_id is not None
            and not await self._storage.async_validate_learning_item_reference(learning_item_id)
        ):
            raise ContentReferenceError(
                f"unknown active learning item reference: {learning_item_id}"
            )

        def write(connection: sqlite3.Connection) -> None:
            if card_key is not None:
                exists = connection.execute(
                    """SELECT 1 FROM progress
                       WHERE profile_id = ? AND card_key = ?
                       LIMIT 1""",
                    (profile_id, card_key),
                ).fetchone()
                if exists is None:
                    # Card annotations may precede Progress materialization; validate
                    # identity against active content through the reader boundary above
                    # is unavailable here, so require at least one track rule for profile.
                    exists = connection.execute(
                        """SELECT 1
                           FROM track_card_rules AS rule
                           JOIN tracks AS track ON track.track_id = rule.track_id
                           WHERE track.profile_id = ? AND rule.card_key = ?
                             AND rule.enabled = 1
                           LIMIT 1""",
                        (profile_id, card_key),
                    ).fetchone()
                if exists is None:
                    raise StateRepositoryError("card is not available to profile")
            connection.execute(
                """INSERT INTO user_annotations(
                       annotation_id, profile_id, learning_item_id, card_key, note,
                       created_at_utc, updated_at_utc
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(annotation_id) DO UPDATE SET
                       note = excluded.note,
                       updated_at_utc = excluded.updated_at_utc
                   WHERE user_annotations.profile_id = excluded.profile_id""",
                (
                    annotation_id,
                    profile_id,
                    learning_item_id,
                    card_key,
                    note.strip(),
                    created_at_utc,
                    updated_at_utc,
                ),
            )
            connection.commit()

        await self._storage._async_writer(write)
        result = await self.async_get(annotation_id=annotation_id, profile_id=profile_id)
        if result is None:
            raise StateRepositoryError("annotation upsert failed")
        return result

    async def async_get(
        self,
        *,
        annotation_id: str,
        profile_id: str,
    ) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT annotation_id, profile_id, learning_item_id, card_key,
                          note, created_at_utc, updated_at_utc
                   FROM user_annotations
                   WHERE annotation_id = ? AND profile_id = ?""",
                (annotation_id, profile_id),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "annotation_id",
                "profile_id",
                "learning_item_id",
                "card_key",
                "note",
                "created_at_utc",
                "updated_at_utc",
            )
            return dict(zip(keys, row, strict=True))

        return await self._storage._async_reader(read)

    async def async_list(
        self,
        *,
        profile_id: str,
        learning_item_id: str | None = None,
        card_key: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            clauses = ["profile_id = ?"]
            params: list[Any] = [profile_id]
            if learning_item_id is not None:
                clauses.append("learning_item_id = ?")
                params.append(learning_item_id)
            if card_key is not None:
                clauses.append("card_key = ?")
                params.append(card_key)
            rows = connection.execute(
                f"""SELECT annotation_id, profile_id, learning_item_id, card_key,
                           note, created_at_utc, updated_at_utc
                    FROM user_annotations
                    WHERE {" AND ".join(clauses)}
                    ORDER BY updated_at_utc DESC, annotation_id""",
                tuple(params),
            ).fetchall()
            keys = (
                "annotation_id",
                "profile_id",
                "learning_item_id",
                "card_key",
                "note",
                "created_at_utc",
                "updated_at_utc",
            )
            return tuple(dict(zip(keys, row, strict=True)) for row in rows)

        return await self._storage._async_reader(read)

    async def async_delete(self, *, annotation_id: str, profile_id: str) -> bool:
        def write(connection: sqlite3.Connection) -> bool:
            cursor = connection.execute(
                "DELETE FROM user_annotations WHERE annotation_id = ? AND profile_id = ?",
                (annotation_id, profile_id),
            )
            connection.commit()
            return cursor.rowcount == 1

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


class NotificationTargetsRepository:
    """Persistence primitives for stable Profile notification targets."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    @staticmethod
    def _target_dict(row: tuple[Any, ...]) -> dict[str, Any]:
        keys = (
            "target_id",
            "profile_id",
            "device_registry_id",
            "platform",
            "capabilities_json",
            "friendly_name",
            "last_resolved_notify_service",
            "shared_device",
            "lockscreen_visibility",
            "enabled",
            "minimum_gap_seconds",
            "maximum_notifications_per_hour",
            "daily_push_budget",
            "adaptive_backoff_json",
            "created_at_utc",
            "updated_at_utc",
        )
        result = dict(zip(keys, row, strict=True))
        result["capabilities"] = json.loads(result.pop("capabilities_json"))
        result["adaptive_backoff"] = json.loads(result.pop("adaptive_backoff_json"))
        result["shared_device"] = bool(result["shared_device"])
        result["enabled"] = bool(result["enabled"])
        return result

    async def async_insert(self, target: NotificationTargetRecord) -> None:
        """Insert one stable Profile target."""
        capabilities_json = json.dumps(
            target.capabilities or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        adaptive_backoff_json = json.dumps(
            target.adaptive_backoff or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO notification_targets(
                       target_id, profile_id, device_registry_id, platform,
                       capabilities_json, friendly_name, last_resolved_notify_service,
                       shared_device, lockscreen_visibility, enabled,
                       minimum_gap_seconds, maximum_notifications_per_hour,
                       daily_push_budget, adaptive_backoff_json,
                       created_at_utc, updated_at_utc
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    target.target_id,
                    target.profile_id,
                    target.device_registry_id,
                    target.platform,
                    capabilities_json,
                    target.friendly_name,
                    target.last_resolved_notify_service,
                    int(target.shared_device),
                    target.lockscreen_visibility,
                    int(target.enabled),
                    target.minimum_gap_seconds,
                    target.maximum_notifications_per_hour,
                    target.daily_push_budget,
                    adaptive_backoff_json,
                    target.created_at_utc,
                    target.updated_at_utc,
                ),
            )
            connection.commit()

        await self._storage._async_writer(write)

    async def async_list_for_profile(
        self,
        profile_id: str,
        *,
        enabled_only: bool = True,
    ) -> tuple[dict[str, Any], ...]:
        """List Profile targets in stable target_id order."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            enabled_clause = "AND enabled = 1" if enabled_only else ""
            rows = connection.execute(
                f"""SELECT target_id, profile_id, device_registry_id, platform,
                           capabilities_json, friendly_name, last_resolved_notify_service,
                           shared_device, lockscreen_visibility, enabled,
                           minimum_gap_seconds, maximum_notifications_per_hour,
                           daily_push_budget, adaptive_backoff_json,
                           created_at_utc, updated_at_utc
                    FROM notification_targets
                    WHERE profile_id = ? {enabled_clause}
                    ORDER BY target_id""",
                (profile_id,),
            ).fetchall()
            return tuple(self._target_dict(row) for row in rows)

        return await self._storage._async_reader(read)


class SchedulerRepository:
    """Persist profile scheduler configuration and materialized slots."""

    def __init__(self, storage: RepositoryStorage) -> None:
        self._storage = storage

    @staticmethod
    def _config_dict(row: tuple[Any, ...]) -> dict[str, Any]:
        keys = (
            "profile_id",
            "version",
            "timezone",
            "active_days_json",
            "active_windows_json",
            "minimum_gap_seconds",
            "maximum_notifications_per_hour",
            "quiet_hours_json",
            "receptive_when",
            "defer_window_minutes",
            "updated_at_utc",
        )
        result = dict(zip(keys, row, strict=True))
        result["active_days"] = json.loads(result.pop("active_days_json"))
        result["active_windows"] = json.loads(result.pop("active_windows_json"))
        result["quiet_hours"] = json.loads(result.pop("quiet_hours_json"))
        return result

    async def async_get_config(self, profile_id: str) -> dict[str, Any] | None:
        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT profile_id, version, timezone, active_days_json,
                          active_windows_json, minimum_gap_seconds,
                          maximum_notifications_per_hour, quiet_hours_json,
                          receptive_when, defer_window_minutes, updated_at_utc
                   FROM scheduler_config
                   WHERE profile_id = ?""",
                (profile_id,),
            ).fetchone()
            return None if row is None else self._config_dict(row)

        return await self._storage._async_reader(read)

    async def async_sync_config(
        self,
        *,
        profile_id: str,
        timezone: str,
        active_days: tuple[int, ...],
        active_windows: tuple[tuple[str, str], ...],
        minimum_gap_seconds: int,
        maximum_notifications_per_hour: int,
        quiet_hours: tuple[str, str],
        receptive_when: str | None,
        defer_window_minutes: int,
        updated_at_utc: str,
    ) -> dict[str, Any]:
        active_days_json = json.dumps(list(active_days), separators=(",", ":"))
        active_windows_json = json.dumps(
            [{"start": start, "end": end} for start, end in active_windows],
            separators=(",", ":"),
            sort_keys=True,
        )
        quiet_hours_json = json.dumps(
            {"start": quiet_hours[0], "end": quiet_hours[1]},
            separators=(",", ":"),
            sort_keys=True,
        )

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = connection.execute(
                    """SELECT version, timezone, active_days_json, active_windows_json,
                              minimum_gap_seconds, maximum_notifications_per_hour,
                              quiet_hours_json, receptive_when, defer_window_minutes
                       FROM scheduler_config
                       WHERE profile_id = ?""",
                    (profile_id,),
                ).fetchone()
                semantic = (
                    timezone,
                    active_days_json,
                    active_windows_json,
                    minimum_gap_seconds,
                    maximum_notifications_per_hour,
                    quiet_hours_json,
                    receptive_when,
                    defer_window_minutes,
                )
                if current is None:
                    version = 1
                    connection.execute(
                        """INSERT INTO scheduler_config(
                               profile_id, version, timezone, active_days_json,
                               active_windows_json, minimum_gap_seconds,
                               maximum_notifications_per_hour, quiet_hours_json,
                               receptive_when, defer_window_minutes, updated_at_utc
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            profile_id,
                            version,
                            *semantic,
                            updated_at_utc,
                        ),
                    )
                elif tuple(current[1:]) != semantic:
                    version = int(current[0]) + 1
                    connection.execute(
                        """UPDATE scheduler_config
                           SET version = ?, timezone = ?, active_days_json = ?,
                               active_windows_json = ?, minimum_gap_seconds = ?,
                               maximum_notifications_per_hour = ?, quiet_hours_json = ?,
                               receptive_when = ?, defer_window_minutes = ?,
                               updated_at_utc = ?
                           WHERE profile_id = ?""",
                        (
                            version,
                            *semantic,
                            updated_at_utc,
                            profile_id,
                        ),
                    )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)
        config = await self.async_get_config(profile_id)
        if config is None:
            raise StateRepositoryError("scheduler config could not be reloaded")
        return config

    async def async_materialize_day(
        self,
        *,
        profile_id: str,
        scheduler_config_version: int,
        seed: str,
        start_utc: str,
        end_utc: str,
        now_utc: str,
        slots: tuple[dict[str, Any], ...],
        updated_at_utc: str,
    ) -> tuple[dict[str, Any], ...]:
        """Insert missing slots while never rewriting already materialized rows."""

        def write(connection: sqlite3.Connection) -> None:
            try:
                connection.execute("BEGIN IMMEDIATE")
                for slot in slots:
                    connection.execute(
                        """INSERT OR IGNORE INTO scheduled_slots(
                               slot_id, profile_id, track_id, target_id, slot_type,
                               scheduled_for_utc, status, scheduler_config_version,
                               seed, created_at_utc, updated_at_utc
                           ) VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?, ?)""",
                        (
                            slot["slot_id"],
                            profile_id,
                            slot.get("track_id"),
                            slot.get("target_id"),
                            slot["slot_type"],
                            slot["scheduled_for_utc"],
                            scheduler_config_version,
                            seed,
                            now_utc,
                            updated_at_utc,
                        ),
                    )
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        await self._storage._async_writer(write)
        return await self.async_list_slots(
            profile_id=profile_id,
            start_utc=start_utc,
            end_utc=end_utc,
        )

    async def async_list_slots(
        self,
        *,
        profile_id: str,
        start_utc: str,
        end_utc: str,
    ) -> tuple[dict[str, Any], ...]:
        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT slot_id, profile_id, track_id, target_id, slot_type,
                          scheduled_for_utc, deferred_until_utc, defer_reason,
                          status, scheduler_config_version, seed,
                          created_at_utc, updated_at_utc
                   FROM scheduled_slots
                   WHERE profile_id = ?
                     AND scheduled_for_utc >= ?
                     AND scheduled_for_utc < ?
                   ORDER BY scheduled_for_utc, slot_id""",
                (profile_id, start_utc, end_utc),
            ).fetchall()
            keys = (
                "slot_id",
                "profile_id",
                "track_id",
                "target_id",
                "slot_type",
                "scheduled_for_utc",
                "deferred_until_utc",
                "defer_reason",
                "status",
                "scheduler_config_version",
                "seed",
                "created_at_utc",
                "updated_at_utc",
            )
            return tuple(dict(zip(keys, row, strict=True)) for row in rows)

        return await self._storage._async_reader(read)

    async def async_list_device_slots(
        self,
        *,
        device_registry_id: str,
        start_utc: str,
        end_utc: str,
    ) -> tuple[dict[str, Any], ...]:
        """List materialized slots sharing one physical device identity."""

        def read(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
            rows = connection.execute(
                """SELECT slot.slot_id, slot.profile_id, slot.track_id, slot.target_id,
                          slot.slot_type, slot.scheduled_for_utc,
                          slot.deferred_until_utc, slot.defer_reason, slot.status,
                          slot.scheduler_config_version, slot.seed,
                          slot.created_at_utc, slot.updated_at_utc
                   FROM scheduled_slots AS slot
                   JOIN notification_targets AS target
                     ON target.target_id = slot.target_id
                   WHERE target.device_registry_id = ?
                     AND slot.scheduled_for_utc >= ?
                     AND slot.scheduled_for_utc < ?
                   ORDER BY slot.scheduled_for_utc, slot.slot_id""",
                (device_registry_id, start_utc, end_utc),
            ).fetchall()
            keys = (
                "slot_id",
                "profile_id",
                "track_id",
                "target_id",
                "slot_type",
                "scheduled_for_utc",
                "deferred_until_utc",
                "defer_reason",
                "status",
                "scheduler_config_version",
                "seed",
                "created_at_utc",
                "updated_at_utc",
            )
            return tuple(dict(zip(keys, row, strict=True)) for row in rows)

        return await self._storage._async_reader(read)

    async def async_get_slot(self, slot_id: str) -> dict[str, Any] | None:
        """Return one materialized scheduler slot."""

        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT slot_id, profile_id, track_id, target_id, slot_type,
                          scheduled_for_utc, deferred_until_utc, defer_reason,
                          status, scheduler_config_version, seed,
                          created_at_utc, updated_at_utc
                   FROM scheduled_slots
                   WHERE slot_id = ?""",
                (slot_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "slot_id",
                "profile_id",
                "track_id",
                "target_id",
                "slot_type",
                "scheduled_for_utc",
                "deferred_until_utc",
                "defer_reason",
                "status",
                "scheduler_config_version",
                "seed",
                "created_at_utc",
                "updated_at_utc",
            )
            return dict(zip(keys, row, strict=True))

        return await self._storage._async_reader(read)

    async def async_defer_slot(
        self,
        *,
        slot_id: str,
        deferred_until_utc: str,
        reason: str,
        updated_at_utc: str,
    ) -> bool:
        """Defer an unsent slot without recording a pedagogical outcome."""

        def write(connection: sqlite3.Connection) -> bool:
            cursor = connection.execute(
                """UPDATE scheduled_slots
                   SET status = 'deferred',
                       deferred_until_utc = ?,
                       defer_reason = ?,
                       updated_at_utc = ?
                   WHERE slot_id = ?
                     AND status IN ('scheduled', 'deferred')""",
                (deferred_until_utc, reason, updated_at_utc, slot_id),
            )
            connection.commit()
            return cursor.rowcount == 1

        return await self._storage._async_writer(write)

    async def async_mark_slot_sent(
        self,
        *,
        slot_id: str,
        delivered_at_utc: str,
        timezone_name: str,
        weekday: int,
        local_hour: int,
    ) -> bool:
        """Mark delivery and initialize the V1 receptivity feature sample."""

        def write(connection: sqlite3.Connection) -> bool:
            try:
                connection.execute("BEGIN IMMEDIATE")
                slot = connection.execute(
                    """SELECT profile_id, target_id, status
                       FROM scheduled_slots
                       WHERE slot_id = ?""",
                    (slot_id,),
                ).fetchone()
                if slot is None or str(slot[2]) not in {"scheduled", "deferred"}:
                    connection.rollback()
                    return False
                connection.execute(
                    """UPDATE scheduled_slots
                       SET status = 'sent',
                           deferred_until_utc = NULL,
                           defer_reason = NULL,
                           updated_at_utc = ?
                       WHERE slot_id = ?""",
                    (delivered_at_utc, slot_id),
                )
                connection.execute(
                    """INSERT INTO receptivity_samples(
                           slot_id, profile_id, target_id, delivered_at_utc,
                           timezone_name, weekday, local_hour, delivered,
                           cleared, answered, delivery_to_action_ms, updated_at_utc
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 0, NULL, ?)
                       ON CONFLICT(slot_id) DO NOTHING""",
                    (
                        slot_id,
                        str(slot[0]),
                        None if slot[1] is None else str(slot[1]),
                        delivered_at_utc,
                        timezone_name,
                        weekday,
                        local_hour,
                        delivered_at_utc,
                    ),
                )
                connection.commit()
                return True
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

        return await self._storage._async_writer(write)

    async def async_record_receptivity_action(
        self,
        *,
        slot_id: str,
        action: str,
        action_at_utc: str,
        delivery_to_action_ms: int,
    ) -> bool:
        """Update only observational receptivity features for a delivered slot."""
        if action not in {"cleared", "answered"}:
            raise ValueError("unsupported receptivity action")

        def write(connection: sqlite3.Connection) -> bool:
            column = "cleared" if action == "cleared" else "answered"
            cursor = connection.execute(
                f"""UPDATE receptivity_samples
                    SET {column} = 1,
                        delivery_to_action_ms = CASE
                            WHEN delivery_to_action_ms IS NULL
                                THEN ?
                            ELSE MIN(delivery_to_action_ms, ?)
                        END,
                        updated_at_utc = ?
                    WHERE slot_id = ?""",
                (
                    delivery_to_action_ms,
                    delivery_to_action_ms,
                    action_at_utc,
                    slot_id,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

        return await self._storage._async_writer(write)

    async def async_get_receptivity_sample(self, slot_id: str) -> dict[str, Any] | None:
        """Read one observational receptivity sample for tests/diagnostics."""

        def read(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                """SELECT slot_id, profile_id, target_id, delivered_at_utc,
                          timezone_name, weekday, local_hour, delivered,
                          cleared, answered, delivery_to_action_ms, updated_at_utc
                   FROM receptivity_samples
                   WHERE slot_id = ?""",
                (slot_id,),
            ).fetchone()
            if row is None:
                return None
            keys = (
                "slot_id",
                "profile_id",
                "target_id",
                "delivered_at_utc",
                "timezone_name",
                "weekday",
                "local_hour",
                "delivered",
                "cleared",
                "answered",
                "delivery_to_action_ms",
                "updated_at_utc",
            )
            result = dict(zip(keys, row, strict=True))
            for key in ("delivered", "cleared", "answered"):
                result[key] = bool(result[key])
            return result

        return await self._storage._async_reader(read)

    async def async_cancel_superseded_future_slots(
        self,
        *,
        profile_id: str,
        active_config_version: int,
        not_before_utc: str,
        updated_at_utc: str,
    ) -> int:
        """Cancel only future unsent slots from an older scheduler config version."""

        def write(connection: sqlite3.Connection) -> int:
            cursor = connection.execute(
                """UPDATE scheduled_slots
                   SET status = 'cancelled', updated_at_utc = ?
                   WHERE profile_id = ?
                     AND scheduler_config_version <> ?
                     AND scheduled_for_utc >= ?
                     AND status IN ('scheduled', 'deferred')""",
                (
                    updated_at_utc,
                    profile_id,
                    active_config_version,
                    not_before_utc,
                ),
            )
            connection.commit()
            return cursor.rowcount

        return await self._storage._async_writer(write)

    async def async_expire_before(
        self,
        *,
        before_utc: str,
        updated_at_utc: str,
    ) -> int:
        """Expire overdue unsent slots during restart/clock reconciliation."""

        def write(connection: sqlite3.Connection) -> int:
            cursor = connection.execute(
                """UPDATE scheduled_slots
                   SET status = 'expired', updated_at_utc = ?
                   WHERE (
                       (status = 'scheduled' AND scheduled_for_utc < ?)
                       OR (
                           status = 'deferred'
                           AND COALESCE(deferred_until_utc, scheduled_for_utc) < ?
                       )
                   )""",
                (updated_at_utc, before_utc, before_utc),
            )
            connection.commit()
            return cursor.rowcount

        return await self._storage._async_writer(write)

    async def async_active_session_track_ids(
        self,
        profile_id: str,
    ) -> frozenset[str]:
        """Return Tracks currently suppressed by an active Profile session."""

        def read(connection: sqlite3.Connection) -> frozenset[str]:
            rows = connection.execute(
                """SELECT DISTINCT track_id
                   FROM sessions
                   WHERE profile_id = ?
                     AND status = 'active'
                     AND track_id IS NOT NULL""",
                (profile_id,),
            ).fetchall()
            return frozenset(str(row[0]) for row in rows)

        return await self._storage._async_reader(read)

    async def async_set_slot_status(
        self,
        slot_id: str,
        status: str,
        *,
        updated_at_utc: str,
    ) -> bool:
        """Small status primitive used by P4.1 tests and later notification stages."""
        allowed = {"scheduled", "deferred", "sent", "consumed", "expired", "cancelled"}
        if status not in allowed:
            raise ValueError("invalid scheduled slot status")

        def write(connection: sqlite3.Connection) -> bool:
            cursor = connection.execute(
                """UPDATE scheduled_slots
                   SET status = ?, updated_at_utc = ?
                   WHERE slot_id = ?""",
                (status, updated_at_utc, slot_id),
            )
            connection.commit()
            return cursor.rowcount == 1

        return await self._storage._async_writer(write)


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
    user_annotations: UserAnnotationsRepository
    content_reports: ContentReportsRepository
    notification_targets: NotificationTargetsRepository
    scheduler: SchedulerRepository
    settings: SettingsRepository

    @classmethod
    def for_storage(cls, storage: RepositoryStorage) -> StateRepositories:
        return cls(
            profiles=ProfilesRepository(storage),
            tracks=TracksRepository(storage),
            progress=ProgressRepository(storage),
            review_events=ReviewEventsRepository(storage),
            user_annotations=UserAnnotationsRepository(storage),
            content_reports=ContentReportsRepository(storage),
            notification_targets=NotificationTargetsRepository(storage),
            scheduler=SchedulerRepository(storage),
            settings=SettingsRepository(storage),
        )
