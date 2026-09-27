"""Secure profile export/import transport and mapping for P6.4."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import math
import os
import secrets
import shutil
import sqlite3
import stat
import tempfile
import uuid
import zipfile
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .const import CONTENT_SCHEMA_VERSION, DB_SCHEMA_VERSION, INTEGRATION_VERSION
from .core.profiles import ProfileValidationError, _validate_profile_settings
from .storage import SQLiteStorage

PROFILE_EXPORT_SCHEMA_VERSION = 1
_EXPORT_TTL = timedelta(minutes=5)
_IMPORT_TTL = timedelta(minutes=15)
_MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
_MAX_MEMBER_BYTES = 32 * 1024 * 1024
_MAX_TOTAL_UNCOMPRESSED = 128 * 1024 * 1024
_MAX_EXPANSION_RATIO = 100.0
_ALLOWED_MEMBERS = frozenset(
    {
        "manifest.json",
        "profile.json",
        "tracks.json",
        "progress.json",
        "annotations.json",
        "stats.json",
        "reviews.json",
        "sessions.json",
    }
)
_REQUIRED_MEMBERS = frozenset(
    {
        "manifest.json",
        "profile.json",
        "tracks.json",
        "progress.json",
        "annotations.json",
        "stats.json",
    }
)


class ProfileTransferError(RuntimeError):
    """Raised when a private profile transfer cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class PrivateTransfer:
    token: str
    path: Path
    owner_user_id: str
    profile_id: str | None
    expires_at: datetime
    filename: str


class ProfileTransferStore:
    """Private temporary transfer storage with owner-bound ephemeral capabilities."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._exports: dict[str, PrivateTransfer] = {}
        self._imports: dict[str, PrivateTransfer] = {}
        self._claimed_imports: set[str] = set()
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task[None] | None = None

    @classmethod
    def private_runtime_root(cls, config_dir: str) -> ProfileTransferStore:
        """Place private transfers outside HA config/backup storage."""
        namespace = hashlib.sha256(config_dir.encode("utf-8")).hexdigest()[:16]
        temp_root = Path(tempfile.gettempdir()).resolve()
        config_root = Path(config_dir).resolve()
        root = temp_root / "locklearn-private" / namespace
        try:
            root.resolve().relative_to(config_root)
        except ValueError:
            return cls(root)
        raise ProfileTransferError(
            "private transfer storage must be outside the HA config directory"
        )

    async def async_initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)
        self._cleanup_task = asyncio.create_task(
            self._async_cleanup_loop(),
            name="locklearn-private-transfer-cleanup",
        )

    async def async_close(self) -> None:
        """Cancel expiry maintenance and remove every private transfer."""
        task = self._cleanup_task
        self._cleanup_task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        async with self._lock:
            self._exports.clear()
            self._imports.clear()
            self._claimed_imports.clear()
        await asyncio.to_thread(shutil.rmtree, self.root, True)

    async def _async_cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(60)
            async with self._lock:
                await self._async_cleanup_locked()

    def _initialize_sync(self) -> None:
        try:
            mode = self.root.lstat()
        except FileNotFoundError:
            mode = None
        if mode is not None and (stat.S_ISLNK(mode.st_mode) or not stat.S_ISDIR(mode.st_mode)):
            raise ProfileTransferError("private transfer root is not a real directory")
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        for candidate in self.root.iterdir():
            if candidate.is_file() or candidate.is_symlink():
                candidate.unlink(missing_ok=True)
            elif candidate.is_dir():
                shutil.rmtree(candidate, ignore_errors=True)

    async def async_create_export(
        self,
        *,
        owner_user_id: str,
        profile_id: str,
        archive_bytes: bytes,
        filename: str,
    ) -> PrivateTransfer:
        async with self._lock:
            await self._async_cleanup_locked()
            token = secrets.token_urlsafe(32)
            path = self.root / f"export-{uuid.uuid4().hex}.zip"
            await asyncio.to_thread(_write_private_file, path, archive_bytes)
            record = PrivateTransfer(
                token=token,
                path=path,
                owner_user_id=owner_user_id,
                profile_id=profile_id,
                expires_at=datetime.now(UTC) + _EXPORT_TTL,
                filename=filename,
            )
            self._exports[token] = record
            return record

    async def async_store_import(
        self,
        *,
        owner_user_id: str,
        archive_bytes: bytes,
    ) -> PrivateTransfer:
        if len(archive_bytes) > _MAX_ARCHIVE_BYTES:
            raise ProfileTransferError("profile import archive exceeds the size limit")
        async with self._lock:
            await self._async_cleanup_locked()
            token = secrets.token_urlsafe(32)
            path = self.root / f"import-{uuid.uuid4().hex}.zip"
            await asyncio.to_thread(_write_private_file, path, archive_bytes)
            record = PrivateTransfer(
                token=token,
                path=path,
                owner_user_id=owner_user_id,
                profile_id=None,
                expires_at=datetime.now(UTC) + _IMPORT_TTL,
                filename="profile-import.zip",
            )
            self._imports[token] = record
            return record

    async def async_consume_export(
        self,
        token: str,
        owner_user_id: str,
    ) -> tuple[PrivateTransfer, bytes] | None:
        """Consume one owner-bound export capability exactly once."""
        async with self._lock:
            await self._async_cleanup_locked()
            record = self._exports.get(token)
            if record is None or record.owner_user_id != owner_user_id:
                return None
            try:
                data = await asyncio.to_thread(record.path.read_bytes)
            except OSError:
                self._exports.pop(token, None)
                return None
            self._exports.pop(token, None)
            await asyncio.to_thread(record.path.unlink, missing_ok=True)
            return record, data

    async def async_resolve_import(
        self,
        token: str,
        owner_user_id: str,
    ) -> PrivateTransfer | None:
        async with self._lock:
            await self._async_cleanup_locked()
            record = self._imports.get(token)
            if (
                record is None
                or record.owner_user_id != owner_user_id
                or token in self._claimed_imports
            ):
                return None
            return record

    async def async_claim_import(
        self,
        token: str,
        owner_user_id: str,
    ) -> PrivateTransfer | None:
        """Claim one import upload so concurrent apply operations cannot duplicate it."""
        async with self._lock:
            await self._async_cleanup_locked()
            record = self._imports.get(token)
            if (
                record is None
                or record.owner_user_id != owner_user_id
                or token in self._claimed_imports
            ):
                return None
            self._claimed_imports.add(token)
            return record

    async def async_delete_import(self, token: str, owner_user_id: str) -> None:
        async with self._lock:
            record = self._imports.get(token)
            if record is None or record.owner_user_id != owner_user_id:
                return
            self._imports.pop(token, None)
            self._claimed_imports.discard(token)
            await asyncio.to_thread(record.path.unlink, missing_ok=True)

    async def async_purge_profile(self, profile_id: str) -> None:
        async with self._lock:
            doomed = [
                token for token, record in self._exports.items() if record.profile_id == profile_id
            ]
            for token in doomed:
                record = self._exports.pop(token)
                await asyncio.to_thread(record.path.unlink, missing_ok=True)

    async def _async_cleanup_locked(self) -> None:
        now = datetime.now(UTC)
        expired: list[PrivateTransfer] = []
        for registry in (self._exports, self._imports):
            for token, record in tuple(registry.items()):
                if record.expires_at <= now or not record.path.is_file():
                    registry.pop(token, None)
                    self._claimed_imports.discard(token)
                    expired.append(record)
        for record in expired:
            await asyncio.to_thread(record.path.unlink, missing_ok=True)


@dataclass(frozen=True, slots=True)
class ImportDryRun:
    source_profile_name: str
    source_profile_id: str
    track_count: int
    progress_count: int
    review_count: int
    session_count: int
    missing_pack_count: int
    missing_card_count: int
    mapping_strategy: str
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "source_profile_name": self.source_profile_name,
            "source_profile_id": self.source_profile_id,
            "track_count": self.track_count,
            "progress_count": self.progress_count,
            "review_count": self.review_count,
            "session_count": self.session_count,
            "missing_pack_count": self.missing_pack_count,
            "missing_card_count": self.missing_card_count,
            "mapping_strategy": self.mapping_strategy,
            "warnings": list(self.warnings),
        }


class ProfileTransferService:
    """Build, validate, dry-run and apply versioned Profile archives."""

    def __init__(self, storage: SQLiteStorage, store: ProfileTransferStore) -> None:
        self.storage = storage
        self.store = store

    async def async_create_export(
        self,
        *,
        profile_id: str,
        owner_user_id: str,
        include_reviews: bool,
        include_sessions: bool,
    ) -> PrivateTransfer:
        payload = await self.storage._async_reader(
            lambda connection: _export_profile_rows(
                connection,
                profile_id,
                include_reviews=include_reviews,
                include_sessions=include_sessions,
            )
        )
        archive = await asyncio.to_thread(_build_archive, payload)
        safe_name = _safe_filename(str(payload["profile"]["name"]))
        return await self.store.async_create_export(
            owner_user_id=owner_user_id,
            profile_id=profile_id,
            archive_bytes=archive,
            filename=f"locklearn-{safe_name}.zip",
        )

    async def async_dry_run_import(
        self,
        *,
        upload_token: str,
        owner_user_id: str,
    ) -> ImportDryRun:
        record = await self.store.async_resolve_import(upload_token, owner_user_id)
        if record is None:
            raise ProfileTransferError("profile import upload is unavailable or expired")
        document = await asyncio.to_thread(_read_archive, record.path)
        return await self._async_dry_run_document(document)

    async def _async_dry_run_document(self, document: dict[str, Any]) -> ImportDryRun:
        tracks = _require_list(document, "tracks")
        progress = _require_list(document, "progress")
        reviews = _optional_list(document, "reviews")
        sessions_document = document.get("sessions")
        sessions = (
            []
            if sessions_document is None
            else _require_object(sessions_document, "sessions").get("sessions", [])
        )
        if not isinstance(sessions, list):
            raise ProfileTransferError("sessions.sessions must be an array")

        pack_ids = {
            str(row["pack_version_id"])
            for row in tracks
            if isinstance(row, dict) and isinstance(row.get("pack_version_id"), str)
        }
        card_ids = {
            str(row["card_key"])
            for row in progress
            if isinstance(row, dict) and isinstance(row.get("card_key"), str)
        }

        def inspect(connection: sqlite3.Connection) -> tuple[set[str], set[str]]:
            existing_packs = {
                str(row[0])
                for row in connection.execute(
                    "SELECT pack_version_id FROM content.pack_versions"
                ).fetchall()
                if str(row[0]) in pack_ids
            }
            existing_cards = {
                str(row[0])
                for row in connection.execute(
                    "SELECT card_key FROM content.card_definitions"
                ).fetchall()
                if str(row[0]) in card_ids
            }
            return existing_packs, existing_cards

        existing_packs, existing_cards = await self.storage._async_reader(inspect)
        profile = _require_object(document.get("profile"), "profile")
        warnings: list[str] = [
            "Home Assistant ACL members and notification targets are never imported.",
            "The imported Profile is archived until explicitly reactivated.",
        ]
        missing_packs = pack_ids - existing_packs
        missing_cards = card_ids - existing_cards
        if missing_packs:
            warnings.append(
                "Tracks referencing unavailable pack versions are imported archived without a pack binding."
            )
        if missing_cards:
            warnings.append(
                "Progress for unavailable cards is preserved as removed-content tombstones."
            )
        return ImportDryRun(
            source_profile_name=str(profile.get("name", "Imported Profile")),
            source_profile_id=str(profile.get("profile_id", "")),
            track_count=len(tracks),
            progress_count=len(progress),
            review_count=len(reviews),
            session_count=len(sessions),
            missing_pack_count=len(missing_packs),
            missing_card_count=len(missing_cards),
            mapping_strategy="new_profile_track_session_ids",
            warnings=tuple(warnings),
        )

    async def async_apply_import(
        self,
        *,
        upload_token: str,
        owner_user_id: str,
        name_override: str | None = None,
    ) -> dict[str, object]:
        record = await self.store.async_claim_import(upload_token, owner_user_id)
        if record is None:
            raise ProfileTransferError("profile import upload is unavailable or expired")
        try:
            document = await asyncio.to_thread(_read_archive, record.path)
            dry_run = await self._async_dry_run_document(document)

            tracks = _require_list(document, "tracks")
            progress = _require_list(document, "progress")
            all_card_ids = {
                str(row["card_key"])
                for row in progress
                if isinstance(row, dict) and isinstance(row.get("card_key"), str)
            }
            pack_ids = {
                str(row["pack_version_id"])
                for row in tracks
                if isinstance(row, dict) and isinstance(row.get("pack_version_id"), str)
            }

            def current_content(
                connection: sqlite3.Connection,
            ) -> tuple[dict[str, str], dict[str, str]]:
                cards = {
                    str(row[0]): _content_status(str(row[1]))
                    for row in connection.execute(
                        """SELECT card_key, lifecycle_status
                           FROM content.card_definitions"""
                    ).fetchall()
                    if str(row[0]) in all_card_ids
                }
                generation = connection.execute(
                    "SELECT generation_id FROM content.generation_metadata WHERE singleton = 1"
                ).fetchone()
                generation_id = "" if generation is None else str(generation[0])
                packs = {
                    str(row[0]): generation_id
                    for row in connection.execute(
                        "SELECT pack_version_id FROM content.pack_versions"
                    ).fetchall()
                    if str(row[0]) in pack_ids
                }
                return cards, packs

            existing_cards, pack_generations = await self.storage._async_reader(current_content)
            result = await self.storage._async_writer(
                lambda connection: _import_profile_rows(
                    connection,
                    document,
                    owner_user_id=owner_user_id,
                    existing_cards=existing_cards,
                    pack_generations=pack_generations,
                    name_override=name_override,
                )
            )
            result["dry_run"] = dry_run.as_dict()
            return result
        finally:
            # Apply is deliberately one-shot, including malformed archives and
            # cancelled/failed operations, so an ambiguous DB outcome cannot be retried.
            await self.store.async_delete_import(upload_token, owner_user_id)


def _write_private_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _select_dicts(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[object, ...] = (),
) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, params)
    columns = [str(item[0]) for item in cursor.description or ()]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _export_profile_rows(
    connection: sqlite3.Connection,
    profile_id: str,
    *,
    include_reviews: bool,
    include_sessions: bool,
) -> dict[str, Any]:
    connection.execute("BEGIN")
    try:
        profiles = _select_dicts(
            connection,
            "SELECT * FROM profiles WHERE profile_id = ?",
            (profile_id,),
        )
        if len(profiles) != 1:
            raise ProfileTransferError("profile does not exist")
        profile = profiles[0]
        profile["settings_json"] = json.loads(str(profile["settings_json"]))

        tracks = _select_dicts(
            connection,
            """SELECT t.*, binding.pack_version_id
               FROM tracks AS t
               LEFT JOIN track_pack_versions AS binding ON binding.track_id = t.track_id
               WHERE t.profile_id = ? ORDER BY t.track_id""",
            (profile_id,),
        )
        for track in tracks:
            track["settings_json"] = json.loads(str(track["settings_json"]))
            track_id = str(track["track_id"])
            rules = _select_dicts(
                connection,
                """SELECT rule_id, rule_kind, card_key, prompt_facet_id,
                          answer_facet_id, rule_json, enabled
                   FROM track_card_rules
                   WHERE track_id = ?
                   ORDER BY rule_id""",
                (track_id,),
            )
            for rule in rules:
                rule["rule_json"] = json.loads(str(rule["rule_json"]))
            track["rules"] = rules
            track["weights"] = _select_dicts(
                connection,
                """SELECT content_type, weight
                   FROM track_content_weights
                   WHERE track_id = ?
                   ORDER BY content_type""",
                (track_id,),
            )

        progress = _select_dicts(
            connection,
            "SELECT * FROM progress WHERE profile_id = ? ORDER BY track_id, card_key",
            (profile_id,),
        )
        annotations = _select_dicts(
            connection,
            "SELECT * FROM user_annotations WHERE profile_id = ? ORDER BY annotation_id",
            (profile_id,),
        )
        stats = _select_dicts(
            connection,
            "SELECT * FROM stats_daily WHERE profile_id = ? ORDER BY track_id, local_date",
            (profile_id,),
        )
        reviews = (
            _select_dicts(
                connection,
                "SELECT * FROM review_events WHERE profile_id = ? ORDER BY created_at_utc, id",
                (profile_id,),
            )
            if include_reviews
            else []
        )
        for review in reviews:
            review["pre_state_snapshot"] = json.loads(str(review["pre_state_snapshot"]))
            review["post_state_snapshot"] = json.loads(str(review["post_state_snapshot"]))

        sessions_document: dict[str, object] | None = None
        if include_sessions:
            sessions = _select_dicts(
                connection,
                "SELECT * FROM sessions WHERE profile_id = ? ORDER BY started_at_utc, id",
                (profile_id,),
            )
            for session in sessions:
                session["settings_json"] = json.loads(str(session["settings_json"]))
            session_ids = [str(row["id"]) for row in sessions]
            if session_ids:
                placeholders = ",".join("?" for _ in session_ids)
                items = _select_dicts(
                    connection,
                    f"SELECT * FROM session_items WHERE session_id IN ({placeholders}) ORDER BY session_id, position",
                    tuple(session_ids),
                )
                answers = _select_dicts(
                    connection,
                    f"SELECT * FROM session_answers WHERE session_id IN ({placeholders}) ORDER BY session_id, resulting_version",
                    tuple(session_ids),
                )
                for item in items:
                    item["payload_json"] = json.loads(str(item["payload_json"]))
                for answer in answers:
                    answer["answer_json"] = json.loads(str(answer["answer_json"]))
            else:
                items = []
                answers = []
            sessions_document = {
                "sessions": sessions,
                "items": items,
                "answers": answers,
            }
    finally:
        connection.rollback()

    return {
        "profile": profile,
        "tracks": tracks,
        "progress": progress,
        "annotations": annotations,
        "stats": stats,
        "reviews": reviews if include_reviews else None,
        "sessions": sessions_document,
    }


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _build_archive(payload: dict[str, Any]) -> bytes:
    members: dict[str, bytes] = {
        "profile.json": _json_bytes(payload["profile"]),
        "tracks.json": _json_bytes(payload["tracks"]),
        "progress.json": _json_bytes(payload["progress"]),
        "annotations.json": _json_bytes(payload["annotations"]),
        "stats.json": _json_bytes(payload["stats"]),
    }
    if payload["reviews"] is not None:
        members["reviews.json"] = _json_bytes(payload["reviews"])
    if payload["sessions"] is not None:
        members["sessions.json"] = _json_bytes(payload["sessions"])

    manifest = {
        "schema_version": PROFILE_EXPORT_SCHEMA_VERSION,
        "locklearn_version": INTEGRATION_VERSION,
        "state_schema_version": DB_SCHEMA_VERSION,
        "content_schema_version": CONTENT_SCHEMA_VERSION,
        "exported_at_utc": datetime.now(UTC).isoformat(),
        "source_profile_id": str(payload["profile"]["profile_id"]),
        "members": {
            name: {
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
            for name, data in sorted(members.items())
        },
    }
    members["manifest.json"] = _json_bytes(manifest)

    import io

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, data)
    value = output.getvalue()
    if len(value) > _MAX_ARCHIVE_BYTES:
        raise ProfileTransferError("profile export archive exceeds the size limit")
    return value


def _safe_filename(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-" for character in value
    )
    cleaned = cleaned.strip("-")[:64]
    return cleaned or "profile"


def _inspect_member(info: zipfile.ZipInfo) -> str:
    name = info.filename
    original = info.orig_filename
    if "\x00" in name or "\x00" in original or "\\" in name:
        raise ProfileTransferError("unsafe ZIP member name")
    path = PurePosixPath(name)
    if (
        not name
        or name.startswith("/")
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != name
        or len(path.parts) != 1
    ):
        raise ProfileTransferError("unsafe ZIP member path")
    if name not in _ALLOWED_MEMBERS:
        raise ProfileTransferError(f"unexpected profile archive member: {name}")
    if info.is_dir():
        raise ProfileTransferError("directories are forbidden in profile archives")
    if info.flag_bits & 0x1:
        raise ProfileTransferError("encrypted ZIP members are unsupported")
    if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise ProfileTransferError("unsupported ZIP compression")
    file_type = stat.S_IFMT(info.external_attr >> 16)
    if file_type not in {0, stat.S_IFREG}:
        raise ProfileTransferError("links and special files are forbidden in imports")
    if info.create_system == 0 and info.external_attr & 0x10:
        raise ProfileTransferError("directories are forbidden in profile archives")
    if info.file_size > _MAX_MEMBER_BYTES:
        raise ProfileTransferError("profile archive member exceeds the size limit")
    if info.file_size and not info.compress_size:
        raise ProfileTransferError("invalid zero compressed size")
    if info.compress_size and info.file_size / info.compress_size > _MAX_EXPANSION_RATIO:
        raise ProfileTransferError("profile archive exceeds the expansion-ratio limit")
    return name


def _read_archive(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > _MAX_ARCHIVE_BYTES:
            raise ProfileTransferError("profile import archive exceeds the size limit")
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > len(_ALLOWED_MEMBERS):
                raise ProfileTransferError("profile archive contains too many entries")
            members: dict[str, zipfile.ZipInfo] = {}
            casefolded: set[str] = set()
            total = 0
            for info in infos:
                name = _inspect_member(info)
                if name in members:
                    raise ProfileTransferError("duplicate profile archive member")
                folded = name.casefold()
                if folded in casefolded:
                    raise ProfileTransferError("case-insensitive profile archive member collision")
                casefolded.add(folded)
                members[name] = info
                total += info.file_size
            if total > _MAX_TOTAL_UNCOMPRESSED:
                raise ProfileTransferError("profile archive exceeds the total size limit")
            missing = _REQUIRED_MEMBERS - members.keys()
            if missing:
                raise ProfileTransferError(
                    f"profile archive is missing required members: {sorted(missing)!r}"
                )

            raw_manifest = _read_archive_member(
                archive,
                members["manifest.json"],
                maximum=_MAX_MEMBER_BYTES,
                label="manifest.json",
            )
            manifest = _load_json(raw_manifest, "manifest.json")
            manifest = _require_object(manifest, "manifest")
            if manifest.get("schema_version") != PROFILE_EXPORT_SCHEMA_VERSION:
                raise ProfileTransferError("unsupported profile export schema version")
            declared = _require_object(manifest.get("members"), "manifest.members")
            actual_payload_names = set(members) - {"manifest.json"}
            if set(declared) != actual_payload_names:
                raise ProfileTransferError("profile archive manifest membership mismatch")

            document: dict[str, Any] = {"manifest": manifest}
            for name in sorted(actual_payload_names):
                info = members[name]
                data = _read_archive_member(
                    archive,
                    info,
                    maximum=_MAX_MEMBER_BYTES,
                    label=name,
                )
                declared_member = _require_object(
                    declared.get(name),
                    f"manifest.members.{name}",
                )
                if declared_member.get("size") != len(data):
                    raise ProfileTransferError("profile archive member size mismatch")
                if declared_member.get("sha256") != hashlib.sha256(data).hexdigest():
                    raise ProfileTransferError("profile archive member checksum mismatch")
                document[name[:-5]] = _load_json(data, name)
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, OSError) as err:
        if isinstance(err, ProfileTransferError):
            raise
        raise ProfileTransferError("invalid profile import archive") from err

    _validate_document(document)
    return document


def _read_archive_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    maximum: int,
    label: str,
) -> bytes:
    """Read a ZIP member with an actual decompressed-byte ceiling."""
    try:
        with archive.open(info) as source:
            data = source.read(maximum + 1)
    except (RuntimeError, EOFError, zlib.error, OSError) as err:
        raise ProfileTransferError(f"cannot read profile archive member: {label}") from err
    if len(data) > maximum or len(data) != info.file_size:
        raise ProfileTransferError(f"profile archive member size mismatch: {label}")
    return data


def _require_object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProfileTransferError(f"{field} must be an object")
    return value


def _load_json(data: bytes, field: str) -> object:
    """Decode strict JSON; Python's permissive NaN/Infinity extensions are rejected."""
    try:
        return json.loads(
            data,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ProfileTransferError(f"{field} contains a non-finite JSON number: {value}")
            ),
        )
    except ProfileTransferError:
        raise
    except json.JSONDecodeError as err:
        raise ProfileTransferError(f"{field} is not valid JSON") from err


_INSTALLATION_BINDING_KEYS = frozenset(
    {
        "device_registry_id",
        "entity_binding",
        "entity_bindings",
        "entity_id",
        "entity_ids",
        "notify_service",
        "receptive_when",
        "routine_trigger",
        "routine_triggers",
        "target_id",
        "target_ids",
    }
)


def _strip_installation_bindings(value: object) -> object:
    """Remove HA-installation capabilities from imported configuration JSON."""
    if isinstance(value, dict):
        return {
            str(key): _strip_installation_bindings(item)
            for key, item in value.items()
            if str(key) not in _INSTALLATION_BINDING_KEYS
        }
    if isinstance(value, list):
        return [_strip_installation_bindings(item) for item in value]
    return value


def _content_status(value: str) -> str:
    return value if value in {"active", "removed", "superseded"} else "removed"


def _validate_track_settings(settings: object) -> dict[str, Any]:
    if not isinstance(settings, dict):
        raise ProfileTransferError("track.settings_json must be an object")
    scheduler = settings.get("scheduler")
    if scheduler is not None:
        if not isinstance(scheduler, dict):
            raise ProfileTransferError("track.settings_json.scheduler must be an object")
        unknown = set(scheduler) - {"learning_count", "quiz_count"}
        if unknown:
            raise ProfileTransferError(
                f"track.settings_json.scheduler contains unsupported keys: {sorted(unknown)!r}"
            )
        for field in ("learning_count", "quiz_count"):
            value = scheduler.get(field, 0)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ProfileTransferError(
                    f"track.settings_json.scheduler.{field} must be an integer >= 0"
                )
    return settings


def _require_list(document: dict[str, Any], field: str) -> list[dict[str, Any]]:
    value = document.get(field)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ProfileTransferError(f"{field} must be an array of objects")
    return value


def _optional_list(document: dict[str, Any], field: str) -> list[dict[str, Any]]:
    value = document.get(field)
    if value is None:
        return []
    return _require_list(document, field)


def _validate_document(document: dict[str, Any]) -> None:
    profile = _require_object(document.get("profile"), "profile")
    for field in ("profile_id", "name", "preset", "timezone"):
        if not isinstance(profile.get(field), str) or not str(profile[field]).strip():
            raise ProfileTransferError(f"profile.{field} must be a non-empty string")
    if profile["preset"] not in {"child", "standard", "intensive", "custom"}:
        raise ProfileTransferError("profile.preset is unsupported")
    try:
        ZoneInfo(str(profile["timezone"]))
    except (ValueError, ZoneInfoNotFoundError) as err:
        raise ProfileTransferError("profile.timezone is invalid") from err
    settings = profile.get("settings_json")
    if not isinstance(settings, dict):
        raise ProfileTransferError("profile.settings_json must be an object")
    sanitized_settings = _strip_installation_bindings(settings)
    if not isinstance(sanitized_settings, dict):
        raise ProfileTransferError("profile.settings_json must be an object")
    try:
        _validate_profile_settings(sanitized_settings)
    except ProfileValidationError as err:
        raise ProfileTransferError(f"profile.settings_json is unsupported: {err}") from err
    tracks = _require_list(document, "tracks")
    for index, track in enumerate(tracks):
        settings = track.get("settings_json")
        _validate_track_settings(_strip_installation_bindings(settings))
        weights = track.get("weights", [])
        if not isinstance(weights, list) or any(not isinstance(item, dict) for item in weights):
            raise ProfileTransferError(f"tracks[{index}].weights must be an array of objects")
        parsed_weights: list[float] = []
        for weight in weights:
            content_type = weight.get("content_type")
            value = weight.get("weight")
            if not isinstance(content_type, str) or not content_type.strip():
                raise ProfileTransferError(f"tracks[{index}].weights.content_type is invalid")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ProfileTransferError(f"tracks[{index}].weights.weight is invalid")
            parsed = float(value)
            if not math.isfinite(parsed) or parsed < 0:
                raise ProfileTransferError(f"tracks[{index}].weights.weight is invalid")
            parsed_weights.append(parsed)
        if parsed_weights and not any(value > 0 for value in parsed_weights):
            raise ProfileTransferError(f"tracks[{index}].weights must contain a positive weight")
    _require_list(document, "progress")
    _require_list(document, "annotations")
    _require_list(document, "stats")
    _optional_list(document, "reviews")
    sessions = document.get("sessions")
    if sessions is not None:
        obj = _require_object(sessions, "sessions")
        for field in ("sessions", "items", "answers"):
            value = obj.get(field)
            if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
                raise ProfileTransferError(f"sessions.{field} must be an array of objects")


def _insert_row(
    connection: sqlite3.Connection,
    table: str,
    row: dict[str, Any],
    allowed_columns: frozenset[str],
) -> None:
    columns = [column for column in row if column in allowed_columns]
    if not columns:
        raise ProfileTransferError(f"no importable columns for {table}")
    placeholders = ",".join("?" for _ in columns)
    quoted = ",".join(columns)
    values = [
        json.dumps(row[column], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if (column.endswith("_json") or column in {"pre_state_snapshot", "post_state_snapshot"})
        and not isinstance(row[column], str)
        else row[column]
        for column in columns
    ]
    connection.execute(
        f"INSERT INTO {table}({quoted}) VALUES ({placeholders})",
        tuple(values),
    )


_PROFILE_COLUMNS = frozenset(
    {
        "profile_id",
        "name",
        "preset",
        "timezone",
        "status",
        "settings_json",
        "created_at_utc",
        "updated_at_utc",
    }
)
_TRACK_COLUMNS = frozenset(
    {
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
    }
)


def _import_profile_rows(
    connection: sqlite3.Connection,
    document: dict[str, Any],
    *,
    owner_user_id: str,
    existing_cards: dict[str, str],
    pack_generations: dict[str, str],
    name_override: str | None,
) -> dict[str, object]:
    profile = dict(_require_object(document.get("profile"), "profile"))
    tracks = _require_list(document, "tracks")
    progress = _require_list(document, "progress")
    reviews = _optional_list(document, "reviews")
    annotations = _require_list(document, "annotations")
    stats = _require_list(document, "stats")
    sessions_doc = document.get("sessions")
    sessions_obj = {} if sessions_doc is None else _require_object(sessions_doc, "sessions")
    sessions = sessions_obj.get("sessions", [])
    items = sessions_obj.get("items", [])
    answers = sessions_obj.get("answers", [])
    if not all(isinstance(value, list) for value in (sessions, items, answers)):
        raise ProfileTransferError("invalid sessions document")

    source_profile_id = str(profile["profile_id"])
    new_profile_id = str(uuid.uuid4())
    track_map = {
        str(track["track_id"]): str(uuid.uuid4())
        for track in tracks
        if isinstance(track.get("track_id"), str)
    }
    session_map = {
        str(session["id"]): str(uuid.uuid4())
        for session in sessions
        if isinstance(session, dict) and isinstance(session.get("id"), str)
    }
    now = datetime.now(UTC).isoformat()

    imported_name = (name_override or str(profile["name"])).strip()
    if not imported_name:
        raise ProfileTransferError("imported Profile name must not be empty")

    profile["profile_id"] = new_profile_id
    profile["name"] = imported_name
    profile["status"] = "archived"
    profile["created_at_utc"] = now
    profile["updated_at_utc"] = now
    profile_settings = profile.get("settings_json")
    if isinstance(profile_settings, dict):
        profile_settings = _strip_installation_bindings(profile_settings)
        if not isinstance(profile_settings, dict):
            raise ProfileTransferError("profile.settings_json must be an object")
        profile_settings.pop("_locklearn_personal_profile", None)
        if "allow_unattended_actions" in profile_settings:
            profile_settings["allow_unattended_actions"] = False
        profile["settings_json"] = profile_settings

    try:
        connection.execute("BEGIN IMMEDIATE")
        _insert_row(connection, "profiles", profile, _PROFILE_COLUMNS)
        connection.execute(
            """INSERT INTO profile_members(profile_id, ha_user_id, role, created_at_utc)
               VALUES (?, ?, 'owner', ?)""",
            (new_profile_id, owner_user_id, now),
        )

        imported_track_ids: set[str] = set()
        for raw in tracks:
            source_track_id = str(raw.get("track_id", ""))
            new_track_id = track_map.get(source_track_id)
            if new_track_id is None:
                raise ProfileTransferError("track_id is missing from export")
            track = dict(raw)
            pack_version_id = track.pop("pack_version_id", None)
            raw_rules = track.pop("rules", [])
            raw_weights = track.pop("weights", [])
            if not isinstance(raw_rules, list) or any(
                not isinstance(rule, dict) for rule in raw_rules
            ):
                raise ProfileTransferError("track.rules must be an array of objects")
            if not isinstance(raw_weights, list) or any(
                not isinstance(weight, dict) for weight in raw_weights
            ):
                raise ProfileTransferError("track.weights must be an array of objects")
            track["track_id"] = new_track_id
            track["profile_id"] = new_profile_id
            track["status"] = "archived"
            settings = track.get("settings_json")
            if isinstance(settings, dict):
                settings = _strip_installation_bindings(settings)
                if not isinstance(settings, dict):
                    raise ProfileTransferError("track.settings_json must be an object")
                track["settings_json"] = settings
            _insert_row(connection, "tracks", track, _TRACK_COLUMNS)
            imported_track_ids.add(new_track_id)

            rule_columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(track_card_rules)").fetchall()
            }
            for raw_rule in raw_rules:
                rule = dict(raw_rule)
                rule["track_id"] = new_track_id
                _insert_row(
                    connection,
                    "track_card_rules",
                    rule,
                    frozenset(rule_columns),
                )

            weight_columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(track_content_weights)").fetchall()
            }
            for raw_weight in raw_weights:
                weight = dict(raw_weight)
                weight["track_id"] = new_track_id
                _insert_row(
                    connection,
                    "track_content_weights",
                    weight,
                    frozenset(weight_columns),
                )

            if isinstance(pack_version_id, str) and pack_version_id in pack_generations:
                connection.execute(
                    """INSERT INTO track_pack_versions(
                           track_id, pack_version_id, dataset_generation, integrated_at_utc
                       ) VALUES (?, ?, ?, ?)""",
                    (
                        new_track_id,
                        pack_version_id,
                        pack_generations[pack_version_id],
                        now,
                    ),
                )

        progress_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(progress)").fetchall()
        }
        for raw in progress:
            row = dict(raw)
            source_track = str(row.get("track_id", ""))
            if source_track not in track_map:
                continue
            row["profile_id"] = new_profile_id
            row["track_id"] = track_map[source_track]
            row["content_status"] = existing_cards.get(str(row.get("card_key", "")), "removed")
            _insert_row(connection, "progress", row, frozenset(progress_columns))

        annotation_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(user_annotations)").fetchall()
        }
        for raw in annotations:
            row = dict(raw)
            row["annotation_id"] = str(uuid.uuid4())
            row["profile_id"] = new_profile_id
            _insert_row(
                connection,
                "user_annotations",
                row,
                frozenset(annotation_columns),
            )

        stats_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(stats_daily)").fetchall()
        }
        for raw in stats:
            row = dict(raw)
            source_track = str(row.get("track_id", ""))
            if source_track not in track_map:
                continue
            row["profile_id"] = new_profile_id
            row["track_id"] = track_map[source_track]
            _insert_row(connection, "stats_daily", row, frozenset(stats_columns))

        session_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
        }
        for raw in sessions:
            if not isinstance(raw, dict):
                continue
            source_session = str(raw.get("id", ""))
            row = dict(raw)
            if isinstance(row.get("settings_json"), dict):
                row["settings_json"] = _strip_installation_bindings(row["settings_json"])
            row["id"] = session_map[source_session]
            row["profile_id"] = new_profile_id
            session_track_ref = row.get("track_id")
            row["track_id"] = (
                track_map.get(str(session_track_ref)) if session_track_ref is not None else None
            )
            if row.get("status") == "active":
                row["status"] = "paused"
            _insert_row(connection, "sessions", row, frozenset(session_columns))

        item_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(session_items)").fetchall()
        }
        for raw in items:
            if not isinstance(raw, dict):
                continue
            source_session = str(raw.get("session_id", ""))
            if source_session not in session_map:
                continue
            row = dict(raw)
            row["session_id"] = session_map[source_session]
            _insert_row(connection, "session_items", row, frozenset(item_columns))

        answer_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(session_answers)").fetchall()
        }
        for raw in answers:
            if not isinstance(raw, dict):
                continue
            source_session = str(raw.get("session_id", ""))
            if source_session not in session_map:
                continue
            row = dict(raw)
            row.pop("id", None)
            row["session_id"] = session_map[source_session]
            _insert_row(connection, "session_answers", row, frozenset(answer_columns))

        review_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(review_events)").fetchall()
        }
        for raw in reviews:
            row = dict(raw)
            row["id"] = str(uuid.uuid4())
            row["profile_id"] = new_profile_id
            source_track = str(row.get("track_id", ""))
            if source_track not in track_map:
                continue
            row["track_id"] = track_map[source_track]
            review_session_ref = row.get("session_id")
            row["session_id"] = (
                session_map.get(str(review_session_ref)) if review_session_ref is not None else None
            )
            _insert_row(connection, "review_events", row, frozenset(review_columns))

        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise

    return {
        "profile_id": new_profile_id,
        "status": "archived",
        "source_profile_id": source_profile_id,
        "track_id_map": track_map,
        "session_id_map": session_map,
        "imported_track_count": len(imported_track_ids),
    }
