"""Deterministic build-time dataset pipeline.

This module is never imported by Home Assistant runtime. Raw upstream corpora
live only in ignored/temporary build workspaces.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import urllib.request
import zipfile
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.const import CONTENT_SCHEMA_VERSION
from custom_components.locklearn.core.assets import Asset, AssetKind, validate_asset_path
from custom_components.locklearn.core.content import make_stable_id
from custom_components.locklearn.datasets import (
    MANIFEST_VERSION,
    DatasetManifest,
    FileRole,
    LicenseReference,
    ManifestFile,
    OfficialRegistryPolicy,
    SourceReference,
    serialize_manifest,
)
from custom_components.locklearn.storage import (
    ContentGenerationValidator,
    initialize_content_database,
)

from .adapters import NormalizedRecord, SourceAdapter, adapter_for_id

_STREAM_CHUNK_SIZE = 1024 * 1024
_FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_CANONICAL_CONTENT_TABLES = (
    "concepts",
    "terms",
    "concept_terms",
    "learning_items",
    "learning_item_concepts",
    "learning_item_requirements",
    "facets",
    "assets_metadata",
    "facet_assets",
    "card_definitions",
    "card_context_hints",
    "content_blocks",
    "tags",
    "learning_item_tags",
    "packs",
    "pack_versions",
    "pack_items",
    "pack_item_prerequisites",
    "pack_item_unlock_conditions",
    "pack_item_card_defaults",
    "confusable_groups",
    "confusable_group_items",
    "stable_id_migrations",
    "tombstones",
)


class DatasetBuildError(ValueError):
    """Raised when a build-time source or artifact contract is violated."""


@dataclass(frozen=True, slots=True)
class SourceFileInput:
    """One local or fetched raw file belonging to an upstream snapshot."""

    path: Path
    source_url: str

    def __post_init__(self) -> None:
        if not self.source_url:
            raise DatasetBuildError("source file source_url is required")


@dataclass(frozen=True, slots=True)
class SourceInput:
    """Exact upstream source input selected for one dataset build."""

    source_id: str
    upstream_version: str
    retrieved_at: datetime
    files: tuple[SourceFileInput, ...]
    upstream_date: str | None = None
    snapshot_url: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id or not self.upstream_version:
            raise DatasetBuildError("source_id and upstream_version are required")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise DatasetBuildError("source retrieved_at must be timezone-aware")
        if not self.files:
            raise DatasetBuildError("source input must contain at least one raw file")
        if len(self.files) > 1 and not self.snapshot_url:
            raise DatasetBuildError("multi-file source input requires snapshot_url")


@dataclass(frozen=True, slots=True)
class BuildAssetInput:
    """One public media file embedded in a signed dataset package."""

    asset_id: str
    source_id: str
    source_record_id: str
    path: Path
    archive_path: str
    kind: AssetKind
    mime_type: str
    attribution: str
    license_id: str | None = None
    width: int | None = None
    height: int | None = None
    author: str | None = None
    modified_from_source: bool = False

    def __post_init__(self) -> None:
        validate_asset_path(self.archive_path)
        if not self.source_record_id:
            raise DatasetBuildError("asset source_record_id is required")
        if self.author == "":
            raise DatasetBuildError("asset author must be None or non-empty")


@dataclass(frozen=True, slots=True)
class PreparedAsset:
    """Validated asset bytes plus package metadata derived from those exact bytes."""

    metadata: Asset
    source_id: str
    source_record_id: str
    author: str | None
    modified_from_source: bool
    source_path: Path


@dataclass(frozen=True, slots=True)
class NormalizedSource:
    """Canonical intermediate representation plus exact source snapshot facts."""

    source_id: str
    snapshot_id: str
    upstream_version: str
    upstream_date: str | None
    retrieved_at: datetime
    source_url: str
    raw_sha256: str
    adapter_version: str
    normalized_path: Path
    normalized_sha256: str
    record_count: int


@dataclass(frozen=True, slots=True)
class DatasetBuildSpec:
    """Versioned inputs for one reproducible dataset build."""

    dataset_id: str
    dataset_version: str
    built_at: datetime
    minimum_locklearn_version: str
    build_tool_version: str
    signing_key_id: str
    sources: tuple[SourceInput, ...]
    assets: tuple[BuildAssetInput, ...] = ()
    added_count: int = 0
    changed_count: int = 0
    removed_count: int = 0
    required_free_disk: int = 0

    def __post_init__(self) -> None:
        if self.built_at.tzinfo is None or self.built_at.utcoffset() is None:
            raise DatasetBuildError("dataset built_at must be timezone-aware")
        if not self.sources:
            raise DatasetBuildError("dataset build requires at least one source")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise DatasetBuildError("dataset build source_id values must be unique")
        asset_ids = [asset.asset_id for asset in self.assets]
        asset_paths = [asset.archive_path for asset in self.assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise DatasetBuildError("dataset asset_id values must be unique")
        if len(asset_paths) != len(set(asset_paths)):
            raise DatasetBuildError("dataset asset paths must be unique")
        if any(asset.source_id not in source_ids for asset in self.assets):
            raise DatasetBuildError("every asset source_id must be declared in sources")
        for count in (
            self.added_count,
            self.changed_count,
            self.removed_count,
            self.required_free_disk,
        ):
            if count < 0:
                raise DatasetBuildError("dataset build counts cannot be negative")


@dataclass(frozen=True, slots=True)
class DatasetBuildResult:
    """Output of a complete local build and signing pass."""

    archive_path: Path
    archive_sha256_path: Path
    manifest: DatasetManifest
    canonical_content_hash: str
    normalized_sources: tuple[NormalizedSource, ...]


class DatasetRecipe(Protocol):
    """Map normalized source records into LockLearn domain tables."""

    recipe_id: str
    recipe_version: str

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        """Populate domain tables and return manifest item counts."""
        ...


@dataclass(frozen=True, slots=True)
class BuildContext:
    """Read-only recipe view over normalized records and snapshot identities."""

    dataset_id: str
    normalized_sources: Mapping[str, NormalizedSource]

    def iter_records(self, source_id: str) -> Iterator[NormalizedRecord]:
        """Read one source's canonical normalized JSONL without buffering it."""
        try:
            normalized = self.normalized_sources[source_id]
        except KeyError as err:
            raise DatasetBuildError(f"recipe requested undeclared source: {source_id}") from err
        with normalized.normalized_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise DatasetBuildError(
                        f"normalized record line {line_number} for {source_id} is invalid"
                    )
                yield NormalizedRecord(
                    source_id=str(value["source_id"]),
                    source_record_id=str(value["source_record_id"]),
                    kind=str(value["kind"]),
                    payload=dict(value["payload"]),
                    author=_optional_string(value.get("author")),
                    language=_optional_string(value.get("language")),
                    license_id=_optional_string(value.get("license_id")),
                    modified_from_source=bool(value.get("modified_from_source", False)),
                )

    def insert_provenance(
        self,
        connection: sqlite3.Connection,
        *,
        record: NormalizedRecord,
        object_type: str,
        object_id: str,
        license_scope: str,
        attribution_text: str | None = None,
    ) -> str:
        """Attach a materialized object to the exact source snapshot used."""
        normalized = self.normalized_sources.get(record.source_id)
        if normalized is None:
            raise DatasetBuildError(f"provenance source is not declared: {record.source_id}")
        row = connection.execute(
            "SELECT license_id, attribution_template FROM sources WHERE source_id = ?",
            (record.source_id,),
        ).fetchone()
        if row is None:
            raise DatasetBuildError(f"source metadata is missing: {record.source_id}")
        default_license_id = str(row[0])
        license_id = record.license_id or default_license_id
        declared = connection.execute(
            """SELECT 1 FROM dataset_licenses
               WHERE dataset_id = ? AND license_id = ? AND license_scope = ?""",
            (self.dataset_id, license_id, license_scope),
        ).fetchone()
        if declared is None:
            raise DatasetBuildError(
                f"provenance license/scope is not declared: {license_id}/{license_scope}"
            )
        provenance_id = make_stable_id(
            "locklearn",
            "provenance",
            self.dataset_id,
            record.source_id,
            object_type,
            object_id,
            record.source_record_id,
        )
        connection.execute(
            """INSERT INTO provenance_records(
                   provenance_id, dataset_id, object_type, object_id,
                   source_snapshot_id, license_id, license_scope,
                   source_record_id, author, language_tag,
                   modified_from_source, attribution_text
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                provenance_id,
                self.dataset_id,
                object_type,
                object_id,
                normalized.snapshot_id,
                license_id,
                license_scope,
                record.source_record_id,
                record.author,
                record.language,
                int(record.modified_from_source),
                attribution_text,
            ),
        )
        return provenance_id


def fetch_snapshot(
    url: str,
    destination: Path,
    *,
    maximum_bytes: int,
    timeout_seconds: float = 120.0,
) -> str:
    """Fetch one raw snapshot atomically into an ignored/temporary workspace."""
    if maximum_bytes <= 0:
        raise DatasetBuildError("maximum_bytes must be positive")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part")
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(url, headers={"User-Agent": "LockLearn-dataset-build/1"})
    try:
        with (
            urllib.request.urlopen(request, timeout=timeout_seconds) as source,
            temporary.open("wb") as target,
        ):
            while chunk := source.read(_STREAM_CHUNK_SIZE):
                size += len(chunk)
                if size > maximum_bytes:
                    raise DatasetBuildError(f"source download exceeds maximum_bytes: {url}")
                target.write(chunk)
                digest.update(chunk)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return digest.hexdigest()


def normalize_source(
    source: SourceInput,
    workspace: Path,
    *,
    repository_root: Path,
) -> NormalizedSource:
    """Normalize one exact upstream source into canonical JSONL."""
    source_rows = _source_registry(repository_root)
    row = source_rows.get(source.source_id)
    if row is None:
        raise DatasetBuildError(f"unknown source registry ID: {source.source_id}")
    adapter_id = _required_string(row, "adapter_id")
    adapter = adapter_for_id(adapter_id)
    if adapter.source_id != source.source_id:
        raise DatasetBuildError("adapter source_id does not match registry source_id")

    policy = OfficialRegistryPolicy.from_repository(repository_root)
    policy.validate_import_fields(source.source_id, set(adapter.emitted_fields))
    policy.validate_provenance_fields(source.source_id, set(adapter.provenance_fields))

    raw_sha = _aggregate_source_sha(source.files)
    snapshot_id = make_stable_id("locklearn", "snapshot", source.source_id, raw_sha)
    normalized_path = workspace / "normalized" / f"{_safe_name(source.source_id)}.jsonl"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_digest = hashlib.sha256()
    record_count = 0
    with normalized_path.open("w", encoding="utf-8", newline="\n") as stream:
        for raw_file in sorted(source.files, key=lambda item: (item.source_url, item.path.name)):
            if not raw_file.path.is_file():
                raise DatasetBuildError(f"source input file does not exist: {raw_file.path}")
            for record in adapter.normalize(raw_file.path):
                if record.source_id != source.source_id:
                    raise DatasetBuildError("adapter emitted a record for the wrong source")
                _validate_record_provenance(adapter, record)
                line = _canonical_record_line(record)
                stream.write(line)
                normalized_digest.update(line.encode("utf-8"))
                record_count += 1
        stream.flush()
        os.fsync(stream.fileno())

    if record_count == 0:
        raise DatasetBuildError(f"adapter emitted no records for source: {source.source_id}")
    source_url = source.snapshot_url or source.files[0].source_url
    return NormalizedSource(
        source_id=source.source_id,
        snapshot_id=snapshot_id,
        upstream_version=source.upstream_version,
        upstream_date=source.upstream_date,
        retrieved_at=source.retrieved_at.astimezone(UTC),
        source_url=source_url,
        raw_sha256=raw_sha,
        adapter_version=adapter.adapter_version,
        normalized_path=normalized_path,
        normalized_sha256=normalized_digest.hexdigest(),
        record_count=record_count,
    )


def build_dataset(
    spec: DatasetBuildSpec,
    recipe: DatasetRecipe,
    *,
    private_key: Ed25519PrivateKey,
    output_directory: Path,
    repository_root: Path,
    workspace: Path | None = None,
) -> DatasetBuildResult:
    """Normalize, materialize, validate, sign, and package one dataset artifact."""
    output_directory.mkdir(parents=True, exist_ok=True)
    owns_workspace = workspace is None
    workspace_path = (
        Path(tempfile.mkdtemp(prefix="locklearn-dataset-build-"))
        if workspace is None
        else workspace
    )
    workspace_path.mkdir(parents=True, exist_ok=True)
    try:
        normalized = tuple(
            normalize_source(source, workspace_path, repository_root=repository_root)
            for source in sorted(spec.sources, key=lambda item: item.source_id)
        )
        normalized_map = MappingProxyType({item.source_id: item for item in normalized})
        prepared_assets = _prepare_assets(
            spec,
            normalized_map=normalized_map,
            repository_root=repository_root,
        )
        database_path = workspace_path / "dataset.db"
        database_path.unlink(missing_ok=True)
        initialize_content_database(database_path)
        registry_sources = _source_registry(repository_root)
        registry_licenses = _license_registry(repository_root)
        policy = OfficialRegistryPolicy.from_repository(repository_root)

        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO datasets(dataset_id) VALUES (?)", (spec.dataset_id,))
            used_license_scopes: set[tuple[str, str]] = set()
            for item in normalized:
                source_row = registry_sources[item.source_id]
                license_id = _required_string(source_row, "license_id")
                license_scope = _required_string(source_row, "license_scope")
                license_row = registry_licenses.get(license_id)
                if license_row is None:
                    raise DatasetBuildError(f"source references unknown license: {license_id}")
                _insert_license(connection, license_row)
                _insert_source(connection, source_row)
                connection.execute(
                    """INSERT INTO source_snapshots(
                           snapshot_id, source_id, upstream_version, upstream_date,
                           retrieved_at, source_url, sha256, adapter_version
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.snapshot_id,
                        item.source_id,
                        item.upstream_version,
                        item.upstream_date,
                        item.retrieved_at.isoformat(),
                        item.source_url,
                        item.raw_sha256,
                        item.adapter_version,
                    ),
                )
                connection.execute(
                    "INSERT INTO dataset_sources(dataset_id, source_id) VALUES (?, ?)",
                    (spec.dataset_id, item.source_id),
                )
                if (license_id, license_scope) not in used_license_scopes:
                    connection.execute(
                        """INSERT INTO dataset_licenses(dataset_id, license_id, license_scope)
                           VALUES (?, ?, ?)""",
                        (spec.dataset_id, license_id, license_scope),
                    )
                    used_license_scopes.add((license_id, license_scope))
                provenance_id = make_stable_id(
                    "locklearn", "provenance", spec.dataset_id, item.source_id, "dataset"
                )
                connection.execute(
                    """INSERT INTO provenance_records(
                           provenance_id, dataset_id, object_type, object_id,
                           source_snapshot_id, license_id, license_scope,
                           source_record_id, author, language_tag,
                           modified_from_source, attribution_text
                       ) VALUES (?, ?, 'dataset', ?, ?, ?, ?, NULL, NULL, NULL, 1, ?)""",
                    (
                        provenance_id,
                        spec.dataset_id,
                        spec.dataset_id,
                        item.snapshot_id,
                        license_id,
                        license_scope,
                        _required_string(source_row, "attribution_template"),
                    ),
                )

            context = BuildContext(spec.dataset_id, normalized_map)
            for prepared in prepared_assets:
                asset = prepared.metadata
                license_row = registry_licenses.get(asset.license_id)
                if license_row is None:
                    raise DatasetBuildError(f"asset references unknown license: {asset.license_id}")
                _insert_license(connection, license_row)
                connection.execute(
                    """INSERT OR IGNORE INTO dataset_licenses(
                           dataset_id, license_id, license_scope
                       ) VALUES (?, ?, 'asset')""",
                    (spec.dataset_id, asset.license_id),
                )
                connection.execute(
                    """INSERT INTO assets_metadata(
                           asset_id, dataset_id, kind, path, sha256, byte_size,
                           mime_type, width, height, license_id, license_scope, attribution
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'asset', ?)""",
                    (
                        asset.asset_id,
                        asset.dataset_id,
                        asset.kind.value,
                        asset.path,
                        asset.sha256,
                        asset.byte_size,
                        asset.mime_type,
                        asset.width,
                        asset.height,
                        asset.license_id,
                        asset.attribution,
                    ),
                )
                context.insert_provenance(
                    connection,
                    record=NormalizedRecord(
                        source_id=prepared.source_id,
                        source_record_id=prepared.source_record_id,
                        kind="asset",
                        payload={},
                        author=prepared.author,
                        license_id=asset.license_id,
                        modified_from_source=prepared.modified_from_source,
                    ),
                    object_type="asset",
                    object_id=asset.asset_id,
                    license_scope="asset",
                    attribution_text=asset.attribution or None,
                )

            item_counts = dict(recipe.materialize(connection, context))
            if any(
                not isinstance(key, str)
                or not key
                or not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
                for key, value in item_counts.items()
            ):
                raise DatasetBuildError("recipe item counts must be non-negative integers")
            canonical_hash = canonical_content_hash(connection)
            dataset_version_id = make_stable_id(
                "locklearn", "dataset-version", spec.dataset_id, spec.dataset_version
            )
            package_id = make_stable_id(
                "locklearn",
                "package",
                spec.dataset_id,
                spec.dataset_version,
                canonical_hash[:16],
            )
            built_at = spec.built_at.astimezone(UTC).isoformat()
            connection.execute(
                """INSERT INTO dataset_versions(
                       dataset_version_id, dataset_id, version, built_at_utc,
                       canonical_content_hash
                   ) VALUES (?, ?, ?, ?, ?)""",
                (
                    dataset_version_id,
                    spec.dataset_id,
                    spec.dataset_version,
                    built_at,
                    canonical_hash,
                ),
            )
            connection.execute(
                """INSERT INTO dataset_packages(
                       package_id, dataset_id, dataset_version_id, built_at_utc,
                       canonical_content_hash
                   ) VALUES (?, ?, ?, ?, ?)""",
                (
                    package_id,
                    spec.dataset_id,
                    dataset_version_id,
                    built_at,
                    canonical_hash,
                ),
            )
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_keys:
                raise DatasetBuildError(
                    f"recipe created foreign-key violations: {foreign_keys[:3]}"
                )
            connection.commit()

        ContentGenerationValidator().validate_package(database_path)
        license_files = _license_payloads(
            normalized,
            prepared_assets=prepared_assets,
            registry_sources=registry_sources,
            registry_licenses=registry_licenses,
        )
        manifest = _build_manifest(
            spec,
            normalized,
            database_path,
            license_files,
            prepared_assets,
            canonical_hash,
            item_counts,
        )
        policy.validate(manifest)
        manifest_bytes = serialize_manifest(manifest)
        signature = private_key.sign(manifest_bytes)
        archive_name = f"{_safe_name(spec.dataset_id)}-{spec.dataset_version}.zip"
        archive_path = output_directory / archive_name
        _write_archive(
            archive_path,
            manifest_bytes=manifest_bytes,
            signature=signature,
            database_path=database_path,
            license_files=license_files,
            prepared_assets=prepared_assets,
        )
        archive_sha = _sha256_file(archive_path)
        checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
        checksum_path.write_text(f"{archive_sha}  {archive_path.name}\n", encoding="utf-8")
        return DatasetBuildResult(
            archive_path=archive_path,
            archive_sha256_path=checksum_path,
            manifest=manifest,
            canonical_content_hash=canonical_hash,
            normalized_sources=normalized,
        )
    finally:
        if owns_workspace:
            shutil.rmtree(workspace_path, ignore_errors=True)


def canonical_content_hash(connection: sqlite3.Connection) -> str:
    """Hash a deterministic canonical export of semantic content tables."""
    digest = hashlib.sha256()
    for table in _CANONICAL_CONTENT_TABLES:
        columns = [
            str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        ]
        if not columns:
            raise DatasetBuildError(f"canonical content table is missing: {table}")
        order_by = ", ".join(f'"{column}"' for column in columns)
        rows = connection.execute(
            f'SELECT {order_by} FROM "{table}" ORDER BY {order_by}'
        ).fetchall()
        digest.update(table.encode("utf-8"))
        digest.update(b"\n")
        digest.update(
            json.dumps(columns, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        digest.update(b"\n")
        for row in rows:
            digest.update(
                json.dumps(
                    list(row),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
            )
            digest.update(b"\n")
    return digest.hexdigest()


def should_publish(previous: DatasetManifest | None, current: DatasetManifest) -> bool:
    """Publish only when canonical content changed or no prior artifact exists."""
    return previous is None or previous.canonical_content_hash != current.canonical_content_hash


def source_is_stale(
    *,
    retrieved_at: datetime,
    target_refresh_days: int | None,
    now: datetime,
) -> bool:
    """Evaluate registry freshness without making runtime depend on upstream access."""
    if target_refresh_days is None:
        return False
    if target_refresh_days <= 0:
        raise DatasetBuildError("target_refresh_days must be positive or null")
    if retrieved_at.tzinfo is None or now.tzinfo is None:
        raise DatasetBuildError("freshness timestamps must be timezone-aware")
    return (now.astimezone(UTC) - retrieved_at.astimezone(UTC)).days > target_refresh_days


def _prepare_assets(
    spec: DatasetBuildSpec,
    *,
    normalized_map: Mapping[str, NormalizedSource],
    repository_root: Path,
) -> tuple[PreparedAsset, ...]:
    registry_sources = _source_registry(repository_root)
    registry_licenses = _license_registry(repository_root)
    prepared: list[PreparedAsset] = []
    for item in sorted(spec.assets, key=lambda asset: asset.archive_path):
        if not item.path.is_file():
            raise DatasetBuildError(f"asset file does not exist: {item.path}")
        source = registry_sources.get(item.source_id)
        if source is None or item.source_id not in normalized_map:
            raise DatasetBuildError(f"asset source is not declared: {item.source_id}")
        license_id = item.license_id or _required_string(source, "license_id")
        license_row = registry_licenses.get(license_id)
        if license_row is None:
            raise DatasetBuildError(f"asset license is not registered: {license_id}")
        allowed_scopes = license_row.get("allowed_scopes")
        if not isinstance(allowed_scopes, list) or "asset" not in allowed_scopes:
            raise DatasetBuildError(f"license is not approved for assets: {license_id}")
        if _required_bool(license_row, "attribution_required") and not item.attribution:
            raise DatasetBuildError(f"asset attribution is required by license: {license_id}")
        metadata = Asset(
            asset_id=item.asset_id,
            dataset_id=spec.dataset_id,
            kind=item.kind,
            path=item.archive_path,
            sha256=_sha256_file(item.path),
            byte_size=item.path.stat().st_size,
            mime_type=item.mime_type,
            license_id=license_id,
            attribution=item.attribution,
            width=item.width,
            height=item.height,
        )
        prepared.append(
            PreparedAsset(
                metadata=metadata,
                source_id=item.source_id,
                source_record_id=item.source_record_id,
                author=item.author,
                modified_from_source=item.modified_from_source,
                source_path=item.path,
            )
        )
    return tuple(prepared)


def _validate_record_provenance(adapter: SourceAdapter, record: NormalizedRecord) -> None:
    fields = {
        "source_record_id": record.source_record_id,
        "author": record.author,
        "license_id": record.license_id,
        "language": record.language,
    }
    missing = [field for field in adapter.provenance_fields if not fields.get(field)]
    if missing:
        raise DatasetBuildError(f"adapter record is missing required provenance: {sorted(missing)}")


def _canonical_record_line(record: NormalizedRecord) -> str:
    return (
        json.dumps(
            {
                "author": record.author,
                "kind": record.kind,
                "language": record.language,
                "license_id": record.license_id,
                "modified_from_source": record.modified_from_source,
                "payload": record.payload,
                "source_id": record.source_id,
                "source_record_id": record.source_record_id,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def _aggregate_source_sha(files: Iterable[SourceFileInput]) -> str:
    ordered = sorted(files, key=lambda value: value.path.name)
    if len(ordered) == 1:
        return _sha256_file(ordered[0].path)
    digest = hashlib.sha256()
    for item in sorted(ordered, key=lambda value: (value.source_url, value.path.name)):
        file_sha = _sha256_file(item.path)
        digest.update(item.source_url.encode("utf-8"))
        digest.update(b"\x1f")
        digest.update(item.path.name.encode("utf-8"))
        digest.update(b"\x1f")
        digest.update(file_sha.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_STREAM_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _source_registry(root: Path) -> dict[str, dict[str, object]]:
    return _registry_rows(root / "datasets" / "resources" / "sources.json", "sources")


def _license_registry(root: Path) -> dict[str, dict[str, object]]:
    return _registry_rows(root / "datasets" / "resources" / "licenses.json", "licenses")


def _registry_rows(path: Path, field: str) -> dict[str, dict[str, object]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get(field)
    if not isinstance(rows, list):
        raise DatasetBuildError(f"registry {field} must be an array")
    result: dict[str, dict[str, object]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise DatasetBuildError(f"registry {field} rows must be objects")
        row = dict(raw)
        row_id = _required_string(row, "id")
        if row_id in result:
            raise DatasetBuildError(f"duplicate registry ID: {row_id}")
        result[row_id] = row
    return result


def _required_string(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise DatasetBuildError(f"registry field {field} must be a non-empty string")
    return value


def _required_bool(row: Mapping[str, object], field: str) -> bool:
    value = row.get(field)
    if not isinstance(value, bool):
        raise DatasetBuildError(f"registry field {field} must be a boolean")
    return value


def _insert_license(connection: sqlite3.Connection, row: Mapping[str, object]) -> None:
    connection.execute(
        """INSERT OR IGNORE INTO licenses(
               license_id, spdx_or_internal_id, name, version,
               commercial_use_allowed, derivatives_allowed, share_alike,
               attribution_required, source_url, notes
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            _required_string(row, "id"),
            _required_string(row, "spdx_or_internal_id"),
            _required_string(row, "name"),
            str(row.get("version", "")),
            int(_required_bool(row, "commercial_use_allowed")),
            int(_required_bool(row, "derivatives_allowed")),
            int(_required_bool(row, "share_alike")),
            int(_required_bool(row, "attribution_required")),
            _required_string(row, "source_url"),
            str(row.get("notes", "")),
        ),
    )


def _insert_source(connection: sqlite3.Connection, row: Mapping[str, object]) -> None:
    connection.execute(
        """INSERT OR IGNORE INTO sources(
               source_id, name, provider, homepage, license_id,
               attribution_template, adapter_id, refresh_policy,
               commercial_compatible, notes
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            _required_string(row, "id"),
            _required_string(row, "name"),
            _required_string(row, "provider"),
            _required_string(row, "homepage"),
            _required_string(row, "license_id"),
            _required_string(row, "attribution_template"),
            _required_string(row, "adapter_id"),
            _required_string(row, "refresh_policy"),
            int(_required_bool(row, "commercial_compatible")),
            str(row.get("notes", "")),
        ),
    )


def _license_payloads(
    normalized: tuple[NormalizedSource, ...],
    *,
    prepared_assets: tuple[PreparedAsset, ...],
    registry_sources: Mapping[str, Mapping[str, object]],
    registry_licenses: Mapping[str, Mapping[str, object]],
) -> dict[str, bytes]:
    attributions: dict[str, list[str]] = {}
    for item in normalized:
        source = registry_sources[item.source_id]
        license_id = _required_string(source, "license_id")
        attributions.setdefault(license_id, []).append(
            _required_string(source, "attribution_template")
        )
    for prepared in prepared_assets:
        attributions.setdefault(prepared.metadata.license_id, []).append(
            prepared.metadata.attribution
        )
    result: dict[str, bytes] = {}
    for license_id in sorted(attributions):
        license_row = registry_licenses[license_id]
        lines = [
            f"License: {_required_string(license_row, 'name')}",
            f"Identifier: {license_id}",
            f"Terms: {_required_string(license_row, 'source_url')}",
            "",
            "Attribution:",
            *sorted(set(attributions[license_id])),
            "",
        ]
        result[f"LICENSES/{license_id}.txt"] = "\n".join(lines).encode("utf-8")
    return result


def _build_manifest(
    spec: DatasetBuildSpec,
    normalized: tuple[NormalizedSource, ...],
    database_path: Path,
    license_files: Mapping[str, bytes],
    prepared_assets: tuple[PreparedAsset, ...],
    canonical_hash: str,
    item_counts: Mapping[str, int],
) -> DatasetManifest:
    files = [
        ManifestFile(
            path="dataset.db",
            size=database_path.stat().st_size,
            sha256=_sha256_file(database_path),
            role=FileRole.DATABASE,
        )
    ]
    files.extend(
        ManifestFile(
            path=path,
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            role=FileRole.LICENSE,
        )
        for path, content in sorted(license_files.items())
    )
    files.extend(
        ManifestFile(
            path=prepared.metadata.path,
            size=prepared.metadata.byte_size,
            sha256=prepared.metadata.sha256,
            role=FileRole.ASSET,
        )
        for prepared in prepared_assets
    )
    licenses = tuple(
        LicenseReference(license_id=Path(path).stem, path=path) for path in sorted(license_files)
    )
    sources = tuple(
        SourceReference(
            source_id=item.source_id,
            snapshot_id=item.snapshot_id,
            upstream_version=item.upstream_version,
            upstream_date=item.upstream_date,
            retrieved_at=item.retrieved_at,
            source_url=item.source_url,
            sha256=item.raw_sha256,
            adapter_version=item.adapter_version,
        )
        for item in normalized
    )
    return DatasetManifest(
        manifest_version=MANIFEST_VERSION,
        dataset_id=spec.dataset_id,
        dataset_version=spec.dataset_version,
        built_at=spec.built_at.astimezone(UTC),
        content_schema_version=CONTENT_SCHEMA_VERSION,
        minimum_locklearn_version=spec.minimum_locklearn_version,
        build_tool_version=spec.build_tool_version,
        signing_key_id=spec.signing_key_id,
        sources=sources,
        licenses=licenses,
        item_counts=MappingProxyType(dict(sorted(item_counts.items()))),
        added_count=spec.added_count,
        changed_count=spec.changed_count,
        removed_count=spec.removed_count,
        asset_count=len(prepared_assets),
        entry_count=len(files),
        required_free_disk=spec.required_free_disk,
        canonical_content_hash=canonical_hash,
        files=tuple(files),
    )


def _write_archive(
    path: Path,
    *,
    manifest_bytes: bytes,
    signature: bytes,
    database_path: Path,
    license_files: Mapping[str, bytes],
    prepared_assets: tuple[PreparedAsset, ...],
) -> None:
    temporary = path.with_name(f".{path.name}.part")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _zip_write(archive, "manifest.json", manifest_bytes)
            _zip_write(archive, "dataset.db", database_path.read_bytes())
            for name, content in sorted(license_files.items()):
                _zip_write(archive, name, content)
            for prepared in sorted(prepared_assets, key=lambda item: item.metadata.path):
                _zip_write(
                    archive,
                    prepared.metadata.path,
                    prepared.source_path.read_bytes(),
                )
            _zip_write(archive, "SIGNATURE.ed25519", signature)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _zip_write(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def _safe_name(value: str) -> str:
    return "".join(
        character if character.isalnum() or character in "._-" else "-" for character in value
    )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DatasetBuildError("normalized optional string field has invalid type")
    return value
