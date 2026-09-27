"""Central V1 dataset artifact, cache, and activation storage budgets."""

from __future__ import annotations

from typing import Final

_MIB: Final = 1024 * 1024
OFFICIAL_DATASET_ARTIFACT_DEFAULT_MAX_BYTES: Final = 150 * _MIB
DATASET_CACHE_WARNING_DEFAULT_BYTES: Final = 500 * _MIB
ACTIVATION_SAFETY_MARGIN_DEFAULT_BYTES: Final = 32 * _MIB


def activation_required_free_disk(
    generated_content_bytes: int,
    *,
    margin_bytes: int = ACTIVATION_SAFETY_MARGIN_DEFAULT_BYTES,
) -> int:
    """Return the V1 activation floor: 2x generated content plus safety margin."""
    if (
        isinstance(generated_content_bytes, bool)
        or not isinstance(generated_content_bytes, int)
        or generated_content_bytes < 0
    ):
        raise ValueError("generated_content_bytes must be an integer >= 0")
    if isinstance(margin_bytes, bool) or not isinstance(margin_bytes, int) or margin_bytes < 0:
        raise ValueError("margin_bytes must be an integer >= 0")
    return generated_content_bytes * 2 + margin_bytes
