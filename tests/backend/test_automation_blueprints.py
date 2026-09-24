"""P4.9 automation blueprint contract tests."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BLUEPRINT_ROOT = ROOT / "blueprints" / "automation" / "locklearn"

EXPECTED = {
    "correct_wrong_light_feedback.yaml",
    "daily_goal_reward.yaml",
    "repeated_failure_encouragement.yaml",
}

FORBIDDEN_CONTENT_KEYS = {
    "prompt",
    "answer",
    "translation",
    "user_response",
    "learning_item_text",
}


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_blueprint_set_and_source_urls_are_stable() -> None:
    files = {path.name for path in BLUEPRINT_ROOT.glob("*.yaml")}
    assert files == EXPECTED
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        blueprint = _load(path)["blueprint"]
        assert blueprint["domain"] == "automation"
        assert blueprint["source_url"] == (
            "https://github.com/rfrachot/LockLearn/blob/main/"
            f"blueprints/automation/locklearn/{path.name}"
        )


def test_blueprints_use_only_documented_locklearn_events_and_services() -> None:
    event_types: set[str] = set()
    locklearn_actions: set[str] = set()
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        raw = _load(path)
        for trigger in raw.get("triggers", []):
            if trigger.get("trigger") == "event":
                event_types.add(str(trigger["event_type"]))
        for action in raw.get("actions", []):
            name = action.get("action")
            if isinstance(name, str) and name.startswith("locklearn."):
                locklearn_actions.add(name)
            for choice in action.get("choose", []):
                for nested in choice.get("sequence", []):
                    name = nested.get("action")
                    if isinstance(name, str) and name.startswith("locklearn."):
                        locklearn_actions.add(name)

    assert event_types <= {
        "locklearn_answered",
        "locklearn_quiz_correct",
        "locklearn_quiz_wrong",
        "locklearn_daily_goal_reached",
    }
    assert locklearn_actions <= {"locklearn.pause_track"}


def test_blueprints_are_content_agnostic_and_privacy_safe() -> None:
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_CONTENT_KEYS:
            assert forbidden not in text
        assert "trigger.event.data.card_key" not in text
        assert "trigger.event.data.learning_item_id" not in text
