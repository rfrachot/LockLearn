"""P1.11 public dataset Asset schema and signed media pipeline tests."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.core.assets import Asset, AssetKind, AssetModelError
from custom_components.locklearn.datasets import (
    KeyStatus,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustStore,
    validate_dataset_package,
)
from custom_components.locklearn.datasets.manager import (
    BundledDataset,
    DatasetInstallError,
    DatasetManager,
)
from custom_components.locklearn.storage import (
    ContentGenerationValidator,
    ContentValidationError,
    SQLiteStorage,
    StoragePaths,
)
from datasets.pipeline import (
    BuildAssetInput,
    BuildContext,
    DatasetBuildSpec,
    SourceFileInput,
    SourceInput,
    build_dataset,
)

ROOT = Path(__file__).resolve().parents[2]
_DATASET_ID = "locklearn:dataset:asset-test"
_ASSET_ID = "locklearn:asset:test-image"
_ITEM_ID = "locklearn:item:asset-test"
_FACET_ID = "locklearn:facet:asset-test-image"
_BLOCK_ID = "locklearn:block:asset-test-image"
_BUILT_AT = datetime(2026, 9, 22, 21, tzinfo=UTC)
_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
_PUBLIC_KEY = _PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)


class MediaRecipe:
    recipe_id = "test:media"
    recipe_version = "1"

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        assert context.dataset_id == _DATASET_ID
        connection.execute(
            """INSERT INTO learning_items(
                   learning_item_id, dataset_id, content_type, register,
                   lifecycle_status, superseded_by_learning_item_id
               ) VALUES (?, ?, 'custom', NULL, 'active', NULL)""",
            (_ITEM_ID, _DATASET_ID),
        )
        connection.execute(
            """INSERT INTO facets(
                   facet_id, learning_item_id, kind, facet_key, language_tag,
                   script, lifecycle_status, superseded_by_facet_id
               ) VALUES (?, ?, 'image', 'image', NULL, NULL, 'active', NULL)""",
            (_FACET_ID, _ITEM_ID),
        )
        connection.execute(
            "INSERT INTO facet_assets(facet_id, asset_id) VALUES (?, ?)",
            (_FACET_ID, _ASSET_ID),
        )
        connection.execute(
            """INSERT INTO content_blocks(
                   content_block_id, learning_item_id, position, kind, role,
                   reveals_answer, mask_strategy, payload_json
               ) VALUES (?, ?, 0, 'image', 'prompt', 0, 'none', ?)""",
            (_BLOCK_ID, _ITEM_ID, json.dumps({"asset_id": _ASSET_ID})),
        )
        return {"learning_items": 1, "assets": 1}


def _editorial(tmp_path: Path) -> Path:
    path = tmp_path / "editorial.jsonl"
    path.write_text(
        '{"id":"asset-source","kind":"fixture","payload":{"value":"asset"}}\n',
        encoding="utf-8",
    )
    return path


def _image(tmp_path: Path) -> Path:
    path = tmp_path / "pixel.webp"
    path.write_bytes(b"synthetic-webp-payload")
    return path


def _spec(tmp_path: Path) -> DatasetBuildSpec:
    return DatasetBuildSpec(
        dataset_id=_DATASET_ID,
        dataset_version="1.0.0",
        built_at=_BUILT_AT,
        minimum_locklearn_version="0.0.2",
        build_tool_version="1.0.0",
        signing_key_id="asset-test-2026",
        sources=(
            SourceInput(
                source_id="locklearn:original",
                upstream_version="asset-fixture-1",
                upstream_date="2026-09-22",
                retrieved_at=_BUILT_AT,
                files=(
                    SourceFileInput(
                        _editorial(tmp_path),
                        "https://example.invalid/editorial.jsonl",
                    ),
                ),
            ),
        ),
        assets=(
            BuildAssetInput(
                asset_id=_ASSET_ID,
                source_id="locklearn:original",
                source_record_id="asset-source",
                path=_image(tmp_path),
                archive_path="assets/images/pixel.webp",
                kind=AssetKind.IMAGE,
                mime_type="image/webp",
                attribution="LockLearn test fixture — CC BY-SA 4.0",
                width=1,
                height=1,
            ),
        ),
        required_free_disk=1024,
    )


def _trust_store() -> TrustStore:
    return TrustStore(
        (
            TrustedKey(
                key_id="asset-test-2026",
                public_key=_PUBLIC_KEY,
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_until=datetime(2027, 1, 1, tzinfo=UTC),
                status=KeyStatus.ACTIVE,
            ),
        )
    )


def _build(tmp_path: Path):
    return build_dataset(
        _spec(tmp_path),
        MediaRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist",
        repository_root=ROOT,
        workspace=tmp_path / "workspace",
    )


def test_asset_model_rejects_unsafe_paths_mime_and_dimensions() -> None:
    common: dict[str, Any] = {
        "asset_id": _ASSET_ID,
        "dataset_id": _DATASET_ID,
        "sha256": "0" * 64,
        "byte_size": 1,
        "license_id": "CC-BY-SA-4.0",
        "attribution": "fixture",
    }
    with pytest.raises(AssetModelError, match="assets/"):
        Asset(
            **common,
            kind=AssetKind.IMAGE,
            path="../escape.webp",
            mime_type="image/webp",
            width=1,
            height=1,
        )
    with pytest.raises(AssetModelError, match="unsupported image"):
        Asset(
            **common,
            kind=AssetKind.IMAGE,
            path="assets/image.svg",
            mime_type="image/svg+xml",
            width=1,
            height=1,
        )
    with pytest.raises(AssetModelError, match="width and height"):
        Asset(
            **common,
            kind=AssetKind.IMAGE,
            path="assets/image.webp",
            mime_type="image/webp",
        )
    with pytest.raises(AssetModelError, match="cannot declare image dimensions"):
        Asset(
            **common,
            kind=AssetKind.AUDIO,
            path="assets/audio.ogg",
            mime_type="audio/ogg",
            width=1,
        )


def test_signed_asset_package_binds_zip_bytes_database_and_provenance(tmp_path: Path) -> None:
    result = _build(tmp_path)
    validated = validate_dataset_package(
        result.archive_path,
        trust_store=_trust_store(),
        policy=OfficialRegistryPolicy.from_repository(ROOT),
    )
    assert validated.manifest.content_schema_version == 2
    assert validated.manifest.asset_count == 1
    asset_file = next(
        item for item in validated.manifest.files if item.path == "assets/images/pixel.webp"
    )
    assert asset_file.size == len(b"synthetic-webp-payload")
    assert asset_file.sha256 == hashlib.sha256(b"synthetic-webp-payload").hexdigest()

    with sqlite3.connect(tmp_path / "workspace" / "dataset.db") as connection:
        assert connection.execute(
            """SELECT kind, path, mime_type, width, height, license_scope
               FROM assets_metadata WHERE asset_id = ?""",
            (_ASSET_ID,),
        ).fetchone() == (
            "image",
            "assets/images/pixel.webp",
            "image/webp",
            1,
            1,
            "asset",
        )
        assert connection.execute(
            "SELECT asset_id FROM facet_assets WHERE facet_id = ?",
            (_FACET_ID,),
        ).fetchone() == (_ASSET_ID,)
        assert connection.execute(
            """SELECT COUNT(*) FROM provenance_records
               WHERE object_type = 'asset' AND object_id = ?
                 AND license_scope = 'asset'""",
            (_ASSET_ID,),
        ).fetchone() == (1,)


def test_v2_package_rejects_missing_asset_provenance(tmp_path: Path) -> None:
    _build(tmp_path)
    database = tmp_path / "workspace" / "dataset.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "DELETE FROM provenance_records WHERE object_type = 'asset' AND object_id = ?",
            (_ASSET_ID,),
        )
        connection.commit()
    with pytest.raises(ContentValidationError, match="missing asset-scope provenance"):
        ContentGenerationValidator().validate_package(database)


def test_v2_package_rejects_missing_or_wrong_media_reference(tmp_path: Path) -> None:
    _build(tmp_path)
    database = tmp_path / "workspace" / "dataset.db"
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM facet_assets WHERE facet_id = ?", (_FACET_ID,))
        connection.commit()
    with pytest.raises(ContentValidationError, match="facet asset reference"):
        ContentGenerationValidator().validate_package(database)

    _build(tmp_path)
    database = tmp_path / "workspace" / "dataset.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE content_blocks SET payload_json = ? WHERE content_block_id = ?",
            (json.dumps({"asset_id": "locklearn:asset:missing"}), _BLOCK_ID),
        )
        connection.commit()
    with pytest.raises(ContentValidationError, match="content block payload"):
        ContentGenerationValidator().validate_package(database)


async def test_dataset_manager_extracts_and_revalidates_public_asset_cache(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path)
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    manager = DatasetManager(
        storage=storage,
        transport=_NoNetworkTransport(),
        definitions=(),
        trust_store=_trust_store(),
        policy=OfficialRegistryPolicy.from_repository(ROOT),
    )
    try:
        bundled = BundledDataset(
            dataset_id=_DATASET_ID,
            version="1.0.0",
            path=result.archive_path,
            sha256=hashlib.sha256(result.archive_path.read_bytes()).hexdigest(),
            size=result.archive_path.stat().st_size,
        )
        installed = await manager.async_install_bundled(bundled)
        assert installed is not None
        resolved = await manager.async_resolve_public_asset(_ASSET_ID)
        assert resolved is not None
        assert resolved.path.read_bytes() == b"synthetic-webp-payload"
        assert resolved.mime_type == "image/webp"
        assert resolved.width == 1
        assert resolved.height == 1

        resolved.path.chmod(0o644)
        resolved.path.write_bytes(b"tampered")
        with pytest.raises(DatasetInstallError, match=r"size mismatch|checksum mismatch"):
            await manager.async_resolve_public_asset(_ASSET_ID)
    finally:
        await storage.async_close()


class _NoNetworkTransport:
    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        raise AssertionError("asset fixture install must not use the network")

    async def async_download(
        self,
        url: str,
        destination: Path,
        *,
        maximum_bytes: int,
    ) -> str:
        raise AssertionError("asset fixture install must not use the network")
