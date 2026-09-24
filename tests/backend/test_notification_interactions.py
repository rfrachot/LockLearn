"""P4.6 persistent notification interaction and replay-protection tests."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from custom_components.locklearn.core.acl import ProfileACLService
from custom_components.locklearn.notifications.interactions import (
    NotificationActionDisposition,
    NotificationInteractionService,
    NotificationStage,
)
from custom_components.locklearn.storage import (
    NotificationTargetRecord,
    ProfileMemberRecord,
    ProfileRecord,
    SQLiteStorage,
    StoragePaths,
)
from custom_components.locklearn.storage.repositories import StateRepositoryError


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


async def _runtime(
    tmp_path: Path,
    *,
    clock: MutableClock,
) -> tuple[SQLiteStorage, NotificationInteractionService]:
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    now = clock.now().isoformat()
    await storage.repositories.profiles.async_insert_with_members(
        ProfileRecord(
            profile_id="profile-1",
            name="Renaud",
            preset="standard",
            timezone="Europe/Paris",
            created_at_utc=now,
            updated_at_utc=now,
        ),
        (
            ProfileMemberRecord(
                profile_id="profile-1",
                ha_user_id="owner-user",
                role="owner",
                created_at_utc=now,
            ),
            ProfileMemberRecord(
                profile_id="profile-1",
                ha_user_id="viewer-user",
                role="viewer",
                created_at_utc=now,
            ),
        ),
    )
    await storage.repositories.notification_targets.async_insert(
        NotificationTargetRecord(
            target_id="target-1",
            profile_id="profile-1",
            device_registry_id="device-1",
            platform="android",
            friendly_name="Phone",
            created_at_utc=now,
            updated_at_utc=now,
        )
    )
    service = NotificationInteractionService(
        storage.repositories.notification_interactions,
        ProfileACLService(storage.repositories.profiles),
        clock=clock,
        id_factory=lambda: "interaction-1",
        token_factory=lambda: "token-1",
    )
    return storage, service


async def test_interaction_persists_single_stage_protocol_state(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    try:
        created = await service.async_create(
            profile_id="profile-1",
            target_id="target-1",
            card_key="card-1",
            stage=NotificationStage.PROMPT,
            tag="locklearn:slot-1",
            expires_at=now + timedelta(minutes=30),
            payload={"slot_id": "slot-1"},
        )
        stored = await storage.repositories.notification_interactions.async_get_by_token(
            created.token
        )
        assert stored is not None
        assert stored["interaction_id"] == "interaction-1"
        assert stored["token"] == "token-1"
        assert stored["tag"] == "locklearn:slot-1"
        assert stored["stage"] == "prompt"
        assert stored["status"] == "pending"
        assert stored["expires_at_utc"] == (now + timedelta(minutes=30)).isoformat()
        assert stored["payload"] == {"slot_id": "slot-1"}
    finally:
        await storage.async_close()


async def test_concurrent_replay_has_exactly_one_claim_winner(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    try:
        await service.async_create(
            profile_id="profile-1",
            target_id="target-1",
            stage="prompt",
            expires_at=now + timedelta(minutes=30),
        )
        first, second = await asyncio.gather(
            service.async_consume_action(
                token="token-1",
                action_id="reveal",
                actor_user_id="owner-user",
            ),
            service.async_consume_action(
                token="token-1",
                action_id="reveal",
                actor_user_id="owner-user",
            ),
        )

        assert {first.disposition, second.disposition} == {
            NotificationActionDisposition.CONSUMED,
            NotificationActionDisposition.REPLAYED,
        }
        assert sum(result.may_apply_pedagogical_result for result in (first, second)) == 1
        stored = await storage.repositories.notification_interactions.async_get_by_token("token-1")
        assert stored is not None
        assert stored["status"] == "consumed"
        assert stored["action_id"] == "reveal"
    finally:
        await storage.async_close()


async def test_expired_then_replayed_action_can_never_apply_result(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    try:
        await service.async_create(
            profile_id="profile-1",
            target_id="target-1",
            stage="prompt",
            expires_at=now + timedelta(minutes=1),
        )
        clock.set(now + timedelta(minutes=2))

        expired = await service.async_consume_action(
            token="token-1",
            action_id="reveal",
            actor_user_id="owner-user",
        )
        replayed = await service.async_consume_action(
            token="token-1",
            action_id="reveal",
            actor_user_id="owner-user",
        )

        assert expired.disposition is NotificationActionDisposition.EXPIRED
        assert replayed.disposition is NotificationActionDisposition.REPLAYED
        assert not expired.may_apply_pedagogical_result
        assert not replayed.may_apply_pedagogical_result
        stored = await storage.repositories.notification_interactions.async_get_by_token("token-1")
        assert stored is not None
        assert stored["status"] == "expired"
        assert stored["consumed_at_utc"] is None
    finally:
        await storage.async_close()


async def test_user_context_is_enforced_when_available(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    try:
        await service.async_create(
            profile_id="profile-1",
            target_id="target-1",
            stage="prompt",
            expires_at=now + timedelta(minutes=30),
        )

        forbidden = await service.async_consume_action(
            token="token-1",
            action_id="reveal",
            actor_user_id="viewer-user",
        )
        pending = await storage.repositories.notification_interactions.async_get_by_token("token-1")
        assert forbidden.disposition is NotificationActionDisposition.FORBIDDEN
        assert pending is not None
        assert pending["status"] == "pending"

        consumed = await service.async_consume_action(
            token="token-1",
            action_id="reveal",
            actor_user_id="owner-user",
        )
        assert consumed.disposition is NotificationActionDisposition.CONSUMED
    finally:
        await storage.async_close()


async def test_missing_user_context_uses_only_single_use_token_gate(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    try:
        await service.async_create(
            profile_id="profile-1",
            target_id="target-1",
            stage="revealed",
            expires_at=now + timedelta(minutes=30),
        )
        result = await service.async_consume_action(
            token="token-1",
            action_id="known",
            actor_user_id=None,
        )
        assert result.disposition is NotificationActionDisposition.CONSUMED
        assert result.may_apply_pedagogical_result
    finally:
        await storage.async_close()


async def test_unknown_token_audit_never_persists_bearer_secret(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    secret = "unknown-bearer-secret"
    try:
        result = await service.async_consume_action(
            token=secret,
            action_id="reveal",
            actor_user_id=None,
        )
        assert result.disposition is NotificationActionDisposition.NOT_FOUND
    finally:
        await storage.async_close()

    connection = sqlite3.connect(storage.paths.state_db)
    try:
        event_type, actor_user_id, profile_id, payload_json = connection.execute(
            """SELECT event_type, actor_user_id, profile_id, payload_json
               FROM audit_events
               WHERE event_type = 'notification_action_rejected'
               ORDER BY id DESC
               LIMIT 1"""
        ).fetchone()
    finally:
        connection.close()
    assert event_type == "notification_action_rejected"
    assert actor_user_id is None
    assert profile_id is None
    assert secret not in payload_json
    assert json.loads(payload_json) == {"reason": "unknown_token"}


async def test_interaction_rejects_target_from_another_profile(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    clock = MutableClock(now)
    storage, service = await _runtime(tmp_path, clock=clock)
    try:
        await storage.repositories.profiles.async_insert_with_members(
            ProfileRecord(
                profile_id="profile-2",
                name="Other",
                preset="standard",
                timezone="Europe/Paris",
                created_at_utc=now.isoformat(),
                updated_at_utc=now.isoformat(),
            ),
            (
                ProfileMemberRecord(
                    profile_id="profile-2",
                    ha_user_id="other-owner",
                    role="owner",
                    created_at_utc=now.isoformat(),
                ),
            ),
        )
        try:
            await service.async_create(
                profile_id="profile-2",
                target_id="target-1",
                stage="prompt",
                expires_at=now + timedelta(minutes=30),
            )
        except StateRepositoryError:
            pass
        else:
            raise AssertionError("cross-profile target binding must be rejected")
    finally:
        await storage.async_close()
