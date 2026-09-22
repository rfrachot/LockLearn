"""Local dataset update orchestration for signed prebuilt LockLearn artifacts."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import shutil
import sqlite3
import uuid
import zipfile
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Protocol

from awesomeversion import AwesomeVersion

from ..const import CONTENT_SCHEMA_VERSION, INTEGRATION_VERSION
from ..storage import ContentGenerationValidator, SQLiteStorage
from .manifest import DatasetManifest
from .package import ValidatedDatasetPackage, validate_dataset_package
from .policy import OfficialRegistryPolicy
from .trust import KeyStatus, KeyUsage, TrustedKey, TrustStore

_OFFICIAL_ARTIFACT_DEFAULT_MAX_BYTES = 150 * 1024 * 1024
_CATALOG_MAX_BYTES = 1024 * 1024
_STREAM_CHUNK_SIZE = 1024 * 1024


class DatasetManagerError(RuntimeError):
    """Base error for dataset discovery, verification, installation, or removal."""


class DatasetDiscoveryError(DatasetManagerError):
    """Raised when untrusted release discovery data is malformed or unavailable."""


class DatasetInstallError(DatasetManagerError):
    """Raised when a dataset artifact cannot be safely installed."""


class DatasetRemovalError(DatasetManagerError):
    """Raised when a dataset cannot be explicitly removed."""


@dataclass(frozen=True, slots=True)
class DatasetDefinition:
    """One official dataset known to the installed integration."""

    dataset_id: str
    name: str
    catalog_url: str
    artifact_hosts: frozenset[str]
    artifact_max_bytes: int = _OFFICIAL_ARTIFACT_DEFAULT_MAX_BYTES

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.name or not self.catalog_url:
            raise DatasetManagerError("dataset definition fields must be non-empty")
        catalog = urlparse(self.catalog_url)
        if catalog.scheme != "https" or not catalog.hostname:
            raise DatasetManagerError("dataset catalog_url must use HTTPS")
        if not self.artifact_hosts:
            raise DatasetManagerError("dataset definition requires artifact_hosts")
        if any(not host or "/" in host or ":" in host for host in self.artifact_hosts):
            raise DatasetManagerError("artifact_hosts must contain plain hostnames")
        if self.artifact_max_bytes <= 0:
            raise DatasetManagerError("artifact_max_bytes must be positive")


@dataclass(frozen=True, slots=True)
class DatasetRelease:
    """Untrusted discovery metadata for one available release."""

    dataset_id: str
    version: str
    artifact_url: str
    artifact_sha256: str
    artifact_size: int
    changelog: str
    release_url: str | None = None

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.version or not self.artifact_url:
            raise DatasetDiscoveryError("release identity fields must be non-empty")
        if (
            len(self.artifact_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.artifact_sha256)
        ):
            raise DatasetDiscoveryError("release artifact_sha256 must be lowercase SHA-256")
        if self.artifact_size <= 0:
            raise DatasetDiscoveryError("release artifact_size must be positive")


@dataclass(frozen=True, slots=True)
class InstalledDataset:
    """Installed dataset facts read from the active immutable generation."""

    dataset_id: str
    version: str
    dataset_version_id: str
    canonical_content_hash: str
    built_at_utc: str
    sources: tuple[dict[str, str | None], ...]
    licenses: tuple[str, ...]
    pack_version_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DatasetStatus:
    """Combined installed/available status exposed to update entities and UI."""

    definition: DatasetDefinition
    installed: InstalledDataset | None
    latest: DatasetRelease | None
    update_available: bool
    source_age_days: int | None
    stale_sources: tuple[str, ...]
    cache_bytes: int
    state: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetInstallResult:
    """Observable result after a fully verified generation switch."""

    dataset_id: str
    version: str
    generation_id: str
    previous_generation_id: str | None
    package_path: Path


class DatasetTransport(Protocol):
    """Network boundary injected into DatasetManager for HA/runtime tests."""

    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        """Fetch bounded UTF-8 JSON."""

    async def async_download(
        self,
        url: str,
        destination: Path,
        *,
        maximum_bytes: int,
    ) -> str:
        """Stream one file atomically and return its SHA-256."""


IssueCallback = Callable[[str, str, Mapping[str, str]], Awaitable[None] | None]
IssueClearCallback = Callable[[str], Awaitable[None] | None]


class DatasetManager:
    """Discover, verify, stage, activate, rollback and explicitly remove datasets."""

    def __init__(
        self,
        *,
        storage: SQLiteStorage,
        transport: DatasetTransport,
        definitions: tuple[DatasetDefinition, ...],
        trust_store: TrustStore,
        policy: OfficialRegistryPolicy,
        freshness_targets: Mapping[str, int] | None = None,
        issue_callback: IssueCallback | None = None,
        issue_clear_callback: IssueClearCallback | None = None,
    ) -> None:
        self._storage = storage
        self._transport = transport
        self._definitions = {definition.dataset_id: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise DatasetManagerError("duplicate official dataset definition")
        self._trust_store = trust_store
        self._policy = policy
        self._freshness_targets = dict(freshness_targets or {})
        self._issue_callback = issue_callback
        self._issue_clear_callback = issue_clear_callback
        self._available: dict[str, tuple[DatasetRelease, ...]] = {}
        self._errors: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._validator = ContentGenerationValidator()
        self._packages_root = storage.paths.content_root / "packages"
        self._downloads_root = storage.paths.content_staging_dir / "downloads"

    @property
    def definitions(self) -> tuple[DatasetDefinition, ...]:
        """Return deterministic official dataset definitions."""
        return tuple(sorted(self._definitions.values(), key=lambda item: item.dataset_id))

    async def async_refresh(self, dataset_id: str | None = None) -> tuple[DatasetStatus, ...]:
        """Refresh untrusted release discovery while preserving installed content offline."""
        selected = (
            (self._definition(dataset_id),)
            if dataset_id is not None
            else self.definitions
        )
        for definition in selected:
            try:
                document = await self._transport.async_get_json(
                    definition.catalog_url,
                    maximum_bytes=_CATALOG_MAX_BYTES,
                )
                releases = _parse_release_catalog(document, definition)
            except Exception as err:
                self._errors[definition.dataset_id] = str(err)
                await self._report_issue(
                    f"dataset_discovery_{_issue_suffix(definition.dataset_id)}",
                    "dataset_discovery_failed",
                    {"dataset_id": definition.dataset_id},
                )
                continue
            self._available[definition.dataset_id] = releases
            self._errors.pop(definition.dataset_id, None)
            await self._clear_issue(
                f"dataset_discovery_{_issue_suffix(definition.dataset_id)}"
            )
        return await self.async_statuses()

    async def async_statuses(self) -> tuple[DatasetStatus, ...]:
        """List installed and available versions with provenance/license facts."""
        installed_rows = await self._storage.async_dataset_inventory()
        installed = {
            item["dataset_id"]: _installed_dataset_from_row(item)
            for item in installed_rows
        }
        statuses: list[DatasetStatus] = []
        now = datetime.now(UTC)
        for definition in self.definitions:
            active = installed.get(definition.dataset_id)
            latest = _latest_release(self._available.get(definition.dataset_id, ()))
            source_age = _source_age_days(active, now)
            stale_sources = _stale_sources(active, self._freshness_targets, now)
            cache_bytes = await asyncio.to_thread(
                _cached_dataset_size,
                self._packages_root,
                definition.dataset_id,
            )
            error = self._errors.get(definition.dataset_id)
            update_available = (
                active is not None
                and latest is not None
                and AwesomeVersion(latest.version) > AwesomeVersion(active.version)
            ) or (active is None and latest is not None)
            state = (
                "error"
                if error is not None
                else "update_available"
                if update_available
                else "installed"
                if active is not None
                else "available"
                if latest is not None
                else "unknown"
            )
            statuses.append(
                DatasetStatus(
                    definition=definition,
                    installed=active,
                    latest=latest,
                    update_available=update_available,
                    source_age_days=source_age,
                    stale_sources=stale_sources,
                    cache_bytes=cache_bytes,
                    state=state,
                    error=error,
                )
            )
            stale_issue_id = f"dataset_stale_{_issue_suffix(definition.dataset_id)}"
            if stale_sources:
                await self._report_issue(
                    stale_issue_id,
                    "dataset_sources_stale",
                    {
                        "dataset_id": definition.dataset_id,
                        "sources": ", ".join(stale_sources),
                    },
                )
            else:
                await self._clear_issue(stale_issue_id)
        return tuple(statuses)

    async def async_status(self, dataset_id: str) -> DatasetStatus:
        """Return one official dataset status without performing network I/O."""
        self._definition(dataset_id)
        for status in await self.async_statuses():
            if status.definition.dataset_id == dataset_id:
                return status
        raise DatasetManagerError(f"dataset status is unavailable: {dataset_id}")

    async def async_install(
        self,
        dataset_id: str,
        *,
        version: str | None = None,
    ) -> DatasetInstallResult:
        """Download, verify, stage, build and atomically activate one dataset version."""
        async with self._lock:
            definition = self._definition(dataset_id)
            release = self._select_release(dataset_id, version)
            if release.artifact_size > definition.artifact_max_bytes:
                raise DatasetInstallError("dataset artifact exceeds the configured official budget")
            artifact_url = urlparse(release.artifact_url)
            if (
                artifact_url.scheme != "https"
                or artifact_url.hostname not in definition.artifact_hosts
            ):
                raise DatasetInstallError(
                    "dataset artifact URL is outside the trusted host allowlist"
                )

            self._downloads_root.mkdir(parents=True, exist_ok=True)
            download = self._downloads_root / f"{uuid.uuid4().hex}.zip"
            extracted = self._downloads_root / f"{uuid.uuid4().hex}.db"
            candidate = self._storage.paths.content_staging_dir / (
                f"content-{uuid.uuid4().hex}.next.db"
            )
            try:
                actual_sha = await self._transport.async_download(
                    release.artifact_url,
                    download,
                    maximum_bytes=definition.artifact_max_bytes,
                )
                if actual_sha != release.artifact_sha256:
                    raise DatasetInstallError("downloaded dataset artifact checksum does not match")
                if download.stat().st_size != release.artifact_size:
                    raise DatasetInstallError("downloaded dataset artifact size does not match")
                validated = await asyncio.to_thread(
                    validate_dataset_package,
                    download,
                    trust_store=self._trust_store,
                    policy=self._policy,
                    key_usage=KeyUsage.HISTORICAL,
                )
                self._validate_release_contract(validated, release)
                if shutil.disk_usage(self._storage.paths.content_root).free < (
                    validated.manifest.required_free_disk
                ):
                    raise DatasetInstallError("insufficient free disk for dataset installation")
                await asyncio.to_thread(_extract_dataset_database, download, extracted)
                package = await asyncio.to_thread(self._validator.validate_package, extracted)
                _validate_package_matches_manifest(package, validated.manifest)
                package_path = _package_cache_path(
                    self._packages_root,
                    dataset_id,
                    validated.manifest.dataset_version,
                )
                await asyncio.to_thread(_store_package_atomically, extracted, package_path)

                installed_rows = await self._storage.async_dataset_inventory()
                current = next(
                    (row for row in installed_rows if row["dataset_id"] == dataset_id),
                    None,
                )
                if current is not None and str(current["version"]) == release.version:
                    if str(current["canonical_content_hash"]) != package.canonical_content_hash:
                        raise DatasetInstallError(
                            "an installed dataset version cannot change canonical content"
                        )
                    raise DatasetInstallError("dataset version is already installed")
                packages = await asyncio.to_thread(
                    self._complete_package_set,
                    installed_rows,
                    dataset_id,
                    package_path,
                )
                generation_id = f"dataset-update-{uuid.uuid4().hex}"
                await self._storage.async_build_content_generation(
                    packages,
                    candidate,
                    generation_id=generation_id,
                )
                metadata = await self._storage.async_activate_content_generation(candidate)
            except Exception as err:
                self._errors[dataset_id] = str(err)
                await self._report_issue(
                    f"dataset_install_{_issue_suffix(dataset_id)}",
                    "dataset_install_failed",
                    {"dataset_id": dataset_id},
                )
                raise
            finally:
                download.unlink(missing_ok=True)
                extracted.unlink(missing_ok=True)
                candidate.unlink(missing_ok=True)

            self._errors.pop(dataset_id, None)
            await self._clear_issue(f"dataset_install_{_issue_suffix(dataset_id)}")
            return DatasetInstallResult(
                dataset_id=dataset_id,
                version=release.version,
                generation_id=metadata.generation_id,
                previous_generation_id=metadata.parent_generation_id,
                package_path=package_path,
            )

    async def async_rollback(self) -> str:
        """Reactivate the retained last-known-good content generation."""
        async with self._lock:
            metadata = await self._storage.async_rollback_content_generation()
            return metadata.generation_id

    async def async_remove(
        self,
        dataset_id: str,
        *,
        confirmed: bool,
        active_pack_version_ids: frozenset[str] = frozenset(),
    ) -> str:
        """Explicitly remove a dataset package while preserving historical identities."""
        if not confirmed:
            raise DatasetRemovalError("dataset removal requires explicit confirmation")
        async with self._lock:
            installed_rows = await self._storage.async_dataset_inventory()
            target = next(
                (row for row in installed_rows if row["dataset_id"] == dataset_id),
                None,
            )
            if target is None:
                raise DatasetRemovalError("dataset is not installed")
            target_pack_versions = frozenset(str(value) for value in target["pack_version_ids"])
            referenced = await self._storage.async_referenced_pack_version_ids()
            used = target_pack_versions & (active_pack_version_ids | referenced)
            if used:
                raise DatasetRemovalError(
                    "dataset contains pack versions used by active tracks; archive tracks first"
                )
            packages = await asyncio.to_thread(
                self._package_set_without,
                installed_rows,
                dataset_id,
            )
            candidate = self._storage.paths.content_staging_dir / (
                f"content-remove-{uuid.uuid4().hex}.next.db"
            )
            try:
                await self._storage.async_build_content_generation(
                    packages,
                    candidate,
                    generation_id=f"dataset-remove-{uuid.uuid4().hex}",
                )
                metadata = await self._storage.async_activate_content_generation(candidate)
                return metadata.generation_id
            finally:
                candidate.unlink(missing_ok=True)

    def _definition(self, dataset_id: str) -> DatasetDefinition:
        try:
            return self._definitions[dataset_id]
        except KeyError as err:
            raise DatasetDiscoveryError(f"unknown official dataset: {dataset_id}") from err

    def _select_release(self, dataset_id: str, version: str | None) -> DatasetRelease:
        releases = self._available.get(dataset_id, ())
        if not releases:
            raise DatasetDiscoveryError("dataset releases have not been discovered")
        if version is None:
            latest = _latest_release(releases)
            assert latest is not None
            return latest
        for release in releases:
            if release.version == version:
                return release
        raise DatasetDiscoveryError(f"dataset version is not available: {version}")

    def _validate_release_contract(
        self,
        validated: ValidatedDatasetPackage,
        release: DatasetRelease,
    ) -> None:
        manifest = validated.manifest
        if manifest.dataset_id != release.dataset_id:
            raise DatasetInstallError("signed manifest dataset_id does not match release")
        if manifest.dataset_version != release.version:
            raise DatasetInstallError("signed manifest dataset_version does not match release")
        if manifest.content_schema_version != CONTENT_SCHEMA_VERSION:
            raise DatasetInstallError("dataset content schema is not supported")
        if AwesomeVersion(manifest.minimum_locklearn_version) > AwesomeVersion(
            INTEGRATION_VERSION
        ):
            raise DatasetInstallError("dataset requires a newer LockLearn integration")

    def _complete_package_set(
        self,
        installed_rows: list[dict[str, Any]],
        updated_dataset_id: str,
        updated_package: Path,
    ) -> tuple[Path, ...]:
        packages = [updated_package]
        for row in installed_rows:
            dataset_id = str(row["dataset_id"])
            if dataset_id == updated_dataset_id:
                continue
            path = _package_cache_path(
                self._packages_root,
                dataset_id,
                str(row["version"]),
            )
            if not path.is_file():
                raise DatasetInstallError(
                    f"cached package required to rebuild generation is missing: {dataset_id}"
                )
            metadata = self._validator.validate_package(path)
            _validate_cached_package(
                path,
                metadata,
                dataset_id=dataset_id,
                version=str(row["version"]),
                canonical_content_hash=str(row["canonical_content_hash"]),
            )
            packages.append(path)
        return tuple(sorted(packages))

    def _package_set_without(
        self,
        installed_rows: list[dict[str, Any]],
        removed_dataset_id: str,
    ) -> tuple[Path, ...]:
        packages: list[Path] = []
        for row in installed_rows:
            dataset_id = str(row["dataset_id"])
            if dataset_id == removed_dataset_id:
                continue
            path = _package_cache_path(
                self._packages_root,
                dataset_id,
                str(row["version"]),
            )
            if not path.is_file():
                raise DatasetRemovalError(
                    f"cached package required to rebuild generation is missing: {dataset_id}"
                )
            metadata = self._validator.validate_package(path)
            try:
                _validate_cached_package(
                    path,
                    metadata,
                    dataset_id=dataset_id,
                    version=str(row["version"]),
                    canonical_content_hash=str(row["canonical_content_hash"]),
                )
            except DatasetInstallError as err:
                raise DatasetRemovalError(str(err)) from err
            packages.append(path)
        return tuple(sorted(packages))

    async def _report_issue(
        self,
        issue_id: str,
        translation_key: str,
        placeholders: Mapping[str, str],
    ) -> None:
        if self._issue_callback is None:
            return
        result = self._issue_callback(issue_id, translation_key, placeholders)
        if result is not None:
            await result

    async def _clear_issue(self, issue_id: str) -> None:
        if self._issue_clear_callback is None:
            return
        result = self._issue_clear_callback(issue_id)
        if result is not None:
            await result


def load_runtime_dataset_definitions(
    resources: Path | None = None,
) -> tuple[DatasetDefinition, ...]:
    """Load official dataset discovery definitions bundled with LockLearn."""
    root = resources or Path(__file__).resolve().parent / "resources"
    document = _load_json_object(root / "official_datasets.json")
    if document.get("schema_version") != 1:
        raise DatasetManagerError("official dataset registry schema_version must be 1")
    rows = document.get("datasets")
    if not isinstance(rows, list):
        raise DatasetManagerError("official dataset registry datasets must be an array")
    result: list[DatasetDefinition] = []
    for row in rows:
        if not isinstance(row, dict):
            raise DatasetManagerError("official dataset definition must be an object")
        result.append(
            DatasetDefinition(
                dataset_id=_required_string(row, "dataset_id"),
                name=_required_string(row, "name"),
                catalog_url=_required_string(row, "catalog_url"),
                artifact_hosts=frozenset(_required_string_list(row, "artifact_hosts")),
                artifact_max_bytes=_required_int(
                    row,
                    "artifact_max_bytes",
                    default=_OFFICIAL_ARTIFACT_DEFAULT_MAX_BYTES,
                ),
            )
        )
    return tuple(result)


def load_runtime_source_freshness(
    resources: Path | None = None,
) -> dict[str, int]:
    """Load per-source target refresh ages bundled with the integration."""
    root = resources or Path(__file__).resolve().parent / "resources"
    document = _load_json_object(root / "sources.json")
    rows = document.get("sources")
    if not isinstance(rows, list):
        raise DatasetManagerError("source registry sources must be an array")
    result: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise DatasetManagerError("source registry row must be an object")
        source_id = _required_string(row, "id")
        target = row.get("target_refresh_days")
        if target is None:
            continue
        if isinstance(target, bool) or not isinstance(target, int) or target <= 0:
            raise DatasetManagerError("target_refresh_days must be a positive integer or null")
        result[source_id] = target
    return result


def load_runtime_trust_store(resources: Path | None = None) -> TrustStore:
    """Load public Ed25519 signing keys bundled with the integration."""
    root = resources or Path(__file__).resolve().parent / "resources"
    document = _load_json_object(root / "signing_keys.json")
    if document.get("schema_version") != 1:
        raise DatasetManagerError("signing key registry schema_version must be 1")
    rows = document.get("keys")
    if not isinstance(rows, list):
        raise DatasetManagerError("signing key registry keys must be an array")
    keys: list[TrustedKey] = []
    for row in rows:
        if not isinstance(row, dict):
            raise DatasetManagerError("signing key registry row must be an object")
        try:
            public_key = base64.b64decode(
                _required_string(row, "public_key_b64"),
                validate=True,
            )
            status = KeyStatus(_required_string(row, "status"))
        except (ValueError, TypeError) as err:
            raise DatasetManagerError("invalid signing key registry value") from err
        keys.append(
            TrustedKey(
                key_id=_required_string(row, "key_id"),
                public_key=public_key,
                valid_from=_parse_timestamp(_required_string(row, "valid_from")),
                valid_until=_parse_timestamp(_required_string(row, "valid_until")),
                status=status,
            )
        )
    return TrustStore(tuple(keys))


def _parse_release_catalog(
    document: object,
    definition: DatasetDefinition,
) -> tuple[DatasetRelease, ...]:
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise DatasetDiscoveryError("release catalog schema_version must be 1")
    if document.get("dataset_id") != definition.dataset_id:
        raise DatasetDiscoveryError("release catalog dataset_id does not match definition")
    raw_releases = document.get("releases")
    if not isinstance(raw_releases, list):
        raise DatasetDiscoveryError("release catalog releases must be an array")
    releases: list[DatasetRelease] = []
    versions: set[str] = set()
    for row in raw_releases:
        if not isinstance(row, dict):
            raise DatasetDiscoveryError("release catalog row must be an object")
        release = DatasetRelease(
            dataset_id=definition.dataset_id,
            version=_required_string(row, "version"),
            artifact_url=_required_string(row, "artifact_url"),
            artifact_sha256=_required_string(row, "artifact_sha256"),
            artifact_size=_required_int(row, "artifact_size"),
            changelog=_optional_string(row.get("changelog")) or "",
            release_url=_optional_string(row.get("release_url")),
        )
        if release.version in versions:
            raise DatasetDiscoveryError("release catalog contains duplicate versions")
        versions.add(release.version)
        releases.append(release)
    return tuple(sorted(releases, key=lambda item: AwesomeVersion(item.version)))


def _latest_release(releases: tuple[DatasetRelease, ...]) -> DatasetRelease | None:
    return releases[-1] if releases else None


def _installed_dataset_from_row(row: dict[str, Any]) -> InstalledDataset:
    return InstalledDataset(
        dataset_id=str(row["dataset_id"]),
        version=str(row["version"]),
        dataset_version_id=str(row["dataset_version_id"]),
        canonical_content_hash=str(row["canonical_content_hash"]),
        built_at_utc=str(row["built_at_utc"]),
        sources=tuple(row["sources"]),
        licenses=tuple(str(value) for value in row["licenses"]),
        pack_version_ids=tuple(str(value) for value in row["pack_version_ids"]),
    )


def _source_age_days(installed: InstalledDataset | None, now: datetime) -> int | None:
    if installed is None or not installed.sources:
        return None
    retrieved = [
        _parse_timestamp(str(source["retrieved_at"]))
        for source in installed.sources
        if source.get("retrieved_at")
    ]
    if not retrieved:
        return None
    return max(0, max((now - value).days for value in retrieved))


def _stale_sources(
    installed: InstalledDataset | None,
    freshness_targets: Mapping[str, int],
    now: datetime,
) -> tuple[str, ...]:
    if installed is None:
        return ()
    stale: list[str] = []
    for source in installed.sources:
        source_id = source.get("source_id")
        retrieved_at = source.get("retrieved_at")
        if source_id is None or retrieved_at is None:
            continue
        target = freshness_targets.get(source_id)
        if target is None:
            continue
        age_days = max(0, (now - _parse_timestamp(str(retrieved_at))).days)
        if age_days > target:
            stale.append(source_id)
    return tuple(sorted(set(stale)))


def _extract_dataset_database(archive_path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            info = archive.getinfo("dataset.db")
            with archive.open(info) as source, temporary.open("wb") as target:
                while chunk := source.read(_STREAM_CHUNK_SIZE):
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_package_matches_manifest(package: Any, manifest: DatasetManifest) -> None:
    if package.dataset_id != manifest.dataset_id:
        raise DatasetInstallError("package database dataset_id does not match signed manifest")
    if package.canonical_content_hash != manifest.canonical_content_hash:
        raise DatasetInstallError(
            "package database canonical content hash does not match signed manifest"
        )
    with sqlite3.connect(f"{package.path.resolve().as_uri()}?mode=ro&immutable=1", uri=True) as db:
        row = db.execute(
            """SELECT version FROM dataset_versions
               WHERE dataset_version_id = ? AND dataset_id = ?""",
            (package.dataset_version_id, package.dataset_id),
        ).fetchone()
    if row is None or str(row[0]) != manifest.dataset_version:
        raise DatasetInstallError("package database version does not match signed manifest")


def _validate_cached_package(
    path: Path,
    package: Any,
    *,
    dataset_id: str,
    version: str,
    canonical_content_hash: str,
) -> None:
    if package.dataset_id != dataset_id:
        raise DatasetInstallError("cached package identity does not match active dataset")
    if package.canonical_content_hash != canonical_content_hash:
        raise DatasetInstallError("cached package content hash does not match active dataset")
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True) as db:
        row = db.execute(
            """SELECT version FROM dataset_versions
               WHERE dataset_version_id = ? AND dataset_id = ?""",
            (package.dataset_version_id, dataset_id),
        ).fetchone()
    if row is None or str(row[0]) != version:
        raise DatasetInstallError("cached package version does not match active dataset")


def _package_cache_path(root: Path, dataset_id: str, version: str) -> Path:
    dataset_key = hashlib.sha256(dataset_id.encode("utf-8")).hexdigest()
    version_key = hashlib.sha256(version.encode("utf-8")).hexdigest()
    return root / dataset_key / f"{version_key}.db"


def _store_package_atomically(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
    shutil.copyfile(source, temporary)
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    os.chmod(destination, 0o444)


def _cached_dataset_size(root: Path, dataset_id: str) -> int:
    directory = root / hashlib.sha256(dataset_id.encode("utf-8")).hexdigest()
    if not directory.is_dir():
        return 0
    return sum(path.stat().st_size for path in directory.glob("*.db") if path.is_file())


def _issue_suffix(dataset_id: str) -> str:
    return hashlib.sha256(dataset_id.encode("utf-8")).hexdigest()[:16]


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise DatasetManagerError(f"cannot load dataset runtime registry: {path}") from err
    if not isinstance(value, dict):
        raise DatasetManagerError("dataset runtime registry root must be an object")
    return value


def _required_string(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise DatasetManagerError(f"{field} must be a non-empty string")
    return value


def _required_string_list(
    row: Mapping[str, object],
    field: str,
) -> list[str]:
    value = row.get(field)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise DatasetManagerError(f"{field} must contain unique non-empty strings")
    return value


def _required_int(
    row: Mapping[str, object],
    field: str,
    *,
    default: int | None = None,
) -> int:
    value = row.get(field, default)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DatasetManagerError(f"{field} must be a positive integer")
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DatasetManagerError("optional string field has invalid type")
    return value


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise DatasetManagerError("timestamp must be RFC3339-compatible") from err
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DatasetManagerError("timestamp must include a UTC offset")
    return parsed.astimezone(UTC)
