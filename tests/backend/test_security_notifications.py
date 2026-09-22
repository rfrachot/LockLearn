"""P0 target capability and unattended-action tests."""

import sqlite3
from pathlib import Path

import pytest

from custom_components.locklearn.core.security import (
    ActionForbiddenError,
    ActionKind,
    ActorKind,
    async_authorize_and_audit,
    authorize_action,
    effective_signal_quality,
)
from custom_components.locklearn.notifications.capabilities import (
    Capability,
    LearningNotificationMode,
    LearningSignal,
    TargetCapabilities,
    classify_learning_signal,
)
from custom_components.locklearn.notifications.targets import legacy_mobile_app_service
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths


def test_two_step_requires_actionable_prompt_evidence() -> None:
    """Unknown actionable behavior falls back to direct exposure."""
    unknown = TargetCapabilities(device_registry_id="device-1", platform="android")
    assert unknown.learning_mode() is LearningNotificationMode.DIRECT_EXPOSURE

    proven = TargetCapabilities(
        device_registry_id="device-1",
        platform="android",
        action_data=Capability.SUPPORTED,
        visible_actions=2,
    )
    assert proven.learning_mode() is LearningNotificationMode.TWO_STEP_REVEAL


def test_second_vibration_does_not_erase_retrieval_attempt() -> None:
    """Silent replacement is UX evidence, not pedagogical evidence."""
    android = TargetCapabilities(
        device_registry_id="device-1",
        platform="android",
        replace_by_tag=Capability.SUPPORTED,
        silent_replace=Capability.UNSUPPORTED,
        action_data=Capability.SUPPORTED,
        visible_actions=3,
    )

    assert android.learning_mode() is LearningNotificationMode.TWO_STEP_REVEAL
    assert (
        classify_learning_signal(
            answer_exposed_before_retrieval=False,
            retrieval_was_usable=True,
        )
        is LearningSignal.SELF_ASSESSMENT_AFTER_RETRIEVAL
    )


def test_exposure_only_depends_on_actual_answer_exposure() -> None:
    assert (
        classify_learning_signal(
            answer_exposed_before_retrieval=True,
            retrieval_was_usable=False,
        )
        is LearningSignal.EXPOSURE_ONLY
    )
    assert (
        classify_learning_signal(
            answer_exposed_before_retrieval=False,
            retrieval_was_usable=False,
        )
        is LearningSignal.NO_RESULT
    )


def test_unattended_allowlist_cannot_read_export_or_delete() -> None:
    """No-user actions remain non-reading and non-destructive."""
    actor = authorize_action(user_id=None, allow_unattended_actions=True, action=ActionKind.SNOOZE)
    assert actor.kind is ActorKind.UNATTENDED_AUTOMATION

    for forbidden in (ActionKind.READ_PRIVATE, ActionKind.EXPORT, ActionKind.DELETE):
        with pytest.raises(ActionForbiddenError):
            authorize_action(
                user_id=None,
                allow_unattended_actions=True,
                action=forbidden,
            )


async def test_unattended_action_is_durably_audited(tmp_path: Path) -> None:
    """The no-user path cannot succeed without a privacy-minimal audit row."""
    storage = SQLiteStorage(StoragePaths(tmp_path / "state.db", tmp_path / "content.db"))
    await storage.async_open()
    await async_authorize_and_audit(
        storage,
        user_id=None,
        profile_id="profile-1",
        allow_unattended_actions=True,
        action=ActionKind.PAUSE_TRACK,
    )
    await storage.async_close()

    connection = sqlite3.connect(storage.paths.state_db)
    try:
        event_type, actor_user_id, profile_id, payload = connection.execute(
            "SELECT event_type, actor_user_id, profile_id, payload_json FROM audit_events"
        ).fetchone()
    finally:
        connection.close()
    assert event_type == "unattended_action"
    assert actor_user_id is None
    assert profile_id == "profile-1"
    assert "pause_track" in payload


def test_user_context_is_identity_not_automatic_profile_access() -> None:
    """A HA user id is preserved for later backend ACL evaluation."""
    actor = authorize_action(
        user_id="ha-user-1",
        allow_unattended_actions=False,
        action=ActionKind.START_SESSION,
    )
    assert actor.kind is ActorKind.HA_USER
    assert actor.user_id == "ha-user-1"


def test_shared_device_reduces_signal_quality_by_default() -> None:
    assert effective_signal_quality(shared_device=True, explicit_trust=False) == "reduced"
    assert effective_signal_quality(shared_device=True, explicit_trust=True) == "normal"


def test_legacy_service_is_recomputed_after_rename() -> None:
    assert legacy_mobile_app_service("Pixel 9 Pro") == "mobile_app_pixel_9_pro"
    assert legacy_mobile_app_service("Learning Phone") == "mobile_app_learning_phone"
