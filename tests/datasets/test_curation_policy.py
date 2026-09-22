"""Dataset-level checks for the official Japanese P1.5 curation policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CURATION = ROOT / "datasets" / "resources" / "curation_policies.json"


def _japanese_policy() -> dict[str, Any]:
    with CURATION.open(encoding="utf-8") as handle:
        root = json.load(handle)
    policies = root["policies"]
    return next(
        policy for policy in policies if policy["id"] == "locklearn:curation:japanese-default"
    )


def test_japanese_isolated_on_and_kun_cards_are_disabled_by_default() -> None:
    policy = _japanese_policy()
    direction_rules = {
        (rule["prompt_facet_key"], rule["answer_facet_key"]): rule["enabled_by_default"]
        for rule in policy["rules"]
        if rule["kind"] == "card_direction_default"
    }

    assert direction_rules[("glyph", "reading_on")] is False
    assert direction_rules[("glyph", "reading_kun")] is False


def test_japanese_curation_declares_contextual_reading_and_complete_production() -> None:
    policy = _japanese_policy()
    kinds = {rule["kind"] for rule in policy["rules"]}

    assert "prefer_contextualized_reading" in kinds
    assert "production_complete_term" in kinds
    assert "production_requires_strong_grading" in kinds


def test_japanese_curation_declares_context_and_example_support_rules() -> None:
    policy = _japanese_policy()
    kinds = {rule["kind"] for rule in policy["rules"]}

    assert "mnemonic_keyword_label" in kinds
    assert "ambiguous_prompt_context_hint" in kinds
    assert "prefer_covered_example" in kinds
    assert "allow_furigana_for_uncovered" in kinds
