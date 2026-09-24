"""P4.9 automation blueprint contract tests."""

from __future__ import annotations

import re
from pathlib import Path

from homeassistant.components.automation import config as automation_config
from homeassistant.components.blueprint import models
from homeassistant.util import yaml as yaml_util

ROOT = Path(__file__).resolve().parents[2]
BLUEPRINT_ROOT = ROOT / "blueprints" / "automation" / "locklearn"

EXPECTED = {
    "correct_wrong_light_feedback.yaml",
    "daily_goal_reward.yaml",
    "repeated_failure_encouragement.yaml",
}

DOCUMENTED_EVENTS = {
    "locklearn_answered",
    "locklearn_quiz_correct",
    "locklearn_quiz_wrong",
    "locklearn_daily_goal_reached",
}

FORBIDDEN_EVENT_FIELDS = {
    "prompt",
    "answer",
    "translation",
    "user_response",
    "learning_item_text",
    "learning_item_id",
    "card_key",
}


def test_blueprints_validate_with_home_assistant_schema() -> None:
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        models.Blueprint(
            yaml_util.load_yaml(path),
            expected_domain="automation",
            path=str(path),
            schema=automation_config.AUTOMATION_BLUEPRINT_SCHEMA,
        )


def test_blueprint_set_and_source_urls_are_stable() -> None:
    files = {path.name for path in BLUEPRINT_ROOT.glob("*.yaml")}
    assert files == EXPECTED
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "domain: automation" in text
        assert (
            "source_url: https://github.com/rfrachot/LockLearn/blob/main/"
            f"blueprints/automation/locklearn/{path.name}"
        ) in text


def test_blueprints_use_only_documented_locklearn_events_and_services() -> None:
    event_pattern = re.compile(r"^\s*event_type:\s*(locklearn_[a-z0-9_]+)\s*$", re.MULTILINE)
    action_pattern = re.compile(r"^\s*action:\s*(locklearn\.[a-z0-9_]+)\s*$", re.MULTILINE)

    events: set[str] = set()
    actions: set[str] = set()
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        events.update(event_pattern.findall(text))
        actions.update(action_pattern.findall(text))

    assert events <= DOCUMENTED_EVENTS
    assert actions <= {"locklearn.pause_track"}


def test_blueprints_are_content_agnostic_and_privacy_safe() -> None:
    for path in BLUEPRINT_ROOT.glob("*.yaml"):
        text = path.read_text(encoding="utf-8").lower()
        for field in FORBIDDEN_EVENT_FIELDS:
            assert f"trigger.event.data.{field}" not in text
