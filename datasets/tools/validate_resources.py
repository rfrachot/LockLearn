"""Validate bootstrap language, normalization, curation, license and source registries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / "datasets" / "resources"

_SCRIPT_RE = re.compile(r"^[A-Z][a-z]{3}$")
_POLICY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_ALLOWED_UNICODE_NORMALIZATION = {"none", "NFC", "NFKC"}
_ALLOWED_CASE_MODES = {"preserve", "casefold"}
_ALLOWED_WHITESPACE_MODES = {"preserve", "trim", "collapse"}
_ALLOWED_PUNCTUATION_MODES = {"preserve", "remove"}


def _load(name: str) -> dict[str, Any]:
    with (RESOURCES / name).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{name}: root must be an object")
    return value


def validate() -> None:
    languages = _load("languages.json")
    licenses = _load("licenses.json")
    sources = _load("sources.json")
    normalization_policies = _load("normalization_policies.json")
    curation_policies = _load("curation_policies.json")

    curation_rows = curation_policies.get("policies", [])
    curation_ids = [row["id"] for row in curation_rows]
    if len(curation_ids) != len(set(curation_ids)):
        raise ValueError("duplicate curation policy IDs")
    allowed_curation_kinds = {
        "card_direction_default",
        "prefer_contextualized_reading",
        "production_complete_term",
        "production_requires_strong_grading",
        "mnemonic_keyword_label",
        "ambiguous_prompt_context_hint",
        "prefer_covered_example",
        "allow_furigana_for_uncovered",
    }
    for row in curation_rows:
        if row.get("version", 0) < 1:
            raise ValueError(f"invalid curation policy version for {row['id']}")
        rules = row.get("rules", [])
        if not rules:
            raise ValueError(f"curation policy {row['id']} has no rules")
        rule_ids = [rule["id"] for rule in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError(f"duplicate curation rule IDs for {row['id']}")
        for rule in rules:
            kind = rule.get("kind")
            if kind not in allowed_curation_kinds:
                raise ValueError(f"unknown curation rule kind {kind} in {row['id']}")
            if kind == "card_direction_default":
                if not rule.get("prompt_facet_key") or not rule.get("answer_facet_key"):
                    raise ValueError(f"card direction rule missing facet keys in {row['id']}")
                if not isinstance(rule.get("enabled_by_default"), bool):
                    raise ValueError(f"card direction rule missing boolean default in {row['id']}")
            elif any(
                field in rule
                for field in ("prompt_facet_key", "answer_facet_key", "enabled_by_default")
            ):
                raise ValueError(f"non-direction curation rule carries direction fields in {row['id']}")

    policy_rows = normalization_policies.get("policies", [])
    policy_ids = [row["id"] for row in policy_rows]
    policy_scripts: dict[str, set[str]] = {}
    if len(policy_ids) != len(set(policy_ids)):
        raise ValueError("duplicate normalization policy IDs")
    for row in policy_rows:
        policy_id = row["id"]
        if not _POLICY_ID_RE.fullmatch(policy_id):
            raise ValueError(f"invalid normalization policy ID: {policy_id}")
        if row.get("normalization_version", 0) < 1:
            raise ValueError(f"invalid normalization_version for {policy_id}")
        if row.get("unicode_normalization") not in _ALLOWED_UNICODE_NORMALIZATION:
            raise ValueError(f"invalid Unicode normalization for {policy_id}")
        if row.get("case_mode") not in _ALLOWED_CASE_MODES:
            raise ValueError(f"invalid case mode for {policy_id}")
        if row.get("whitespace_mode") not in _ALLOWED_WHITESPACE_MODES:
            raise ValueError(f"invalid whitespace mode for {policy_id}")
        if row.get("punctuation_mode") not in _ALLOWED_PUNCTUATION_MODES:
            raise ValueError(f"invalid punctuation mode for {policy_id}")
        scripts = row.get("allowed_scripts", [])
        if len(scripts) != len(set(scripts)):
            raise ValueError(f"duplicate scripts for normalization policy {policy_id}")
        if any(not _SCRIPT_RE.fullmatch(script) for script in scripts):
            raise ValueError(f"invalid ISO 15924 script in normalization policy {policy_id}")
        policy_scripts[policy_id] = set(scripts)

    language_rows = languages.get("languages", [])
    language_tags = [row["tag"] for row in language_rows]
    if len(language_tags) != len(set(language_tags)):
        raise ValueError("duplicate BCP47 language tags")
    if {"en", "fr"} - {row["tag"] for row in language_rows if row["ui_v1"]}:
        raise ValueError("V1 UI must include en and fr")
    if "ja" not in language_tags:
        raise ValueError("Japanese showcase language metadata is required")
    for row in language_rows:
        if row["normalizer"] not in policy_ids:
            raise ValueError(f"unknown normalizer {row['normalizer']} for language {row['tag']}")
        scripts = row.get("scripts", [])
        if len(scripts) != len(set(scripts)):
            raise ValueError(f"duplicate scripts for language {row['tag']}")
        if any(not _SCRIPT_RE.fullmatch(script) for script in scripts):
            raise ValueError(f"invalid ISO 15924 script for language {row['tag']}")
        allowed_scripts = policy_scripts[row["normalizer"]]
        if allowed_scripts and not set(scripts).issubset(allowed_scripts):
            raise ValueError(
                f"language {row['tag']} declares scripts outside normalizer {row['normalizer']}"
            )

    license_rows = licenses.get("licenses", [])
    license_ids = {row["id"] for row in license_rows}
    for row in license_rows:
        if row.get("official_dataset_allowed") and not row.get("commercial_use_allowed"):
            raise ValueError(f"official license is not commercial-compatible: {row['id']}")
        if row.get("official_dataset_allowed") and not row.get("derivatives_allowed"):
            raise ValueError(f"official license forbids derivatives: {row['id']}")

    source_rows = sources.get("sources", [])
    source_ids = [row["id"] for row in source_rows]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source IDs")
    for row in source_rows:
        if row["license_id"] not in license_ids:
            raise ValueError(f"unknown license {row['license_id']} for source {row['id']}")
        if not row.get("commercial_compatible"):
            raise ValueError(f"official candidate is not commercial-compatible: {row['id']}")


if __name__ == "__main__":
    validate()
    print("LockLearn resource registries: OK")
