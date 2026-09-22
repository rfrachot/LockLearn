"""Tests for the secret-safe real-instance qualification harness."""

import os
from pathlib import Path

import pytest

from scripts.p0_real_instance import event_payload, load_allowed_env


def test_load_allowed_env_ignores_unrelated_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The harness never imports arbitrary values from a local env file."""
    monkeypatch.delenv("LOCKLEARN_HA_URL", raising=False)
    monkeypatch.delenv("UNRELATED_SECRET", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOCKLEARN_HA_URL='http://example.invalid:8123'\nUNRELATED_SECRET=must-not-load\n",
        encoding="utf-8",
    )

    load_allowed_env(env_file)

    assert os.environ["LOCKLEARN_HA_URL"] == "http://example.invalid:8123"
    assert "UNRELATED_SECRET" not in os.environ


def test_event_payload_accepts_current_ha_envelope() -> None:
    """HA 2026 sends Event.as_dict directly in the event field."""
    message = {
        "event": {
            "event_type": "mobile_app_notification_action",
            "data": {"action": "LOCKLEARN_P07_TEST"},
            "context": {"user_id": "user"},
        }
    }

    assert event_payload(message) == (
        "mobile_app_notification_action",
        {"action": "LOCKLEARN_P07_TEST"},
        {"user_id": "user"},
    )


def test_event_payload_accepts_legacy_nested_envelope() -> None:
    """Older probe captures with an extra event wrapper remain readable."""
    message = {
        "event": {
            "event": {
                "event_type": "mobile_app_notification_cleared",
                "data": {"tag": "locklearn_p07_test"},
                "context": {"user_id": None},
            }
        }
    }

    assert event_payload(message) == (
        "mobile_app_notification_cleared",
        {"tag": "locklearn_p07_test"},
        {"user_id": None},
    )
