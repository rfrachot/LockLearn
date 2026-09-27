"""P6.8 shared-runner hot-path gate with jitter-resistant aggregation."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from statistics import median
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import scripts.p5_9_performance as p5_9_performance  # noqa: E402

ATTEMPTS = 3
GATED_METRICS = (
    ("session_answer_p95_ms", p5_9_performance.SESSION_ANSWER_P95_BUDGET_MS),
    ("next_card_p95_ms", p5_9_performance.NEXT_CARD_P95_BUDGET_MS),
    ("scheduler_day_p95_ms", p5_9_performance.SCHEDULER_DAY_P95_BUDGET_MS),
)


async def _run() -> dict[str, Any]:
    attempts = [await p5_9_performance._run() for _ in range(ATTEMPTS)]
    medians = {
        metric: round(median(float(run[metric]) for run in attempts), 3)
        for metric, _budget in GATED_METRICS
    }
    return {
        "policy": {
            "attempts": ATTEMPTS,
            "aggregation": "median of per-attempt p95 values",
            "purpose": "shared GitHub runner jitter resistance",
            "budgets_unchanged": True,
        },
        "attempts": attempts,
        "median_p95_ms": medians,
        "budgets_ms": {metric: budget for metric, budget in GATED_METRICS},
    }


def _passes(result: dict[str, Any]) -> bool:
    medians = result["median_p95_ms"]
    return all(float(medians[metric]) < budget for metric, budget in GATED_METRICS)


def main() -> int:
    result = asyncio.run(_run())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if _passes(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
