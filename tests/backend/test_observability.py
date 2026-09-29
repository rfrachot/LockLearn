"""P6.7 bounded privacy-safe internal metrics tests."""

from __future__ import annotations

import logging

import pytest

from custom_components.locklearn.observability import InternalMetrics


def test_internal_metrics_are_bounded_and_use_nearest_rank_p95() -> None:
    metrics = InternalMetrics(sample_limit=3)
    for value in (1.0, 2.0, 3.0, 4.0):
        metrics.record("session.answer_ms", value)

    snapshot = metrics.snapshot()["session.answer_ms"]
    assert snapshot == {
        "count": 4,
        "retained_samples": 3,
        "last_ms": 4.0,
        "p95_ms": 4.0,
        "max_ms": 4.0,
    }


def test_internal_metrics_reject_unknown_or_invalid_samples() -> None:
    metrics = InternalMetrics(sample_limit=2)

    with pytest.raises(ValueError, match="unsupported internal metric"):
        metrics.record("private.profile.metric", 1.0)
    for value in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite non-negative"):
            metrics.record("content.activation_ms", value)


def test_internal_metric_log_contains_only_fixed_name_and_timing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    metrics = InternalMetrics(sample_limit=2)
    private_sentinel = "PRIVATE_PROFILE_SENTINEL"

    with caplog.at_level(
        logging.DEBUG,
        logger="custom_components.locklearn.observability",
    ):
        metrics.record("storage.writer_queue_wait_ms", 12.5)

    rendered = caplog.text
    assert "storage.writer_queue_wait_ms" in rendered
    assert "12.500" in rendered
    assert private_sentinel not in rendered
