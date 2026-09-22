"""Strict version-2 manifest model for signed dataset packages."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any

from ..core.content import ContentModelError, validate_license_id, validate_stable_id

MANIFEST_VERSION = 2
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+-]*$")
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_COUNT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class ManifestError(ValueError):
    """Raised when a manifest does not satisfy the selected envelope version."""


class FileRole(StrEnum):
    """Signed payload roles supported by the V1 package."""

    DATABASE = "database"
    ASSET = "asset"
    LICENSE = "license"


@dataclass(frozen=True, slots=True)
class ManifestFile:
    """One payload file transitively authenticated by the signed manifest."""

    path: str
    size: int
    sha256: str
    role: FileRole


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Stable provenance for one exact upstream source snapshot."""

    source_id: str
    snapshot_id: str
    upstream_version: str
    upstream_date: str | None
    retrieved_at: datetime
    source_url: str
    sha256: str
    adapter_version: str


@dataclass(frozen=True, slots=True)
class LicenseReference:
    """A registry license and its signed attribution/license payload."""

    license_id: str
    path: str


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """Immutable parsed representation of a manifest-version-2 document."""

    manifest_version: int
    dataset_id: str
    dataset_version: str
    built_at: datetime
    content_schema_version: int
    minimum_locklearn_version: str
    build_tool_version: str
    signing_key_id: str
    sources: tuple[SourceReference, ...]
    licenses: tuple[LicenseReference, ...]
    item_counts: Mapping[str, int]
    added_count: int
    changed_count: int
    removed_count: int
    asset_count: int
    entry_count: int
    required_free_disk: int
    canonical_content_hash: str
    files: tuple[ManifestFile, ...]


_TOP_LEVEL_FIELDS = frozenset(DatasetManifest.__dataclass_fields__)
_FILE_FIELDS = frozenset({"path", "size", "sha256", "role"})
_SOURCE_FIELDS = frozenset(
    {
        "source_id",
        "snapshot_id",
        "upstream_version",
        "upstream_date",
        "retrieved_at",
        "source_url",
        "sha256",
        "adapter_version",
    }
)
_LICENSE_FIELDS = frozenset({"license_id", "path"})


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _object(value: object, *, field: str, fields: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object")
    actual = frozenset(value)
    if actual != fields:
        missing = sorted(fields - actual)
        unknown = sorted(actual - fields)
        raise ManifestError(f"{field} fields mismatch; missing={missing}, unknown={unknown}")
    return value


def _string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{field} must be a non-empty string")
    return value


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ManifestError(f"{field} must be an integer >= {minimum}")
    return value


def _sha256(value: object, *, field: str) -> str:
    text = _string(value, field=field)
    if not _SHA256_RE.fullmatch(text):
        raise ManifestError(f"{field} must be a lowercase SHA-256 hex digest")
    return text


def _timestamp(value: object, *, field: str) -> datetime:
    text = _string(value, field=field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as err:
        raise ManifestError(f"{field} must be an RFC 3339 timestamp") from err
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ManifestError(f"{field} must include a UTC offset")
    return parsed.astimezone(UTC)


def _stable_id(value: object, *, field: str) -> str:
    text = _string(value, field=field)
    try:
        return validate_stable_id(text, field=field)
    except ContentModelError as err:
        raise ManifestError(str(err)) from err


def _license_id(value: object, *, field: str) -> str:
    text = _string(value, field=field)
    try:
        return validate_license_id(text)
    except ContentModelError as err:
        raise ManifestError(f"{field}: {err}") from err


def _version(value: object, *, field: str) -> str:
    text = _string(value, field=field)
    if not _VERSION_RE.fullmatch(text):
        raise ManifestError(f"{field} contains unsupported characters")
    return text


def _list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ManifestError(f"{field} must be an array")
    return value


def parse_manifest(raw: bytes) -> DatasetManifest:
    """Parse exact manifest bytes without changing the bytes used for signature verification."""
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ManifestError("manifest.json must be valid UTF-8 JSON") from err
    root = _object(document, field="manifest", fields=_TOP_LEVEL_FIELDS)

    manifest_version = _integer(root["manifest_version"], field="manifest_version", minimum=1)
    if manifest_version != MANIFEST_VERSION:
        raise ManifestError(f"unsupported manifest_version: {manifest_version}")

    sources = tuple(
        _parse_source(value, index)
        for index, value in enumerate(_list(root["sources"], field="sources"))
    )
    licenses = tuple(
        _parse_license(value, index)
        for index, value in enumerate(_list(root["licenses"], field="licenses"))
    )
    files = tuple(
        _parse_file(value, index) for index, value in enumerate(_list(root["files"], field="files"))
    )
    if not sources:
        raise ManifestError("sources must contain at least one provenance record")
    if not licenses:
        raise ManifestError("licenses must contain at least one license record")
    if not files:
        raise ManifestError("files must contain signed payloads")
    _require_unique((item.source_id for item in sources), field="source_id")
    _require_unique((item.snapshot_id for item in sources), field="snapshot_id")
    _require_unique((item.license_id for item in licenses), field="license_id")
    _require_unique((item.path for item in licenses), field="license path")
    _require_unique((item.path for item in files), field="file path")

    item_counts_value = root["item_counts"]
    if not isinstance(item_counts_value, dict):
        raise ManifestError("item_counts must be an object")
    item_counts: dict[str, int] = {}
    for key, value in item_counts_value.items():
        if not _COUNT_KEY_RE.fullmatch(key):
            raise ManifestError(f"invalid item_counts key: {key!r}")
        item_counts[key] = _integer(value, field=f"item_counts.{key}")

    asset_count = _integer(root["asset_count"], field="asset_count")
    entry_count = _integer(root["entry_count"], field="entry_count")
    if asset_count != sum(item.role is FileRole.ASSET for item in files):
        raise ManifestError("asset_count does not match files[]")
    if entry_count != len(files):
        raise ManifestError("entry_count does not match files[]")
    database_files = [item for item in files if item.role is FileRole.DATABASE]
    if len(database_files) != 1 or database_files[0].path != "dataset.db":
        raise ManifestError("files[] must declare dataset.db as its single database")

    license_files = {item.path for item in files if item.role is FileRole.LICENSE}
    if {item.path for item in licenses} != license_files:
        raise ManifestError("licenses[] must reference every and only license-role file")

    key_id = _string(root["signing_key_id"], field="signing_key_id")
    if not _KEY_ID_RE.fullmatch(key_id):
        raise ManifestError("signing_key_id contains unsupported characters")

    return DatasetManifest(
        manifest_version=manifest_version,
        dataset_id=_stable_id(root["dataset_id"], field="dataset_id"),
        dataset_version=_version(root["dataset_version"], field="dataset_version"),
        built_at=_timestamp(root["built_at"], field="built_at"),
        content_schema_version=_integer(
            root["content_schema_version"], field="content_schema_version", minimum=1
        ),
        minimum_locklearn_version=_version(
            root["minimum_locklearn_version"], field="minimum_locklearn_version"
        ),
        build_tool_version=_version(root["build_tool_version"], field="build_tool_version"),
        signing_key_id=key_id,
        sources=sources,
        licenses=licenses,
        item_counts=MappingProxyType(item_counts),
        added_count=_integer(root["added_count"], field="added_count"),
        changed_count=_integer(root["changed_count"], field="changed_count"),
        removed_count=_integer(root["removed_count"], field="removed_count"),
        asset_count=asset_count,
        entry_count=entry_count,
        required_free_disk=_integer(root["required_free_disk"], field="required_free_disk"),
        canonical_content_hash=_sha256(
            root["canonical_content_hash"], field="canonical_content_hash"
        ),
        files=files,
    )


def _parse_file(value: object, index: int) -> ManifestFile:
    row = _object(value, field=f"files[{index}]", fields=_FILE_FIELDS)
    path = _payload_path(row["path"], field=f"files[{index}].path")
    try:
        role = FileRole(_string(row["role"], field=f"files[{index}].role"))
    except ValueError as err:
        raise ManifestError(f"files[{index}].role is unsupported") from err
    if role is FileRole.DATABASE and path != "dataset.db":
        raise ManifestError("database role is reserved for dataset.db")
    if role is FileRole.ASSET and not path.startswith("assets/"):
        raise ManifestError("asset files must be below assets/")
    if role is FileRole.LICENSE and not path.startswith("LICENSES/"):
        raise ManifestError("license files must be below LICENSES/")
    return ManifestFile(
        path=path,
        size=_integer(row["size"], field=f"files[{index}].size"),
        sha256=_sha256(row["sha256"], field=f"files[{index}].sha256"),
        role=role,
    )


def _parse_source(value: object, index: int) -> SourceReference:
    row = _object(value, field=f"sources[{index}]", fields=_SOURCE_FIELDS)
    return SourceReference(
        source_id=_stable_id(row["source_id"], field=f"sources[{index}].source_id"),
        snapshot_id=_stable_id(row["snapshot_id"], field=f"sources[{index}].snapshot_id"),
        upstream_version=_string(
            row["upstream_version"], field=f"sources[{index}].upstream_version"
        ),
        upstream_date=(
            None
            if row["upstream_date"] is None
            else _string(row["upstream_date"], field=f"sources[{index}].upstream_date")
        ),
        retrieved_at=_timestamp(row["retrieved_at"], field=f"sources[{index}].retrieved_at"),
        source_url=_string(row["source_url"], field=f"sources[{index}].source_url"),
        sha256=_sha256(row["sha256"], field=f"sources[{index}].sha256"),
        adapter_version=_version(
            row["adapter_version"], field=f"sources[{index}].adapter_version"
        ),
    )


def _parse_license(value: object, index: int) -> LicenseReference:
    row = _object(value, field=f"licenses[{index}]", fields=_LICENSE_FIELDS)
    return LicenseReference(
        license_id=_license_id(row["license_id"], field=f"licenses[{index}].license_id"),
        path=_payload_path(row["path"], field=f"licenses[{index}].path"),
    )


def _payload_path(value: object, *, field: str) -> str:
    text = _string(value, field=field)
    if "\x00" in text or "\\" in text:
        raise ManifestError(f"{field} must be a normalized POSIX path")
    if text.startswith("/") or (len(text) >= 2 and text[0].isalpha() and text[1] == ":"):
        raise ManifestError(f"{field} must be relative")
    path = PurePosixPath(text)
    if any(part in {"", ".", ".."} for part in path.parts) or path.as_posix() != text:
        raise ManifestError(f"{field} must be a normalized relative path")
    return text


def _require_unique(values: Iterable[str], *, field: str) -> None:
    sequence = list(values)
    if len(sequence) != len(set(sequence)):
        raise ManifestError(f"duplicate logical {field}")


def serialize_manifest(manifest: DatasetManifest) -> bytes:
    """Build deterministic UTF-8 JSON bytes suitable for detached signing."""
    document: dict[str, Any] = {
        "manifest_version": manifest.manifest_version,
        "dataset_id": manifest.dataset_id,
        "dataset_version": manifest.dataset_version,
        "built_at": manifest.built_at.isoformat().replace("+00:00", "Z"),
        "content_schema_version": manifest.content_schema_version,
        "minimum_locklearn_version": manifest.minimum_locklearn_version,
        "build_tool_version": manifest.build_tool_version,
        "signing_key_id": manifest.signing_key_id,
        "sources": [
            {
                "source_id": source.source_id,
                "snapshot_id": source.snapshot_id,
                "upstream_version": source.upstream_version,
                "upstream_date": source.upstream_date,
                "retrieved_at": source.retrieved_at.isoformat().replace("+00:00", "Z"),
                "source_url": source.source_url,
                "sha256": source.sha256,
                "adapter_version": source.adapter_version,
            }
            for source in manifest.sources
        ],
        "licenses": [
            {"license_id": license_ref.license_id, "path": license_ref.path}
            for license_ref in manifest.licenses
        ],
        "item_counts": dict(manifest.item_counts),
        "added_count": manifest.added_count,
        "changed_count": manifest.changed_count,
        "removed_count": manifest.removed_count,
        "asset_count": manifest.asset_count,
        "entry_count": manifest.entry_count,
        "required_free_disk": manifest.required_free_disk,
        "canonical_content_hash": manifest.canonical_content_hash,
        "files": [
            {"path": item.path, "size": item.size, "sha256": item.sha256, "role": item.role}
            for item in manifest.files
        ],
    }
    return (
        json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()
