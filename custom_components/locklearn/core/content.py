"""Canonical content-domain identities and grading metadata for LockLearn P1."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import quote

from .localization import (
    NormalizationPolicy,
    canonicalize_script_code,
    normalize_text,
    parse_language_tag,
)

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*(?::[A-Za-z0-9._~%+-]+)+$")
_CARD_SEPARATOR = "\x1f"
_LICENSE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*$")


class ContentModelError(ValueError):
    """Raised when canonical content invariants are violated."""


def validate_stable_id(value: str, *, field: str = "id") -> str:
    """Validate a namespaced, transport-safe stable identifier."""
    if not _STABLE_ID_RE.fullmatch(value):
        raise ContentModelError(f"{field} must be a namespaced stable id: {value!r}")
    return value


def validate_license_id(value: str) -> str:
    """Validate the registry key used for SPDX/internal license identifiers."""
    if not _LICENSE_ID_RE.fullmatch(value):
        raise ContentModelError(f"invalid license_id: {value!r}")
    return value


def make_stable_id(namespace: str, *parts: str) -> str:
    """Build a deterministic ID from stable source-owned components.

    Mutable labels, translations and display text must never be supplied as
    parts. Callers should prefer upstream stable record identifiers.
    """
    if not namespace or not parts or any(not part for part in parts):
        raise ContentModelError("stable IDs require a namespace and non-empty parts")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._~-]*", namespace):
        raise ContentModelError(f"invalid stable-id namespace: {namespace!r}")
    encoded = [quote(part, safe="._~+-") for part in parts]
    return validate_stable_id(":".join((namespace, *encoded)))


def _card_digest(learning_item_id: str, prompt_facet_id: str, answer_facet_id: str) -> str:
    for field, value in (
        ("learning_item_id", learning_item_id),
        ("prompt_facet_id", prompt_facet_id),
        ("answer_facet_id", answer_facet_id),
    ):
        validate_stable_id(value, field=field)
    canonical = _CARD_SEPARATOR.join((learning_item_id, prompt_facet_id, answer_facet_id))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def derive_card_key(learning_item_id: str, prompt_facet_id: str, answer_facet_id: str) -> str:
    """Derive progression identity from the exact tested facet pair."""
    return f"locklearn:card:{_card_digest(learning_item_id, prompt_facet_id, answer_facet_id)}"


def derive_card_definition_id(
    learning_item_id: str, prompt_facet_id: str, answer_facet_id: str
) -> str:
    """Derive the stable CardDefinition identifier from immutable identities."""
    return f"locklearn:carddef:{_card_digest(learning_item_id, prompt_facet_id, answer_facet_id)}"


class ConceptType(StrEnum):
    """Source-native concept categories understood by the generic core."""

    LEXICAL = "lexical"
    GRAMMAR = "grammar"
    PEDAGOGICAL = "pedagogical"
    CUSTOM = "custom"


class ContentType(StrEnum):
    """V1 learning-item categories without language-specific behavior."""

    VOCABULARY = "vocabulary"
    KANJI = "kanji"
    GRAMMAR = "grammar"
    EXPRESSION = "expression"
    SENTENCE = "sentence"
    CULTURE = "culture"
    CONJUGATION = "conjugation"
    CUSTOM = "custom"


class FacetKind(StrEnum):
    """Rendering modality of a facet, not a pedagogical direction."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    STRUCTURED = "structured"


class AnswerSemantics(StrEnum):
    """Shape of the answer expected by a CardDefinition."""

    SINGLE_VALUE = "single_value"
    SET_OF_VALID_VALUES = "set_of_valid_values"
    ORDERED_SEQUENCE = "ordered_sequence"
    FREE_TEXT = "free_text"
    RESERVED_RULE_BASED = "reserved_rule_based"


class GradingPolicyKind(StrEnum):
    """Stable grading-policy kinds; execution is implemented in later phases."""

    EXACT = "exact"
    ANY_OF = "any_of"
    FUZZY_NORMALIZED = "fuzzy_normalized"
    RULE_BASED_RESERVED = "rule_based_reserved"


class GradingOutcome(StrEnum):
    """Grading result without conflating uncertainty with a wrong answer."""

    CORRECT = "correct"
    WRONG = "wrong"
    UNRECOGNIZED = "unrecognized"

    @property
    def is_definitive_failure(self) -> bool:
        """Return whether downstream planning may safely treat this as wrong."""
        return self is GradingOutcome.WRONG


@dataclass(frozen=True, slots=True)
class GradingPolicy:
    """Versioned grading metadata that never participates in card identity."""

    kind: GradingPolicyKind
    policy_version: int = 1

    def __post_init__(self) -> None:
        if self.policy_version < 1:
            raise ContentModelError("grading policy_version must be >= 1")


class AlignmentReviewStatus(StrEnum):
    """Human-review state for an explicit cross-source semantic alignment."""

    PROPOSED = "proposed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class StableObjectType(StrEnum):
    """Object kinds that may receive an explicit released-ID migration."""

    CONCEPT = "concept"
    TERM = "term"
    LEARNING_ITEM = "learning_item"
    FACET = "facet"
    CARD_DEFINITION = "card_definition"
    CARD_KEY = "card_key"


@dataclass(frozen=True, slots=True)
class Source:
    """An upstream source identity; detailed licensing lands in P1.6."""

    source_id: str
    name: str
    provider: str
    license_id: str

    def __post_init__(self) -> None:
        validate_stable_id(self.source_id, field="source_id")
        validate_license_id(self.license_id)
        if not self.name or not self.provider:
            raise ContentModelError("source name and provider are required")


@dataclass(frozen=True, slots=True)
class Dataset:
    """A versioned content corpus assembled from one or more declared sources."""

    dataset_id: str
    version: str
    source_ids: tuple[str, ...]
    license_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.dataset_id, field="dataset_id")
        if not self.version:
            raise ContentModelError("dataset version is required")
        if not self.source_ids:
            raise ContentModelError("dataset must declare at least one source")
        if not self.license_ids:
            raise ContentModelError("dataset must declare at least one license")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ContentModelError("dataset source_ids must be unique")
        if len(set(self.license_ids)) != len(self.license_ids):
            raise ContentModelError("dataset license_ids must be unique")
        for source_id in self.source_ids:
            validate_stable_id(source_id, field="source_id")
        for license_id in self.license_ids:
            validate_license_id(license_id)


@dataclass(frozen=True, slots=True)
class Concept:
    """A source-native semantic unit; never inferred across independent sources."""

    concept_id: str
    dataset_id: str
    source_id: str
    source_record_id: str
    source_sense_id: str | None
    concept_type: ConceptType

    def __post_init__(self) -> None:
        validate_stable_id(self.concept_id, field="concept_id")
        validate_stable_id(self.dataset_id, field="dataset_id")
        validate_stable_id(self.source_id, field="source_id")
        if not self.source_record_id:
            raise ContentModelError("source_record_id is required")
        if self.source_sense_id == "":
            raise ContentModelError("source_sense_id must be None or non-empty")


@dataclass(frozen=True, slots=True)
class Term:
    """A linguistic representation with versioned, non-identifying normalization."""

    term_id: str
    dataset_id: str
    language_tag: str
    text: str
    script: str | None = None
    normalized_text: str | None = None
    normalization_version: int | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.term_id, field="term_id")
        validate_stable_id(self.dataset_id, field="dataset_id")
        if not self.text:
            raise ContentModelError("term text is required")

        try:
            parsed_language = parse_language_tag(self.language_tag)
            canonical_script = (
                canonicalize_script_code(self.script)
                if self.script is not None
                else parsed_language.script
            )
        except ValueError as err:
            raise ContentModelError(str(err)) from err

        if (
            parsed_language.script is not None
            and canonical_script is not None
            and parsed_language.script != canonical_script
        ):
            raise ContentModelError(
                "Term.script must match the explicit script in language_tag"
            )

        object.__setattr__(self, "language_tag", parsed_language.value)
        object.__setattr__(self, "script", canonical_script)

        if (self.normalized_text is None) != (self.normalization_version is None):
            raise ContentModelError(
                "normalized_text and normalization_version must be set together"
            )
        if self.normalized_text == "":
            raise ContentModelError("normalized_text must be None or non-empty")
        if self.normalization_version is not None and self.normalization_version < 1:
            raise ContentModelError("normalization_version must be >= 1")

    def with_normalization(self, policy: NormalizationPolicy) -> Term:
        """Return the same stable Term identity with policy-derived normalized text."""
        normalized = normalize_text(self.text, policy, script=self.script)
        return Term(
            term_id=self.term_id,
            dataset_id=self.dataset_id,
            language_tag=self.language_tag,
            text=self.text,
            script=self.script,
            normalized_text=normalized,
            normalization_version=policy.normalization_version,
        )


@dataclass(frozen=True, slots=True)
class LearningItem:
    """An interrogable pedagogical object connected to source-native concepts."""

    learning_item_id: str
    dataset_id: str
    content_type: ContentType
    concept_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.learning_item_id, field="learning_item_id")
        validate_stable_id(self.dataset_id, field="dataset_id")
        if not self.concept_ids:
            raise ContentModelError("learning item must reference at least one concept")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ContentModelError("learning-item concept_ids must be unique")
        for concept_id in self.concept_ids:
            validate_stable_id(concept_id, field="concept_id")


@dataclass(frozen=True, slots=True)
class Facet:
    """One addressable face of a LearningItem."""

    facet_id: str
    learning_item_id: str
    kind: FacetKind
    key: str
    language_tag: str | None = None
    script: str | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.facet_id, field="facet_id")
        validate_stable_id(self.learning_item_id, field="learning_item_id")
        if not self.key:
            raise ContentModelError("facet key is required")


@dataclass(frozen=True, slots=True)
class CardDefinition:
    """A stable prompt-facet -> answer-facet skill definition."""

    card_definition_id: str
    card_key: str
    learning_item_id: str
    prompt_facet_id: str
    answer_facet_id: str
    answer_semantics: AnswerSemantics = AnswerSemantics.SINGLE_VALUE
    grading_policy: GradingPolicy = GradingPolicy(GradingPolicyKind.EXACT)
    context_hint_facet_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.card_definition_id, field="card_definition_id")
        validate_stable_id(self.card_key, field="card_key")
        expected_key = derive_card_key(
            self.learning_item_id, self.prompt_facet_id, self.answer_facet_id
        )
        expected_id = derive_card_definition_id(
            self.learning_item_id, self.prompt_facet_id, self.answer_facet_id
        )
        if self.card_key != expected_key:
            raise ContentModelError("card_key does not match its immutable facet identity")
        if self.card_definition_id != expected_id:
            raise ContentModelError(
                "card_definition_id does not match its immutable facet identity"
            )
        if self.prompt_facet_id == self.answer_facet_id:
            raise ContentModelError("prompt and answer facets must be distinct")
        if len(set(self.context_hint_facet_ids)) != len(self.context_hint_facet_ids):
            raise ContentModelError("context_hint_facet_ids must be unique")
        for facet_id in self.context_hint_facet_ids:
            validate_stable_id(facet_id, field="context_hint_facet_id")
            if facet_id == self.answer_facet_id:
                raise ContentModelError("answer facet cannot also be a context hint")

    @classmethod
    def from_facets(
        cls,
        learning_item: LearningItem,
        prompt: Facet,
        answer: Facet,
        *,
        answer_semantics: AnswerSemantics = AnswerSemantics.SINGLE_VALUE,
        grading_policy: GradingPolicy | None = None,
        context_hints: tuple[Facet, ...] = (),
    ) -> CardDefinition:
        """Construct a card only when all referenced facets belong to one item."""
        if prompt.learning_item_id != learning_item.learning_item_id:
            raise ContentModelError("prompt facet belongs to a different LearningItem")
        if answer.learning_item_id != learning_item.learning_item_id:
            raise ContentModelError("answer facet belongs to a different LearningItem")
        if len({hint.facet_id for hint in context_hints}) != len(context_hints):
            raise ContentModelError("context hint facets must be unique")
        for hint in context_hints:
            if hint.learning_item_id != learning_item.learning_item_id:
                raise ContentModelError("context hint facet belongs to a different LearningItem")
            if hint.facet_id == answer.facet_id:
                raise ContentModelError("answer facet cannot also be a context hint")
        card_key = derive_card_key(
            learning_item.learning_item_id,
            prompt.facet_id,
            answer.facet_id,
        )
        return cls(
            card_definition_id=derive_card_definition_id(
                learning_item.learning_item_id,
                prompt.facet_id,
                answer.facet_id,
            ),
            card_key=card_key,
            learning_item_id=learning_item.learning_item_id,
            prompt_facet_id=prompt.facet_id,
            answer_facet_id=answer.facet_id,
            answer_semantics=answer_semantics,
            grading_policy=grading_policy
            if grading_policy is not None
            else GradingPolicy(GradingPolicyKind.EXACT),
            context_hint_facet_ids=tuple(hint.facet_id for hint in context_hints),
        )


@dataclass(frozen=True, slots=True)
class ConceptAlignment:
    """Explicit, provenance-friendly semantic relation between independent concepts."""

    source_concept_id: str
    target_concept_id: str
    confidence: float
    method: str
    review_status: AlignmentReviewStatus = AlignmentReviewStatus.PROPOSED

    def __post_init__(self) -> None:
        validate_stable_id(self.source_concept_id, field="source_concept_id")
        validate_stable_id(self.target_concept_id, field="target_concept_id")
        if self.source_concept_id == self.target_concept_id:
            raise ContentModelError("concept alignment must connect distinct concepts")
        if not 0.0 <= self.confidence <= 1.0:
            raise ContentModelError("alignment confidence must be within [0, 1]")
        if not self.method:
            raise ContentModelError("alignment method is required")


@dataclass(frozen=True, slots=True)
class StableIdMigration:
    """Explicit mapping required when a released stable ID must change."""

    object_type: StableObjectType
    dataset_id: str
    old_id: str
    new_id: str
    introduced_in_version: str
    reason: str

    def __post_init__(self) -> None:
        validate_stable_id(self.dataset_id, field="dataset_id")
        validate_stable_id(self.old_id, field="old_id")
        validate_stable_id(self.new_id, field="new_id")
        if self.old_id == self.new_id:
            raise ContentModelError("ID migration must change the identifier")
        if not self.introduced_in_version:
            raise ContentModelError("ID migration requires a dataset version")
        if not self.reason:
            raise ContentModelError("ID migration requires a reason")
