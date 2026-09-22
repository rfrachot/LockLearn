"""P1.10 signed first-run Japanese Starter dataset tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.datasets import (
    OfficialRegistryPolicy,
    validate_dataset_package,
)
from custom_components.locklearn.datasets.manager import (
    BundledDataset,
    DatasetInstallError,
    DatasetManager,
    load_runtime_bundled_datasets,
    load_runtime_dataset_definitions,
    load_runtime_trust_store,
)
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths
from datasets.pipeline import DatasetBuildSpec, SourceFileInput, SourceInput, build_dataset
from datasets.recipes.japanese_starter import (
    DATASET_ID,
    PACK_VERSION_ID,
    JapaneseStarterRecipe,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "datasets" / "src" / "japanese_starter.jsonl"
_BUILT_AT = datetime(2026, 9, 22, 20, tzinfo=UTC)


class NoNetworkTransport:
    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        raise AssertionError("bundled first-run install must not use the network")

    async def async_download(
        self,
        url: str,
        destination: Path,
        *,
        maximum_bytes: int,
    ) -> str:
        raise AssertionError("bundled first-run install must not use the network")


def test_starter_recipe_builds_120_items_and_one_pack(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    result = build_dataset(
        DatasetBuildSpec(
            dataset_id=DATASET_ID,
            dataset_version="1.0.0",
            built_at=_BUILT_AT,
            minimum_locklearn_version="0.0.2",
            build_tool_version="1.0.0",
            signing_key_id="starter-test",
            sources=(
                SourceInput(
                    source_id="locklearn:original",
                    upstream_version="japanese-starter-source-1.0.0",
                    upstream_date="2026-09-22",
                    retrieved_at=_BUILT_AT,
                    files=(
                        SourceFileInput(
                            SOURCE,
                            "https://example.invalid/japanese_starter.jsonl",
                        ),
                    ),
                ),
            ),
            added_count=120,
            required_free_disk=1024,
        ),
        JapaneseStarterRecipe(),
        private_key=private_key,
        output_directory=tmp_path / "dist",
        repository_root=ROOT,
        workspace=tmp_path / "workspace",
    )
    assert result.manifest.item_counts == {
        "cards": 240,
        "learning_items": 120,
        "pack_versions": 1,
        "packs": 1,
    }
    with sqlite3.connect(tmp_path / "workspace" / "dataset.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM learning_items").fetchone() == (120,)
        assert connection.execute("SELECT COUNT(*) FROM card_definitions").fetchone() == (240,)
        assert connection.execute(
            "SELECT COUNT(*) FROM pack_items WHERE pack_version_id = ?",
            (PACK_VERSION_ID,),
        ).fetchone() == (120,)
        assert connection.execute(
            "SELECT COUNT(*) FROM provenance_records WHERE object_type = 'learning_item'"
        ).fetchone() == (120,)
        assert connection.execute(
            """SELECT COUNT(*) FROM card_definitions AS card
               JOIN facets AS prompt ON prompt.facet_id = card.prompt_facet_id
               WHERE prompt.facet_key IN ('reading_on', 'reading_kun')"""
        ).fetchone() == (0,)


def test_bundled_starter_is_signed_by_runtime_key_and_small() -> None:
    bundled = load_runtime_bundled_datasets()
    assert len(bundled) == 1
    starter = bundled[0]
    assert starter.dataset_id == DATASET_ID
    assert starter.version == "1.0.0"
    assert starter.size < 10 * 1024 * 1024

    validated = validate_dataset_package(
        starter.path,
        trust_store=load_runtime_trust_store(),
        policy=OfficialRegistryPolicy.from_runtime(),
    )
    assert validated.manifest.dataset_id == DATASET_ID
    assert validated.manifest.dataset_version == "1.0.0"
    assert validated.manifest.item_counts["learning_items"] == 120
    assert validated.manifest.item_counts["cards"] == 240


async def test_fresh_storage_bootstraps_starter_without_network(tmp_path: Path) -> None:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    try:
        manager = DatasetManager(
            storage=storage,
            transport=NoNetworkTransport(),
            definitions=load_runtime_dataset_definitions(),
            trust_store=load_runtime_trust_store(),
            policy=OfficialRegistryPolicy.from_runtime(),
        )
        bundled = load_runtime_bundled_datasets()
        assert len(bundled) == 1
        installed = await manager.async_install_bundled(bundled[0])
        assert installed is not None

        inventory = await storage.async_dataset_inventory()
        assert len(inventory) == 1
        assert inventory[0]["dataset_id"] == DATASET_ID
        assert inventory[0]["version"] == "1.0.0"
        assert inventory[0]["pack_version_ids"] == (PACK_VERSION_ID,)

        # Re-running first-run bootstrap is idempotent and never downgrades.
        assert await manager.async_install_bundled(bundled[0]) is None
    finally:
        await storage.async_close()


async def test_corrupt_bundled_starter_reports_issue_without_activation(
    tmp_path: Path,
) -> None:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    created: list[tuple[str, str]] = []

    async def report(
        issue_id: str,
        translation_key: str,
        placeholders: Mapping[str, str],
    ) -> None:
        assert placeholders["dataset_id"] == DATASET_ID
        created.append((issue_id, translation_key))

    try:
        corrupt = tmp_path / "corrupt.zip"
        corrupt.write_bytes(b"not-the-signed-starter")
        manager = DatasetManager(
            storage=storage,
            transport=NoNetworkTransport(),
            definitions=load_runtime_dataset_definitions(),
            trust_store=load_runtime_trust_store(),
            policy=OfficialRegistryPolicy.from_runtime(),
            issue_callback=report,
        )
        bundled = BundledDataset(
            dataset_id=DATASET_ID,
            version="1.0.0",
            path=corrupt,
            sha256="0" * 64,
            size=corrupt.stat().st_size,
        )
        with pytest.raises(DatasetInstallError, match="checksum"):
            await manager.async_install_bundled(bundled)

        assert await storage.async_dataset_inventory() == []
        assert created and created[-1][1] == "dataset_install_failed"
    finally:
        await storage.async_close()
