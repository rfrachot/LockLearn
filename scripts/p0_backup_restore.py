#!/usr/bin/env python3
"""Secret-safe, bounded P0.7 Home Assistant backup/restore qualification."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any, cast
from uuid import uuid4

from scripts.p0_real_instance import HAWebSocket, connect, load_allowed_env

SAFETY_BACKUP_NAMES = {"PRE_P0.7", "Pre-locklearn"}
LOCAL_BACKUP_AGENT = "hassio.local"


def backup_summary(backup: dict[str, Any]) -> dict[str, Any]:
    """Return only the backup metadata needed for the qualification evidence."""
    return {
        "backup_id": backup.get("backup_id"),
        "name": backup.get("name"),
        "date": backup.get("date"),
        "homeassistant_included": backup.get("homeassistant_included"),
        "homeassistant_version": backup.get("homeassistant_version"),
        "database_included": backup.get("database_included"),
        "addons": backup.get("addons"),
        "folders": backup.get("folders"),
        "agents": sorted((backup.get("agents") or {}).keys()),
        "failed_addons": backup.get("failed_addons"),
        "failed_agent_ids": backup.get("failed_agent_ids"),
        "failed_folders": backup.get("failed_folders"),
    }


async def backup_inventory(client: HAWebSocket) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return backup manager state and known backups."""
    info = await client.call("backup/info")
    return info, list(info.get("backups", []))


def safety_backups(backups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find safety backups without inspecting archive contents."""
    return [backup_summary(item) for item in backups if item.get("name") in SAFETY_BACKUP_NAMES]


async def wait_for_backup(client: HAWebSocket, *, name: str, timeout: int = 600) -> dict[str, Any]:
    """Wait until the named backup exists and the manager is idle."""
    deadline = monotonic() + timeout
    last_state: Any = None
    while monotonic() < deadline:
        info, backups = await backup_inventory(client)
        last_state = info.get("state")
        match = next((item for item in backups if item.get("name") == name), None)
        if match is not None and last_state == "idle":
            details = await client.call("backup/details", backup_id=match["backup_id"])
            return cast(dict[str, Any], details["backup"])
        await asyncio.sleep(2)
    raise TimeoutError(f"Backup did not complete; last manager state: {last_state}")


async def prepare() -> None:
    """Create pre-backup state and the smallest HA backup that contains it."""
    session, client = await connect()
    run_id = uuid4().hex[:12].upper()
    backup_name = f"LockLearn P0.7 state restore {run_id}"
    try:
        agents = await client.call("backup/agents/info")
        available_agents = {item["agent_id"] for item in agents.get("agents", [])}
        if LOCAL_BACKUP_AGENT not in available_agents:
            raise RuntimeError("Required local HA backup agent is unavailable")
        before_info, before_backups = await backup_inventory(client)
        safety = safety_backups(before_backups)
        if not safety:
            raise RuntimeError("Safety backup is not visible; refusing to create test backup")
        if before_info.get("state") != "idle":
            raise RuntimeError(f"Backup manager is not idle: {before_info.get('state')}")

        started = await client.call("locklearn/session/start", track_id=f"p0.7-pre-backup-{run_id}")
        pre_state = await client.call(
            "locklearn/session/answer",
            session_id=started["id"],
            expected_version=1,
            question_id=f"p0.7-before-{run_id}",
            answer={"marker": "before-backup"},
        )
        storage_before = await client.call("locklearn/admin/storage/status")
        initiated = await client.call(
            "backup/generate",
            agent_ids=[LOCAL_BACKUP_AGENT],
            include_addons=[],
            include_all_addons=False,
            include_database=False,
            include_folders=[],
            include_homeassistant=True,
            name=backup_name,
        )
        backup = await wait_for_backup(client, name=backup_name)
        storage_after = await client.call("locklearn/admin/storage/status")
        print(
            json.dumps(
                {
                    "phase": "prepared",
                    "run_id": run_id,
                    "tested_at_utc": datetime.now(UTC).isoformat(),
                    "pre_session": pre_state,
                    "storage_before_backup": storage_before,
                    "backup_job_id": initiated.get("backup_job_id"),
                    "backup": backup_summary(backup),
                    "storage_after_backup": storage_after,
                    "safety_backups": safety,
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        await session.close()


async def mutate(pre_session_id: str, backup_id: str) -> None:
    """Create state that must disappear when the test backup is restored."""
    session, client = await connect()
    run_id = uuid4().hex[:12].upper()
    try:
        pre_after = await client.call(
            "locklearn/session/answer",
            session_id=pre_session_id,
            expected_version=2,
            question_id=f"p0.7-after-{run_id}",
            answer={"marker": "after-backup"},
        )
        post_started = await client.call(
            "locklearn/session/start", track_id=f"p0.7-post-backup-only-{run_id}"
        )
        post_after = await client.call(
            "locklearn/session/answer",
            session_id=post_started["id"],
            expected_version=1,
            question_id=f"p0.7-post-only-{run_id}",
            answer={"marker": "must-disappear-after-restore"},
        )
        details = await client.call("backup/details", backup_id=backup_id)
        _, backups = await backup_inventory(client)
        safety = safety_backups(backups)
        if not safety:
            raise RuntimeError("Safety backup disappeared; restore checkpoint is unsafe")
        print(
            json.dumps(
                {
                    "phase": "mutated",
                    "run_id": run_id,
                    "tested_at_utc": datetime.now(UTC).isoformat(),
                    "pre_session_after_backup": pre_after,
                    "post_only_session": post_after,
                    "storage": await client.call("locklearn/admin/storage/status"),
                    "backup": backup_summary(details["backup"]),
                    "safety_backups": safety,
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        await session.close()


async def verify(pre_session_id: str, post_session_id: str, backup_id: str) -> None:
    """Verify restored state, integrity, runtime health and a fresh writer roundtrip."""
    session, client = await connect()
    try:
        bootstrap = await client.call("locklearn/bootstrap")
        pre_restored = await client.call("locklearn/session/get", session_id=pre_session_id)
        try:
            await client.call("locklearn/session/get", session_id=post_session_id)
        except RuntimeError as err:
            post_absent = "locklearn/not_found" in str(err)
        else:
            post_absent = False
        storage_before_write = await client.call("locklearn/admin/storage/status")
        writer_roundtrip = await client.call(
            "locklearn/session/answer",
            session_id=pre_session_id,
            expected_version=pre_restored["version"],
            question_id=f"p0.7-restore-verify-{uuid4().hex[:12].upper()}",
            answer={"marker": "post-restore-writer-check"},
        )
        storage_after_write = await client.call("locklearn/admin/storage/status")
        details = await client.call("backup/details", backup_id=backup_id)
        _, backups = await backup_inventory(client)
        panels = await client.call("get_panels")
        panel = panels.get("locklearn")
        print(
            json.dumps(
                {
                    "phase": "verified",
                    "tested_at_utc": datetime.now(UTC).isoformat(),
                    "bootstrap_protocol": bootstrap.get("frontend_protocol"),
                    "authenticated_user_present": bool(bootstrap.get("authenticated_user_id")),
                    "pre_session_restored": pre_restored,
                    "pre_session_expected_version_restored": pre_restored["version"] == 2,
                    "post_only_session_absent": post_absent,
                    "storage_before_writer_roundtrip": storage_before_write,
                    "writer_roundtrip": writer_roundtrip,
                    "storage_after_writer_roundtrip": storage_after_write,
                    "panel_present": panel is not None,
                    "panel_module_url": (
                        None
                        if panel is None
                        else (panel.get("config") or {}).get("_panel_custom", {}).get("module_url")
                    ),
                    "backup": backup_summary(details["backup"]),
                    "safety_backups": safety_backups(backups),
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        await session.close()


def main() -> None:
    """Run one explicit phase of the destructive-boundary qualification."""
    load_allowed_env(Path(".env"))
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    mutate_parser = subparsers.add_parser("mutate")
    mutate_parser.add_argument("--pre-session-id", required=True)
    mutate_parser.add_argument("--backup-id", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--pre-session-id", required=True)
    verify_parser.add_argument("--post-session-id", required=True)
    verify_parser.add_argument("--backup-id", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        asyncio.run(prepare())
    elif args.command == "mutate":
        asyncio.run(mutate(args.pre_session_id, args.backup_id))
    else:
        asyncio.run(verify(args.pre_session_id, args.post_session_id, args.backup_id))


if __name__ == "__main__":
    main()
