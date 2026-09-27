"""Repeatable P5.9 hot-path performance gate."""

from __future__ import annotations

import asyncio
import json
import tempfile
import sys
from datetime import date
from pathlib import Path
from statistics import quantiles
from time import perf_counter
from typing import Any, cast

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from custom_components.locklearn.core.scheduler import SchedulerConfig, SchedulerService
from custom_components.locklearn.storage.database import SQLiteStorage, StoragePaths

SESSION_SAMPLES = 100
SCHEDULER_SAMPLES = 40
SESSION_ANSWER_P95_BUDGET_MS = 100.0
SCHEDULER_DAY_P95_BUDGET_MS = 250.0


def _p95(samples: list[float]) -> float:
    return quantiles(samples, n=20)[18]


async def _session_answer_p95(root: Path) -> float:
    storage = SQLiteStorage(
        StoragePaths(root / "state" / "state.db", root / "content" / "current.db")
    )
    await storage.async_open()
    try:
        samples: list[float] = []
        item = {
            "question_id": "q1",
            "card_key": "locklearn:card:benchmark",
            "learning_item_id": "locklearn:item:benchmark",
            "prompt_facet_id": "locklearn:facet:prompt",
            "answer_facet_id": "locklearn:facet:answer",
            "payload": {},
        }
        for index in range(SESSION_SAMPLES):
            session_id = f"p5-9-session-{index}"
            await storage.async_create_session(
                session_id,
                "p5-9-profile",
                None,
                items=(item,),
            )
            started = perf_counter()
            await storage.async_answer_session(
                session_id,
                1,
                "q1",
                {"kind": "benchmark", "choice": 1},
            )
            samples.append((perf_counter() - started) * 1000)
        return _p95(samples)
    finally:
        await storage.async_close()


def _scheduler_day_p95() -> float:
    # _generate is the production deterministic slot-generation primitive. It
    # is intentionally benchmarked without repository I/O because the V1
    # 250 ms budget is for slot generation itself.
    service = SchedulerService(
        cast(Any, object()),
        cast(Any, object()),
        cast(Any, object()),
        cast(Any, object()),
        cast(Any, object()),
    )
    config = SchedulerConfig(
        profile_id="p5-9-profile",
        version=1,
        timezone="Europe/Paris",
        active_days=(0, 1, 2, 3, 4, 5, 6),
        active_windows=(("08:00", "20:00"),),
        minimum_gap_seconds=1800,
        maximum_notifications_per_hour=4,
        quiet_hours=("22:00", "07:00"),
    )
    samples: list[float] = []
    for _ in range(SCHEDULER_SAMPLES):
        started = perf_counter()
        drafts = service._generate(  # noqa: SLF001 - deliberate performance gate
            config,
            local_date=date(2026, 9, 27),
            daily_push_budget=12,
            not_before_utc=None,
        )
        elapsed = (perf_counter() - started) * 1000
        if len(drafts) != 12:
            raise RuntimeError(f"expected 12 scheduler drafts, got {len(drafts)}")
        samples.append(elapsed)
    return _p95(samples)


async def _run() -> dict[str, float | int]:
    with tempfile.TemporaryDirectory(prefix="locklearn-p5-9-") as temporary:
        session_p95 = await _session_answer_p95(Path(temporary))
    scheduler_p95 = _scheduler_day_p95()
    return {
        "session_samples": SESSION_SAMPLES,
        "session_answer_p95_ms": round(session_p95, 3),
        "session_answer_budget_ms": SESSION_ANSWER_P95_BUDGET_MS,
        "scheduler_samples": SCHEDULER_SAMPLES,
        "scheduler_day_p95_ms": round(scheduler_p95, 3),
        "scheduler_day_budget_ms": SCHEDULER_DAY_P95_BUDGET_MS,
    }


def main() -> int:
    result = asyncio.run(_run())
    print(json.dumps(result, indent=2, sort_keys=True))
    if float(result["session_answer_p95_ms"]) >= SESSION_ANSWER_P95_BUDGET_MS:
        return 1
    if float(result["scheduler_day_p95_ms"]) >= SCHEDULER_DAY_P95_BUDGET_MS:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
