"""P1.8 deterministic dataset build pipeline tests."""

from __future__ import annotations

import base64
import sqlite3
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Mapping

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.datasets import (
    KeyStatus,
    KeyUsage,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustStore,
    validate_dataset_package,
)
from datasets.pipeline import (
    BuildContext,
    DatasetBuildError,
    DatasetBuildSpec,
    SourceFileInput,
    SourceInput,
    build_dataset,
    fetch_snapshot,
    normalize_source,
    should_publish,
    source_is_stale,
)

ROOT = Path(__file__).resolve().parents[2]
_BUILT_AT = datetime(2026, 9, 22, 12, tzinfo=UTC)
_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))


class RecordTagRecipe:
    recipe_id = "test:record-tag"
    recipe_version = "1"

    def materialize(
        self, connection: sqlite3.Connection, context: BuildContext
    ) -> Mapping[str, int]:
        record = next(context.iter_records("locklearn:original"))
        value = str(record.payload["value"])
        connection.execute(
            "INSERT INTO tags(tag_id, label) VALUES ('locklearn:tag:recipe-output', ?)",
            (value,),
        )
        return {"learning_items": 0, "cards": 0, "tags": 1}


class EmptyRecipe:
    recipe_id = "test:empty"
    recipe_version = "1"

    def materialize(
        self, connection: sqlite3.Connection, context: BuildContext
    ) -> Mapping[str, int]:
        assert context.dataset_id == "locklearn:dataset:pipeline-test"
        return {"learning_items": 0, "cards": 0}


def _source(path: Path, retrieved_at: datetime = _BUILT_AT) -> SourceInput:
    return SourceInput(
        source_id="locklearn:original",
        upstream_version="fixture-1",
        upstream_date="2026-09-22",
        retrieved_at=retrieved_at,
        files=(SourceFileInput(path, "https://example.invalid/editorial.jsonl"),),
    )


def _spec(
    path: Path,
    *,
    version: str = "1.0.0",
    built_at: datetime = _BUILT_AT,
) -> DatasetBuildSpec:
    return DatasetBuildSpec(
        dataset_id="locklearn:dataset:pipeline-test",
        dataset_version=version,
        built_at=built_at,
        minimum_locklearn_version="0.0.2",
        build_tool_version="1.0.0",
        signing_key_id="test-pipeline-2026",
        sources=(_source(path, built_at),),
        required_free_disk=1024,
    )


def _editorial(path: Path) -> Path:
    path.write_text(
        '{"id":"fixture:one","kind":"fixture","payload":{"value":"synthetic"}}\n',
        encoding="utf-8",
    )
    return path


def test_fetch_snapshot_is_atomic_and_bounded(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"synthetic-source")
    destination = tmp_path / "downloads" / "source.bin"
    digest = fetch_snapshot(source.as_uri(), destination, maximum_bytes=1024)
    assert destination.read_bytes() == b"synthetic-source"
    assert len(digest) == 64
    with pytest.raises(DatasetBuildError, match="maximum_bytes"):
        fetch_snapshot(source.as_uri(), tmp_path / "too-small.bin", maximum_bytes=2)
    assert not (tmp_path / ".too-small.bin.part").exists()


def test_normalization_is_reproducible_for_same_snapshot(tmp_path: Path) -> None:
    raw = _editorial(tmp_path / "editorial.jsonl")
    source = _source(raw)
    first = normalize_source(source, tmp_path / "one", repository_root=ROOT)
    second = normalize_source(source, tmp_path / "two", repository_root=ROOT)
    assert first.snapshot_id == second.snapshot_id
    assert first.raw_sha256 == second.raw_sha256
    assert first.normalized_sha256 == second.normalized_sha256
    assert first.normalized_path.read_bytes() == second.normalized_path.read_bytes()


def test_complete_signed_build_validates_with_p1_2_contract(tmp_path: Path) -> None:
    raw = _editorial(tmp_path / "editorial.jsonl")
    result = build_dataset(
        _spec(raw),
        EmptyRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist",
        repository_root=ROOT,
        workspace=tmp_path / "workspace",
    )
    public_key = _PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    trust = TrustStore(
        (
            TrustedKey(
                key_id="test-pipeline-2026",
                public_key=public_key,
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_until=datetime(2027, 1, 1, tzinfo=UTC),
                status=KeyStatus.ACTIVE,
            ),
        )
    )
    validated = validate_dataset_package(
        result.archive_path,
        trust_store=trust,
        policy=OfficialRegistryPolicy.from_repository(ROOT),
        key_usage=KeyUsage.NEW_BUILD,
    )
    assert validated.manifest.canonical_content_hash == result.canonical_content_hash
    assert result.archive_sha256_path.read_text(encoding="utf-8").endswith(
        f"  {result.archive_path.name}\n"
    )
    with zipfile.ZipFile(result.archive_path) as archive:
        assert archive.namelist() == [
            "manifest.json",
            "dataset.db",
            "LICENSES/CC-BY-SA-4.0.txt",
            "SIGNATURE.ed25519",
        ]
        assert len(archive.read("SIGNATURE.ed25519")) == 64


def test_canonical_content_hash_ignores_build_version_and_timestamp(tmp_path: Path) -> None:
    raw = _editorial(tmp_path / "editorial.jsonl")
    first = build_dataset(
        _spec(raw, version="1.0.0", built_at=_BUILT_AT),
        EmptyRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist-one",
        repository_root=ROOT,
        workspace=tmp_path / "workspace-one",
    )
    second = build_dataset(
        _spec(raw, version="1.0.1", built_at=_BUILT_AT + timedelta(days=1)),
        EmptyRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist-two",
        repository_root=ROOT,
        workspace=tmp_path / "workspace-two",
    )
    assert first.canonical_content_hash == second.canonical_content_hash
    assert should_publish(first.manifest, second.manifest) is False

    raw.write_text(
        '{"id":"fixture:two","kind":"fixture","payload":{"value":"changed"}}\n',
        encoding="utf-8",
    )
    third = build_dataset(
        _spec(raw, version="1.0.2", built_at=_BUILT_AT + timedelta(days=2)),
        EmptyRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist-three",
        repository_root=ROOT,
        workspace=tmp_path / "workspace-three",
    )
    assert should_publish(second.manifest, third.manifest) is False


def test_source_freshness_is_policy_data_not_network_availability() -> None:
    now = datetime(2026, 9, 22, tzinfo=UTC)
    assert source_is_stale(
        retrieved_at=now - timedelta(days=31),
        target_refresh_days=30,
        now=now,
    )
    assert not source_is_stale(
        retrieved_at=now - timedelta(days=30),
        target_refresh_days=30,
        now=now,
    )
    assert not source_is_stale(
        retrieved_at=now - timedelta(days=999),
        target_refresh_days=None,
        now=now,
    )


def test_private_signing_key_fixture_never_needs_repository_secret() -> None:
    raw = _PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    assert base64.b64encode(raw).decode("ascii") != ""


def test_publish_gate_detects_real_canonical_content_change(tmp_path: Path) -> None:
    raw = _editorial(tmp_path / "editorial.jsonl")
    first = build_dataset(
        _spec(raw, version="2.0.0", built_at=_BUILT_AT),
        RecordTagRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist-a",
        repository_root=ROOT,
        workspace=tmp_path / "workspace-a",
    )
    raw.write_text(
        '{"id":"fixture:one","kind":"fixture","payload":{"value":"changed"}}\n',
        encoding="utf-8",
    )
    second = build_dataset(
        _spec(raw, version="2.0.1", built_at=_BUILT_AT + timedelta(days=1)),
        RecordTagRecipe(),
        private_key=_PRIVATE_KEY,
        output_directory=tmp_path / "dist-b",
        repository_root=ROOT,
        workspace=tmp_path / "workspace-b",
    )
    assert first.canonical_content_hash != second.canonical_content_hash
    assert should_publish(first.manifest, second.manifest) is True


def test_multifile_snapshot_and_normalization_ignore_config_file_order(tmp_path: Path) -> None:
    first_file = tmp_path / "a.jsonl"
    second_file = tmp_path / "b.jsonl"
    first_file.write_text(
        '{"id":"a","kind":"fixture","payload":{"value":"a"}}\n',
        encoding="utf-8",
    )
    second_file.write_text(
        '{"id":"b","kind":"fixture","payload":{"value":"b"}}\n',
        encoding="utf-8",
    )
    first_input = SourceInput(
        source_id="locklearn:original",
        upstream_version="fixture-multi",
        upstream_date="2026-09-22",
        retrieved_at=_BUILT_AT,
        files=(
            SourceFileInput(first_file, "https://example.invalid/a"),
            SourceFileInput(second_file, "https://example.invalid/b"),
        ),
        snapshot_url="https://example.invalid/composite",
    )
    reversed_input = SourceInput(
        source_id="locklearn:original",
        upstream_version="fixture-multi",
        upstream_date="2026-09-22",
        retrieved_at=_BUILT_AT,
        files=tuple(reversed(first_input.files)),
        snapshot_url="https://example.invalid/composite",
    )
    first = normalize_source(first_input, tmp_path / "multi-one", repository_root=ROOT)
    second = normalize_source(reversed_input, tmp_path / "multi-two", repository_root=ROOT)
    assert first.snapshot_id == second.snapshot_id
    assert first.raw_sha256 == second.raw_sha256
    assert first.normalized_sha256 == second.normalized_sha256
    assert first.normalized_path.read_bytes() == second.normalized_path.read_bytes()
