"""P1.11 public dataset Asset schema, packaging, cache, and reference tests."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.core.assets import Asset, AssetKind, AssetModelError
from custom_components.locklearn.core.content import (
    derive_card_definition_id,
    derive_card_key,
    make_stable_id,
)
from custom_components.locklearn.datasets import (
    KeyStatus,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustStore,
    validate_dataset_package,
)
from custom_components.locklearn.datasets.manager import BundledDataset, DatasetManager
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
_ITEM_ID = "locklearn:item:asset-test"
_IMAGE_FACET_ID = "locklearn:facet:asset-image"
_TEXT_FACET_ID = "locklearn:facet:asset-text"
_ASSET_ID = "locklearn:asset:cat"
_BUILT_AT = datetime(2026, 9, 22, 20, tzinfo=UTC)
_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))


class AssetRecipe:
    recipe_id = "test:asset"
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
        connection.executemany(
            """INSERT INTO facets(
                   facet_id, learning_item_id, kind, facet_key, language_tag, script,
                   lifecycle_status, superseded_by_facet_id
               ) VALUES (?, ?, ?, ?, NULL, NULL, 'active', NULL)""",
            (
                (_IMAGE_FACET_ID, _ITEM_ID, "image", "image"),
                (_TEXT_FACET_ID, _ITEM_ID, "text", "label"),
            ),
        )
        connection.execute(
            "INSERT INTO facet_assets(facet_id, asset_id) VALUES (?, ?)",
            (_IMAGE_FACET_ID, _ASSET_ID),
        )
        card_id = derive_card_definition_id(
            _ITEM_ID,
            _IMAGE_FACET_ID,
            _TEXT_FACET_ID,
        )
        card_key = derive_card_key(
            _ITEM_ID,
            _IMAGE_FACET_ID,
            _TEXT_FACET_ID,
        )
        connection.execute(
            """INSERT INTO card_definitions(
                   card_definition_id, card_key, learning_item_id,
                   prompt_facet_id, answer_facet_id, answer_semantics,
                   grading_policy_kind, grading_policy_version,
                   lifecycle_status, superseded_by_card_definition_id
               ) VALUES (?, ?, ?, ?, ?, 'single_value', 'exact', 1, 'active', NULL)""",
            (
                card_id,
                card_key,
                _ITEM_ID,
                _IMAGE_FACET_ID,
                _TEXT_FACET_ID,
            ),
        )
        connection.execute(
            """INSERT INTO content_blocks(
                   content_block_id, learning_item_id, position, kind, role,
                   reveals_answer, mask_strategy, payload_json
               ) VALUES (?, ?, 0, 'image', 'prompt', 0, 'none', ?)""",
            (
                "locklearn:block:asset-image",
                _ITEM_ID,
                json.dumps({"asset_id": _ASSET_ID}, separators=(",", ":")),
            ),
        )
        return {"learning_items": 1, "cards": 1, "assets": 1}


class NoNetworkTransport:
    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        raise AssertionError("asset cache test must not use the network")

    async def async_download(
        self,
        url: str,
        destination: Path,
        *,
        maximum_bytes: int,
    ) -> str:
        raise AssertionError("asset cache test must not use the network")


def _editorial(path: Path) -> Path:
    path.write_text(
        '{"id":"asset-fixture","kind":"fixture","payload":{"value":"asset"}}\n',
        encoding="utf-8",
    )
    return path


def _build_asset_package(tmp_path: Path):
    source = _editorial(tmp_path / "editorial.jsonl")
    image = tmp_path / "cat.webp"
    image.write_bytes(b"RIFFsynthetic-webp-asset")
    result = build_dataset(
        DatasetBuildSpec(
            dataset_id=_DATASET_ID,
            dataset_version="1.0.0",
            built_at=_BUILT_AT,
            minimum_locklearn_version="0.0.2",
            build_tool_version="1.0.0",
            signing_key_id="asset-test-2026",
            sources=(
                SourceInput(
                    source_id="locklearn:original",
                    upstream_version="fixture-1",
                    upstream_date="2026-09-22",
                    retrieved_at=_BUILT_AT,
                    files=(
                        SourceFileInput(
                            source,
                            "https://example.invalid/editorial.jsonl",
                        ),
                    ),
                ),
            ),
            assets=(
                BuildAssetInput(
                    asset_id=_ASSET_ID,
                    source_id="locklearn:original",
                    source_record_id="asset-fixture",
                    path=image,
                    archive_path="assets/15/cat.webp",
                    kind=AssetKind.IMAGE,
                    mime_type="image/webp",
                    attribution="LockLearn contributors — CC BY-SA 4.0",
                    width=320,
                    height=240,
                ),
            ),
            added_count=1,
            required_free_disk=1024,
        ),
        AssetRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist",
        repository_root=ROOT,
        workspace=tmp_path / "workspace",
    )
    return result, image


def _trust_store() -> TrustStore:
    public_key = _PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return TrustStore(
        (
            TrustedKey(
                key_id="asset-test-2026",
                public_key=public_key,
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_until=datetime(2027, 1, 1, tzinfo=UTC),
                status=KeyStatus.ACTIVE,
            ),
        )
    )


def test_asset_model_enforces_media_shape_and_safe_paths() -> None:
    asset = Asset(
        asset_id=_ASSET_ID,
        dataset_id=_DATASET_ID,
        kind=AssetKind.IMAGE,
        path="assets/15/cat.webp",
        sha256="a" * 64,
        byte_size=10,
        mime_type="image/webp",
        license_id="CC-BY-SA-4.0",
        attribution="Example attribution",
        width=320,
        height=240,
    )
    assert asset.width == 320

    with pytest.raises(AssetModelError, match="traversal|normalized"):
        Asset(
            asset_id=_ASSET_ID,
            dataset_id=_DATASET_ID,
            kind=AssetKind.IMAGE,
            path="assets/../private/cat.webp",
            sha256="a" * 64,
            byte_size=10,
            mime_type="image/webp",
            license_id="CC-BY-SA-4.0",
            attribution="Example attribution",
            width=320,
            height=240,
        )

    with pytest.raises(AssetModelError, match="dimensions"):
        Asset(
            asset_id="locklearn:asset:audio",
            dataset_id=_DATASET_ID,
            kind=AssetKind.AUDIO,
            path="assets/audio/voice.ogg",
            sha256="b" * 64,
            byte_size=10,
            mime_type="audio/ogg",
            license_id="CC0-1.0",
            attribution="",
            width=1,
        )


def test_signed_asset_package_binds_db_manifest_and_payload(tmp_path: Path) -> None:
    result, image = _build_asset_package(tmp_path)
    assert result.manifest.content_schema_version == 2
    assert result.manifest.asset_count == 1
    asset_files = [item for item in result.manifest.files if item.role.value == "asset"]
    assert [(item.path, item.size, item.sha256) for item in asset_files] == [
        (
            "assets/15/cat.webp",
            image.stat().st_size,
            hashlib.sha256(image.read_bytes()).hexdigest(),
        )
    ]

    validated = validate_dataset_package(
        result.archive_path,
        trust_store=_trust_store(),
        policy=OfficialRegistryPolicy.from_repository(ROOT),
    )
    assert validated.manifest.asset_count == 1
    with zipfile.ZipFile(result.archive_path) as archive:
        assert archive.read("assets/15/cat.webp") == image.read_bytes()

    with sqlite3.connect(tmp_path / "workspace" / "dataset.db") as connection:
        assert connection.execute(
            """SELECT kind, path, mime_type, width, height, license_scope
               FROM assets_metadata WHERE asset_id = ?""",
            (_ASSET_ID,),
        ).fetchone() == (
            "image",
            "assets/15/cat.webp",
            "image/webp",
            320,
            240,
            "asset",
        )
        assert connection.execute(
            "SELECT asset_id FROM facet_assets WHERE facet_id = ?",
            (_IMAGE_FACET_ID,),
        ).fetchone() == (_ASSET_ID,)
        assert connection.execute(
            """SELECT license_scope FROM provenance_records
               WHERE object_type = 'asset' AND object_id = ?""",
            (_ASSET_ID,),
        ).fetchone() == ("asset",)


async def test_asset_install_extracts_cache_and_resolves_only_active_asset(
    tmp_path: Path,
) -> None:
    result, image = _build_asset_package(tmp_path)
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    try:
        manager = DatasetManager(
            storage=storage,
            transport=NoNetworkTransport(),
            definitions=(),
            trust_store=_trust_store(),
            policy=OfficialRegistryPolicy.from_repository(ROOT),
        )
        archive = result.archive_path
        bundled = BundledDataset(
            dataset_id=_DATASET_ID,
            version="1.0.0",
            path=archive,
            sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            size=archive.stat().st_size,
        )
        installed = await manager.async_install_bundled(bundled)
        assert installed is not None

        resolved = await manager.async_resolve_public_asset(_ASSET_ID)
        assert resolved is not None
        assert resolved.kind == "image"
        assert resolved.mime_type == "image/webp"
        assert resolved.path.read_bytes() == image.read_bytes()
        assert resolved.path.is_relative_to(storage.paths.content_root / "assets")
        assert await manager.async_resolve_public_asset("locklearn:asset:missing") is None
    finally:
        await storage.async_close()


def test_v2_validator_rejects_media_block_with_missing_asset(tmp_path: Path) -> None:
    result, _image = _build_asset_package(tmp_path)
    database = tmp_path / "workspace" / "dataset.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE content_blocks SET payload_json = ? WHERE kind = 'image'",
            ('{"asset_id":"locklearn:asset:missing"}',),
        )
        connection.commit()

    with pytest.raises(ContentValidationError, match="content block"):
        ContentGenerationValidator().validate_package(database)


def test_v2_validator_rejects_image_facet_without_matching_asset(tmp_path: Path) -> None:
    _result, _image = _build_asset_package(tmp_path)
    database = tmp_path / "workspace" / "dataset.db"
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM facet_assets")
        connection.commit()

    with pytest.raises(ContentValidationError, match="facet asset"):
        ContentGenerationValidator().validate_package(database)
