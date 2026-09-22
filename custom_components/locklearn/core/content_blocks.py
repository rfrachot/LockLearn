"""Content-block and safe rich-text primitives for LockLearn P1.3."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .content import validate_stable_id

MAX_RICH_TEXT_DEPTH = 16
MAX_RICH_TEXT_NODES = 512
MAX_RICH_TEXT_TEXT_LENGTH = 16_384


class ContentBlockError(ValueError):
    """Raised when P1.3 content metadata violates its contract."""


class ContentBlockKind(StrEnum):
    """Supported content modalities; renderers may implement a subset."""

    TEXT = "text"
    RICH_TEXT = "rich_text"
    IMAGE = "image"
    AUDIO = "audio"


class ContentRole(StrEnum):
    """Semantic purpose of a content block."""

    PROMPT = "prompt"
    ANSWER = "answer"
    HINT = "hint"
    EXAMPLE = "example"
    MNEMONIC = "mnemonic"
    METADATA = "metadata"


class MaskStrategy(StrEnum):
    """How answer-bearing content may be hidden for retrieval."""

    NONE = "none"
    HIDE_BLOCK = "hide_block"
    BLANK_TERM = "blank_term"
    BLANK_SPAN = "blank_span"
    REPLACE_WITH_PLACEHOLDER = "replace_with_placeholder"


@dataclass(frozen=True, slots=True)
class RubySegment:
    """A text segment with optional reading; no Unicode offsets are stored."""

    text: str
    reading: str | None = None

    def __post_init__(self) -> None:
        if not self.text:
            raise ContentBlockError("ruby segment text must be non-empty")
        if self.reading == "":
            raise ContentBlockError("ruby segment reading must be None or non-empty")


@dataclass(frozen=True, slots=True)
class TextContent:
    """Structured text payload with optional reading/furigana metadata."""

    text: str
    reading: str | None = None
    furigana: str | None = None
    ruby_segments: tuple[RubySegment, ...] = ()

    def __post_init__(self) -> None:
        if not self.text:
            raise ContentBlockError("text content must be non-empty")
        if self.reading == "":
            raise ContentBlockError("reading must be None or non-empty")
        if self.furigana == "":
            raise ContentBlockError("furigana must be None or non-empty")
        if self.ruby_segments:
            rendered = "".join(segment.text for segment in self.ruby_segments)
            if rendered != self.text:
                raise ContentBlockError(
                    "ruby segment text must concatenate to the visible text exactly"
                )


class RichTextNodeType(StrEnum):
    """Closed rich-text AST allowlist."""

    PARAGRAPH = "paragraph"
    TEXT = "text"
    EMPHASIS = "emphasis"
    STRONG = "strong"
    INLINE_CODE = "inline_code"
    LINE_BREAK = "line_break"
    RUBY = "ruby"


_CONTAINER_NODE_TYPES = {
    RichTextNodeType.PARAGRAPH,
    RichTextNodeType.EMPHASIS,
    RichTextNodeType.STRONG,
}
_TEXT_NODE_TYPES = {
    RichTextNodeType.TEXT,
    RichTextNodeType.INLINE_CODE,
}


@dataclass(frozen=True, slots=True)
class RichTextNode:
    """One validated node in the canonical rich-text AST."""

    node_type: RichTextNodeType
    text: str | None = None
    reading: str | None = None
    children: tuple[RichTextNode, ...] = ()

    def __post_init__(self) -> None:
        if self.node_type in _CONTAINER_NODE_TYPES:
            if self.text is not None or self.reading is not None or not self.children:
                raise ContentBlockError(f"{self.node_type.value} nodes require children only")
            if any(child.node_type is RichTextNodeType.PARAGRAPH for child in self.children):
                raise ContentBlockError("paragraph nodes are top-level only")
            return

        if self.node_type in _TEXT_NODE_TYPES:
            if self.text is None or self.text == "" or self.reading is not None or self.children:
                raise ContentBlockError(f"{self.node_type.value} nodes require non-empty text only")
            return

        if self.node_type is RichTextNodeType.LINE_BREAK:
            if self.text is not None or self.reading is not None or self.children:
                raise ContentBlockError("line_break nodes cannot carry payload")
            return

        if self.node_type is RichTextNodeType.RUBY:
            if (
                self.text is None
                or self.text == ""
                or self.reading is None
                or self.reading == ""
                or self.children
            ):
                raise ContentBlockError("ruby nodes require non-empty text and reading")
            return

        raise ContentBlockError(f"unsupported rich-text node: {self.node_type!r}")


@dataclass(frozen=True, slots=True)
class RichTextDocument:
    """Canonical rich-text document; top-level nodes are paragraphs only."""

    children: tuple[RichTextNode, ...]

    def __post_init__(self) -> None:
        if not self.children:
            raise ContentBlockError("rich-text document must contain at least one paragraph")
        if any(node.node_type is not RichTextNodeType.PARAGRAPH for node in self.children):
            raise ContentBlockError("rich-text document children must be paragraphs")


@dataclass(frozen=True, slots=True)
class MediaReference:
    """Minimal content reference; full Asset metadata remains P1.11 scope."""

    asset_id: str

    def __post_init__(self) -> None:
        validate_stable_id(self.asset_id, field="asset_id")


ContentPayload = TextContent | RichTextDocument | MediaReference


@dataclass(frozen=True, slots=True)
class ContentBlock:
    """Ordered semantic block attached to a LearningItem."""

    content_block_id: str
    learning_item_id: str
    position: int
    kind: ContentBlockKind
    role: ContentRole
    reveals_answer: bool
    payload: ContentPayload
    mask_strategy: MaskStrategy = MaskStrategy.NONE

    def __post_init__(self) -> None:
        validate_stable_id(self.content_block_id, field="content_block_id")
        validate_stable_id(self.learning_item_id, field="learning_item_id")
        if self.position < 0:
            raise ContentBlockError("content block position must be >= 0")

        if self.kind is ContentBlockKind.TEXT:
            valid_payload = isinstance(self.payload, TextContent)
            expected_type_name = "TextContent"
        elif self.kind is ContentBlockKind.RICH_TEXT:
            valid_payload = isinstance(self.payload, RichTextDocument)
            expected_type_name = "RichTextDocument"
        else:
            valid_payload = isinstance(self.payload, MediaReference)
            expected_type_name = "MediaReference"

        if not valid_payload:
            raise ContentBlockError(
                f"{self.kind.value} block payload must be {expected_type_name}"
            )

        if self.mask_strategy in {
            MaskStrategy.BLANK_TERM,
            MaskStrategy.BLANK_SPAN,
        } and self.kind not in {ContentBlockKind.TEXT, ContentBlockKind.RICH_TEXT}:
            raise ContentBlockError(
                f"{self.mask_strategy.value} is only valid for text/rich_text blocks"
            )
        if self.mask_strategy is not MaskStrategy.NONE and not self.reveals_answer:
            raise ContentBlockError("mask_strategy requires reveals_answer=true")
        if self.role is ContentRole.ANSWER and not self.reveals_answer:
            raise ContentBlockError("answer blocks must declare reveals_answer=true")

    @property
    def requires_reveal_action(self) -> bool:
        """Return whether the unmasked block must stay gated before retrieval."""
        if self.role in {
            ContentRole.ANSWER,
            ContentRole.HINT,
            ContentRole.MNEMONIC,
        }:
            return True
        return self.reveals_answer and self.mask_strategy in {
            MaskStrategy.NONE,
            MaskStrategy.HIDE_BLOCK,
        }


def parse_rich_text_ast(value: object) -> RichTextDocument:
    """Parse a strict JSON-like rich-text AST and reject every unknown construct."""
    if not isinstance(value, Mapping):
        raise ContentBlockError("rich-text AST root must be an object")
    _require_exact_keys(value, {"type", "children"}, "document")
    if value.get("type") != "document":
        raise ContentBlockError("rich-text AST root type must be 'document'")
    raw_children = _require_sequence(value.get("children"), "document.children")
    counter = [0]
    children = tuple(
        _parse_rich_text_node(child, depth=1, counter=counter) for child in raw_children
    )
    return RichTextDocument(children)


def _parse_rich_text_node(value: object, *, depth: int, counter: list[int]) -> RichTextNode:
    if depth > MAX_RICH_TEXT_DEPTH:
        raise ContentBlockError("rich-text AST exceeds maximum depth")
    counter[0] += 1
    if counter[0] > MAX_RICH_TEXT_NODES:
        raise ContentBlockError("rich-text AST exceeds maximum node count")
    if not isinstance(value, Mapping):
        raise ContentBlockError("rich-text node must be an object")

    raw_type = value.get("type")
    if not isinstance(raw_type, str):
        raise ContentBlockError("rich-text node type must be a string")
    try:
        node_type = RichTextNodeType(raw_type)
    except ValueError as err:
        raise ContentBlockError(f"unsupported rich-text node type: {raw_type!r}") from err

    if node_type in _CONTAINER_NODE_TYPES:
        _require_exact_keys(value, {"type", "children"}, node_type.value)
        raw_children = _require_sequence(value.get("children"), f"{node_type.value}.children")
        children = tuple(
            _parse_rich_text_node(child, depth=depth + 1, counter=counter) for child in raw_children
        )
        return RichTextNode(node_type=node_type, children=children)

    if node_type in _TEXT_NODE_TYPES:
        _require_exact_keys(value, {"type", "text"}, node_type.value)
        return RichTextNode(node_type=node_type, text=_require_text(value.get("text")))

    if node_type is RichTextNodeType.LINE_BREAK:
        _require_exact_keys(value, {"type"}, node_type.value)
        return RichTextNode(node_type=node_type)

    _require_exact_keys(value, {"type", "text", "reading"}, node_type.value)
    return RichTextNode(
        node_type=node_type,
        text=_require_text(value.get("text")),
        reading=_require_text(value.get("reading")),
    )


def _require_exact_keys(value: Mapping[Any, Any], expected: set[str], label: str) -> None:
    keys = set(value)
    if keys != expected:
        raise ContentBlockError(
            f"{label} keys must be exactly {sorted(expected)!r}; got {sorted(map(str, keys))!r}"
        )


def _require_sequence(value: object, field: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ContentBlockError(f"{field} must be an array")
    if not value:
        raise ContentBlockError(f"{field} must be non-empty")
    return value


def _require_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ContentBlockError("rich-text text fields must be non-empty strings")
    if len(value) > MAX_RICH_TEXT_TEXT_LENGTH:
        raise ContentBlockError("rich-text text field exceeds maximum length")
    return value
