"""Backend integration fixtures."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from custom_components.locklearn.storage import StoragePaths


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[None]:
    """Enable LockLearn and isolate HA-backed storage for each backend test."""

    def isolated_paths(_config_dir: str) -> StoragePaths:
        return StoragePaths(
            state_db=tmp_path / ".storage" / "locklearn" / "state.db",
            content_db=tmp_path / "locklearn-content" / "current.db",
        )

    monkeypatch.setattr(StoragePaths, "from_config_dir", staticmethod(isolated_paths))
    yield
