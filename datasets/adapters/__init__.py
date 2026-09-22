"""Build-time source adapters."""

from .base import NormalizedRecord, SourceAdapter
from .recommended import (
    JMdictAdapter,
    Kanjidic2Adapter,
    KaikkiAdapter,
    KanjiVGAdapter,
    LockLearnEditorialAdapter,
    TatoebaTextAdapter,
    adapter_for_id,
)

__all__ = [
    "JMdictAdapter",
    "Kanjidic2Adapter",
    "KaikkiAdapter",
    "KanjiVGAdapter",
    "LockLearnEditorialAdapter",
    "NormalizedRecord",
    "SourceAdapter",
    "TatoebaTextAdapter",
    "adapter_for_id",
]
