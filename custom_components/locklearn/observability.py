"""Bounded privacy-safe process-local performance metrics for LockLearn."""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Final

_LOGGER = logging.getLogger(__name__)
DEFAULT_METRIC_SAMPLE_LIMIT: Final = 256
INTERNAL_METRIC_NAMES: Final = frozenset(
    {
        "storage.writer_queue_wait_ms",
        "session.answer_ms",
        "scheduler.slot_generation_ms",
        "content.build_ms",
        "content.activation_ms",
    }
)


@dataclass(slots=True)
class _MetricSeries:
    samples: deque[float]
    count: int = 0
    last_ms: float | None = None
    max_ms: float | None = None


class InternalMetrics:
    """Collect fixed-name timing metrics without identifiers or payload data."""

    def __init__(self, *, sample_limit: int = DEFAULT_METRIC_SAMPLE_LIMIT) -> None:
        if isinstance(sample_limit, bool) or not isinstance(sample_limit, int) or sample_limit <= 0:
            raise ValueError("sample_limit must be a positive integer")
        self._sample_limit = sample_limit
        self._series: dict[str, _MetricSeries] = {}
        self._lock = Lock()

    @property
    def sample_limit(self) -> int:
        return self._sample_limit

    def record(self, name: str, value_ms: float) -> None:
        if name not in INTERNAL_METRIC_NAMES:
            raise ValueError(f"unsupported internal metric: {name}")
        if isinstance(value_ms, bool) or not isinstance(value_ms, (int, float)):
            raise ValueError("metric value must be a finite non-negative number")
        value = float(value_ms)
        if not math.isfinite(value) or value < 0:
            raise ValueError("metric value must be a finite non-negative number")
        with self._lock:
            series = self._series.get(name)
            if series is None:
                series = _MetricSeries(deque(maxlen=self._sample_limit))
                self._series[name] = series
            series.samples.append(value)
            series.count += 1
            series.last_ms = value
            series.max_ms = value if series.max_ms is None else max(series.max_ms, value)
        _LOGGER.debug("locklearn_metric name=%s value_ms=%.3f", name, value)

    def snapshot(self) -> dict[str, dict[str, float | int | None]]:
        with self._lock:
            return {
                name: {
                    "count": series.count,
                    "retained_samples": len(series.samples),
                    "last_ms": series.last_ms,
                    "p95_ms": _nearest_rank_percentile(tuple(series.samples), 0.95),
                    "max_ms": series.max_ms,
                }
                for name, series in sorted(self._series.items())
            }

    def clear(self) -> None:
        with self._lock:
            self._series.clear()


def _nearest_rank_percentile(values: tuple[float, ...], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


INTERNAL_METRICS = InternalMetrics()
