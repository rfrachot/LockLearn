"""Validate machine-readable dataset/resource schemas and committed instances."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "datasets" / "schemas"
DATASET_RESOURCES = ROOT / "datasets" / "resources"
RUNTIME_RESOURCES = ROOT / "custom_components" / "locklearn" / "datasets" / "resources"

INSTANCE_GROUPS: dict[str, tuple[Path, ...]] = {
    "language-registry.schema.json": (DATASET_RESOURCES / "languages.json",),
    "license-registry.schema.json": (
        DATASET_RESOURCES / "licenses.json",
        RUNTIME_RESOURCES / "licenses.json",
    ),
    "source-registry.schema.json": (
        DATASET_RESOURCES / "sources.json",
        RUNTIME_RESOURCES / "sources.json",
    ),
    "source-build-registry.schema.json": (DATASET_RESOURCES / "source_builds.json",),
    "official-dataset-registry.schema.json": (RUNTIME_RESOURCES / "official_datasets.json",),
    "bundled-dataset-registry.schema.json": (RUNTIME_RESOURCES / "bundled_datasets.json",),
    "dataset-build-config.schema.json": tuple(
        sorted((ROOT / "datasets" / "configs").glob("*.json"))
    ),
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> int:
    """Validate every schema and all committed instances with a defined schema."""
    checked_instances = 0
    schema_paths = tuple(sorted(SCHEMAS.glob("*.schema.json")))
    if not schema_paths:
        raise ValueError("no dataset JSON schemas found")

    for schema_path in schema_paths:
        schema = _load(schema_path)
        validator_class = validator_for(schema)
        validator_class.check_schema(schema)
        validator = validator_class(schema)
        for instance_path in INSTANCE_GROUPS.get(schema_path.name, ()):
            if not instance_path.is_file():
                raise ValueError(f"schema instance is missing: {instance_path.relative_to(ROOT)}")
            errors = sorted(
                validator.iter_errors(_load(instance_path)),
                key=lambda item: list(item.path),
            )
            if errors:
                details = "; ".join(
                    f"{instance_path.relative_to(ROOT)}:{'/'.join(map(str, error.path))}: "
                    f"{error.message}"
                    for error in errors
                )
                raise ValueError(details)
            checked_instances += 1

    return checked_instances


if __name__ == "__main__":
    instance_count = validate()
    print(
        "LockLearn JSON schemas: OK "
        f"({len(tuple(SCHEMAS.glob('*.schema.json')))} schemas, {instance_count} instances)"
    )
