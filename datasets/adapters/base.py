"""Common contracts for build-time source adapters."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class NormalizedRecord:
    """Adapter-neutral source record written to canonical JSONL."""

    source_id: str
    source_record_id: str
    kind: str
    payload: dict[str, Any]
    author: str | None = None
    language: str | None = None
    license_id: str | None = None
    modified_from_source: bool = False

    def __post_init__(self) -> None:
        if not self.source_id or not self.source_record_id or not self.kind:
            raise ValueError("normalized record identity fields are required")
        if self.author == "":
            raise ValueError("author must be None or non-empty")
        if self.language == "":
            raise ValueError("language must be None or non-empty")


class SourceAdapter(Protocol):
    """Trusted build-time adapter over an already downloaded upstream snapshot."""

    source_id: str
    adapter_id: str
    adapter_version: str
    emitted_fields: frozenset[str]
    provenance_fields: frozenset[str]

    def normalize(self, path: Path) -> Iterable[NormalizedRecord]:
        """Yield deterministic normalized records from one local snapshot."""
        ...
