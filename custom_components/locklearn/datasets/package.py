"""Hostile-archive-safe validation of signed LockLearn dataset packages."""

from __future__ import annotations

import hashlib
import sqlite3
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .manifest import DatasetManifest, parse_manifest
from .policy import OfficialRegistryPolicy
from .trust import KeyUsage, TrustedKey, TrustStore

_MANIFEST_PATH = "manifest.json"
_SIGNATURE_PATH = "SIGNATURE.ed25519"
_DATABASE_PATH = "dataset.db"
_DIRECTORY_ENTRIES = frozenset({"assets/", "LICENSES/"})
_SUPPORTED_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})
_STREAM_CHUNK_SIZE = 1024 * 1024


class DatasetPackageError(ValueError):
    """Base error for structural, payload and SQLite package failures."""


class ArchiveStructureError(DatasetPackageError):
    """Raised before package-controlled bytes are trusted or extracted."""


class PayloadIntegrityError(DatasetPackageError):
    """Raised when a signed payload does not match its manifest declaration."""


class DatasetDatabaseError(DatasetPackageError):
    """Raised when dataset.db is not a self-contained, integral SQLite file."""


@dataclass(frozen=True, slots=True)
class ArchiveLimits:
    """Absolute hostile-input ceilings, not recommended official artifact budgets."""

    max_entries: int
    max_manifest_bytes: int
    max_signature_bytes: int
    max_member_uncompressed: int
    max_total_uncompressed: int
    max_total_compressed: int
    max_expansion_ratio: float


DEFAULT_ARCHIVE_LIMITS = ArchiveLimits(
    max_entries=8192,
    max_manifest_bytes=1024 * 1024,
    max_signature_bytes=64,
    max_member_uncompressed=2 * 1024 * 1024 * 1024,
    max_total_uncompressed=4 * 1024 * 1024 * 1024,
    max_total_compressed=2 * 1024 * 1024 * 1024,
    max_expansion_ratio=1000.0,
)


@dataclass(frozen=True, slots=True)
class ValidatedDatasetPackage:
    """Immutable descriptor returned only after every P1.2 validation stage passes."""

    archive_path: Path
    manifest: DatasetManifest
    signing_key: TrustedKey


def validate_dataset_package(
    archive_path: Path,
    *,
    trust_store: TrustStore,
    policy: OfficialRegistryPolicy,
    limits: ArchiveLimits = DEFAULT_ARCHIVE_LIMITS,
    key_usage: KeyUsage = KeyUsage.HISTORICAL,
) -> ValidatedDatasetPackage:
    """Validate a package without installing or naively extracting its archive."""
    path = archive_path.resolve()
    try:
        with zipfile.ZipFile(path) as archive:
            members = _inspect_archive(archive, limits)
            manifest_bytes = _bounded_read(
                archive,
                members[_MANIFEST_PATH],
                maximum=limits.max_manifest_bytes,
                label=_MANIFEST_PATH,
            )
            signature = _bounded_read(
                archive,
                members[_SIGNATURE_PATH],
                maximum=limits.max_signature_bytes,
                label=_SIGNATURE_PATH,
            )
            manifest = parse_manifest(manifest_bytes)
            signing_key = trust_store.verify(
                key_id=manifest.signing_key_id,
                built_at=manifest.built_at,
                manifest_bytes=manifest_bytes,
                signature=signature,
                usage=key_usage,
            )
            _validate_membership(manifest, members)
            _verify_payloads(archive, manifest, members)
            policy.validate(manifest)
            _verify_sqlite(archive, members[_DATABASE_PATH])
    except zipfile.BadZipFile as err:
        raise ArchiveStructureError("invalid or corrupt ZIP archive") from err
    except OSError as err:
        raise DatasetPackageError(f"cannot read dataset package: {path}") from err
    return ValidatedDatasetPackage(
        archive_path=path,
        manifest=manifest,
        signing_key=signing_key,
    )


def _inspect_archive(archive: zipfile.ZipFile, limits: ArchiveLimits) -> dict[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > limits.max_entries:
        raise ArchiveStructureError("archive exceeds the entry-count safety limit")
    members: dict[str, zipfile.ZipInfo] = {}
    casefolded: set[str] = set()
    total_uncompressed = 0
    total_compressed = 0
    for info in infos:
        name = _validate_member_name(info)
        if name in members:
            raise ArchiveStructureError(f"duplicate ZIP member: {name}")
        folded = name.casefold()
        if folded in casefolded:
            raise ArchiveStructureError(f"case-insensitive ZIP member collision: {name}")
        members[name] = info
        casefolded.add(folded)
        _validate_member_type(info)
        if info.flag_bits & 0x1:
            raise ArchiveStructureError(f"encrypted ZIP members are unsupported: {name}")
        if info.compress_type not in _SUPPORTED_COMPRESSION:
            raise ArchiveStructureError(f"unsupported ZIP compression for: {name}")
        if info.file_size > limits.max_member_uncompressed:
            raise ArchiveStructureError(f"ZIP member exceeds the size safety limit: {name}")
        if info.file_size and not info.compress_size:
            raise ArchiveStructureError(f"invalid zero compressed size for: {name}")
        if info.compress_size and info.file_size / info.compress_size > limits.max_expansion_ratio:
            raise ArchiveStructureError(f"ZIP member exceeds the expansion-ratio limit: {name}")
        total_uncompressed += info.file_size
        total_compressed += info.compress_size
    if total_uncompressed > limits.max_total_uncompressed:
        raise ArchiveStructureError("archive exceeds the total uncompressed-size limit")
    if total_compressed > limits.max_total_compressed:
        raise ArchiveStructureError("archive exceeds the total compressed-size limit")
    for required in (_MANIFEST_PATH, _SIGNATURE_PATH, _DATABASE_PATH):
        if required not in members:
            raise ArchiveStructureError(f"missing required ZIP member: {required}")
        if members[required].is_dir():
            raise ArchiveStructureError(f"required ZIP member is not a file: {required}")
    if members[_MANIFEST_PATH].file_size > limits.max_manifest_bytes:
        raise ArchiveStructureError("manifest.json exceeds its bounded-read limit")
    if members[_SIGNATURE_PATH].file_size != limits.max_signature_bytes:
        raise ArchiveStructureError("SIGNATURE.ed25519 must be a raw 64-byte signature")
    return members


def _validate_member_name(info: zipfile.ZipInfo) -> str:
    original_name = info.orig_filename
    name = info.filename
    if "\x00" in original_name or "\x00" in name:
        raise ArchiveStructureError("NUL is forbidden in ZIP member names")
    if not name or "\\" in name:
        raise ArchiveStructureError(
            f"ZIP member paths must use normalized POSIX separators: {name!r}"
        )
    if name.startswith("/") or (len(name) >= 2 and name[0].isalpha() and name[1] == ":"):
        raise ArchiveStructureError(f"absolute ZIP member path is forbidden: {name}")
    path = PurePosixPath(name)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ArchiveStructureError(f"non-normal ZIP member path is forbidden: {name}")
    normalized = path.as_posix() + ("/" if info.is_dir() else "")
    if normalized != name:
        raise ArchiveStructureError(f"non-normal ZIP member path is forbidden: {name}")
    if info.is_dir():
        if name not in _DIRECTORY_ENTRIES:
            raise ArchiveStructureError(f"unexpected directory entry: {name}")
        return name
    if name in {_MANIFEST_PATH, _SIGNATURE_PATH, _DATABASE_PATH}:
        return name
    if name.startswith("assets/") and len(path.parts) > 1:
        return name
    if name.startswith("LICENSES/") and len(path.parts) > 1:
        return name
    raise ArchiveStructureError(f"unexpected ZIP member path: {name}")


def _validate_member_type(info: zipfile.ZipInfo) -> None:
    if info.create_system != 3:
        return
    file_type = stat.S_IFMT(info.external_attr >> 16)
    allowed_type = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
    if file_type not in {0, allowed_type}:
        raise ArchiveStructureError(f"non-regular ZIP member is forbidden: {info.filename}")


def _bounded_read(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    maximum: int,
    label: str,
) -> bytes:
    try:
        with archive.open(info) as handle:
            value = handle.read(maximum + 1)
    except (RuntimeError, EOFError) as err:
        raise ArchiveStructureError(f"cannot read {label}") from err
    if len(value) > maximum:
        raise ArchiveStructureError(f"{label} exceeds its bounded-read limit")
    return value


def _validate_membership(manifest: DatasetManifest, members: dict[str, zipfile.ZipInfo]) -> None:
    archive_payloads = {
        path
        for path, info in members.items()
        if path not in {_MANIFEST_PATH, _SIGNATURE_PATH} and not info.is_dir()
    }
    declared_payloads = {item.path for item in manifest.files}
    extra = sorted(archive_payloads - declared_payloads)
    missing = sorted(declared_payloads - archive_payloads)
    if extra or missing:
        raise PayloadIntegrityError(
            f"signed payload membership mismatch; extra={extra}, missing={missing}"
        )


def _verify_payloads(
    archive: zipfile.ZipFile,
    manifest: DatasetManifest,
    members: dict[str, zipfile.ZipInfo],
) -> None:
    for declared in manifest.files:
        info = members[declared.path]
        if info.file_size != declared.size:
            raise PayloadIntegrityError(f"payload size mismatch: {declared.path}")
        digest, streamed_size = _stream_digest(archive, info)
        if streamed_size != declared.size:
            raise PayloadIntegrityError(f"streamed payload size mismatch: {declared.path}")
        if digest != declared.sha256:
            raise PayloadIntegrityError(f"payload SHA-256 mismatch: {declared.path}")


def _stream_digest(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    try:
        with archive.open(info) as handle:
            while chunk := handle.read(_STREAM_CHUNK_SIZE):
                digest.update(chunk)
                size += len(chunk)
    except (RuntimeError, EOFError) as err:
        raise PayloadIntegrityError(f"cannot stream payload: {info.filename}") from err
    return digest.hexdigest(), size


def _verify_sqlite(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> None:
    with tempfile.TemporaryDirectory(prefix="locklearn-dataset-") as temporary_directory:
        database_path = Path(temporary_directory) / _DATABASE_PATH
        try:
            with archive.open(info) as source, database_path.open("xb") as destination:
                while chunk := source.read(_STREAM_CHUNK_SIZE):
                    destination.write(chunk)
        except (RuntimeError, EOFError, OSError) as err:
            raise DatasetDatabaseError("cannot stage dataset.db for read-only validation") from err
        uri = f"{database_path.as_uri()}?mode=ro&immutable=1"
        try:
            with sqlite3.connect(uri, uri=True) as connection:
                rows = connection.execute("PRAGMA integrity_check").fetchall()
        except sqlite3.DatabaseError as err:
            raise DatasetDatabaseError(
                "dataset.db is not a valid standalone SQLite database"
            ) from err
        if rows != [("ok",)]:
            raise DatasetDatabaseError(f"dataset.db integrity_check failed: {rows!r}")
