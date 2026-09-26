#!/usr/bin/env python3
"""Run the P3.8 real-Home-Assistant qualification through public APIs only.

This creates a temporary Profile and Track using the installed signed starter
pack.  It never accepts a client-prepared question, never reads or changes the
state database directly, and removes its temporary Profile (and therefore its
Track/session/audit rows) through the public API before exiting.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

from scripts.p0_real_instance import HAWebSocket, connect, load_allowed_env

PACK_VERSION_ID = "locklearn:pack-version:japanese-starter-1.0.0"


class QualificationError(RuntimeError):
    """Raised when a mandatory qualification assertion fails."""


async def _response(client: HAWebSocket, message_type: str, **data: Any) -> dict[str, Any]:
    """Return a raw WebSocket response while preserving subscription events."""
    client.message_id += 1
    message_id = client.message_id
    await client.websocket.send_json({"id": message_id, "type": message_type, **data})
    while True:
        response = await client.websocket.receive_json()
        if response.get("id") != message_id:
            client.pending.append(response)
            continue
        return response


async def _result(client: HAWebSocket, message_type: str, **data: Any) -> Any:
    response = await _response(client, message_type, **data)
    if not response.get("success", False):
        error = response.get("error", {})
        raise QualificationError(f"{message_type} failed: {error.get('code', 'unknown')}")
    return response.get("result")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise QualificationError(message)


async def _expect_stale(client: HAWebSocket, message_type: str, **data: Any) -> None:
    response = await _response(client, message_type, **data)
    _assert(not response.get("success", False), f"{message_type} unexpectedly succeeded")
    _assert(
        response.get("error", {}).get("code") == "locklearn/stale_session",
        f"{message_type} did not return locklearn/stale_session",
    )


async def _next_event(client: HAWebSocket, expected_version: int) -> None:
    message = await client.next_message(timeout=5)
    _assert(message.get("type") == "event", "subscriber did not receive an event")
    _assert(
        message.get("event", {}).get("version") == expected_version,
        "subscriber received an unexpected snapshot version",
    )


async def _expect_no_event(client: HAWebSocket) -> None:
    with suppress(asyncio.TimeoutError):
        message = await client.next_message(timeout=1)
        raise QualificationError(f"pre-reload subscriber survived reload: {message.get('type')}")


def _locklearn_error_keys(records: list[dict[str, Any]]) -> set[str]:
    """Return only stable log record metadata; never retain log message bodies."""
    return {
        str(record.get("key"))
        for record in records
        if str(record.get("name", "")).startswith("custom_components.locklearn")
        and str(record.get("level", "")).lower() in {"error", "critical"}
    }


async def _close(session: Any, client: HAWebSocket | None) -> None:
    if client is not None:
        with suppress(Exception):
            await client.websocket.close()
    with suppress(Exception):
        await session.close()


async def main() -> None:
    load_allowed_env(Path(".env"))
    run_label = uuid4().hex[:8]
    primary_session, primary = await connect()
    secondary_session: Any | None = None
    secondary: HAWebSocket | None = None
    reconnect_session: Any | None = None
    reconnect: HAWebSocket | None = None
    post_reload_session: Any | None = None
    post_reload: HAWebSocket | None = None
    profile_id: str | None = None

    try:
        config = await _result(primary, "get_config")
        entries = await _result(primary, "config_entries/get", domain="locklearn")
        panels = await _result(primary, "get_panels")
        packs = await _result(primary, "locklearn/packs/list", limit=100)
        diagnostics_before = await _result(primary, "locklearn/admin/storage/status")
        log_keys_before = _locklearn_error_keys(await _result(primary, "system_log/list"))

        _assert(len(entries) == 1, "expected exactly one LockLearn Config Entry")
        _assert("locklearn" in panels, "expected exactly one LockLearn panel")
        _assert(
            sum(1 for panel in panels if panel == "locklearn") == 1,
            "expected exactly one LockLearn panel",
        )
        _assert(
            any(item.get("pack_version_id") == PACK_VERSION_ID for item in packs.get("items", [])),
            "Japanese Starter PackVersion is not active",
        )

        profile = await _result(
            primary,
            "locklearn/profiles/create",
            name=f"P3.8 qualification {run_label}",
            preset="standard",
            timezone="Europe/Paris",
        )
        profile_id = str(profile["profile_id"])
        track = await _result(
            primary,
            "locklearn/tracks/create",
            profile_id=profile_id,
            name=f"P3.8 track {run_label}",
            pack_version_id=PACK_VERSION_ID,
            source_language="ja",
            target_language="ja-Latn",
        )
        track_id = str(track["track_id"])
        started = await _result(
            primary,
            "locklearn/session/start",
            profile_id=profile_id,
            track_id=track_id,
            session_type="bounded",
            strategy="default",
            settings={"requested_cards": 2},
        )
        current = started.get("current_question")
        _assert(int(started.get("question_count", 0)) >= 1, "start returned no questions")
        _assert(isinstance(current, dict), "start returned no current_question")
        _assert(bool(current.get("card_key")), "question has no CardDefinition identity")
        _assert(
            bool(current.get("payload", {}).get("dataset_generation")),
            "question has no backend-pinned dataset_generation",
        )
        session_id = str(started["id"])
        question_id = str(current["question_id"])
        initial_version = int(started["version"])
        _assert(initial_version == 1, "unexpected initial session version")

        secondary_session, secondary = await connect()
        same_snapshot = await _result(secondary, "locklearn/session/get", session_id=session_id)
        _assert(
            same_snapshot["id"] == session_id
            and int(same_snapshot["version"]) == initial_version
            and same_snapshot["current_question"]["question_id"] == question_id,
            "independent client did not reconstruct the initial snapshot",
        )
        subscribed = await _result(secondary, "locklearn/session/subscribe", session_id=session_id)
        _assert(int(subscribed["version"]) == initial_version, "subscribe returned stale snapshot")

        answer = {
            "session_id": session_id,
            "expected_version": initial_version,
            "question_id": question_id,
            "answer": {"qualification": "transport-only"},
        }
        first, second = await asyncio.gather(
            _response(primary, "locklearn/session/answer", **answer),
            _response(secondary, "locklearn/session/answer", **answer),
        )
        responses = (first, second)
        winners = [response for response in responses if response.get("success", False)]
        losers = [response for response in responses if not response.get("success", False)]
        _assert(
            len(winners) == 1 and len(losers) == 1, "CAS did not produce one winner and one loser"
        )
        winner = winners[0]["result"]
        _assert(
            int(winner["version"]) == initial_version + 1, "winner did not advance version once"
        )
        _assert(
            losers[0].get("error", {}).get("code") == "locklearn/stale_session",
            "CAS loser did not receive locklearn/stale_session",
        )
        winner_client = "primary" if first.get("success", False) else "secondary"
        await _next_event(secondary, initial_version + 1)
        answered = await _result(primary, "locklearn/session/get", session_id=session_id)
        _assert(len(answered["answers"]) == 1, "CAS created more than one answer attempt")
        _assert(
            int(diagnostics_before["session_answer_count"]) + 1
            == int(
                (await _result(primary, "locklearn/admin/storage/status"))["session_answer_count"]
            ),
            "state.db answer count did not increase by exactly one",
        )

        undo_version = int(answered["version"])
        undone = await _result(
            primary,
            "locklearn/session/undo",
            session_id=session_id,
            expected_version=undo_version,
        )
        _assert(int(undone["version"]) == undo_version + 1, "undo did not advance version")
        _assert(
            undone["current_question"]["question_id"] == question_id,
            "undo did not make the previous question navigable",
        )
        _assert(len(undone["answers"]) == 1, "undo deleted answer history")
        await _next_event(secondary, undo_version + 1)
        await _expect_stale(
            primary,
            "locklearn/session/undo",
            session_id=session_id,
            expected_version=undo_version,
        )

        await _close(secondary_session, secondary)
        secondary_session = None
        secondary = None
        reconnect_session, reconnect = await connect()
        reconnected = await _result(reconnect, "locklearn/session/get", session_id=session_id)
        _assert(
            int(reconnected["version"]) == undo_version + 1 and len(reconnected["answers"]) == 1,
            "reconnect did not reconstruct the persisted snapshot",
        )
        await _result(reconnect, "locklearn/session/subscribe", session_id=session_id)

        entry_id = str(entries[0]["entry_id"])
        await _result(
            primary,
            "call_service",
            domain="homeassistant",
            service="reload_config_entry",
            service_data={"entry_id": entry_id},
        )
        post_reload_session, post_reload = await connect()
        after_reload = await _result(post_reload, "locklearn/session/get", session_id=session_id)
        _assert(
            int(after_reload["version"]) == undo_version + 1 and len(after_reload["answers"]) == 1,
            "reload did not preserve the session snapshot",
        )
        await _result(post_reload, "locklearn/session/subscribe", session_id=session_id)
        paused = await _result(
            post_reload,
            "locklearn/session/pause",
            session_id=session_id,
            expected_version=int(after_reload["version"]),
            paused=True,
        )
        await _next_event(post_reload, int(paused["version"]))
        await _expect_no_event(reconnect)

        entries_after = await _result(post_reload, "config_entries/get", domain="locklearn")
        panels_after = await _result(post_reload, "get_panels")
        diagnostics_after = await _result(post_reload, "locklearn/admin/storage/status")
        log_keys_after = _locklearn_error_keys(await _result(post_reload, "system_log/list"))
        _assert(len(entries_after) == 1, "reload changed LockLearn Config Entry count")
        _assert(
            sum(1 for panel in panels_after if panel == "locklearn") == 1,
            "reload changed panel count",
        )
        _assert(diagnostics_after["integrity_check"] == ["ok"], "SQLite integrity_check failed")
        _assert(diagnostics_after["foreign_key_violation_count"] == 0, "SQLite FK violation")
        _assert(diagnostics_after["journal_mode"] == "wal", "SQLite is not in WAL mode")
        _assert(
            diagnostics_after["reader_off_event_loop"] is True, "SQLite reader ran on event loop"
        )
        _assert(diagnostics_after["writer_initialized"] is True, "SQLite writer is not initialized")
        _assert(log_keys_after <= log_keys_before, "new LockLearn ERROR/CRITICAL log record")

        print("P3.8 real HA qualification: PASS")
        print(f"ha_version={config.get('version', 'unknown')}")
        print("bootstrap=question_count>=1,current_question,card_identity,dataset_generation")
        print(
            "answer_cas="
            f"winner={winner_client},one_stale_loser,version_1_to_2,"
            "one_answer_row,winner_only_event"
        )
        print(
            "undo=version_2_to_3,previous_question_restored,answer_history_preserved,stale_rejected"
        )
        print(
            "reconnect_reload=persisted_snapshot,old_subscription_cleared,new_subscription_received_event"
        )
        print("storage=integrity_ok,fk_zero,wal,reader_off_event_loop,writer_initialized")
    finally:
        if profile_id is not None:
            with suppress(Exception):
                await _result(
                    post_reload or primary,
                    "locklearn/profiles/delete",
                    profile_id=profile_id,
                )
        await _close(post_reload_session, post_reload)
        await _close(reconnect_session, reconnect)
        await _close(secondary_session, secondary)
        await _close(primary_session, primary)


if __name__ == "__main__":
    started_at = monotonic()
    asyncio.run(main())
    print(f"elapsed_seconds={monotonic() - started_at:.2f}")
