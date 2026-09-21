#!/usr/bin/env python3
"""Reproducible, secret-safe P0.7 probes for a real Home Assistant instance."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
from collections import deque
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import aiohttp
from homeassistant.util import slugify

ALLOWED_ENV_PREFIX = "LOCKLEARN_HA_"
EVENT_ACTION = "mobile_app_notification_action"
EVENT_CLEARED = "mobile_app_notification_cleared"
EVENT_RECEIVED = "mobile_app_notification_received"


def load_allowed_env(path: Path) -> None:
    """Load only LOCKLEARN_HA_* values without logging their contents."""
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
        if not key.startswith(ALLOWED_ENV_PREFIX):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


class HAWebSocket:
    """Small HA WebSocket client which preserves interleaved event messages."""

    def __init__(self, websocket: aiohttp.ClientWebSocketResponse) -> None:
        self.websocket = websocket
        self.message_id = 0
        self.pending: deque[dict[str, Any]] = deque()

    async def call(self, message_type: str, **data: Any) -> Any:
        """Send a command and return its result without losing events."""
        self.message_id += 1
        message_id = self.message_id
        await self.websocket.send_json({"id": message_id, "type": message_type, **data})
        while True:
            response = await self.websocket.receive_json()
            if response.get("id") != message_id:
                self.pending.append(response)
                continue
            if not response.get("success", False):
                error = response.get("error", {})
                raise RuntimeError(
                    f"HA command {message_type!r} failed: "
                    f"{error.get('code', 'unknown')}: {error.get('message', 'no message')}"
                )
            return response.get("result")

    async def next_message(self, timeout: float) -> dict[str, Any]:
        """Return the next buffered/live message within timeout seconds."""
        if self.pending:
            return self.pending.popleft()
        return await asyncio.wait_for(self.websocket.receive_json(), timeout=timeout)


async def connect() -> tuple[aiohttp.ClientSession, HAWebSocket]:
    """Connect with a threaded resolver so local mDNS names work."""
    base_url = os.environ["LOCKLEARN_HA_URL"].rstrip("/")
    token = os.environ["LOCKLEARN_HA_ACCESS_TOKEN"]
    verify_tls = os.environ.get("LOCKLEARN_HA_VERIFY_TLS", "true").lower() != "false"
    ssl_context: ssl.SSLContext | bool = ssl.create_default_context() if verify_tls else False
    parts = urlsplit(base_url)
    websocket_url = urlunsplit(
        (
            "wss" if parts.scheme == "https" else "ws",
            parts.netloc,
            "/api/websocket",
            "",
            "",
        )
    )
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    )
    try:
        websocket = await session.ws_connect(websocket_url, ssl=ssl_context)
        await websocket.receive_json()
        await websocket.send_json({"type": "auth", "access_token": token})
        auth_result = await websocket.receive_json()
        if auth_result.get("type") != "auth_ok":
            raise RuntimeError("Home Assistant authentication failed")
    except Exception:
        await session.close()
        raise
    return session, HAWebSocket(websocket)


async def resolve_target(
    client: HAWebSocket, device_id: str
) -> tuple[str, set[str], dict[str, Any]]:
    """Resolve a stable registry ID to a data-capable mobile_app action."""
    devices = await client.call("config/device_registry/list")
    entities = await client.call("config/entity_registry/list")
    services = await client.call("get_services")
    device = next((item for item in devices if item.get("id") == device_id), None)
    if device is None:
        raise RuntimeError("Explicit device-registry ID was not found")
    notify_entities = sorted(
        entity["entity_id"]
        for entity in entities
        if entity.get("device_id") == device_id
        and entity.get("entity_id", "").startswith("notify.")
        and entity.get("disabled_by") is None
    )
    if not notify_entities:
        raise RuntimeError("Explicit device has no enabled notify entity")
    notify_services = (services.get("notify") or {}).keys()
    route_candidates = {
        slugify(f"mobile_app_{candidate}")
        for candidate in (
            device.get("name"),
            device.get("name_by_user"),
            device.get("model"),
        )
        if candidate
    }
    matched_routes = sorted(route_candidates.intersection(notify_services))
    if len(matched_routes) != 1:
        raise RuntimeError(
            "Explicit device does not resolve to exactly one data-capable mobile_app action"
        )
    app_ids = {
        str(identifier[1])
        for identifier in device.get("identifiers", [])
        if identifier[0] == "mobile_app"
    }
    metadata = {
        "device_registry_id": device_id,
        "name": device.get("name_by_user") or device.get("name"),
        "manufacturer": device.get("manufacturer"),
        "model": device.get("model"),
        "sw_version": device.get("sw_version"),
        "hw_version": device.get("hw_version"),
        "notify_entity": notify_entities[0],
        "notify_action": f"notify.{matched_routes[0]}",
    }
    return matched_routes[0], app_ids, metadata


async def subscribe_companion_events(client: HAWebSocket) -> None:
    """Subscribe to every Companion event used by the qualification."""
    for event_type in (EVENT_ACTION, EVENT_CLEARED, EVENT_RECEIVED):
        await client.call("subscribe_events", event_type=event_type)


async def send_notification(
    client: HAWebSocket,
    notify_service: str,
    *,
    title: str,
    message: str,
    data: dict[str, Any],
) -> None:
    """Send through the current data-capable mobile_app action."""
    await client.call(
        "call_service",
        domain="notify",
        service=notify_service,
        service_data={"title": title, "message": message, "data": data},
    )


def event_payload(message: dict[str, Any]) -> tuple[str | None, dict[str, Any], dict[str, Any]]:
    """Extract event type, data and context from an HA subscription message."""
    envelope = message.get("event", {})
    event = envelope.get("event", envelope)
    return event.get("event_type"), event.get("data", {}), event.get("context", {})


def probe_event_summary(
    message: dict[str, Any],
    *,
    tag: str,
    action_id: str | None,
    app_ids: set[str],
    expected_reply: str | None = None,
) -> dict[str, Any]:
    """Summarize a probe event without retaining notification contents."""
    event_type, data, context = event_payload(message)
    event_device_id = data.get("device_id")
    reply_text = data.get("reply_text")
    return {
        "event_type": event_type,
        "data_keys": sorted(data),
        "tag_present": data.get("tag") is not None,
        "tag_matches": data.get("tag") == tag,
        "action_present": data.get("action") is not None,
        "action_matches": action_id is None or data.get("action") == action_id,
        "device_id_present": event_device_id is not None,
        "device_id_matches_registry_identifier": str(event_device_id) in app_ids,
        "context_user_id_present": context.get("user_id") is not None,
        "time_fired": (
            message.get("event", {}).get("event", message.get("event", {})).get("time_fired")
        ),
        "reply_text_present": bool(reply_text),
        "reply_text_matches_expected": expected_reply is None or reply_text == expected_reply,
    }


async def action_probe(device_id: str, scenario: str, timeout: int) -> None:
    """Send one unique actionable notification and capture its real event."""
    session, client = await connect()
    run_id = uuid4().hex[:12].upper()
    prefix = f"LOCKLEARN_P07_{scenario.upper()}_{run_id}"
    tag = prefix.lower()
    expected_action = f"{prefix}_ACTION"
    try:
        notify_service, app_ids, metadata = await resolve_target(client, device_id)
        await subscribe_companion_events(client)
        if scenario == "clear":
            actions = [{"action": f"{prefix}_KEEP", "title": "Keep"}]
            expected_event = EVENT_CLEARED
            expected_action_for_event = None
            instruction = "swipe"
        elif scenario == "text":
            actions = [
                {
                    "action": expected_action,
                    "title": "Type P07",
                    "behavior": "textInput",
                }
            ]
            expected_event = EVENT_ACTION
            expected_action_for_event = expected_action
            instruction = "text"
        else:
            actions = [
                {
                    "action": expected_action,
                    "title": "Reveal" if scenario == "reveal" else "I don't know",
                },
                {"action": f"{prefix}_OTHER", "title": "Other"},
            ]
            expected_event = EVENT_ACTION
            expected_action_for_event = expected_action
            instruction = "tap"
        await send_notification(
            client,
            notify_service,
            title=f"LockLearn P0.7 {scenario}",
            message=f"Qualification {run_id}; no personal learning content.",
            data={
                "tag": tag,
                "channel": "LockLearn P0 Learning",
                "confirmation": True,
                "timeout": timeout,
                "actions": actions,
            },
        )
        print(
            json.dumps(
                {
                    "ready": True,
                    "scenario": scenario,
                    "run_id": run_id,
                    "instruction": instruction,
                    "target": metadata,
                    "timeout_seconds": timeout,
                    "tested_at_utc": datetime.now(UTC).isoformat(),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        received: dict[str, Any] | None = None
        result: dict[str, Any] | None = None
        observed_probe_events: list[dict[str, Any]] = []
        deadline = monotonic() + timeout
        while monotonic() < deadline and result is None:
            try:
                message = await client.next_message(max(0.1, deadline - monotonic()))
            except TimeoutError:
                break
            event_type, data, _ = event_payload(message)
            action = str(data.get("action", ""))
            event_tag = str(data.get("tag", ""))
            is_probe_event = action.startswith(prefix) or event_tag == tag
            if not is_probe_event:
                continue
            summary = probe_event_summary(
                message,
                tag=tag,
                action_id=expected_action_for_event,
                app_ids=app_ids,
                expected_reply="P07" if scenario == "text" else None,
            )
            observed_probe_events.append(summary)
            if event_type == EVENT_RECEIVED and data.get("tag") == tag:
                received = summary
            if event_type != expected_event:
                continue
            if expected_action_for_event is not None:
                if data.get("action") == expected_action_for_event:
                    result = summary
            elif data.get("tag") == tag:
                result = summary
        if result is None:
            print(
                json.dumps(
                    {
                        "complete": False,
                        "scenario": scenario,
                        "run_id": run_id,
                        "reason": "timeout",
                        "observed_probe_events": observed_probe_events,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                flush=True,
            )
            return
        replacement_latency_ms: int | None = None
        if scenario == "reveal":
            started = monotonic()
            await send_notification(
                client,
                notify_service,
                title="LockLearn P0.7 replacement",
                message=f"Replacement {run_id}; dismiss when inspected.",
                data={
                    "tag": tag,
                    "channel": "LockLearn P0 Learning",
                    "alert_once": True,
                    "actions": [
                        {"action": f"{prefix}_KNEW", "title": "I knew"},
                        {"action": f"{prefix}_REVIEW", "title": "Review"},
                    ],
                },
            )
            replacement_latency_ms = round((monotonic() - started) * 1000)
        duplicate_count = 0
        grace_deadline = monotonic() + 2
        while monotonic() < grace_deadline:
            with suppress(TimeoutError):
                message = await client.next_message(grace_deadline - monotonic())
                event_type, data, _ = event_payload(message)
                action = str(data.get("action", ""))
                event_tag = str(data.get("tag", ""))
                if action.startswith(prefix) or event_tag == tag:
                    summary = probe_event_summary(
                        message,
                        tag=tag,
                        action_id=expected_action_for_event,
                        app_ids=app_ids,
                        expected_reply="P07" if scenario == "text" else None,
                    )
                    observed_probe_events.append(summary)
                    if event_type == EVENT_RECEIVED and data.get("tag") == tag:
                        received = summary
                    if (
                        event_type == expected_event
                        and data.get("tag") == tag
                        and (
                            expected_action_for_event is None
                            or data.get("action") == expected_action_for_event
                        )
                    ):
                        duplicate_count += 1
                continue
            break
        print(
            json.dumps(
                {
                    "complete": True,
                    "scenario": scenario,
                    "run_id": run_id,
                    "tested_at_utc": datetime.now(UTC).isoformat(),
                    "received_confirmation": received,
                    "interaction": result,
                    "observed_probe_events": observed_probe_events,
                    "additional_matching_events_during_grace": duplicate_count,
                    "replacement_latency_ms": replacement_latency_ms,
                },
                indent=2,
                sort_keys=True,
            ),
            flush=True,
        )
    finally:
        await session.close()


async def visual_probe(device_id: str, scenario: str) -> None:
    """Send bounded, non-personal notifications for a human visual check."""
    session, client = await connect()
    run_id = uuid4().hex[:12].upper()
    tag_prefix = f"locklearn_p07_visual_{scenario}_{run_id.lower()}"
    try:
        notify_service, app_ids, metadata = await resolve_target(client, device_id)
        await client.call("subscribe_events", event_type=EVENT_RECEIVED)
        notifications: list[tuple[str, str, dict[str, Any]]]
        if scenario == "actions":
            notifications = [
                (
                    "LockLearn P0.7 four actions",
                    f"Visual action-count probe {run_id}.",
                    {
                        "tag": tag_prefix,
                        "channel": "LockLearn P0 Learning",
                        "confirmation": True,
                        "timeout": 300,
                        "actions": [
                            {"action": f"{run_id}_ONE", "title": "One"},
                            {"action": f"{run_id}_TWO", "title": "Two"},
                            {"action": f"{run_id}_THREE", "title": "Three"},
                            {"action": f"{run_id}_FOUR", "title": "Four"},
                        ],
                    },
                )
            ]
        elif scenario == "visibility":
            notifications = [
                (
                    f"LockLearn P0.7 {visibility}",
                    f"Non-personal {visibility} probe {run_id}.",
                    {
                        "tag": f"{tag_prefix}_{visibility}",
                        "channel": "LockLearn P0 Learning",
                        "confirmation": True,
                        "timeout": 300,
                        "visibility": visibility,
                    },
                )
                for visibility in ("public", "private", "secret")
            ]
        else:
            notifications = [
                (
                    "LockLearn P0.7 expiration",
                    f"This probe {run_id} must disappear after 10 seconds.",
                    {
                        "tag": tag_prefix,
                        "channel": "LockLearn P0 Learning",
                        "confirmation": True,
                        "timeout": 10,
                    },
                )
            ]
        for title, message, data in notifications:
            await send_notification(
                client,
                notify_service,
                title=title,
                message=message,
                data=data,
            )

        expected_tags = {str(item[2]["tag"]) for item in notifications}
        received_tags: set[str] = set()
        deadline = monotonic() + 5
        while received_tags != expected_tags and monotonic() < deadline:
            with suppress(TimeoutError):
                event = await client.next_message(deadline - monotonic())
                event_type, data, _ = event_payload(event)
                if event_type == EVENT_RECEIVED and data.get("tag") in expected_tags:
                    received_tags.add(str(data["tag"]))
                continue
            break
        print(
            json.dumps(
                {
                    "send_complete": True,
                    "delivery_confirmation_complete": received_tags == expected_tags,
                    "scenario": scenario,
                    "run_id": run_id,
                    "target": metadata,
                    "notifications_sent": len(notifications),
                    "received_confirmations": len(received_tags),
                    "device_identifiers_present": bool(app_ids),
                    "tested_at_utc": datetime.now(UTC).isoformat(),
                },
                indent=2,
                sort_keys=True,
            ),
            flush=True,
        )
    finally:
        await session.close()


def main() -> None:
    """Run a bounded real-instance probe."""
    load_allowed_env(Path(".env"))
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    action = subparsers.add_parser("action")
    action.add_argument("--device-id", required=True)
    action.add_argument("--scenario", choices=("reveal", "idk", "clear", "text"), required=True)
    action.add_argument("--timeout", type=int, default=180)
    visual = subparsers.add_parser("visual")
    visual.add_argument("--device-id", required=True)
    visual.add_argument("--scenario", choices=("actions", "visibility", "timeout"), required=True)
    args = parser.parse_args()
    if args.command == "action":
        asyncio.run(action_probe(args.device_id, args.scenario, args.timeout))
    else:
        asyncio.run(visual_probe(args.device_id, args.scenario))


if __name__ == "__main__":
    main()
