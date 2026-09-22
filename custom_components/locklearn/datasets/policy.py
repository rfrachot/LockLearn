"""Registry-backed official dataset license and provenance policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import DatasetManifest


class LicensePolicyError(ValueError):
    """Raised when signed declarations fail the local official-data policy."""


@dataclass(frozen=True, slots=True)
class LicensePolicyRecord:
    """Acceptance facts owned by LockLearn rather than by a package."""

    license_id: str
    commercial_use_allowed: bool
    derivatives_allowed: bool
    official_dataset_allowed: bool


@dataclass(frozen=True, slots=True)
class SourcePolicyRecord:
    """Known source and the audited license attached to it."""

    source_id: str
    license_id: str


class OfficialRegistryPolicy:
    """Official-package policy loaded from the existing project registries."""

    def __init__(
        self,
        *,
        licenses: tuple[LicensePolicyRecord, ...],
        sources: tuple[SourcePolicyRecord, ...],
    ) -> None:
        self._licenses = {record.license_id: record for record in licenses}
        self._sources = {record.source_id: record for record in sources}
        if len(self._licenses) != len(licenses):
            raise LicensePolicyError("duplicate license ID in registry")
        if len(self._sources) != len(sources):
            raise LicensePolicyError("duplicate source ID in registry")

    @classmethod
    def from_repository(cls, root: Path | None = None) -> OfficialRegistryPolicy:
        """Load the canonical build-time registries without copying their policy."""
        repository_root = root or Path(__file__).resolve().parents[3]
        resources = repository_root / "datasets" / "resources"
        licenses_document = _load_object(resources / "licenses.json")
        sources_document = _load_object(resources / "sources.json")
        licenses = tuple(
            LicensePolicyRecord(
                license_id=_required_string(row, "id"),
                commercial_use_allowed=_required_bool(row, "commercial_use_allowed"),
                derivatives_allowed=_required_bool(row, "derivatives_allowed"),
                official_dataset_allowed=_required_bool(row, "official_dataset_allowed"),
            )
            for row in _rows(licenses_document, "licenses")
        )
        sources = tuple(
            SourcePolicyRecord(
                source_id=_required_string(row, "id"),
                license_id=_required_string(row, "license_id"),
            )
            for row in _rows(sources_document, "sources")
        )
        return cls(licenses=licenses, sources=sources)

    def validate(self, manifest: DatasetManifest) -> None:
        """Reject unknown, NC, ND or otherwise non-official license declarations."""
        declared_license_ids = {record.license_id for record in manifest.licenses}
        for license_id in declared_license_ids:
            record = self._licenses.get(license_id)
            if record is None:
                raise LicensePolicyError(f"unknown official dataset license: {license_id}")
            if not record.commercial_use_allowed:
                raise LicensePolicyError(f"license forbids commercial use: {license_id}")
            if not record.derivatives_allowed:
                raise LicensePolicyError(f"license forbids derivatives: {license_id}")
            if not record.official_dataset_allowed:
                raise LicensePolicyError(
                    f"license is not approved for official datasets: {license_id}"
                )

        required_license_ids: set[str] = set()
        for source in manifest.sources:
            registry_source = self._sources.get(source.source_id)
            if registry_source is None:
                raise LicensePolicyError(f"unknown official dataset source: {source.source_id}")
            required_license_ids.add(registry_source.license_id)
        missing = required_license_ids - declared_license_ids
        if missing:
            raise LicensePolicyError(
                f"source registry licenses are not declared: {sorted(missing)}"
            )


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise LicensePolicyError(f"cannot load registry: {path}") from err
    if not isinstance(value, dict):
        raise LicensePolicyError(f"registry root must be an object: {path}")
    return value


def _rows(document: dict[str, Any], field: str) -> list[dict[str, Any]]:
    value = document.get(field)
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise LicensePolicyError(f"registry {field} must be an array of objects")
    return value


def _required_string(row: dict[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise LicensePolicyError(f"registry field {field} must be a non-empty string")
    return value


def _required_bool(row: dict[str, Any], field: str) -> bool:
    value = row.get(field)
    if not isinstance(value, bool):
        raise LicensePolicyError(f"registry field {field} must be a boolean")
    return value
