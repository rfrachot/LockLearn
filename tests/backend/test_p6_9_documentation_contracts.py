"""P6.9 documentation-set and generated-contract invariants."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOCUMENTS = {
    "README.md": (
        "## Vision",
        "## Screenshots",
        "## Installation",
        "## Quick start",
        "## Compatibility",
    ),
    "ARCHITECTURE.md": ("## System view", "## Backend", "## Frontend", "## Databases"),
    "DATA_MODEL.md": (
        "## Content concepts",
        "## User/runtime model",
        "CardDefinition",
        "ReviewEvent",
    ),
    "DATABASE.md": ("## state.db", "## content.db", "## Migration policy", "## Backup/recovery"),
    "PACK_FORMAT.md": (
        "## Package envelope",
        "## Manifest and signature",
        "## Machine-readable schemas",
    ),
    "DATA_SOURCES.md": ("## Source inventory", "## Provenance contract", "## Source audit"),
    "DATA_UPDATES.md": ("## P1.8 implementation", "## P1.9 runtime update path"),
    "LICENSING.md": ("## Software", "## Third-party datasets and assets"),
    "PERMISSIONS.md": ("owner", "editor", "viewer"),
    "SRS.md": (
        "## States",
        "## Short learning steps",
        "## Long-review intervals",
        "## Leech policy",
    ),
    "SCHEDULER.md": ("## Configuration", "## DST and timezone", "## Restart and clock jumps"),
    "NOTIFICATIONS.md": ("## Platforms", "## Lifecycle", "## Threat model"),
    "FRONTEND.md": ("## Architecture", "## WebSocket interface", "## Rendering and sanitization"),
    "API.md": ("## Version", "## Command contract", "## Permission classes"),
    "MIGRATIONS.md": ("## Home Assistant Config Entry", "## `state.db`", "## Recovery rules"),
    "SECURITY.md": ("threat", "ACL"),
    "PRIVACY.md": ("private", "shared"),
    "DEVELOPMENT.md": ("## Bootstrap", "## Backend workflow", "## Frontend workflow"),
    "TESTING.md": ("## Backend/unit/integration", "## Frontend", "## CI"),
    "RELEASE.md": ("## Before tagging", "## Release"),
    "TROUBLESHOOTING.md": (
        "## Notifications do not arrive",
        "## Database migration/integrity failure",
    ),
    "ROADMAP.md": ("## Committed", "## Candidate", "## Ideas", "## Rejected / out of V1"),
    "AGENTS.md": ("## 3. Non-negotiable architecture invariants", "## 9. Definition of Done"),
    "CHANGELOG.md": ("### Added", "### Fixed", "### Changed"),
}

GENERATED_DOCUMENTS = (
    "docs/generated/STATE_DB.md",
    "docs/generated/CONTENT_DB.md",
    "docs/generated/WEBSOCKET_CONTRACTS.md",
    "docs/generated/websocket-contracts.json",
)


def test_required_documentation_set_and_sections_exist() -> None:
    missing: list[str] = []
    for relative, markers in REQUIRED_DOCUMENTS.items():
        path = ROOT / relative
        if not path.is_file():
            missing.append(relative)
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                missing.append(f"{relative}: {marker}")
    assert missing == []


def test_generated_contract_outputs_are_committed() -> None:
    assert all((ROOT / relative).is_file() for relative in GENERATED_DOCUMENTS)


def test_spec_remains_normative_in_reference_docs() -> None:
    for relative in ("README.md", "ARCHITECTURE.md", "ROADMAP.md"):
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "SPEC_V1.md" in content


def test_readme_uses_committed_real_panel_screenshot() -> None:
    screenshot = ROOT / "docs" / "assets" / "locklearn-home.png"
    assert screenshot.is_file()
    assert screenshot.stat().st_size > 0
    assert screenshot.read_bytes().startswith(b"\\x89PNG\\r\\n\\x1a\\n")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "![LockLearn Home dashboard](docs/assets/locklearn-home.png)" in readme
    assert "deterministic Playwright harness" in readme
