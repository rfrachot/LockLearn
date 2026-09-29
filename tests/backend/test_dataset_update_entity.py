"""Dataset UpdateEntity remains separate from private learning state."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.components.update import UpdateEntity

from custom_components.locklearn.datasets.manager import (
    DatasetDefinition,
    DatasetRelease,
    DatasetStatus,
    InstalledDataset,
)
from custom_components.locklearn.update import LockLearnDatasetUpdateEntity


def _definition() -> DatasetDefinition:
    return DatasetDefinition(
        dataset_id="locklearn:dataset:fixture",
        name="Public fixture dataset",
        catalog_url="https://datasets.example.invalid/catalog.json",
        artifact_hosts=frozenset({"datasets.example.invalid"}),
    )


def test_dataset_entity_exposes_public_provenance_not_learning_state() -> None:
    """The existing update platform carries dataset metadata only."""
    definition = _definition()
    entity = LockLearnDatasetUpdateEntity(cast(Any, object()), definition)

    assert isinstance(entity, UpdateEntity)
    assert entity.unique_id is not None
    assert entity.unique_id.startswith("dataset_")
    assert entity.name == definition.name

    entity._apply_status(
        DatasetStatus(
            definition=definition,
            installed=InstalledDataset(
                dataset_id=definition.dataset_id,
                version="1.0.0",
                dataset_version_id="locklearn:dataset-version:fixture-1.0.0",
                canonical_content_hash="a" * 64,
                built_at_utc="2026-09-27T12:00:00+00:00",
                sources=(
                    {
                        "source_id": "fixture:source",
                        "upstream_version": "1",
                        "upstream_date": "2026-09-27",
                        "retrieved_at": "2026-09-27T12:00:00+00:00",
                    },
                ),
                licenses=("CC-BY-4.0",),
                pack_version_ids=("locklearn:pack-version:fixture-1.0.0",),
            ),
            latest=DatasetRelease(
                dataset_id=definition.dataset_id,
                version="1.1.0",
                artifact_url="https://datasets.example.invalid/fixture-1.1.0.zip",
                artifact_sha256="b" * 64,
                artifact_size=1024,
                changelog="Public fixture release",
                release_url="https://datasets.example.invalid/releases/1.1.0",
            ),
            update_available=True,
            source_age_days=0,
            stale_sources=(),
            cache_bytes=2048,
            state="update_available",
        )
    )

    assert entity.extra_state_attributes == {
        "dataset_id": definition.dataset_id,
        "dataset_state": "update_available",
        "source_age_days": 0,
        "stale_sources": [],
        "cache_bytes": 2048,
        "licenses": ["CC-BY-4.0"],
        "sources": [
            {
                "source_id": "fixture:source",
                "upstream_version": "1",
                "upstream_date": "2026-09-27",
                "retrieved_at": "2026-09-27T12:00:00+00:00",
            }
        ],
    }

    serialized = repr(entity.extra_state_attributes).lower()
    assert all(
        private_fragment not in serialized
        for private_fragment in (
            "answer",
            "annotation",
            "card_id",
            "learning_item",
            "profile_name",
            "track_name",
        )
    )
