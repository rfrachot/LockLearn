"""Run the local P5.6 realistic-content qualification against one package."""

from __future__ import annotations

import argparse
import asyncio
import base64
import binascii
import json
import tempfile
import time
import zipfile
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from custom_components.locklearn.core.presentation import CardPresentationService
from custom_components.locklearn.core.profiles import ProfileService
from custom_components.locklearn.core.selection import SelectionConstraintService
from custom_components.locklearn.core.session_selection import SessionSelectionService
from custom_components.locklearn.core.tracks import TrackService
from custom_components.locklearn.datasets import (
    KeyStatus,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustStore,
    validate_dataset_package,
)
from custom_components.locklearn.storage import (
    ContentGenerationValidator,
    SQLiteStorage,
    StoragePaths,
)

PACK_VERSION_ID = "locklearn:pack:jmdict-scale:version:2026.09"
PROFILE_ID = "p5-6-profile"
TRACK_ID = "p5-6-track"


def _stats(values: list[float]) -> dict[str, float]:
    milliseconds = sorted(value * 1000 for value in values)
    return {
        "p50_ms": median(milliseconds),
        "p95_ms": milliseconds[min(len(milliseconds) - 1, int(len(milliseconds) * 0.95) - 1)],
        "max_ms": max(milliseconds),
    }


async def _sample(
    factory: Callable[[], Awaitable[Any]],
    count: int,
) -> dict[str, float]:
    values: list[float] = []
    for _ in range(count):
        started = time.perf_counter()
        await factory()
        values.append(time.perf_counter() - started)
    return _stats(values)


def _trust_store(public_key_b64: str) -> TrustStore:
    try:
        public_key = base64.b64decode(public_key_b64, validate=True)
        Ed25519PublicKey.from_public_bytes(public_key)
    except (ValueError, binascii.Error) as err:
        raise ValueError("--public-key-b64 must contain 32 raw Ed25519 public-key bytes") from err
    return TrustStore(
        (
            TrustedKey(
                key_id="locklearn-qualification-2026-09",
                public_key=public_key,
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_until=datetime(2027, 1, 1, tzinfo=UTC),
                status=KeyStatus.ACTIVE,
            ),
        )
    )


async def _qualify(package: Path, public_key_b64: str, repository_root: Path) -> dict[str, Any]:
    trust_store = _trust_store(public_key_b64)
    started = time.perf_counter()
    validated = validate_dataset_package(
        package,
        trust_store=trust_store,
        policy=OfficialRegistryPolicy.from_repository(repository_root),
    )
    package_validation_s = time.perf_counter() - started

    with tempfile.TemporaryDirectory(prefix="locklearn-p5-6-") as temporary:
        root = Path(temporary)
        package_db = root / "dataset.db"
        with (
            zipfile.ZipFile(package) as archive,
            archive.open("dataset.db") as source,
            package_db.open("wb") as target,
        ):
            while chunk := source.read(1024 * 1024):
                target.write(chunk)

        package_metadata = ContentGenerationValidator().validate_package(package_db)
        storage = SQLiteStorage(
            StoragePaths(root / "state" / "state.db", root / "content" / "current.db")
        )
        await storage.async_open()
        try:
            builds: list[float] = []
            activations: list[float] = []
            for generation_id in ("p5-6-scale-1", "p5-6-scale-2"):
                candidate = storage.paths.content_staging_dir / f"{generation_id}.next.db"
                started = time.perf_counter()
                await storage.async_build_content_generation(
                    (package_db,), candidate, generation_id=generation_id
                )
                builds.append(time.perf_counter() - started)
                started = time.perf_counter()
                await storage.async_activate_content_generation(candidate)
                activations.append(time.perf_counter() - started)

            active_before_rollback = storage.content_generations.active_metadata.generation_id
            previous_generation = storage.content_generations.previous_generation_id
            started = time.perf_counter()
            rolled_back = await storage.async_rollback_content_generation()
            rollback_s = time.perf_counter() - started

            profiles = ProfileService(storage.repositories.profiles, id_factory=lambda: PROFILE_ID)
            await profiles.async_create_profile(
                name="P5.6 scale qualification",
                preset="intensive",
                timezone="UTC",
                owner_ha_user_ids=("p5-6-ha-user",),
            )
            tracks = TrackService(storage.repositories.tracks, id_factory=lambda: TRACK_ID)
            track = await tracks.async_create_track(
                profile_id=PROFILE_ID,
                name="JMdict scale",
                pack_version_id=PACK_VERSION_ID,
                source_language="ja",
                target_language="en",
                scheduler_settings={"learning_count": 20, "quiz_count": 20},
            )
            constraints = SelectionConstraintService(storage.repositories.tracks)
            selection = SessionSelectionService(
                storage.repositories.tracks,
                storage.repositories.profiles,
                storage.repositories.review_events,
                constraints,
            )
            presentation = CardPresentationService(storage)

            async def pack_lookup() -> dict[str, str] | None:
                return await storage.repositories.tracks.async_pack_version_info(PACK_VERSION_ID)

            async def direction_cards() -> tuple[dict[str, str], ...]:
                return await storage.repositories.tracks.async_resolve_direction_cards(
                    pack_version_id=PACK_VERSION_ID,
                    source_language="ja",
                    target_language="en",
                )

            async def new_cards() -> list[str]:
                return await storage.async_new_cards(PROFILE_ID, TRACK_ID, PACK_VERSION_ID, 20)

            async def due_cards() -> list[str]:
                return await storage.async_due_cards(
                    PROFILE_ID, TRACK_ID, "2026-09-27T00:00:00+00:00", 20
                )

            async def session_candidates() -> tuple[dict[str, Any], ...]:
                return await storage.repositories.tracks.async_session_candidates(
                    profile_id=PROFILE_ID, track_id=TRACK_ID
                )

            candidate_rows = await session_candidates()
            cards = await direction_cards()
            first_card = cards[0]
            started = time.perf_counter()
            prepared = await selection.async_prepare(
                profile_id=PROFILE_ID,
                track_id=TRACK_ID,
                session_type="learn",
                settings={"session_length_cards": 20, "max_new_per_day_cards": 20},
            )
            session_prepare_s = time.perf_counter() - started
            output = {
                "manifest": {
                    "dataset_id": validated.manifest.dataset_id,
                    "dataset_version": validated.manifest.dataset_version,
                    "canonical_content_hash": validated.manifest.canonical_content_hash,
                },
                "package": {
                    "archive_bytes": package.stat().st_size,
                    "database_bytes": package_metadata.path.stat().st_size,
                    "validation_s": package_validation_s,
                    "item_counts": dict(validated.manifest.item_counts),
                },
                "generations": {
                    "build_s": builds,
                    "activation_s": activations,
                    "active_before_rollback": active_before_rollback,
                    "previous_generation": previous_generation,
                    "rollback_s": rollback_s,
                    "active_after_rollback": rolled_back.generation_id,
                    "active_content_db_bytes": storage.content_generations.active_path.stat().st_size,
                },
                "hot_paths": {
                    "pack_lookup": await _sample(pack_lookup, 20),
                    "new_card": {
                        "count": len(await new_cards()),
                        **(await _sample(new_cards, 20)),
                    },
                    "due_card": {
                        "count": len(await due_cards()),
                        **(await _sample(due_cards, 20)),
                    },
                    "direction_cards": {
                        "count": len(cards),
                        **(await _sample(direction_cards, 5)),
                    },
                    "session_candidates": {
                        "count": len(candidate_rows),
                        **(await _sample(session_candidates, 3)),
                    },
                    "session_prepare": {"count": len(prepared), "seconds": session_prepare_s},
                    "presentation": await _sample(
                        lambda: presentation.async_for_card(
                            track_id=TRACK_ID, card_key=first_card["card_key"]
                        ),
                        10,
                    ),
                },
                "track_cards": len(candidate_rows),
                "track": track["track_id"],
            }
            return output
        finally:
            await storage.async_close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--public-key-b64", required=True)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    result = asyncio.run(
        _qualify(
            arguments.package.resolve(),
            arguments.public_key_b64,
            arguments.repository_root.resolve(),
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
