"""P6.8 complete negative WebSocket ACL matrix."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DOMAIN
from tests.backend.content_db_helpers import ITEM_A, card_identity, create_package, facet_ids


async def _assert_denied(client: Any, payload: dict[str, Any], code: str) -> None:
    await client.send_json_auto_id(payload)
    response = await client.receive_json()
    assert response["success"] is False, payload["type"]
    assert response["error"]["code"] == code, payload["type"]


async def test_all_acl_scoped_websocket_endpoints_have_negative_access_coverage(
    hass: HomeAssistant,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
    hass_read_only_user: Any,
    tmp_path: Path,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = hass.data[DOMAIN]["runtime"]

    package = create_package(
        tmp_path / "p6-8-acl-package.db",
        "p6-8-acl",
        active_item_ids=(ITEM_A,),
    )
    candidate = runtime.storage.paths.content_staging_dir / "generation-p6-8-acl.db"
    await runtime.storage.async_build_content_generation(
        (package,),
        candidate,
        generation_id="generation-p6-8-acl",
    )
    await runtime.storage.async_activate_content_generation(candidate)

    owner = await hass_ws_client(hass)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/create",
            "name": "P6.8 ACL owner",
            "preset": "standard",
            "timezone": "Europe/Paris",
        }
    )
    profile_response = await owner.receive_json()
    assert profile_response["success"] is True
    profile_id = profile_response["result"]["profile_id"]

    card_key = card_identity(ITEM_A)[1]
    prompt_facet_id, answer_facet_id = facet_ids(ITEM_A)
    await owner.send_json_auto_id(
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "P6.8 ACL track",
            "pack_version_id": "locklearn:pack-version:p6-8-acl",
            "source_language": "en",
            "target_language": "fr",
            "explicit_card_keys": [card_key],
        }
    )
    track_response = await owner.receive_json()
    assert track_response["success"] is True
    track_id = track_response["result"]["track_id"]

    await owner.send_json_auto_id(
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "track_id": track_id,
            "settings": {"requested_cards": 1},
        }
    )
    session_response = await owner.receive_json()
    assert session_response["success"] is True
    session = session_response["result"]
    session_id = session["id"]
    question_id = session["current_question"]["question_id"]

    non_admin = await hass_ws_client(hass, hass_read_only_access_token)

    outsider_reads = (
        {"type": "locklearn/tracks/list", "profile_id": profile_id},
        {"type": "locklearn/stats/get", "profile_id": profile_id},
        {"type": "locklearn/dashboard/get", "profile_id": profile_id},
        {"type": "locklearn/difficulties/list", "profile_id": profile_id},
        {"type": "locklearn/confusions/list", "profile_id": profile_id},
        {"type": "locklearn/annotations/list", "profile_id": profile_id},
        {"type": "locklearn/notifications/unrecorded_responses", "profile_id": profile_id},
        {"type": "locklearn/scheduler/preview", "profile_id": profile_id},
        {"type": "locklearn/session/get", "session_id": session_id},
        {"type": "locklearn/session/subscribe", "session_id": session_id},
    )
    for payload in outsider_reads:
        await _assert_denied(non_admin, payload, "locklearn/not_found")

    await owner.send_json_auto_id(
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": hass_read_only_user.id,
            "role": "viewer",
        }
    )
    assert (await owner.receive_json())["success"] is True

    profile_mutations = (
        {"type": "locklearn/profiles/update", "profile_id": profile_id},
        {"type": "locklearn/profiles/delete", "profile_id": profile_id},
        {"type": "locklearn/profiles/export", "profile_id": profile_id},
        {
            "type": "locklearn/profiles/share",
            "profile_id": profile_id,
            "target_user_id": "other-user",
            "role": "viewer",
        },
        {"type": "locklearn/profiles/members", "profile_id": profile_id},
        {"type": "locklearn/profiles/share_targets", "profile_id": profile_id},
        {"type": "locklearn/targets/list", "profile_id": profile_id},
        {
            "type": "locklearn/tracks/create",
            "profile_id": profile_id,
            "name": "Denied",
            "pack_version_id": "locklearn:pack-version:p6-8-acl",
            "source_language": "en",
            "target_language": "fr",
        },
        {
            "type": "locklearn/content/report",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card_key,
            "learning_item_id": ITEM_A,
            "prompt_facet_id": prompt_facet_id,
            "answer_facet_id": answer_facet_id,
            "submitted_text": "denied",
            "grading_policy_kind": "exact",
            "grading_policy_version": 1,
            "normalization_version": 1,
        },
        {
            "type": "locklearn/content/report_question",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card_key,
            "learning_item_id": ITEM_A,
            "prompt_facet_id": prompt_facet_id,
            "answer_facet_id": answer_facet_id,
        },
        {
            "type": "locklearn/progress/set_user_state",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card_key,
            "user_state": "active",
        },
        {
            "type": "locklearn/calibration/sample",
            "profile_id": profile_id,
            "track_id": track_id,
            "sample_size": 20,
        },
        {"type": "locklearn/annotations/create", "profile_id": profile_id, "note": "denied"},
        {
            "type": "locklearn/annotations/update",
            "profile_id": profile_id,
            "annotation_id": "missing",
            "note": "denied",
        },
        {
            "type": "locklearn/annotations/delete",
            "profile_id": profile_id,
            "annotation_id": "missing",
        },
        {
            "type": "locklearn/leeches/reactivate",
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card_key,
        },
        {"type": "locklearn/progress/undo_last", "profile_id": profile_id},
        {
            "type": "locklearn/session/start",
            "profile_id": profile_id,
            "track_id": track_id,
        },
    )
    for payload in profile_mutations:
        await _assert_denied(non_admin, payload, "locklearn/forbidden")

    plan_fields = {
        "max_new_per_day_cards": 8,
        "max_reviews_per_day_cards": 80,
        "max_notification_new_teasers": 2,
        "target_coverage": 1.0,
        "target_retention": 0.9,
    }
    track_mutations = (
        {"type": "locklearn/tracks/update", "track_id": track_id, "name": "Denied"},
        {"type": "locklearn/tracks/delete", "track_id": track_id},
        {
            "type": "locklearn/tracks/integrate_pack_update",
            "track_id": track_id,
            "pack_version_id": "locklearn:pack-version:p6-8-acl",
        },
        {
            "type": "locklearn/tracks/preview_pack_update",
            "track_id": track_id,
            "pack_version_id": "locklearn:pack-version:p6-8-acl",
        },
        {"type": "locklearn/tracks/plan_preview", "track_id": track_id, **plan_fields},
        {"type": "locklearn/tracks/plan_set", "track_id": track_id, **plan_fields},
    )
    for payload in track_mutations:
        await _assert_denied(non_admin, payload, "locklearn/forbidden")

    session_mutations = (
        {
            "type": "locklearn/quiz/evaluate",
            "session_id": session_id,
            "question_id": question_id,
            "answer": {"choice": "denied"},
        },
        {
            "type": "locklearn/quiz/answer",
            "session_id": session_id,
            "expected_version": 1,
            "question_id": question_id,
            "answer": {"choice": "denied"},
        },
        {
            "type": "locklearn/session/answer",
            "session_id": session_id,
            "expected_version": 1,
            "question_id": question_id,
            "answer": {"choice": "denied"},
        },
        {
            "type": "locklearn/session/pause",
            "session_id": session_id,
            "expected_version": 1,
        },
        {
            "type": "locklearn/session/complete",
            "session_id": session_id,
            "expected_version": 1,
        },
        {
            "type": "locklearn/session/undo",
            "session_id": session_id,
            "expected_version": 1,
        },
    )
    for payload in session_mutations:
        await _assert_denied(non_admin, payload, "locklearn/forbidden")

    import_record = await runtime.profile_transfers.store.async_store_import(
        owner_user_id="different-owner",
        archive_bytes=b"not-for-this-user",
    )
    for command in ("locklearn/profiles/import_dry_run", "locklearn/profiles/import_apply"):
        await _assert_denied(
            non_admin,
            {"type": command, "upload_token": import_record.token},
            "locklearn/invalid_request",
        )

    for payload in (
        {"type": "locklearn/datasets/refresh"},
        {"type": "locklearn/datasets/install", "dataset_id": "missing"},
    ):
        await _assert_denied(non_admin, payload, "locklearn/forbidden")

    admin_commands = (
        {"type": "locklearn/admin/rebuild_progress"},
        {"type": "locklearn/admin/rebuild_stats"},
        {"type": "locklearn/admin/recompute_progress", "policy_version": 1},
        {"type": "locklearn/admin/storage/status"},
    )
    for payload in admin_commands:
        await _assert_denied(non_admin, payload, "unauthorized")

    operation_gate = asyncio.Event()

    async def operation_worker(_context: Any) -> None:
        await operation_gate.wait()

    operation_id = runtime.operations.start(
        "p6_8_acl",
        operation_worker,
        owner_user_id="different-owner",
    )
    for command in ("locklearn/operations/subscribe", "locklearn/operations/cancel"):
        await _assert_denied(
            non_admin,
            {"type": command, "operation_id": operation_id},
            "locklearn/forbidden",
        )

    task = runtime.operations.task(operation_id)
    assert runtime.operations.cancel(operation_id)
    if task is not None:
        await asyncio.gather(task, return_exceptions=True)

    await hass.config_entries.async_unload(entry.entry_id)
