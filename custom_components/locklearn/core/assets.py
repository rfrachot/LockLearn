"""Media asset metadata primitives for LockLearn content schema v2."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from .content import validate_license_id, validate_stable_id

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AssetModelError(ValueError):
    """Raised when public dataset asset metadata is unsafe or inconsistent."""


class AssetKind(StrEnum):
    """Media kinds reserved by the V1 content model."""

    IMAGE = "image"
    AUDIO = "audio"


@dataclass(frozen=True, slots=True)
class Asset:
    """One immutable public dataset asset stored outside SQLite BLOBs."""

    asset_id: str
    dataset_id: str
    kind: AssetKind
    path: str
    sha256: str
    byte_size: int
    mime_type: str
    license_id: str
    attribution: str
    width: int | None = None
    height: int | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.asset_id, field="asset_id")
        validate_stable_id(self.dataset_id, field="dataset_id")
        validate_license_id(self.license_id)
        _validate_asset_path(self.path)
        if not _SHA256_RE.fullmatch(self.sha256):
            raise AssetModelError("asset sha256 must be lowercase hexadecimal")
        if self.byte_size <= 0:
            raise AssetModelError("asset byte_size must be positive")
        if not self.mime_type or "/" not in self.mime_type:
            raise AssetModelError("asset mime_type must be a non-empty media type")
        expected_prefix = f"{self.kind.value}/"
        if not self.mime_type.startswith(expected_prefix):
            raise AssetModelError(
                f"{self.kind.value} asset MIME type must start with {expected_prefix!r}"
            )
        if self.kind is AssetKind.IMAGE:
            if self.width is None or self.height is None:
                raise AssetModelError("image assets require width and height")
            if self.width <= 0 or self.height <= 0:
                raise AssetModelError("image dimensions must be positive")
        elif self.width is not None or self.height is not None:
            raise AssetModelError("audio assets cannot declare image dimensions")


def _validate_asset_path(value: str) -> None:
    if not value or "\" in value or value.startswith("/"):
        raise AssetModelError("asset path must be a normalized relative POSIX path")
    path = PurePosixPath(value)
    if path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise AssetModelError("asset path must be normalized and cannot contain traversal")
    if len(path.parts) < 2 or path.parts[0] != "assets":
        raise AssetModelError("public dataset asset path must live below assets/")


def validate_asset_path(value: str) -> str:
    """Validate and return one package-relative public dataset asset path."""
    _validate_asset_path(value)
    return value
