"""Registry-backed official dataset license and provenance policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import DatasetManifest


class LicensePolicyError(ValueError):
    """Raised when signed declarations fail the local official-data policy."""


_ALLOWED_LICENSE_SCOPES = frozenset({"software", "editorial", "dataset", "asset"})


@dataclass(frozen=True, slots=True)
class LicensePolicyRecord:
    """Acceptance facts owned by LockLearn rather than by a package."""

    license_id: str
    commercial_use_allowed: bool
    derivatives_allowed: bool
    official_dataset_allowed: bool
    allowed_scopes: frozenset[str] = frozenset({"dataset", "editorial", "asset"})
    attribution_required: bool = False
    share_alike: bool = False


@dataclass(frozen=True, slots=True)
class SourcePolicyRecord:
    """Known source and the audited import/provenance contract attached to it."""

    source_id: str
    license_id: str
    license_scope: str = "dataset"
    commercial_compatible: bool = True
    required_provenance: tuple[str, ...] = ()
    field_allowlist: frozenset[str] | None = None
    excluded_fields: frozenset[str] = frozenset()


class OfficialRegistryPolicy:
    """Official-package policy loaded from the canonical project registries."""

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
        for license_record in licenses:
            if not license_record.allowed_scopes:
                raise LicensePolicyError(
                    f"license has no allowed usage scope: {license_record.license_id}"
                )
            if not license_record.allowed_scopes <= _ALLOWED_LICENSE_SCOPES:
                raise LicensePolicyError(
                    f"license has unknown usage scope: {license_record.license_id}"
                )
        for source in sources:
            if source.license_scope not in _ALLOWED_LICENSE_SCOPES - {"software"}:
                raise LicensePolicyError(
                    f"source has invalid license scope: {source.source_id}"
                )
            if source.field_allowlist is not None and (
                source.field_allowlist & source.excluded_fields
            ):
                raise LicensePolicyError(
                    f"source allowlist overlaps excluded fields: {source.source_id}"
                )

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
                allowed_scopes=frozenset(_required_string_list(row, "allowed_scopes")),
                attribution_required=_required_bool(row, "attribution_required"),
                share_alike=_required_bool(row, "share_alike"),
            )
            for row in _rows(licenses_document, "licenses")
        )
        sources = tuple(
            SourcePolicyRecord(
                source_id=_required_string(row, "id"),
                license_id=_required_string(row, "license_id"),
                license_scope=_required_string(row, "license_scope"),
                commercial_compatible=_required_bool(row, "commercial_compatible"),
                required_provenance=tuple(_optional_string_list(row, "required_provenance")),
                field_allowlist=(
                    frozenset(_optional_string_list(row, "field_allowlist"))
                    if "field_allowlist" in row
                    else None
                ),
                excluded_fields=frozenset(_optional_string_list(row, "excluded_by_default")),
            )
            for row in _rows(sources_document, "sources")
        )
        return cls(licenses=licenses, sources=sources)

    def validate(self, manifest: DatasetManifest) -> None:
        """Reject unknown, NC, ND, ambiguous, or scope-incompatible declarations."""
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
            if not registry_source.commercial_compatible:
                raise LicensePolicyError(
                    f"source is not commercially compatible: {source.source_id}"
                )
            license_record = self._licenses.get(registry_source.license_id)
            if license_record is None:
                raise LicensePolicyError(
                    f"source registry references unknown license: {registry_source.source_id}"
                )
            if registry_source.license_scope not in license_record.allowed_scopes:
                raise LicensePolicyError(
                    f"license scope is not allowed for source: {registry_source.source_id}"
                )
            required_license_ids.add(registry_source.license_id)
        missing = required_license_ids - declared_license_ids
        if missing:
            raise LicensePolicyError(
                f"source registry licenses are not declared: {sorted(missing)}"
            )

    def validate_import_fields(self, source_id: str, fields: set[str]) -> None:
        """Enforce audited field boundaries before a future adapter emits official data."""
        source = self._source(source_id)
        if source.field_allowlist is not None:
            disallowed = fields - source.field_allowlist
            if disallowed:
                raise LicensePolicyError(
                    f"source fields are not allowlisted for {source_id}: {sorted(disallowed)}"
                )
        excluded = fields & source.excluded_fields
        if excluded:
            raise LicensePolicyError(
                f"source fields are excluded by policy for {source_id}: {sorted(excluded)}"
            )

    def validate_provenance_fields(self, source_id: str, fields: set[str]) -> None:
        """Require source-specific attribution/provenance fields at import time."""
        source = self._source(source_id)
        missing = set(source.required_provenance) - fields
        if missing:
            raise LicensePolicyError(
                f"required provenance is missing for {source_id}: {sorted(missing)}"
            )

    def _source(self, source_id: str) -> SourcePolicyRecord:
        try:
            return self._sources[source_id]
        except KeyError as err:
            raise LicensePolicyError(f"unknown official dataset source: {source_id}") from err


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


def _required_string_list(row: dict[str, Any], field: str) -> list[str]:
    if field not in row:
        raise LicensePolicyError(f"registry field {field} is required")
    return _optional_string_list(row, field)


def _optional_string_list(row: dict[str, Any], field: str) -> list[str]:
    value = row.get(field, [])
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise LicensePolicyError(
            f"registry field {field} must be an array of unique non-empty strings"
        )
    return value
