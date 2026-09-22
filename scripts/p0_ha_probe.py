#!/usr/bin/env python3
"""Read-only HA inventory and opt-in Companion P0 notification probe.

The ``inventory`` command has no external side effects. ``companion`` sends a
clearly labelled test notification to the explicit device-registry id and waits
for real Companion events; it never guesses a target from a service name.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any

import aiohttp


def _load_env(path: Path) -> None:
    """Load only the explicitly allowed Home Assistant probe variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.startswith("LOCKLEARN_HA_"):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


class HAWebSocket:
    def __init__(self, websocket: aiohttp.ClientWebSocketResponse) -> None:
        self.websocket = websocket
        self.message_id = 0

    async def call(self, message_type: str, **data: Any) -> Any:
        self.message_id += 1
        message_id = self.message_id
        await self.websocket.send_json({"id": message_id, "type": message_type, **data})
        while True:
            response = await self.websocket.receive_json()
            if response.get("id") != message_id:
                continue
            if not response.get("success", False):
                raise RuntimeError(response.get("error", {}))
            return response.get("result")


async def _connect() -> tuple[aiohttp.ClientSession, HAWebSocket]:
    url = os.environ["LOCKLEARN_HA_URL"].rstrip("/")
    token = os.environ["LOCKLEARN_HA_ACCESS_TOKEN"]
    verify_tls = os.environ.get("LOCKLEARN_HA_VERIFY_TLS", "true").lower() != "false"
    ssl_context: ssl.SSLContext | bool = ssl.create_default_context() if verify_tls else False
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    )
    try:
        websocket = await session.ws_connect(
            f"{url.replace('http://', 'ws://').replace('https://', 'wss://')}/api/websocket",
            ssl=ssl_context,
        )
    except Exception:
        await session.close()
        raise
    auth_required = await websocket.receive_json()
    if auth_required.get("type") != "auth_required":
        await session.close()
        raise RuntimeError("Unexpected HA WebSocket handshake")
    await websocket.send_json({"type": "auth", "access_token": token})
    auth_result = await websocket.receive_json()
    if auth_result.get("type") != "auth_ok":
        await session.close()
        raise RuntimeError("Home Assistant authentication failed")
    return session, HAWebSocket(websocket)


async def inventory() -> None:
    session, client = await _connect()
    try:
        config = await client.call("get_config")
        devices = await client.call("config/device_registry/list")
        entities = await client.call("config/entity_registry/list")
        notify_by_device: dict[str, list[str]] = {}
        for entity in entities:
            if entity["entity_id"].startswith("notify.") and entity.get("device_id"):
                notify_by_device.setdefault(entity["device_id"], []).append(entity["entity_id"])
        mobile_devices = [
            {
                "device_registry_id": device["id"],
                "name": device.get("name_by_user") or device.get("name"),
                "manufacturer": device.get("manufacturer"),
                "model": device.get("model"),
                "notify_entities": sorted(notify_by_device.get(device["id"], [])),
            }
            for device in devices
            if any(identifier[0] == "mobile_app" for identifier in device.get("identifiers", []))
        ]
        print(json.dumps({"ha_version": config["version"], "devices": mobile_devices}, indent=2))
    finally:
        await session.close()


@dataclass(slots=True)
class CompanionEvidence:
    device_registry_id: str
    platform: str
    tested_at_utc: str
    action_event_received: bool = False
    action_context_user_id_present: bool = False
    replacement_latency_ms: int | None = None
    cleared_signal: bool = False


async def companion(device_id: str, platform: str, timeout: int) -> None:
    session, client = await _connect()
    evidence = CompanionEvidence(device_id, platform, datetime.now(UTC).isoformat())
    try:
        entities = await client.call("config/entity_registry/list")
        notify_entities = sorted(
            entity["entity_id"]
            for entity in entities
            if entity.get("device_id") == device_id
            and entity["entity_id"].startswith("notify.")
            and entity.get("disabled_by") is None
        )
        if not notify_entities:
            raise RuntimeError("Explicit device has no enabled notify entity")
        notify_entity = notify_entities[0]
        tag = f"locklearn-p0-{int(monotonic() * 1000)}"
        await client.call("subscribe_events", event_type="mobile_app_notification_action")
        await client.call("subscribe_events", event_type="mobile_app_notification_cleared")
        await client.call(
            "call_service",
            domain="notify",
            service="send_message",
            target={"entity_id": notify_entity},
            service_data={
                "title": "LockLearn P0 capability test",
                "message": "Tap Reveal to measure the real replacement path.",
                "data": {
                    "tag": tag,
                    "ttl": timeout,
                    "actions": [
                        {"action": "LOCKLEARN_P0_REVEAL", "title": "Reveal"},
                        {"action": "LOCKLEARN_P0_UNKNOWN", "title": "I don't know"},
                    ],
                },
            },
        )
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            response = await asyncio.wait_for(
                client.websocket.receive_json(), timeout=max(0.1, deadline - monotonic())
            )
            event = response.get("event", {}).get("event", {})
            event_type = event.get("event_type")
            event_data = event.get("data", {})
            if event_type == "mobile_app_notification_cleared":
                evidence.cleared_signal = True
            if event_type != "mobile_app_notification_action":
                continue
            if event_data.get("action") not in {
                "LOCKLEARN_P0_REVEAL",
                "LOCKLEARN_P0_UNKNOWN",
            }:
                continue
            evidence.action_event_received = True
            evidence.action_context_user_id_present = (
                event.get("context", {}).get("user_id") is not None
            )
            replacement_started = monotonic()
            await client.call(
                "call_service",
                domain="notify",
                service="send_message",
                target={"entity_id": notify_entity},
                service_data={
                    "title": "LockLearn P0 replacement",
                    "message": "Replacement received. You can dismiss this notification.",
                    "data": {"tag": tag, "alert_once": True},
                },
            )
            evidence.replacement_latency_ms = round((monotonic() - replacement_started) * 1000)
            break
        print(json.dumps(asdict(evidence), indent=2))
    finally:
        await session.close()


def main() -> None:
    _load_env(Path(".env"))
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inventory")
    companion_parser = subparsers.add_parser("companion")
    companion_parser.add_argument("--device-id", required=True)
    companion_parser.add_argument("--platform", required=True, choices=("android", "ios"))
    companion_parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.command == "inventory":
        asyncio.run(inventory())
    else:
        asyncio.run(companion(args.device_id, args.platform, args.timeout))


if __name__ == "__main__":
    main()
