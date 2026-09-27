"""Content security primitives shared by dataset build and render contracts."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path

_MAX_RICH_TEXT_DEPTH = 16
_MAX_RICH_TEXT_NODES = 512
_MAX_RICH_TEXT_TEXT = 16_384
MAX_SVG_BYTES = 4 * 1024 * 1024

_SVG_NS = "http://www.w3.org/2000/svg"
_XLINK_NS = "http://www.w3.org/1999/xlink"
_DANGEROUS_SVG_ELEMENTS = frozenset(
    {
        "script",
        "foreignObject",
        "style",
        "iframe",
        "object",
        "embed",
    }
)
_EXTERNAL_SCHEME_RE = re.compile(
    r"^(?:https?:|data:|javascript:|file:|//)",
    re.IGNORECASE,
)
_LOCAL_URL_RE = re.compile(r"^url\(\s*#[A-Za-z_][A-Za-z0-9_.:-]*\s*\)$")


class ContentSecurityError(ValueError):
    """Raised when third-party content violates the closed security model."""


class _NodeBudget:
    def __init__(self) -> None:
        self.count = 0

    def consume(self) -> None:
        self.count += 1
        if self.count > _MAX_RICH_TEXT_NODES:
            raise ContentSecurityError("rich_text exceeds the node-count limit")


def _require_exact_keys(
    node: Mapping[str, object],
    *,
    allowed: frozenset[str],
    node_type: str,
) -> None:
    unknown = set(node) - allowed
    if unknown:
        raise ContentSecurityError(
            f"rich_text {node_type} contains unsupported fields: {sorted(unknown)!r}"
        )


def _rich_text_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContentSecurityError(f"rich_text {field} must be a non-empty string")
    if len(value) > _MAX_RICH_TEXT_TEXT:
        raise ContentSecurityError(f"rich_text {field} exceeds the text limit")
    return value


def _sanitize_rich_node(
    value: object,
    *,
    depth: int,
    budget: _NodeBudget,
) -> dict[str, object]:
    if depth > _MAX_RICH_TEXT_DEPTH:
        raise ContentSecurityError("rich_text exceeds the nesting-depth limit")
    if not isinstance(value, Mapping):
        raise ContentSecurityError("rich_text nodes must be objects")

    budget.consume()
    node = dict(value)
    node_type = node.get("type")
    if not isinstance(node_type, str):
        raise ContentSecurityError("rich_text node type must be a string")

    if node_type in {"text", "inline_code"}:
        _require_exact_keys(
            node,
            allowed=frozenset({"type", "text"}),
            node_type=node_type,
        )
        return {
            "type": node_type,
            "text": _rich_text_string(node.get("text"), f"{node_type}.text"),
        }

    if node_type == "line_break":
        _require_exact_keys(
            node,
            allowed=frozenset({"type"}),
            node_type=node_type,
        )
        return {"type": node_type}

    if node_type == "ruby":
        _require_exact_keys(
            node,
            allowed=frozenset({"type", "text", "reading"}),
            node_type=node_type,
        )
        return {
            "type": node_type,
            "text": _rich_text_string(node.get("text"), "ruby.text"),
            "reading": _rich_text_string(node.get("reading"), "ruby.reading"),
        }

    if node_type in {"paragraph", "emphasis", "strong"}:
        _require_exact_keys(
            node,
            allowed=frozenset({"type", "children"}),
            node_type=node_type,
        )
        if node_type == "paragraph" and depth != 1:
            raise ContentSecurityError("rich_text paragraph nodes are top-level only")
        children = node.get("children")
        if not isinstance(children, list) or not children:
            raise ContentSecurityError(
                f"rich_text {node_type}.children must be a non-empty array"
            )
        return {
            "type": node_type,
            "children": [
                _sanitize_rich_node(child, depth=depth + 1, budget=budget)
                for child in children
            ],
        }

    raise ContentSecurityError(f"unsupported rich_text node type: {node_type}")


def sanitize_rich_text_payload(payload: object) -> dict[str, object]:
    """Validate and canonicalize the strict rich-text AST allowlist.

    HTML, links, images, style/event attributes and arbitrary Markdown extensions
    are not representable in this AST.
    """
    if not isinstance(payload, Mapping):
        raise ContentSecurityError("rich_text payload must be an object")
    document = dict(payload)
    _require_exact_keys(
        document,
        allowed=frozenset({"type", "children"}),
        node_type="document",
    )
    if document.get("type") != "document":
        raise ContentSecurityError("rich_text root type must be document")
    children = document.get("children")
    if not isinstance(children, list) or not children:
        raise ContentSecurityError(
            "rich_text document.children must be a non-empty array"
        )

    for child in children:
        if not isinstance(child, Mapping) or child.get("type") != "paragraph":
            raise ContentSecurityError(
                "rich_text document children must be paragraphs"
            )

    budget = _NodeBudget()
    return {
        "type": "document",
        "children": [
            _sanitize_rich_node(child, depth=1, budget=budget)
            for child in children
        ],
    }


def _local_name(name: str) -> str:
    if name.startswith("{"):
        return name.split("}", 1)[1]
    return name


def _namespace(name: str) -> str | None:
    if not name.startswith("{"):
        return None
    return name[1:].split("}", 1)[0]


def _svg_attribute_is_safe(name: str, value: str) -> bool:
    local = _local_name(name)
    if local.lower().startswith("on") or local == "style":
        return False

    normalized = value.strip()
    if local in {"href", "src"}:
        return normalized.startswith("#")

    if _EXTERNAL_SCHEME_RE.match(normalized):
        return False

    if "url(" in normalized.lower() and not _LOCAL_URL_RE.fullmatch(normalized):
        return False

    return True


def sanitize_svg_bytes(payload: bytes) -> bytes:
    """Strip executable/external SVG features before bytes enter a signed dataset."""
    if not payload or len(payload) > MAX_SVG_BYTES:
        raise ContentSecurityError("SVG payload is empty or exceeds the size limit")

    lowered = payload.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise ContentSecurityError("DTD/entity declarations are forbidden in SVG")

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as err:
        raise ContentSecurityError("SVG is not well-formed XML") from err

    if _local_name(root.tag) != "svg" or _namespace(root.tag) not in {None, _SVG_NS}:
        raise ContentSecurityError("SVG root element/namespace is invalid")

    def clean(parent: ET.Element) -> None:
        for child in tuple(parent):
            child_namespace = _namespace(child.tag)
            child_name = _local_name(child.tag)
            if (
                child_namespace not in {None, _SVG_NS}
                or child_name in _DANGEROUS_SVG_ELEMENTS
            ):
                parent.remove(child)
                continue
            clean(child)

        for attribute, value in tuple(parent.attrib.items()):
            attribute_namespace = _namespace(attribute)
            if attribute_namespace not in {None, _SVG_NS, _XLINK_NS}:
                del parent.attrib[attribute]
                continue
            if not _svg_attribute_is_safe(attribute, value):
                del parent.attrib[attribute]

    clean(root)
    ET.register_namespace("", _SVG_NS)
    ET.register_namespace("xlink", _XLINK_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def sanitize_svg_file(path: Path) -> tuple[bytes, bool]:
    """Read one SVG with a hard byte ceiling and return sanitized bytes/change flag."""
    try:
        size = path.stat().st_size
    except OSError as err:
        raise ContentSecurityError(f"cannot stat SVG asset: {path}") from err
    if size <= 0 or size > MAX_SVG_BYTES:
        raise ContentSecurityError("SVG payload is empty or exceeds the size limit")
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_SVG_BYTES + 1)
    except OSError as err:
        raise ContentSecurityError(f"cannot read SVG asset: {path}") from err
    if len(raw) != size or len(raw) > MAX_SVG_BYTES:
        raise ContentSecurityError("SVG asset changed or exceeds the size limit while reading")
    sanitized = sanitize_svg_bytes(raw)
    return sanitized, sanitized != raw
