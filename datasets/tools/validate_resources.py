"""Validate bootstrap language, normalization, curation, license and source registries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / "datasets" / "resources"
RUNTIME_RESOURCES = ROOT / "custom_components" / "locklearn" / "datasets" / "resources"

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
    source_builds = _load("source_builds.json")
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
                raise ValueError(
                    f"non-direction curation rule carries direction fields in {row['id']}"
                )

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

    if licenses.get("schema_version") != 2:
        raise ValueError("license registry schema_version must be 2")
    license_rows = licenses.get("licenses", [])
    license_ids = {row["id"] for row in license_rows}
    if len(license_ids) != len(license_rows):
        raise ValueError("duplicate license IDs")
    allowed_license_scopes = {"software", "editorial", "dataset", "asset"}
    for row in license_rows:
        required = {
            "spdx_or_internal_id",
            "name",
            "version",
            "commercial_use_allowed",
            "derivatives_allowed",
            "share_alike",
            "attribution_required",
            "official_dataset_allowed",
            "allowed_scopes",
            "source_url",
            "notes",
        }
        if missing := required - set(row):
            raise ValueError(f"license {row['id']} is missing fields: {sorted(missing)}")
        scopes = row["allowed_scopes"]
        if not scopes or len(scopes) != len(set(scopes)):
            raise ValueError(f"license {row['id']} has invalid allowed_scopes")
        if not set(scopes) <= allowed_license_scopes:
            raise ValueError(f"license {row['id']} has unknown allowed_scopes")
        if row.get("official_dataset_allowed") and not row.get("commercial_use_allowed"):
            raise ValueError(f"official license is not commercial-compatible: {row['id']}")
        if row.get("official_dataset_allowed") and not row.get("derivatives_allowed"):
            raise ValueError(f"official license forbids derivatives: {row['id']}")

    if sources.get("schema_version") != 2:
        raise ValueError("source registry schema_version must be 2")
    source_rows = sources.get("sources", [])
    source_ids = [row["id"] for row in source_rows]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source IDs")
    licenses_by_id = {row["id"]: row for row in license_rows}
    for row in source_rows:
        required = {
            "name",
            "provider",
            "homepage",
            "license_id",
            "license_scope",
            "attribution_template",
            "adapter_id",
            "status",
            "commercial_compatible",
            "refresh_policy",
            "check_interval_days",
            "target_refresh_days",
            "uses",
            "required_provenance",
            "excluded_by_default",
            "notes",
        }
        if missing := required - set(row):
            raise ValueError(f"source {row['id']} is missing fields: {sorted(missing)}")
        license_id = row["license_id"]
        if license_id not in license_ids:
            raise ValueError(f"unknown license {license_id} for source {row['id']}")
        if not row.get("commercial_compatible"):
            raise ValueError(f"official candidate is not commercial-compatible: {row['id']}")
        scope = row["license_scope"]
        if scope == "software" or scope not in allowed_license_scopes:
            raise ValueError(f"invalid content license scope for source {row['id']}")
        if scope not in licenses_by_id[license_id]["allowed_scopes"]:
            raise ValueError(f"license scope is incompatible for source {row['id']}")
        allowlist = row.get("field_allowlist")
        excluded = row.get("excluded_by_default", [])
        if allowlist is not None:
            if len(allowlist) != len(set(allowlist)):
                raise ValueError(f"duplicate field allowlist entries for source {row['id']}")
            if set(allowlist) & set(excluded):
                raise ValueError(f"source allowlist overlaps excluded fields for {row['id']}")
        check_interval = row.get("check_interval_days")
        target_refresh = row.get("target_refresh_days")
        if check_interval is not None and (
            isinstance(check_interval, bool)
            or not isinstance(check_interval, int)
            or check_interval < 1
        ):
            raise ValueError(f"invalid check_interval_days for source {row['id']}")
        if target_refresh is not None and (
            isinstance(target_refresh, bool)
            or not isinstance(target_refresh, int)
            or target_refresh < 1
        ):
            raise ValueError(f"invalid target_refresh_days for source {row['id']}")
        if (
            check_interval is not None
            and target_refresh is not None
            and check_interval > target_refresh
        ):
            raise ValueError(f"source check interval exceeds refresh target for {row['id']}")
        required_provenance = row.get("required_provenance", [])
        if len(required_provenance) != len(set(required_provenance)):
            raise ValueError(f"duplicate required provenance fields for source {row['id']}")

    runtime_sources = json.loads((RUNTIME_RESOURCES / "sources.json").read_text(encoding="utf-8"))
    runtime_licenses = json.loads((RUNTIME_RESOURCES / "licenses.json").read_text(encoding="utf-8"))
    if runtime_sources != sources or runtime_licenses != licenses:
        raise ValueError("runtime source/license registries must match build registries")

    official = json.loads(
        (RUNTIME_RESOURCES / "official_datasets.json").read_text(encoding="utf-8")
    )
    if official.get("schema_version") != 1:
        raise ValueError("official dataset registry schema_version must be 1")
    warning_bytes = official.get("cumulative_installed_warning_bytes")
    if isinstance(warning_bytes, bool) or not isinstance(warning_bytes, int) or warning_bytes < 1:
        raise ValueError("official dataset cumulative warning bytes must be positive")
    official_rows = official.get("datasets")
    if not isinstance(official_rows, list):
        raise ValueError("official dataset registry datasets must be an array")
    official_ids: set[str] = set()
    for row in official_rows:
        if not isinstance(row, dict):
            raise ValueError("official dataset registry rows must be objects")
        dataset_id = row.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id or dataset_id in official_ids:
            raise ValueError("official dataset IDs must be unique non-empty strings")
        official_ids.add(dataset_id)
        catalog_url = row.get("catalog_url")
        if not isinstance(catalog_url, str) or not catalog_url.startswith("https://"):
            raise ValueError(f"official dataset catalog must use HTTPS: {dataset_id}")
        hosts = row.get("artifact_hosts")
        if (
            not isinstance(hosts, list)
            or not hosts
            or len(hosts) != len(set(hosts))
            or any(
                not isinstance(host, str) or not host or "/" in host or ":" in host
                for host in hosts
            )
        ):
            raise ValueError(f"invalid artifact host allowlist for {dataset_id}")

    signing = json.loads((RUNTIME_RESOURCES / "signing_keys.json").read_text(encoding="utf-8"))
    if signing.get("schema_version") != 1 or not isinstance(signing.get("keys"), list):
        raise ValueError("runtime signing key registry is invalid")
    key_ids = [row.get("key_id") for row in signing["keys"] if isinstance(row, dict)]
    if len(key_ids) != len(signing["keys"]) or len(key_ids) != len(set(key_ids)):
        raise ValueError("runtime signing key IDs must be unique")

    if source_builds.get("schema_version") != 1:
        raise ValueError("source build registry schema_version must be 1")
    build_rows = source_builds.get("sources", [])
    if not isinstance(build_rows, list):
        raise ValueError("source build registry sources must be an array")
    build_ids = [row.get("source_id") for row in build_rows]
    if len(build_ids) != len(set(build_ids)):
        raise ValueError("duplicate source build IDs")
    if set(build_ids) != set(source_ids):
        raise ValueError("source build registry must cover every registered source exactly once")
    allowed_fetch_modes = {"direct", "template", "recipe_url", "local"}
    for row in build_rows:
        source_id = row["source_id"]
        mode = row.get("fetch_mode")
        if mode not in allowed_fetch_modes:
            raise ValueError(f"invalid fetch_mode for source {source_id}")
        discovery_url = row.get("discovery_url")
        if not isinstance(discovery_url, str) or not discovery_url:
            raise ValueError(f"source build discovery_url is required for {source_id}")
        download_url = row.get("download_url")
        if mode in {"direct", "template"}:
            if not isinstance(download_url, str) or not download_url:
                raise ValueError(f"source build download_url is required for {source_id}")
        elif download_url is not None:
            raise ValueError(f"source build download_url must be null for {source_id}")
        maximum_bytes = row.get("maximum_bytes")
        if (
            isinstance(maximum_bytes, bool)
            or not isinstance(maximum_bytes, int)
            or maximum_bytes < 1
        ):
            raise ValueError(f"invalid source build maximum_bytes for {source_id}")
        notes = row.get("notes")
        if not isinstance(notes, str) or not notes:
            raise ValueError(f"source build notes are required for {source_id}")


if __name__ == "__main__":
    validate()
    print("LockLearn resource registries: OK")
