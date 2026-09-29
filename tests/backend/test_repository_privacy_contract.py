"""Repository privacy contract for pseudonymized examples."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# SHA-256 digests of personal first names that must never appear in committed
# examples, fixtures, docs, generated assets, or identifiers. Keeping only the
# digests avoids reintroducing the names into the repository through this gate.
FORBIDDEN_NAME_DIGESTS = frozenset(
    {
        "bf6e04f9d6d1d7dba9fc604d0b1692f33d7de9a34f0038018f51725fe74358de",
        "e5b01cccc6e4fec148d7d8d70fcbaadba3fc83a6913d048ef67d12a9c7e1d8f0",
        "6e1a5d40108164ad38168f58271ef4411cb9c75cc001cf7a14a6047eb05192f2",
    }
)

TEXT_SUFFIXES = frozenset(
    {
        ".md",
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".json",
        ".yaml",
        ".yml",
        ".html",
        ".toml",
        ".txt",
    }
)
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")


def _digest(token: str) -> str:
    return hashlib.sha256(token.casefold().encode("utf-8")).hexdigest()


def test_committed_text_uses_pseudonymized_examples() -> None:
    violations: list[str] = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if any(part in {".git", ".venv", "node_modules"} for part in relative.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if any(_digest(token) in FORBIDDEN_NAME_DIGESTS for token in WORD_RE.findall(line)):
                violations.append(f"{relative}:{line_number}")

    assert violations == [], (
        "Personal first-name references must be pseudonymized; offending locations: "
        + ", ".join(violations)
    )
