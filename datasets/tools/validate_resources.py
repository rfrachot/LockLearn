"""Validate the bootstrap language/license/source registries without extra deps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / "datasets" / "resources"


def _load(name: str) -> dict[str, Any]:
    with (RESOURCES / name).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{name}: root must be an object")
    return value


def validate() -> None:
    languages = _load("languages.json")
    licenses = _load("licenses.json")
    sources = _load("sources.json")

    language_rows = languages.get("languages", [])
    language_tags = [row["tag"] for row in language_rows]
    if len(language_tags) != len(set(language_tags)):
        raise ValueError("duplicate BCP47 language tags")
    if {"en", "fr"} - {row["tag"] for row in language_rows if row["ui_v1"]}:
        raise ValueError("V1 UI must include en and fr")
    if "ja" not in language_tags:
        raise ValueError("Japanese showcase language metadata is required")

    license_rows = licenses.get("licenses", [])
    license_ids = {row["id"] for row in license_rows}
    for row in license_rows:
        if row.get("official_dataset_allowed") and not row.get("commercial_use_allowed"):
            raise ValueError(f"official license is not commercial-compatible: {row['id']}")
        if row.get("official_dataset_allowed") and not row.get("derivatives_allowed"):
            raise ValueError(f"official license forbids derivatives: {row['id']}")

    source_rows = sources.get("sources", [])
    source_ids = [row["id"] for row in source_rows]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source IDs")
    for row in source_rows:
        if row["license_id"] not in license_ids:
            raise ValueError(f"unknown license {row['license_id']} for source {row['id']}")
        if not row.get("commercial_compatible"):
            raise ValueError(f"official candidate is not commercial-compatible: {row['id']}")


if __name__ == "__main__":
    validate()
    print("LockLearn resource registries: OK")
