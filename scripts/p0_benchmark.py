#!/usr/bin/env python3
"""Repeatable P0 SQLite/session micro-benchmark using representative fixtures."""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import quantiles
from time import perf_counter

from custom_components.locklearn.storage.database import SQLiteStorage, StoragePaths
from custom_components.locklearn.storage.schema import CONTENT_SCHEMA

CARD_COUNT = 60_000
PROGRESS_COUNT = 20_000
QUERY_SAMPLES = 100
ANSWER_SAMPLES = 100


def _p95(samples: list[float]) -> float:
    return quantiles(samples, n=20)[18]


def _make_package(path: Path, offset: int, count: int) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(CONTENT_SCHEMA)
        connection.execute("INSERT INTO schema_version VALUES (1)")
        connection.executemany(
            "INSERT INTO card_definitions VALUES (?, 'benchmark-pack', ?)",
            ((f"card-{index}", index) for index in range(offset, offset + count)),
        )
        connection.commit()
    finally:
        connection.close()


async def _run(root: Path) -> dict[str, float | int]:
    paths = StoragePaths(root / "state" / "state.db", root / "content" / "current.db")
    storage = SQLiteStorage(paths)
    await storage.async_open()
    packages: list[Path] = []
    per_package = CARD_COUNT // 3
    for number in range(3):
        package = root / f"package-{number}.db"
        _make_package(package, number * per_package, per_package)
        packages.append(package)

    merge_target = root / "generation" / "current.db"
    started = perf_counter()
    merged = await storage.async_build_content_generation(packages, merge_target)
    merge_seconds = perf_counter() - started
    await storage.async_close()
    paths.content_db.unlink()
    merge_target.replace(paths.content_db)

    due_at = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    state = sqlite3.connect(paths.state_db)
    try:
        state.executemany(
            "INSERT INTO progress VALUES ('profile', 'track', ?, 'review', ?)",
            ((f"card-{index}", due_at) for index in range(PROGRESS_COUNT)),
        )
        state.commit()
    finally:
        state.close()

    storage = SQLiteStorage(paths)
    await storage.async_open()
    try:
        due_samples: list[float] = []
        new_samples: list[float] = []
        for _ in range(QUERY_SAMPLES):
            started = perf_counter()
            await storage.async_due_cards("profile", "track", datetime.now(UTC).isoformat(), 20)
            due_samples.append((perf_counter() - started) * 1000)
            started = perf_counter()
            await storage.async_new_cards("profile", "track", "benchmark-pack", 20)
            new_samples.append((perf_counter() - started) * 1000)

        answer_samples: list[float] = []
        for index in range(ANSWER_SAMPLES):
            session_id = f"session-{index}"
            await storage.async_create_session(session_id, "profile", "track")
            started = perf_counter()
            await storage.async_answer_session(session_id, 1, "question", {"choice": 1})
            answer_samples.append((perf_counter() - started) * 1000)

        return {
            "cards": merged,
            "progress_rows": PROGRESS_COUNT,
            "content_merge_seconds": round(merge_seconds, 3),
            "due_query_p95_ms": round(_p95(due_samples), 3),
            "new_query_p95_ms": round(_p95(new_samples), 3),
            "session_answer_p95_ms": round(_p95(answer_samples), 3),
        }
    finally:
        await storage.async_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path)
    args = parser.parse_args()
    if args.workdir is not None:
        args.workdir.mkdir(parents=True, exist_ok=True)
        result = asyncio.run(_run(args.workdir))
    else:
        with tempfile.TemporaryDirectory(prefix="locklearn-p0-") as temporary:
            result = asyncio.run(_run(Path(temporary)))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
