"""Pack, tag and curation primitives for LockLearn P1.5."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import quote

from .content import validate_stable_id

_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


class PackModelError(ValueError):
    """Raised when pack or curation metadata violates the P1.5 contract."""


def derive_pack_version_id(pack_id: str, version: str) -> str:
    """Derive the immutable pin target for one released pack version."""
    validate_stable_id(pack_id, field="pack_id")
    if not _VERSION_RE.fullmatch(version):
        raise PackModelError(f"invalid pack version: {version!r}")
    return f"{pack_id}:version:{quote(version, safe='._+-')}"


@dataclass(frozen=True, slots=True)
class Tag:
    """Queryable tag attached to learning content."""

    tag_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.tag_id, field="tag_id")
        if self.label == "":
            raise PackModelError("tag label must be None or non-empty")


@dataclass(frozen=True, slots=True)
class Pack:
    """Stable pedagogical selection identity, distinct from dataset content."""

    pack_id: str
    dataset_id: str
    name: str

    def __post_init__(self) -> None:
        validate_stable_id(self.pack_id, field="pack_id")
        validate_stable_id(self.dataset_id, field="dataset_id")
        if not self.name:
            raise PackModelError("pack name is required")


@dataclass(frozen=True, slots=True)
class PackVersion:
    """Immutable released curation version that Tracks can pin later."""

    pack_version_id: str
    pack_id: str
    version: str
    curation_policy_id: str | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.pack_version_id, field="pack_version_id")
        validate_stable_id(self.pack_id, field="pack_id")
        expected = derive_pack_version_id(self.pack_id, self.version)
        if self.pack_version_id != expected:
            raise PackModelError("pack_version_id does not match pack_id + version")
        if self.curation_policy_id is not None:
            validate_stable_id(self.curation_policy_id, field="curation_policy_id")

    @classmethod
    def create(
        cls,
        pack_id: str,
        version: str,
        *,
        curation_policy_id: str | None = None,
    ) -> PackVersion:
        """Create an immutable pin target from the pack identity and version."""
        return cls(
            pack_version_id=derive_pack_version_id(pack_id, version),
            pack_id=pack_id,
            version=version,
            curation_policy_id=curation_policy_id,
        )


class UnlockMetric(StrEnum):
    """Stable prerequisite metrics; evaluation belongs to P3."""

    VERIFIED_CORRECT_COUNT = "verified_correct_count"
    MASTERY = "mastery"
    BOX = "box"


@dataclass(frozen=True, slots=True)
class UnlockCondition:
    """Declarative threshold applied to prerequisite cards."""

    metric: UnlockMetric
    minimum: float

    def __post_init__(self) -> None:
        if self.minimum < 0:
            raise PackModelError("unlock condition minimum must be >= 0")
        if self.metric is UnlockMetric.MASTERY and self.minimum > 1:
            raise PackModelError("mastery unlock threshold must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class PackCardDefault:
    """Default activation state for one stable CardDefinition progression key."""

    card_key: str
    enabled_by_default: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.card_key, field="card_key")


@dataclass(frozen=True, slots=True)
class PackItem:
    """One ordered LearningItem reference inside an immutable PackVersion."""

    pack_version_id: str
    learning_item_id: str
    position: int
    prerequisite_card_keys: tuple[str, ...] = ()
    unlock_when: tuple[UnlockCondition, ...] = ()
    card_defaults: tuple[PackCardDefault, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.pack_version_id, field="pack_version_id")
        validate_stable_id(self.learning_item_id, field="learning_item_id")
        if self.position < 0:
            raise PackModelError("pack item position must be >= 0")

        if len(set(self.prerequisite_card_keys)) != len(self.prerequisite_card_keys):
            raise PackModelError("prerequisite_card_keys must be unique")
        for card_key in self.prerequisite_card_keys:
            validate_stable_id(card_key, field="prerequisite_card_key")

        card_default_keys = tuple(default.card_key for default in self.card_defaults)
        if len(set(card_default_keys)) != len(card_default_keys):
            raise PackModelError("card_defaults must contain each card_key at most once")

        if self.unlock_when and not self.prerequisite_card_keys:
            raise PackModelError("unlock_when requires at least one prerequisite_card_key")

    def default_card_enabled(self, card_key: str) -> bool | None:
        """Return an explicit pack default, or None when the pack does not override it."""
        validate_stable_id(card_key, field="card_key")
        for default in self.card_defaults:
            if default.card_key == card_key:
                return default.enabled_by_default
        return None


@dataclass(frozen=True, slots=True)
class ConfusableGroup:
    """Items that should not be introduced too close together."""

    confusable_group_id: str
    pack_version_id: str
    learning_item_ids: tuple[str, ...]
    min_intro_gap_days: int

    def __post_init__(self) -> None:
        validate_stable_id(self.confusable_group_id, field="confusable_group_id")
        validate_stable_id(self.pack_version_id, field="pack_version_id")
        if len(self.learning_item_ids) < 2:
            raise PackModelError("confusable group requires at least two learning items")
        if len(set(self.learning_item_ids)) != len(self.learning_item_ids):
            raise PackModelError("confusable-group learning_item_ids must be unique")
        for learning_item_id in self.learning_item_ids:
            validate_stable_id(learning_item_id, field="learning_item_id")
        if self.min_intro_gap_days < 1:
            raise PackModelError("confusable group min_intro_gap_days must be >= 1")


@dataclass(frozen=True, slots=True)
class TrackPackPin:
    """Immutable association pinning a Track identity to one PackVersion."""

    track_id: str
    pack_version_id: str

    def __post_init__(self) -> None:
        validate_stable_id(self.track_id, field="track_id")
        validate_stable_id(self.pack_version_id, field="pack_version_id")


class CurationRuleKind(StrEnum):
    """Generic curation directives interpreted by pack builders/selectors."""

    CARD_DIRECTION_DEFAULT = "card_direction_default"
    PREFER_CONTEXTUALIZED_READING = "prefer_contextualized_reading"
    PRODUCTION_COMPLETE_TERM = "production_complete_term"
    PRODUCTION_REQUIRES_STRONG_GRADING = "production_requires_strong_grading"
    MNEMONIC_KEYWORD_LABEL = "mnemonic_keyword_label"
    AMBIGUOUS_PROMPT_CONTEXT_HINT = "ambiguous_prompt_context_hint"
    PREFER_COVERED_EXAMPLE = "prefer_covered_example"
    ALLOW_FURIGANA_FOR_UNCOVERED = "allow_furigana_for_uncovered"


@dataclass(frozen=True, slots=True)
class CurationRule:
    """One versioned, data-owned pedagogical curation directive."""

    rule_id: str
    kind: CurationRuleKind
    enabled: bool = True
    prompt_facet_key: str | None = None
    answer_facet_key: str | None = None
    enabled_by_default: bool | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.rule_id, field="rule_id")
        if self.kind is CurationRuleKind.CARD_DIRECTION_DEFAULT:
            if not self.prompt_facet_key or not self.answer_facet_key:
                raise PackModelError(
                    "card_direction_default requires prompt_facet_key and answer_facet_key"
                )
            if self.enabled_by_default is None:
                raise PackModelError("card_direction_default requires enabled_by_default")
        elif (
            self.prompt_facet_key is not None
            or self.answer_facet_key is not None
            or self.enabled_by_default is not None
        ):
            raise PackModelError(
                "facet/default fields are only valid for card_direction_default rules"
            )


@dataclass(frozen=True, slots=True)
class CurationPolicy:
    """Versioned pack-owned policy; language-specific choices remain data."""

    curation_policy_id: str
    version: int
    rules: tuple[CurationRule, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.curation_policy_id, field="curation_policy_id")
        if self.version < 1:
            raise PackModelError("curation policy version must be >= 1")
        if not self.rules:
            raise PackModelError("curation policy requires at least one rule")
        rule_ids = tuple(rule.rule_id for rule in self.rules)
        if len(set(rule_ids)) != len(rule_ids):
            raise PackModelError("curation rule IDs must be unique")


@dataclass(frozen=True, slots=True)
class PackVersionDiff:
    """Preview metadata for deliberate integration of a newer pack version."""

    from_pack_version_id: str
    to_pack_version_id: str
    added_learning_item_ids: tuple[str, ...] = ()
    removed_learning_item_ids: tuple[str, ...] = ()
    changed_learning_item_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.from_pack_version_id, field="from_pack_version_id")
        validate_stable_id(self.to_pack_version_id, field="to_pack_version_id")
        if self.from_pack_version_id == self.to_pack_version_id:
            raise PackModelError("pack diff must compare two distinct versions")

        buckets = (
            self.added_learning_item_ids,
            self.removed_learning_item_ids,
            self.changed_learning_item_ids,
        )
        for bucket in buckets:
            if len(set(bucket)) != len(bucket):
                raise PackModelError("pack diff item IDs must be unique within each bucket")
            for learning_item_id in bucket:
                validate_stable_id(learning_item_id, field="learning_item_id")

        added, removed, changed = (set(bucket) for bucket in buckets)
        if added & removed or added & changed or removed & changed:
            raise PackModelError("pack diff item buckets must be disjoint")
