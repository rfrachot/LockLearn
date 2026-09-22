"""P1.9 local DatasetManager installation, update, rollback, and removal tests."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.datasets import (
    KeyStatus,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustStore,
)
from custom_components.locklearn.datasets.manager import (
    DatasetDefinition,
    DatasetInstallError,
    DatasetManager,
    DatasetRemovalError,
)
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from datasets.pipeline import (
    BuildContext,
    DatasetBuildSpec,
    SourceFileInput,
    SourceInput,
    build_dataset,
)

ROOT = Path(__file__).resolve().parents[2]
_BUILT_AT = datetime(2026, 9, 22, 12, tzinfo=UTC)
_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
_PUBLIC_KEY = _PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
_DATASET_ID = "locklearn:dataset:manager-test"


class PackRecipe:
    """Materialize one versioned pack without introducing P1.10 starter content."""

    recipe_id = "test:manager-pack"
    recipe_version = "1"

    def __init__(self, version: str) -> None:
        self._version = version

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        assert context.dataset_id == _DATASET_ID
        connection.execute(
            "INSERT INTO packs(pack_id, dataset_id, name) VALUES (?, ?, ?)",
            ("locklearn:pack:manager-test", _DATASET_ID, "Manager fixture"),
        )
        connection.execute(
            """INSERT INTO pack_versions(
                   pack_version_id, pack_id, version, curation_policy_id
               ) VALUES (?, ?, ?, NULL)""",
            (
                f"locklearn:pack-version:manager-{self._version}",
                "locklearn:pack:manager-test",
                self._version,
            ),
        )
        return {"packs": 1, "pack_versions": 1}


class FakeTransport:
    """In-memory discovery plus local-file artifact transfer."""

    def __init__(self) -> None:
        self.catalogs: dict[str, object] = {}
        self.artifacts: dict[str, Path] = {}
        self.override_sha256: str | None = None

    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        assert maximum_bytes > 0
        return self.catalogs[url]

    async def async_download(
        self,
        url: str,
        destination: Path,
        *,
        maximum_bytes: int,
    ) -> str:
        source = self.artifacts[url]
        assert source.stat().st_size <= maximum_bytes
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if self.override_sha256 is not None:
            return self.override_sha256
        return hashlib.sha256(source.read_bytes()).hexdigest()


def _raw_editorial(tmp_path: Path, version: str) -> Path:
    path = tmp_path / f"editorial-{version}.jsonl"
    path.write_text(
        '{"id":"fixture:manager","kind":"fixture","payload":{"value":"synthetic"}}\n',
        encoding="utf-8",
    )
    return path


def _artifact(tmp_path: Path, version: str) -> Path:
    raw = _raw_editorial(tmp_path, version)
    result = build_dataset(
        DatasetBuildSpec(
            dataset_id=_DATASET_ID,
            dataset_version=version,
            built_at=_BUILT_AT,
            minimum_locklearn_version="0.0.2",
            build_tool_version="1.0.0",
            signing_key_id="manager-test-2026",
            sources=(
                SourceInput(
                    source_id="locklearn:original",
                    upstream_version=f"fixture-{version}",
                    upstream_date="2026-09-22",
                    retrieved_at=_BUILT_AT,
                    files=(
                        SourceFileInput(
                            raw,
                            f"https://example.invalid/editorial-{version}.jsonl",
                        ),
                    ),
                ),
            ),
            required_free_disk=1024,
        ),
        PackRecipe(version),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / f"dist-{version}",
        repository_root=ROOT,
        workspace=tmp_path / f"workspace-{version}",
    )
    return result.archive_path


def _catalog(version_to_artifact: Mapping[str, Path]) -> dict[str, object]:
    releases = []
    for version, artifact in version_to_artifact.items():
        releases.append(
            {
                "version": version,
                "artifact_url": f"https://example.invalid/{version}.zip",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "artifact_size": artifact.stat().st_size,
                "changelog": f"Synthetic {version}",
                "release_url": f"https://example.invalid/releases/{version}",
            }
        )
    return {"schema_version": 1, "dataset_id": _DATASET_ID, "releases": releases}


def _trust_store() -> TrustStore:
    return TrustStore(
        (
            TrustedKey(
                key_id="manager-test-2026",
                public_key=_PUBLIC_KEY,
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_until=datetime(2027, 1, 1, tzinfo=UTC),
                status=KeyStatus.ACTIVE,
            ),
        )
    )


async def _manager(
    tmp_path: Path,
) -> tuple[SQLiteStorage, DatasetManager, FakeTransport]:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    transport = FakeTransport()
    manager = DatasetManager(
        storage=storage,
        transport=transport,
        definitions=(
            DatasetDefinition(
                dataset_id=_DATASET_ID,
                name="Manager fixture",
                catalog_url="https://example.invalid/catalog.json",
                artifact_hosts=frozenset({"example.invalid"}),
            ),
        ),
        trust_store=_trust_store(),
        policy=OfficialRegistryPolicy.from_repository(ROOT),
    )
    return storage, manager, transport


async def test_signed_install_update_and_rollback_keep_pack_versions(tmp_path: Path) -> None:
    storage, manager, transport = await _manager(tmp_path)
    try:
        v1 = _artifact(tmp_path, "1.0.0")
        v2 = _artifact(tmp_path, "1.1.0")
        transport.artifacts["https://example.invalid/1.0.0.zip"] = v1
        transport.artifacts["https://example.invalid/1.1.0.zip"] = v2

        transport.catalogs["https://example.invalid/catalog.json"] = _catalog({"1.0.0": v1})
        await manager.async_refresh()
        first = await manager.async_install(_DATASET_ID)
        assert first.version == "1.0.0"

        first_inventory = await storage.async_dataset_inventory()
        assert first_inventory[0]["version"] == "1.0.0"
        assert first_inventory[0]["pack_version_ids"] == (
            "locklearn:pack-version:manager-1.0.0",
        )

        transport.catalogs["https://example.invalid/catalog.json"] = _catalog(
            {"1.0.0": v1, "1.1.0": v2}
        )
        statuses = await manager.async_refresh()
        assert statuses[0].update_available is True
        assert statuses[0].latest is not None
        assert statuses[0].latest.version == "1.1.0"

        second = await manager.async_install(_DATASET_ID)
        assert second.version == "1.1.0"
        second_inventory = await storage.async_dataset_inventory()
        assert second_inventory[0]["version"] == "1.1.0"
        assert second_inventory[0]["pack_version_ids"] == (
            "locklearn:pack-version:manager-1.0.0",
            "locklearn:pack-version:manager-1.1.0",
        )

        rolled_back_generation = await manager.async_rollback()
        assert rolled_back_generation == first.generation_id
        assert (await storage.async_dataset_inventory())[0]["version"] == "1.0.0"
    finally:
        await storage.async_close()


async def test_checksum_failure_never_replaces_active_generation(tmp_path: Path) -> None:
    storage, manager, transport = await _manager(tmp_path)
    try:
        artifact = _artifact(tmp_path, "1.0.0")
        transport.artifacts["https://example.invalid/1.0.0.zip"] = artifact
        transport.catalogs["https://example.invalid/catalog.json"] = _catalog(
            {"1.0.0": artifact}
        )
        await manager.async_refresh()
        active_before = storage.content_generations.active_metadata.generation_id
        transport.override_sha256 = "0" * 64

        with pytest.raises(DatasetInstallError, match="checksum"):
            await manager.async_install(_DATASET_ID)

        assert storage.content_generations.active_metadata.generation_id == active_before
        assert await storage.async_dataset_inventory() == []
    finally:
        await storage.async_close()


async def test_removal_requires_confirmation_and_blocks_active_pack_usage(
    tmp_path: Path,
) -> None:
    storage, manager, transport = await _manager(tmp_path)
    try:
        artifact = _artifact(tmp_path, "1.0.0")
        transport.artifacts["https://example.invalid/1.0.0.zip"] = artifact
        transport.catalogs["https://example.invalid/catalog.json"] = _catalog(
            {"1.0.0": artifact}
        )
        await manager.async_refresh()
        await manager.async_install(_DATASET_ID)

        with pytest.raises(DatasetRemovalError, match="confirmation"):
            await manager.async_remove(_DATASET_ID, confirmed=False)

        with pytest.raises(DatasetRemovalError, match="active tracks"):
            await manager.async_remove(
                _DATASET_ID,
                confirmed=True,
                active_pack_version_ids=frozenset(
                    {"locklearn:pack-version:manager-1.0.0"}
                ),
            )

        await manager.async_remove(_DATASET_ID, confirmed=True)
        assert await storage.async_dataset_inventory() == []
    finally:
        await storage.async_close()


async def test_untrusted_catalog_cannot_redirect_artifact_download_to_other_host(
    tmp_path: Path,
) -> None:
    storage, manager, transport = await _manager(tmp_path)
    try:
        artifact = _artifact(tmp_path, "1.0.0")
        catalog = _catalog({"1.0.0": artifact})
        releases = catalog["releases"]
        assert isinstance(releases, list)
        assert isinstance(releases[0], dict)
        releases[0]["artifact_url"] = "https://attacker.invalid/payload.zip"
        transport.catalogs["https://example.invalid/catalog.json"] = catalog
        await manager.async_refresh()

        with pytest.raises(DatasetInstallError, match="host allowlist"):
            await manager.async_install(_DATASET_ID)
    finally:
        await storage.async_close()
