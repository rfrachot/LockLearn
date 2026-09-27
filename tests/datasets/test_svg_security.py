"""P6.6 build-time SVG and rich-text security regressions."""

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

from custom_components.locklearn.core.assets import AssetKind
from custom_components.locklearn.core.security_content import sanitize_svg_bytes
from custom_components.locklearn.datasets import (
    KeyStatus,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustStore,
    validate_dataset_package,
)
from custom_components.locklearn.datasets.package import PayloadIntegrityError
from datasets.pipeline import (
    BuildAssetInput,
    BuildContext,
    DatasetBuildError,
    DatasetBuildSpec,
    SourceFileInput,
    SourceInput,
    build_dataset,
)

ROOT = Path(__file__).resolve().parents[2]
_BUILT_AT = datetime(2026, 9, 27, 14, tzinfo=UTC)
_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
_PUBLIC_KEY = _PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
_DATASET_ID = "locklearn:dataset:p6-security"
_ITEM_ID = "locklearn:item:p6-security"
_ASSET_ID = "locklearn:asset:p6-svg"


class _SvgRecipe:
    recipe_id = "test:p6-svg"
    recipe_version = "1"

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        connection.execute(
            """INSERT INTO learning_items(
                   learning_item_id, dataset_id, content_type, register,
                   lifecycle_status, superseded_by_learning_item_id
               ) VALUES (?, ?, 'custom', NULL, 'active', NULL)""",
            (_ITEM_ID, context.dataset_id),
        )
        connection.execute(
            """INSERT INTO facets(
                   facet_id, learning_item_id, kind, facet_key, language_tag,
                   script, lifecycle_status, superseded_by_facet_id
               ) VALUES (
                   'locklearn:facet:p6-svg', ?, 'image', 'image',
                   NULL, NULL, 'active', NULL
               )""",
            (_ITEM_ID,),
        )
        connection.execute(
            """INSERT INTO facet_assets(facet_id, asset_id)
               VALUES ('locklearn:facet:p6-svg', ?)""",
            (_ASSET_ID,),
        )
        connection.execute(
            """INSERT INTO content_blocks(
                   content_block_id, learning_item_id, position, kind, role,
                   reveals_answer, mask_strategy, payload_json
               ) VALUES (
                   'locklearn:block:p6-svg', ?, 0, 'image', 'prompt',
                   0, 'none', ?
               )""",
            (_ITEM_ID, json.dumps({"asset_id": _ASSET_ID})),
        )
        return {"learning_items": 1, "assets": 1}


class _UnsafeRichTextRecipe:
    recipe_id = "test:p6-rich-text"
    recipe_version = "1"

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        connection.execute(
            """INSERT INTO learning_items(
                   learning_item_id, dataset_id, content_type, register,
                   lifecycle_status, superseded_by_learning_item_id
               ) VALUES (?, ?, 'custom', NULL, 'active', NULL)""",
            (_ITEM_ID, context.dataset_id),
        )
        connection.execute(
            """INSERT INTO content_blocks(
                   content_block_id, learning_item_id, position, kind, role,
                   reveals_answer, mask_strategy, payload_json
               ) VALUES (
                   'locklearn:block:p6-rich', ?, 0, 'rich_text', 'prompt',
                   0, 'none', ?
               )""",
            (
                _ITEM_ID,
                json.dumps(
                    {
                        "type": "document",
                        "children": [
                            {
                                "type": "html",
                                "text": "<img src=x onerror=alert(1)>",
                            }
                        ],
                    }
                ),
            ),
        )
        return {"learning_items": 1}


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "source.jsonl"
    path.write_text(
        '{"id":"p6-security","kind":"fixture","payload":{"value":"security"}}\n',
        encoding="utf-8",
    )
    return path


def _source_input(tmp_path: Path) -> SourceInput:
    return SourceInput(
        source_id="locklearn:original",
        upstream_version="p6-security-1",
        upstream_date="2026-09-27",
        retrieved_at=_BUILT_AT,
        files=(
            SourceFileInput(
                _source(tmp_path),
                "https://example.invalid/p6-security.jsonl",
            ),
        ),
    )


def _build_svg_dataset(tmp_path: Path, raw_svg: bytes):
    svg = tmp_path / "kanji.svg"
    svg.write_bytes(raw_svg)
    return build_dataset(
        DatasetBuildSpec(
            dataset_id=_DATASET_ID,
            dataset_version="1.0.0",
            built_at=_BUILT_AT,
            minimum_locklearn_version="0.0.2",
            build_tool_version="1.0.0",
            signing_key_id="p6-security-key",
            sources=(_source_input(tmp_path),),
            assets=(
                BuildAssetInput(
                    asset_id=_ASSET_ID,
                    source_id="locklearn:original",
                    source_record_id="p6-security",
                    path=svg,
                    archive_path="assets/svg/kanji.svg",
                    kind=AssetKind.IMAGE,
                    mime_type="image/svg+xml",
                    attribution="LockLearn security fixture — CC BY-SA 4.0",
                    width=100,
                    height=100,
                ),
            ),
        ),
        _SvgRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist",
        repository_root=ROOT,
        workspace=tmp_path / "workspace",
    )


def test_svg_is_sanitized_before_hash_signature_and_packaging(tmp_path: Path) -> None:
    raw_svg = b"""<svg xmlns="http://www.w3.org/2000/svg"
      xmlns:xlink="http://www.w3.org/1999/xlink" onload="alert(1)">
      <script>alert(1)</script>
      <foreignObject><body xmlns="http://www.w3.org/1999/xhtml">x</body></foreignObject>
      <path id="safe" d="M0 0"/>
      <use href="#safe"/>
      <use xlink:href="https://evil.invalid/payload.svg#x"/>
    </svg>"""
    result = _build_svg_dataset(tmp_path, raw_svg)

    expected = sanitize_svg_bytes(raw_svg)
    assert expected != raw_svg
    with zipfile.ZipFile(result.archive_path) as archive:
        packaged = archive.read("assets/svg/kanji.svg")
    assert packaged == expected
    assert b"<script" not in packaged.lower()
    assert b"foreignobject" not in packaged.lower()
    assert b"onload" not in packaged.lower()
    assert b"evil.invalid" not in packaged.lower()

    declared = next(item for item in result.manifest.files if item.path == "assets/svg/kanji.svg")
    assert declared.size == len(packaged)
    assert declared.sha256 == hashlib.sha256(packaged).hexdigest()

    with sqlite3.connect(tmp_path / "workspace" / "dataset.db") as connection:
        assert connection.execute(
            """SELECT mime_type, byte_size, sha256
               FROM assets_metadata
               WHERE asset_id = ?""",
            (_ASSET_ID,),
        ).fetchone() == (
            "image/svg+xml",
            len(packaged),
            hashlib.sha256(packaged).hexdigest(),
        )
        assert connection.execute(
            """SELECT modified_from_source
               FROM provenance_records
               WHERE object_type = 'asset' AND object_id = ?""",
            (_ASSET_ID,),
        ).fetchone() == (1,)


def test_unsafe_rich_text_is_rejected_before_signing(tmp_path: Path) -> None:
    with pytest.raises(DatasetBuildError, match="unsafe rich_text"):
        build_dataset(
            DatasetBuildSpec(
                dataset_id=_DATASET_ID,
                dataset_version="1.0.0",
                built_at=_BUILT_AT,
                minimum_locklearn_version="0.0.2",
                build_tool_version="1.0.0",
                signing_key_id="p6-security-key",
                sources=(_source_input(tmp_path),),
            ),
            _UnsafeRichTextRecipe(),
            private_key=_PRIVATE_KEY,
            output_directory=tmp_path / "dist",
            repository_root=ROOT,
            workspace=tmp_path / "workspace",
        )

    assert list((tmp_path / "dist").glob("*.zip")) == []


def test_runtime_rejects_raw_svg_even_when_a_manifest_is_signed(tmp_path: Path) -> None:
    """A trusted signature cannot bypass the build-time SVG derivative contract."""
    raw_svg = b'<svg xmlns="http://www.w3.org/2000/svg"><SCRIPT>alert(1)</SCRIPT></svg>'
    result = _build_svg_dataset(tmp_path, raw_svg)

    members: dict[str, bytes]
    with zipfile.ZipFile(result.archive_path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}

    database = tmp_path / "raw-svg.db"
    database.write_bytes(members["dataset.db"])
    raw_digest = hashlib.sha256(raw_svg).hexdigest()
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE assets_metadata SET sha256 = ?, byte_size = ? WHERE asset_id = ?",
            (raw_digest, len(raw_svg), _ASSET_ID),
        )
        connection.commit()
    members["dataset.db"] = database.read_bytes()

    document = json.loads(members["manifest.json"])
    for item in document["files"]:
        if item["path"] == "assets/svg/kanji.svg":
            item["size"] = len(raw_svg)
            item["sha256"] = raw_digest
        elif item["path"] == "dataset.db":
            item["size"] = len(members["dataset.db"])
            item["sha256"] = hashlib.sha256(members["dataset.db"]).hexdigest()
    manifest = (
        json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode("utf-8")
    members["manifest.json"] = manifest
    members["assets/svg/kanji.svg"] = raw_svg
    members["SIGNATURE.ed25519"] = _PRIVATE_KEY.sign(manifest)

    package = tmp_path / "raw-signed-svg.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in members.items():
            archive.writestr(name, value)

    key = TrustedKey(
        key_id="p6-security-key",
        public_key=_PUBLIC_KEY,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=datetime(2027, 1, 1, tzinfo=UTC),
        status=KeyStatus.ACTIVE,
    )
    with pytest.raises(PayloadIntegrityError, match="sanitized"):
        validate_dataset_package(
            package,
            trust_store=TrustStore((key,)),
            policy=OfficialRegistryPolicy.from_repository(ROOT),
        )
