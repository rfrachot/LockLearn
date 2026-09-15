from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ROLES = ("explore", "tests", "quality", "review")


def _claude_body(role: str) -> tuple[str, str]:
    text = (ROOT / ".claude" / "agents" / f"{role}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, frontmatter, body = text.split("---", 2)
    return frontmatter, body.lstrip()


@pytest.mark.parametrize("role", ROLES)
def test_claude_agent_role_matches_shared_role(role: str) -> None:
    shared = (ROOT / ".ai" / "agents" / f"{role}.md").read_text(encoding="utf-8")
    frontmatter, body = _claude_body(role)

    assert "model: haiku" in frontmatter
    assert body == shared
