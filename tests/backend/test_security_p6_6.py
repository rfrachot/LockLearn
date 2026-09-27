"""P6.6 cross-boundary security hardening tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from tempfile import gettempdir

import pytest

from custom_components.locklearn.const import STATIC_URL_PATH
from custom_components.locklearn.core.pack_filters import (
    PackFilterError,
    compile_pack_content_filter,
)
from custom_components.locklearn.core.security_content import (
    ContentSecurityError,
    sanitize_rich_text_payload,
    sanitize_svg_bytes,
)
from custom_components.locklearn.profile_transfer import ProfileTransferStore
from custom_components.locklearn.profile_transfer_http import (
    ProfileExportDownloadView,
    ProfileImportUploadView,
)


def test_rich_text_ast_rejects_html_links_attributes_and_excess_depth() -> None:
    """Third-party rich text has no representation for executable HTML."""
    safe = sanitize_rich_text_payload(
        {
            "type": "document",
            "children": [
                {
                    "type": "paragraph",
                    "children": [
                        {"type": "text", "text": "<script>alert(1)</script>"},
                        {"type": "strong", "children": [{"type": "text", "text": "safe"}]},
                    ],
                }
            ],
        }
    )
    assert safe == {
        "type": "document",
        "children": [
            {
                "type": "paragraph",
                "children": [
                    {"type": "text", "text": "<script>alert(1)</script>"},
                    {
                        "type": "strong",
                        "children": [{"type": "text", "text": "safe"}],
                    },
                ],
            }
        ],
    }

    for unsafe in (
        {
            "type": "document",
            "children": [{"type": "html", "text": "<img src=x onerror=alert(1)>"}],
        },
        {
            "type": "document",
            "children": [
                {
                    "type": "paragraph",
                    "children": [
                        {
                            "type": "text",
                            "text": "x",
                            "onload": "alert(1)",
                        }
                    ],
                }
            ],
        },
        {
            "type": "document",
            "children": [
                {
                    "type": "link",
                    "href": "javascript:alert(1)",
                    "children": [{"type": "text", "text": "click"}],
                }
            ],
        },
    ):
        with pytest.raises(ContentSecurityError):
            sanitize_rich_text_payload(unsafe)


def test_svg_sanitizer_removes_executable_and_external_features() -> None:
    """Signed SVG bytes cannot retain active/external content."""
    raw = b"""<svg xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        onload="alert(1)">
      <script>alert(1)</script>
      <foreignObject><body xmlns="http://www.w3.org/1999/xhtml">x</body></foreignObject>
      <a href="https://evil.invalid/"><path d="M0 0"/></a>
      <use xlink:href="javascript:alert(1)"/>
      <path id="local" d="M0 0" style="background:url(https://evil.invalid/x)"/>
      <use href="#local"/>
    </svg>"""
    cleaned = sanitize_svg_bytes(raw)
    lowered = cleaned.lower()

    assert b"<script" not in lowered
    assert b"foreignobject" not in lowered
    assert b"onload" not in lowered
    assert b"javascript:" not in lowered
    assert b"https://evil.invalid" not in lowered
    assert b"style=" not in lowered
    assert b'href="#local"' in lowered

    mixed_case = sanitize_svg_bytes(b"<svg><SCRIPT>alert(1)</SCRIPT><STYLE>*{}</STYLE></svg>")
    assert b"<script" not in mixed_case.lower()
    assert b"<style" not in mixed_case.lower()

    deep = b"<svg>" + (b"<g>" * 257) + (b"</g>" * 257) + b"</svg>"
    with pytest.raises(ContentSecurityError, match="depth"):
        sanitize_svg_bytes(deep)

    with pytest.raises(ContentSecurityError, match="DTD"):
        sanitize_svg_bytes(
            b'<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            b'<svg xmlns="http://www.w3.org/2000/svg">&xxe;</svg>'
        )


def test_pack_filter_sql_is_allowlisted_and_values_are_bound() -> None:
    """Package-provided values can never become SQL syntax."""
    malicious = "vocabulary' OR 1=1; DROP TABLE learning_items; --"
    compiled = compile_pack_content_filter(
        {
            "all": [
                {"field": "content_type", "op": "eq", "value": malicious},
                {
                    "field": "register",
                    "op": "in",
                    "value": ["common", "formal"],
                },
            ]
        }
    )
    assert malicious not in compiled.where_sql
    assert compiled.where_sql == (
        "item.lifecycle_status = 'active' AND item.content_type = ? AND item.register IN (?,?)"
    )
    assert compiled.parameters == (malicious, "common", "formal")

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(
            """CREATE TABLE learning_items(
                   content_type TEXT,
                   register TEXT,
                   lifecycle_status TEXT
               )"""
        )
        connection.execute("INSERT INTO learning_items VALUES ('vocabulary', 'common', 'active')")
        rows = connection.execute(
            f"SELECT content_type FROM learning_items AS item WHERE {compiled.where_sql}",
            compiled.parameters,
        ).fetchall()
        assert rows == []
        assert connection.execute("SELECT COUNT(*) FROM learning_items").fetchone() == (1,)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "document",
    (
        {"all": [{"field": "content_type) OR 1=1 --", "op": "eq", "value": "x"}]},
        {"all": [{"field": "content_type", "op": "raw_sql", "value": "1=1"}]},
        {"all": [{"field": "content_type", "op": "eq", "value": 123}]},
        {"any": []},
        {"all": [{"field": "content_type", "op": "eq", "value": "x", "sql": "1=1"}]},
    ),
)
def test_pack_filter_rejects_unknown_schema_surface(document: object) -> None:
    with pytest.raises(PackFilterError):
        compile_pack_content_filter(document)


@pytest.mark.parametrize(
    "document",
    (
        {"all": ({"field": "content_type", "op": "eq", "value": "x"},)},
        {"all": [{"field": "content_type", "op": "in", "value": ("x",)}]},
    ),
)
def test_pack_filter_rejects_non_json_array_types(document: object) -> None:
    with pytest.raises(PackFilterError):
        compile_pack_content_filter(document)


def test_content_filter_json_schema_is_closed() -> None:
    """The distributed schema documents the same fail-closed grammar."""
    schema_path = Path("datasets/schemas/content-filter.schema.json")
    document = json.loads(schema_path.read_text(encoding="utf-8"))
    assert document["additionalProperties"] is False
    assert document["properties"]["all"]["items"]["additionalProperties"] is False
    assert document["properties"]["all"]["items"]["properties"]["field"]["enum"] == [
        "content_type",
        "register",
        "dataset_id",
    ]
    assert document["properties"]["all"]["items"]["properties"]["op"]["enum"] == [
        "eq",
        "in",
    ]


def test_private_transfers_cannot_share_the_public_static_asset_boundary(
    tmp_path: Path,
) -> None:
    """Private export/import files stay authenticated and outside HA static roots."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    store = ProfileTransferStore.private_runtime_root(str(config_dir))

    assert ProfileExportDownloadView.requires_auth is True
    assert ProfileImportUploadView.requires_auth is True
    assert ProfileExportDownloadView.url.startswith("/api/locklearn/")
    assert ProfileImportUploadView.url.startswith("/api/locklearn/")
    assert STATIC_URL_PATH == "/locklearn_static"
    assert not store.root.is_relative_to(config_dir)
    assert store.root.is_relative_to(Path(gettempdir()))
    assert "frontend" not in store.root.parts
