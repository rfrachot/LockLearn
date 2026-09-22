"""CLI wrapper for the P1.8 build pipeline."""

from __future__ import annotations

import argparse
import base64
import importlib
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import cast

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.core.assets import AssetKind
from custom_components.locklearn.datasets import parse_manifest
from datasets.pipeline import (
    BuildAssetInput,
    DatasetBuildSpec,
    DatasetRecipe,
    SourceFileInput,
    SourceInput,
    build_dataset,
    fetch_snapshot,
    should_publish,
)


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return parsed


def _load_recipe(reference: str) -> DatasetRecipe:
    module_name, separator, attribute_name = reference.partition(":")
    if not separator or not module_name or not attribute_name:
        raise ValueError("recipe must use module:attribute syntax")
    value = getattr(importlib.import_module(module_name), attribute_name)
    recipe = value() if isinstance(value, type) else value
    if not hasattr(recipe, "materialize"):
        raise ValueError("recipe object must implement materialize()")
    return cast(DatasetRecipe, recipe)


def _private_key() -> Ed25519PrivateKey:
    encoded = os.environ.get("LOCKLEARN_DATASET_SIGNING_KEY_B64")
    if not encoded:
        raise ValueError("LOCKLEARN_DATASET_SIGNING_KEY_B64 is required")
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) != 32:
        raise ValueError("dataset signing key must decode to 32 raw Ed25519 bytes")
    return Ed25519PrivateKey.from_private_bytes(raw)


def _previous_manifest(path: Path | None):
    if path is None:
        return None
    with zipfile.ZipFile(path) as archive:
        return parse_manifest(archive.read("manifest.json"))


def _source_build_rows(repository_root: Path) -> dict[str, dict[str, object]]:
    document = json.loads(
        (repository_root / "datasets" / "resources" / "source_builds.json").read_text(
            encoding="utf-8"
        )
    )
    rows = document.get("sources")
    if not isinstance(rows, list):
        raise ValueError("source build registry sources must be an array")
    result: dict[str, dict[str, object]] = {}
    for raw in rows:
        if not isinstance(raw, dict) or not isinstance(raw.get("source_id"), str):
            raise ValueError("invalid source build registry row")
        result[str(raw["source_id"])] = dict(raw)
    return result


def _validate_fetch_url(row: dict[str, object], fetch_url: str) -> int:
    mode = row.get("fetch_mode")
    registered_url = row.get("download_url")
    if mode == "local":
        raise ValueError("local source cannot be fetched from the network")
    if mode == "direct" and fetch_url != registered_url:
        raise ValueError("direct source fetch_url must match the registered download_url")
    if mode == "template":
        if not isinstance(registered_url, str) or "{language}" not in registered_url:
            raise ValueError("template source has an invalid registered download_url")
        prefix, suffix = registered_url.split("{language}", 1)
        if not fetch_url.startswith(prefix) or not fetch_url.endswith(suffix):
            raise ValueError("template source fetch_url does not match its registered pattern")
    if mode == "recipe_url" and not fetch_url.startswith("https://"):
        raise ValueError("recipe_url sources require an explicit HTTPS fetch_url")
    maximum = row.get("maximum_bytes")
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
        raise ValueError("source build registry has an invalid maximum_bytes")
    return maximum


def _load_config(
    path: Path,
    *,
    workspace: Path,
    repository_root: Path,
) -> tuple[DatasetBuildSpec, DatasetRecipe]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("build config root must be an object")
    sources: list[SourceInput] = []
    source_build_rows = _source_build_rows(repository_root)
    for raw_source in document.get("sources", []):
        if not isinstance(raw_source, dict):
            raise ValueError("source config must be an object")
        source_id = str(raw_source["source_id"])
        try:
            source_build_row = source_build_rows[source_id]
        except KeyError as err:
            raise ValueError(f"unknown source build ID: {source_id}") from err
        files: list[SourceFileInput] = []
        for index, raw_file in enumerate(raw_source.get("files", [])):
            if not isinstance(raw_file, dict):
                raise ValueError("source file config must be an object")
            source_url = str(raw_file["source_url"])
            local_path_value = raw_file.get("path")
            fetch_url = raw_file.get("fetch_url")
            if local_path_value is None:
                if not isinstance(fetch_url, str) or not fetch_url:
                    raise ValueError("source file requires path or fetch_url")
                registered_maximum = _validate_fetch_url(source_build_row, fetch_url)
                requested_maximum = raw_file.get("maximum_bytes", registered_maximum)
                if (
                    isinstance(requested_maximum, bool)
                    or not isinstance(requested_maximum, int)
                    or requested_maximum < 1
                    or requested_maximum > registered_maximum
                ):
                    raise ValueError(
                        f"source file maximum_bytes exceeds registry limit for {source_id}"
                    )
                filename = str(raw_file.get("filename") or f"{source_id}-{index}.raw")
                local_path = workspace / "downloads" / filename
                fetch_snapshot(fetch_url, local_path, maximum_bytes=requested_maximum)
            else:
                local_path = (path.parent / str(local_path_value)).resolve()
            files.append(SourceFileInput(local_path, source_url))
        sources.append(
            SourceInput(
                source_id=source_id,
                upstream_version=str(raw_source["upstream_version"]),
                upstream_date=(
                    None
                    if raw_source.get("upstream_date") is None
                    else str(raw_source["upstream_date"])
                ),
                retrieved_at=_timestamp(str(raw_source["retrieved_at"])),
                files=tuple(files),
                snapshot_url=(
                    None
                    if raw_source.get("snapshot_url") is None
                    else str(raw_source["snapshot_url"])
                ),
            )
        )
    assets: list[BuildAssetInput] = []
    for raw_asset in document.get("assets", []):
        if not isinstance(raw_asset, dict):
            raise ValueError("asset config must be an object")
        local_path = (path.parent / str(raw_asset["path"])).resolve()
        raw_kind = raw_asset["kind"]
        if not isinstance(raw_kind, str):
            raise ValueError("asset kind must be a string")
        assets.append(
            BuildAssetInput(
                asset_id=str(raw_asset["asset_id"]),
                source_id=str(raw_asset["source_id"]),
                source_record_id=str(raw_asset["source_record_id"]),
                path=local_path,
                archive_path=str(raw_asset["archive_path"]),
                kind=AssetKind(raw_kind),
                mime_type=str(raw_asset["mime_type"]),
                attribution=str(raw_asset.get("attribution", "")),
                license_id=(
                    None if raw_asset.get("license_id") is None else str(raw_asset["license_id"])
                ),
                width=(None if raw_asset.get("width") is None else int(raw_asset["width"])),
                height=(None if raw_asset.get("height") is None else int(raw_asset["height"])),
                author=(None if raw_asset.get("author") is None else str(raw_asset["author"])),
                modified_from_source=bool(raw_asset.get("modified_from_source", False)),
            )
        )

    spec = DatasetBuildSpec(
        dataset_id=str(document["dataset_id"]),
        dataset_version=str(document["dataset_version"]),
        built_at=_timestamp(str(document["built_at"])),
        minimum_locklearn_version=str(document["minimum_locklearn_version"]),
        build_tool_version=str(document["build_tool_version"]),
        signing_key_id=str(document["signing_key_id"]),
        sources=tuple(sources),
        assets=tuple(assets),
        added_count=int(document.get("added_count", 0)),
        changed_count=int(document.get("changed_count", 0)),
        removed_count=int(document.get("removed_count", 0)),
        required_free_disk=int(document.get("required_free_disk", 0)),
    )
    return spec, _load_recipe(str(document["recipe"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path, default=Path("datasets/dist"))
    parser.add_argument("--workspace", type=Path, default=Path("datasets/staging/build"))
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    args.workspace.mkdir(parents=True, exist_ok=True)
    repository_root = args.repository_root.resolve()
    spec, recipe = _load_config(
        args.config.resolve(),
        workspace=args.workspace.resolve(),
        repository_root=repository_root,
    )
    result = build_dataset(
        spec,
        recipe,
        private_key=_private_key(),
        output_directory=args.output.resolve(),
        repository_root=repository_root,
        workspace=args.workspace.resolve(),
    )
    publish = should_publish(_previous_manifest(args.previous), result.manifest)
    print(
        json.dumps(
            {
                "archive": str(result.archive_path),
                "canonical_content_hash": result.canonical_content_hash,
                "checksum": str(result.archive_sha256_path),
                "publish": publish,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
