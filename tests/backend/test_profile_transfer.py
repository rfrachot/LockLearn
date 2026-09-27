"""P6.4 secure Profile export/import and deletion lifecycle tests."""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from aiohttp import web
from homeassistant.components.http import KEY_HASS, KEY_HASS_USER

from custom_components.locklearn import profile_transfer_http
from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
from custom_components.locklearn.core.profiles import ProfileService, ProfileValidationError
from custom_components.locklearn.profile_transfer import (
    ProfileTransferError,
    ProfileTransferService,
    ProfileTransferStore,
    _import_profile_rows,
    _read_archive,
)
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths

_NOW = "2026-09-27T12:00:00+00:00"


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 9, 27, 12, tzinfo=UTC)


async def _storage(tmp_path: Path) -> SQLiteStorage:
    storage = SQLiteStorage(
        StoragePaths(
            tmp_path / "state" / "state.db",
            tmp_path / "content" / "current.db",
        )
    )
    await storage.async_open()
    return storage


async def _seed_private_profile(storage: SQLiteStorage) -> None:
    def seed(connection: sqlite3.Connection) -> None:
        connection.execute(
            """INSERT INTO profiles(
                   profile_id, name, preset, timezone, status, settings_json,
                   created_at_utc, updated_at_utc
               ) VALUES (?, ?, 'standard', 'Europe/Paris', 'active', ?, ?, ?)""",
            (
                "source-profile",
                "Private learner",
                '{"_locklearn_personal_profile":true,"scheduler":{"active_windows":[{"start":"08:00","end":"20:00"}],"receptive_when":"{{ is_state(\'binary_sensor.source\', \'on\') }}","routine_triggers":{"entity_ids":["automation.source"]},"target_ids":["target-1"]}}',
                _NOW,
                _NOW,
            ),
        )
        connection.execute(
            """INSERT INTO profile_members(profile_id, ha_user_id, role, created_at_utc)
               VALUES ('source-profile', 'source-owner', 'owner', ?)""",
            (_NOW,),
        )
        connection.execute(
            """INSERT INTO notification_targets(
                   target_id, profile_id, device_registry_id, platform, friendly_name,
                   created_at_utc, updated_at_utc
               ) VALUES ('target-1', 'source-profile', 'device-1', 'mobile_app', 'Phone', ?, ?)""",
            (_NOW, _NOW),
        )
        connection.execute(
            """INSERT INTO scheduler_config(
                   profile_id, version, timezone, active_days_json, active_windows_json,
                   minimum_gap_seconds, maximum_notifications_per_hour, quiet_hours_json,
                   updated_at_utc
               ) VALUES ('source-profile', 1, 'Europe/Paris', '[0,1,2,3,4,5,6]',
                        '[{"start":"08:00","end":"20:00"}]', 3600, 1,
                        '{"start":"22:00","end":"08:00"}', ?)""",
            (_NOW,),
        )
        connection.execute(
            """INSERT INTO tracks(
                   track_id, profile_id, name, source_language, target_language,
                   status, priority, settings_json, created_at_utc, updated_at_utc
               ) VALUES (
                   'source-track', 'source-profile', 'Private track', 'ja', 'fr',
                   'active', 1, '{"card_selection_mode":"explicit","scheduler":{"learning_count":1,"quiz_count":2,"target_ids":["target-1"]}}', ?, ?
               )""",
            (_NOW, _NOW),
        )
        connection.execute(
            """INSERT INTO track_card_rules(
                   track_id, rule_id, rule_kind, card_key, prompt_facet_id,
                   answer_facet_id, rule_json, enabled
               ) VALUES (
                   'source-track', 'rule-1', 'explicit_card', 'missing-card',
                   'prompt-facet', 'answer-facet', '{}', 1
               )"""
        )
        connection.execute(
            """INSERT INTO track_content_weights(track_id, content_type, weight)
               VALUES ('source-track', 'vocabulary', 1.0)"""
        )
        connection.execute(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, learning_item_id,
                   prompt_facet_id, answer_facet_id, state, mastery,
                   content_status, updated_at_utc
               ) VALUES (
                   'source-profile', 'source-track', 'missing-card', 'missing-item',
                   'prompt-facet', 'answer-facet', 'review', 0.6, 'active', ?
               )""",
            (_NOW,),
        )
        connection.execute(
            """INSERT INTO user_annotations(
                   annotation_id, profile_id, learning_item_id, card_key, note,
                   created_at_utc, updated_at_utc
               ) VALUES (
                   'annotation-1', 'source-profile', 'missing-item', 'missing-card',
                   'private note', ?, ?
               )""",
            (_NOW, _NOW),
        )
        connection.execute(
            """INSERT INTO stats_daily(
                   profile_id, track_id, local_date, timezone_name,
                   utc_offset_minutes, policy_version, verified_correct
               ) VALUES (
                   'source-profile', 'source-track', '2026-09-27',
                   'Europe/Paris', 120, 1, 1
               )"""
        )
        connection.execute(
            """INSERT INTO review_events(
                   id, profile_id, track_id, learning_item_id, prompt_facet_id,
                   answer_facet_id, card_key, mode, question_type, result,
                   hint_used, retrieval_occurred, signal_quality, policy_version,
                   dataset_generation, pre_state_snapshot, post_state_snapshot,
                   created_at_utc, local_date, timezone_name, utc_offset_minutes
               ) VALUES (
                   'review-1', 'source-profile', 'source-track', 'missing-item',
                   'prompt-facet', 'answer-facet', 'missing-card', 'learn',
                   'free_text', 'correct', 0, 1, 'verified', 1, 'generation-old',
                   '{"state":"learning"}', '{"state":"review"}',
                   ?, '2026-09-27', 'Europe/Paris', 120
               )""",
            (_NOW,),
        )
        connection.execute(
            """INSERT INTO sessions(
                   id, profile_id, track_id, status, version, current_position,
                   started_at_utc, last_activity_at_utc, question_count
               ) VALUES (
                   'session-1', 'source-profile', 'source-track', 'active', 2, 1,
                   ?, ?, 1
               )""",
            (_NOW, _NOW),
        )
        connection.execute(
            """INSERT INTO session_items(
                   session_id, position, question_id, card_key, learning_item_id,
                   prompt_facet_id, answer_facet_id, status, payload_json
               ) VALUES (
                   'session-1', 0, 'question-1', 'missing-card', 'missing-item',
                   'prompt-facet', 'answer-facet', 'answered', '{}'
               )"""
        )
        connection.execute(
            """INSERT INTO session_answers(
                   session_id, question_id, answer_json, resulting_version,
                   created_at_utc
               ) VALUES (
                   'session-1', 'question-1', '{"text":"private answer"}', 2, ?
               )""",
            (_NOW,),
        )
        connection.execute(
            """INSERT INTO scheduled_slots(
                   slot_id, profile_id, track_id, slot_type, scheduled_for_utc,
                   status, scheduler_config_version, seed, created_at_utc,
                   updated_at_utc
               ) VALUES (
                   'slot-1', 'source-profile', 'source-track', 'review', ?,
                   'scheduled', 1, 'seed', ?, ?
               )""",
            (_NOW, _NOW, _NOW),
        )
        connection.execute(
            """INSERT INTO notification_interactions(
                   interaction_id, token, profile_id, track_id, target_id,
                   stage, status, created_at_utc, expires_at_utc
               ) VALUES (
                   'interaction-1', 'token-1', 'source-profile', 'source-track',
                   'target-1', 'prompt', 'pending', ?, ?
               )""",
            (_NOW, _NOW),
        )
        connection.execute(
            """INSERT INTO receptivity_samples(
                   slot_id, profile_id, target_id, delivered_at_utc, timezone_name,
                   weekday, local_hour, updated_at_utc
               ) VALUES ('slot-1', 'source-profile', 'target-1', ?, 'Europe/Paris', 6, 14, ?)""",
            (_NOW, _NOW),
        )
        connection.commit()

    await storage._async_writer(seed)


async def test_export_import_round_trip_remaps_identity_and_preserves_tombstones(
    tmp_path: Path,
) -> None:
    storage = await _storage(tmp_path)
    store = ProfileTransferStore(tmp_path / "private-transfer")
    await store.async_initialize()
    service = ProfileTransferService(storage, store)
    try:
        await _seed_private_profile(storage)
        transfer = await service.async_create_export(
            profile_id="source-profile",
            owner_user_id="source-owner",
            include_reviews=True,
            include_sessions=True,
        )
        consumed = await store.async_consume_export(
            transfer.token,
            "source-owner",
        )
        assert consumed is not None
        _, archive = consumed
        assert await store.async_consume_export(transfer.token, "source-owner") is None

        uploaded = await store.async_store_import(
            owner_user_id="import-owner",
            archive_bytes=archive,
        )
        dry_run = await service.async_dry_run_import(
            upload_token=uploaded.token,
            owner_user_id="import-owner",
        )
        assert dry_run.track_count == 1
        assert dry_run.progress_count == 1
        assert dry_run.review_count == 1
        assert dry_run.session_count == 1
        assert dry_run.missing_card_count == 1
        assert (
            await storage._async_reader(
                lambda connection: connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
            )
            == 1
        )

        result = await service.async_apply_import(
            upload_token=uploaded.token,
            owner_user_id="import-owner",
            name_override="Imported learner",
        )
        imported_profile_id = str(result["profile_id"])
        assert imported_profile_id != "source-profile"

        def inspect(connection: sqlite3.Connection) -> dict[str, object]:
            profile = connection.execute(
                "SELECT name, status, settings_json FROM profiles WHERE profile_id = ?",
                (imported_profile_id,),
            ).fetchone()
            member = connection.execute(
                """SELECT ha_user_id, role FROM profile_members
                   WHERE profile_id = ?""",
                (imported_profile_id,),
            ).fetchone()
            track = connection.execute(
                """SELECT track_id, status FROM tracks
                   WHERE profile_id = ?""",
                (imported_profile_id,),
            ).fetchone()
            assert track is not None
            track_settings = connection.execute(
                "SELECT settings_json FROM tracks WHERE track_id = ?",
                (str(track[0]),),
            ).fetchone()
            progress = connection.execute(
                """SELECT content_status FROM progress
                   WHERE profile_id = ?""",
                (imported_profile_id,),
            ).fetchone()
            rule_count = connection.execute(
                "SELECT COUNT(*) FROM track_card_rules WHERE track_id = ?",
                (str(track[0]),),
            ).fetchone()[0]
            weight_count = connection.execute(
                "SELECT COUNT(*) FROM track_content_weights WHERE track_id = ?",
                (str(track[0]),),
            ).fetchone()[0]
            session = connection.execute(
                "SELECT id, status FROM sessions WHERE profile_id = ?",
                (imported_profile_id,),
            ).fetchone()
            review = connection.execute(
                """SELECT pre_state_snapshot, post_state_snapshot
                   FROM review_events WHERE profile_id = ?""",
                (imported_profile_id,),
            ).fetchone()
            return {
                "profile": profile,
                "member": member,
                "track": track,
                "track_settings": track_settings,
                "progress": progress,
                "rule_count": rule_count,
                "weight_count": weight_count,
                "session": session,
                "review": review,
            }

        values = await storage._async_reader(inspect)
        track_values = cast(tuple[object, ...], values["track"])
        session_values = cast(tuple[object, ...], values["session"])
        review_values = cast(tuple[str, str], values["review"])
        profile_values = cast(tuple[str, str, str], values["profile"])
        imported_settings = json.loads(profile_values[2])
        track_settings = json.loads(cast(tuple[str], values["track_settings"])[0])
        assert profile_values[0:2] == ("Imported learner", "archived")
        assert "_locklearn_personal_profile" not in imported_settings
        assert "routine_triggers" not in imported_settings["scheduler"]
        assert "receptive_when" not in imported_settings["scheduler"]
        assert "target_ids" not in imported_settings["scheduler"]
        assert "target_ids" not in track_settings["scheduler"]
        assert values["member"] == ("import-owner", "owner")
        assert track_values[1] == "archived"
        assert values["progress"] == ("removed",)
        assert values["rule_count"] == 1
        assert values["weight_count"] == 1
        assert session_values[1] == "paused"
        assert json.loads(review_values[0]) == {"state": "learning"}
        assert json.loads(review_values[1]) == {"state": "review"}
    finally:
        await store.async_close()
        await storage.async_close()


async def test_import_rejects_hostile_archive_and_owner_mismatch(tmp_path: Path) -> None:
    storage = await _storage(tmp_path)
    store = ProfileTransferStore(tmp_path / "private-transfer")
    await store.async_initialize()
    service = ProfileTransferService(storage, store)
    try:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("../profile.json", b"{}")
        uploaded = await store.async_store_import(
            owner_user_id="owner-a",
            archive_bytes=output.getvalue(),
        )
        with pytest.raises(ProfileTransferError, match="unsafe ZIP member"):
            await service.async_dry_run_import(
                upload_token=uploaded.token,
                owner_user_id="owner-a",
            )
        with pytest.raises(ProfileTransferError, match="unavailable or expired"):
            await service.async_dry_run_import(
                upload_token=uploaded.token,
                owner_user_id="owner-b",
            )
    finally:
        await store.async_close()
        await storage.async_close()


async def test_import_preserves_superseded_card_lifecycle_status(tmp_path: Path) -> None:
    storage = await _storage(tmp_path)
    store = ProfileTransferStore(tmp_path / "private-transfer")
    await store.async_initialize()
    service = ProfileTransferService(storage, store)
    try:
        await _seed_private_profile(storage)
        transfer = await service.async_create_export(
            profile_id="source-profile",
            owner_user_id="source-owner",
            include_reviews=False,
            include_sessions=False,
        )
        consumed = await store.async_consume_export(transfer.token, "source-owner")
        assert consumed is not None
        archive_path = tmp_path / "superseded.zip"
        archive_path.write_bytes(consumed[1])
        document = _read_archive(archive_path)
        result = await storage._async_writer(
            lambda connection: _import_profile_rows(
                connection,
                document,
                owner_user_id="import-owner",
                existing_cards={"missing-card": "superseded"},
                pack_generations={},
                name_override=None,
            )
        )

        assert (
            await storage._async_reader(
                lambda connection: connection.execute(
                    "SELECT content_status FROM progress WHERE profile_id = ?",
                    (str(result["profile_id"]),),
                ).fetchone()[0]
            )
            == "superseded"
        )
    finally:
        await store.async_close()
        await storage.async_close()


@pytest.mark.parametrize(
    ("member_name", "expected"),
    [
        ("/profile.json", "unsafe ZIP member path"),
        ("..\\profile.json", "unsafe ZIP member name"),
        ("../profile.json", "unsafe ZIP member path"),
        ("unexpected.json", "unexpected profile archive member"),
    ],
)
def test_hostile_archive_member_names_are_rejected(
    tmp_path: Path,
    member_name: str,
    expected: str,
) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(member_name, b"{}")
    path = tmp_path / "hostile.zip"
    path.write_bytes(output.getvalue())
    with pytest.raises(ProfileTransferError, match=expected):
        _read_archive(path)


@pytest.mark.parametrize("kind", ("duplicate", "symlink", "dos_directory", "bzip2"))
def test_hostile_archive_members_are_rejected(tmp_path: Path, kind: str) -> None:
    output = io.BytesIO()
    compression = zipfile.ZIP_BZIP2 if kind == "bzip2" else zipfile.ZIP_STORED
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        if kind == "duplicate":
            archive.writestr("profile.json", b"{}")
            archive.writestr("profile.json", b"{}")
        else:
            info = zipfile.ZipInfo("profile.json")
            info.compress_type = compression
            if kind == "symlink":
                info.create_system = 3
                info.external_attr = (0o120777 << 16) | 0xA000
            elif kind == "dos_directory":
                info.create_system = 0
                info.external_attr = 0x10
            archive.writestr(info, b"{}")
    path = tmp_path / f"hostile-{kind}.zip"
    path.write_bytes(output.getvalue())
    with pytest.raises(ProfileTransferError):
        _read_archive(path)


async def test_import_capability_claim_is_owner_bound_and_one_shot(tmp_path: Path) -> None:
    store = ProfileTransferStore(tmp_path / "private-transfer")
    await store.async_initialize()
    try:
        uploaded = await store.async_store_import(
            owner_user_id="owner-a",
            archive_bytes=b"not-a-zip",
        )
        assert await store.async_claim_import(uploaded.token, "owner-b") is None
        claimed = await store.async_claim_import(uploaded.token, "owner-a")
        assert claimed == uploaded
        assert await store.async_resolve_import(uploaded.token, "owner-a") is None
        await store.async_delete_import(uploaded.token, "owner-a")
        assert await store.async_claim_import(uploaded.token, "owner-a") is None
    finally:
        await store.async_close()


async def test_http_export_route_requires_auth_owner_and_consumes_once(
    tmp_path: Path, monkeypatch
) -> None:
    store = ProfileTransferStore(tmp_path / "private-transfer")
    await store.async_initialize()
    monkeypatch.setattr(profile_transfer_http, "LockLearnRuntime", SimpleNamespace)
    try:
        transfer = await store.async_create_export(
            owner_user_id="owner-a",
            profile_id="profile-a",
            archive_bytes=b"private-archive",
            filename="locklearn-profile.zip",
        )
        runtime = SimpleNamespace(profile_transfers=SimpleNamespace(store=store))
        hass = SimpleNamespace(data={DOMAIN: {DATA_RUNTIME: runtime}})

        def request_for(user_id: str | None) -> web.Request:
            return cast(
                web.Request,
                SimpleNamespace(
                    app={KEY_HASS: hass},
                    get=lambda key: (
                        None
                        if user_id is None or key != KEY_HASS_USER
                        else SimpleNamespace(id=user_id)
                    ),
                ),
            )

        view = profile_transfer_http.ProfileExportDownloadView()
        assert view.requires_auth is True
        with pytest.raises(web.HTTPUnauthorized):
            profile_transfer_http._authenticated_user_id(request_for(None))
        with pytest.raises(web.HTTPNotFound):
            await view.get(request_for("owner-b"), transfer.token)

        response = await view.get(request_for("owner-a"), transfer.token)
        assert response.status == 200
        assert response.body == b"private-archive"
        assert response.headers["Cache-Control"] == "no-store, max-age=0"
        with pytest.raises(web.HTTPNotFound):
            await view.get(request_for("owner-a"), transfer.token)
    finally:
        await store.async_close()


async def test_archive_quiesces_delivery_state_and_permanent_delete_requires_confirmation(
    tmp_path: Path,
) -> None:
    storage = await _storage(tmp_path)
    service = ProfileService(
        storage.repositories.profiles,
        clock=_Clock(),
    )
    try:
        await _seed_private_profile(storage)
        assert await service.async_archive_profile("source-profile")

        def archived(connection: sqlite3.Connection) -> tuple[str, str, str, str]:
            profile_status = connection.execute(
                "SELECT status FROM profiles WHERE profile_id = 'source-profile'"
            ).fetchone()[0]
            session_status = connection.execute(
                "SELECT status FROM sessions WHERE id = 'session-1'"
            ).fetchone()[0]
            slot_status = connection.execute(
                "SELECT status FROM scheduled_slots WHERE slot_id = 'slot-1'"
            ).fetchone()[0]
            interaction_status = connection.execute(
                """SELECT status FROM notification_interactions
                   WHERE interaction_id = 'interaction-1'"""
            ).fetchone()[0]
            return (
                str(profile_status),
                str(session_status),
                str(slot_status),
                str(interaction_status),
            )

        assert await storage._async_reader(archived) == (
            "archived",
            "paused",
            "cancelled",
            "cleared",
        )

        with pytest.raises(ProfileValidationError, match="exact confirmation"):
            await service.async_delete_profile(
                "source-profile",
                confirmation="DELETE",
            )

        assert await service.async_delete_profile(
            "source-profile",
            confirmation="DELETE source-profile",
        )

        def remaining(connection: sqlite3.Connection) -> dict[str, int]:
            tables = (
                "profiles",
                "profile_members",
                "tracks",
                "notification_targets",
                "scheduler_config",
                "progress",
                "review_events",
                "user_annotations",
                "sessions",
                "stats_daily",
                "scheduled_slots",
                "receptivity_samples",
                "notification_interactions",
                "audit_events",
            )
            result: dict[str, int] = {}
            for table in tables:
                if table == "profiles":
                    sql = "SELECT COUNT(*) FROM profiles WHERE profile_id = ?"
                elif table == "profile_members":
                    sql = "SELECT COUNT(*) FROM profile_members WHERE profile_id = ?"
                elif table == "tracks":
                    sql = "SELECT COUNT(*) FROM tracks WHERE profile_id = ?"
                else:
                    sql = f"SELECT COUNT(*) FROM {table} WHERE profile_id = ?"
                result[table] = int(connection.execute(sql, ("source-profile",)).fetchone()[0])
            return result

        assert all(count == 0 for count in (await storage._async_reader(remaining)).values())
    finally:
        await storage.async_close()
