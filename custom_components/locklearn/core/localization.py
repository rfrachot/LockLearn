"""Generic multilingual locale and normalization primitives for LockLearn P1.4."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,8}$")
_EXTLANG_RE = re.compile(r"^[A-Za-z]{3}$")
_SCRIPT_RE = re.compile(r"^[A-Za-z]{4}$")
_REGION_RE = re.compile(r"^(?:[A-Za-z]{2}|[0-9]{3})$")
_VARIANT_RE = re.compile(r"^(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3})$")
_SINGLETON_RE = re.compile(r"^[A-WY-Za-wy-z0-9]$")
_EXTENSION_RE = re.compile(r"^[A-Za-z0-9]{2,8}$")
_PRIVATE_USE_RE = re.compile(r"^[A-Za-z0-9]{1,8}$")
_POLICY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class LocalizationError(ValueError):
    """Raised when language/script/normalization metadata is invalid."""


@dataclass(frozen=True, slots=True)
class LanguageTag:
    """Canonical modern BCP 47 language tag used by LockLearn."""

    value: str
    language: str
    script: str | None = None
    region: str | None = None

    @property
    def base_language(self) -> str:
        """Return the primary language subtag used for fallback."""
        return self.language


def parse_language_tag(value: str) -> LanguageTag:
    """Parse and canonicalize the modern BCP 47 langtag/private-use syntax.

    Legacy grandfathered tags are intentionally rejected; LockLearn-controlled
    datasets use modern BCP 47 tags so fallback remains deterministic.
    """
    if not value or "_" in value or not value.isascii():
        raise LocalizationError(f"invalid BCP 47 language tag: {value!r}")

    parts = value.split("-")
    if any(not part for part in parts):
        raise LocalizationError(f"invalid BCP 47 language tag: {value!r}")

    if parts[0].lower() == "x":
        if len(parts) == 1 or any(not _PRIVATE_USE_RE.fullmatch(part) for part in parts[1:]):
            raise LocalizationError(f"invalid BCP 47 private-use tag: {value!r}")
        canonical = "-".join(part.lower() for part in parts)
        return LanguageTag(canonical, canonical)

    index = 0
    primary = parts[index]
    if not _LANGUAGE_RE.fullmatch(primary):
        raise LocalizationError(f"invalid BCP 47 primary language: {primary!r}")
    language = primary.lower()
    canonical_parts = [language]
    index += 1

    if len(primary) <= 3:
        extlang_count = 0
        while index < len(parts) and extlang_count < 3 and _EXTLANG_RE.fullmatch(parts[index]):
            canonical_parts.append(parts[index].lower())
            extlang_count += 1
            index += 1

    script: str | None = None
    if index < len(parts) and _SCRIPT_RE.fullmatch(parts[index]):
        script = canonicalize_script_code(parts[index])
        canonical_parts.append(script)
        index += 1

    region: str | None = None
    if index < len(parts) and _REGION_RE.fullmatch(parts[index]):
        region_part = parts[index]
        region = region_part.upper() if region_part.isalpha() else region_part
        canonical_parts.append(region)
        index += 1

    variants: set[str] = set()
    while index < len(parts) and _VARIANT_RE.fullmatch(parts[index]):
        variant = parts[index].lower()
        if variant in variants:
            raise LocalizationError(f"duplicate BCP 47 variant: {variant!r}")
        variants.add(variant)
        canonical_parts.append(variant)
        index += 1

    extension_singletons: set[str] = set()
    while index < len(parts) and _SINGLETON_RE.fullmatch(parts[index]):
        singleton = parts[index].lower()
        if singleton in extension_singletons:
            raise LocalizationError(f"duplicate BCP 47 extension singleton: {singleton!r}")
        extension_singletons.add(singleton)
        canonical_parts.append(singleton)
        index += 1

        extension_start = index
        while index < len(parts) and _EXTENSION_RE.fullmatch(parts[index]):
            canonical_parts.append(parts[index].lower())
            index += 1
        if index == extension_start:
            raise LocalizationError(f"BCP 47 extension {singleton!r} requires a value")

    if index < len(parts) and parts[index].lower() == "x":
        canonical_parts.append("x")
        index += 1
        private_start = index
        while index < len(parts) and _PRIVATE_USE_RE.fullmatch(parts[index]):
            canonical_parts.append(parts[index].lower())
            index += 1
        if index == private_start:
            raise LocalizationError("BCP 47 private-use marker requires a value")

    if index != len(parts):
        raise LocalizationError(f"invalid BCP 47 language tag: {value!r}")

    return LanguageTag("-".join(canonical_parts), language, script, region)


def canonicalize_language_tag(value: str) -> str:
    """Return the canonical casing used by LockLearn for a BCP 47 tag."""
    return parse_language_tag(value).value


def canonicalize_script_code(value: str) -> str:
    """Validate the structural ISO 15924 alpha-code form and canonicalize casing."""
    if not value.isascii() or not _SCRIPT_RE.fullmatch(value):
        raise LocalizationError(f"invalid ISO 15924 script code: {value!r}")
    return value.title()


class UnicodeNormalization(StrEnum):
    """Unicode normalization transform selected by a data policy."""

    NONE = "none"
    NFC = "NFC"
    NFKC = "NFKC"


class CaseMode(StrEnum):
    """Case handling selected by a normalization policy."""

    PRESERVE = "preserve"
    CASEFOLD = "casefold"


class WhitespaceMode(StrEnum):
    """Whitespace handling selected by a normalization policy."""

    PRESERVE = "preserve"
    TRIM = "trim"
    COLLAPSE = "collapse"


class PunctuationMode(StrEnum):
    """Unicode punctuation handling selected by a normalization policy."""

    PRESERVE = "preserve"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class NormalizationPolicy:
    """Generic, versioned normalization policy supplied by dataset metadata."""

    policy_id: str
    normalization_version: int
    unicode_normalization: UnicodeNormalization = UnicodeNormalization.NFC
    case_mode: CaseMode = CaseMode.PRESERVE
    whitespace_mode: WhitespaceMode = WhitespaceMode.COLLAPSE
    punctuation_mode: PunctuationMode = PunctuationMode.PRESERVE
    allowed_scripts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _POLICY_ID_RE.fullmatch(self.policy_id):
            raise LocalizationError(f"invalid normalization policy id: {self.policy_id!r}")
        if self.normalization_version < 1:
            raise LocalizationError("normalization_version must be >= 1")

        canonical_scripts = tuple(
            canonicalize_script_code(script) for script in self.allowed_scripts
        )
        if len(set(canonical_scripts)) != len(canonical_scripts):
            raise LocalizationError("normalization policy scripts must be unique")
        object.__setattr__(self, "allowed_scripts", canonical_scripts)


def normalization_rebuild_required(
    previous: NormalizationPolicy,
    current: NormalizationPolicy,
) -> bool:
    """Return whether indexes derived from a policy must be rebuilt.

    Reusing a version after changing behavior is invalid because persisted
    normalized values would become ambiguous.
    """
    if previous.policy_id != current.policy_id:
        return True

    previous_behavior = (
        previous.unicode_normalization,
        previous.case_mode,
        previous.whitespace_mode,
        previous.punctuation_mode,
        previous.allowed_scripts,
    )
    current_behavior = (
        current.unicode_normalization,
        current.case_mode,
        current.whitespace_mode,
        current.punctuation_mode,
        current.allowed_scripts,
    )
    behavior_changed = previous_behavior != current_behavior

    if behavior_changed and current.normalization_version <= previous.normalization_version:
        raise LocalizationError(
            "changed normalization behavior requires a higher normalization_version"
        )
    if current.normalization_version < previous.normalization_version:
        raise LocalizationError("normalization_version cannot move backwards")
    return behavior_changed or current.normalization_version != previous.normalization_version


def normalize_text(
    text: str,
    policy: NormalizationPolicy,
    *,
    script: str | None = None,
) -> str:
    """Normalize text according to an explicit generic policy."""
    if not isinstance(text, str):
        raise LocalizationError("text to normalize must be a string")

    canonical_script = canonicalize_script_code(script) if script is not None else None
    if policy.allowed_scripts:
        if canonical_script is None:
            raise LocalizationError(f"normalization policy {policy.policy_id!r} requires a script")
        if canonical_script not in policy.allowed_scripts:
            raise LocalizationError(
                f"script {canonical_script!r} is not allowed by policy {policy.policy_id!r}"
            )

    result = text
    if policy.unicode_normalization is UnicodeNormalization.NFC:
        result = unicodedata.normalize("NFC", result)
    elif policy.unicode_normalization is UnicodeNormalization.NFKC:
        result = unicodedata.normalize("NFKC", result)

    if policy.case_mode is CaseMode.CASEFOLD:
        result = result.casefold()

    if policy.punctuation_mode is PunctuationMode.REMOVE:
        result = "".join(
            character for character in result if not unicodedata.category(character).startswith("P")
        )

    if policy.whitespace_mode is WhitespaceMode.TRIM:
        result = result.strip()
    elif policy.whitespace_mode is WhitespaceMode.COLLAPSE:
        result = " ".join(result.split())

    return result


def language_fallback_chain(
    requested_tag: str,
    *,
    default_tag: str | None = None,
    final_fallback_tag: str | None = None,
) -> tuple[str, ...]:
    """Return exact -> base -> explicit default/final fallback, deduplicated."""
    requested = parse_language_tag(requested_tag)
    candidates = [requested.value]

    if requested.base_language != requested.value:
        candidates.append(requested.base_language)
    if default_tag is not None:
        candidates.append(canonicalize_language_tag(default_tag))
    if final_fallback_tag is not None:
        candidates.append(canonicalize_language_tag(final_fallback_tag))

    result: list[str] = []
    for candidate in candidates:
        if candidate not in result:
            result.append(candidate)
    return tuple(result)


def resolve_localized_value[T](
    values: Mapping[str, T],
    requested_tag: str,
    *,
    default_tag: str | None = None,
    final_fallback_tag: str | None = None,
) -> T | None:
    """Resolve an existing localized value without inventing a translation."""
    canonical_values: dict[str, T] = {}
    for tag, value in values.items():
        canonical_tag = canonicalize_language_tag(tag)
        if canonical_tag in canonical_values:
            raise LocalizationError(f"multiple localized values canonicalize to {canonical_tag!r}")
        canonical_values[canonical_tag] = value

    for candidate in language_fallback_chain(
        requested_tag,
        default_tag=default_tag,
        final_fallback_tag=final_fallback_tag,
    ):
        if candidate in canonical_values:
            return canonical_values[candidate]
    return None
