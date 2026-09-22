"""Build-time source adapters."""

from .base import NormalizedRecord, SourceAdapter
from .recommended import (
    JMdictAdapter,
    KaikkiAdapter,
    Kanjidic2Adapter,
    KanjiVGAdapter,
    LockLearnEditorialAdapter,
    TatoebaTextAdapter,
    adapter_for_id,
)

__all__ = [
    "JMdictAdapter",
    "KaikkiAdapter",
    "Kanjidic2Adapter",
    "KanjiVGAdapter",
    "LockLearnEditorialAdapter",
    "NormalizedRecord",
    "SourceAdapter",
    "TatoebaTextAdapter",
    "adapter_for_id",
]
