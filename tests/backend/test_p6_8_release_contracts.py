"""P6.8 permanent release-contract gates."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WEBSOCKET_PATH = ROOT / "custom_components" / "locklearn" / "api" / "websocket.py"
CORE_ROOT = ROOT / "custom_components" / "locklearn" / "core"

AUTHENTICATED_COMMANDS = frozenset(
    {
        "locklearn/bootstrap",
        "locklearn/profiles/list",
        "locklearn/profiles/create",
        "locklearn/packs/list",
        "locklearn/datasets/list",
        "locklearn/datasets/attributions",
    }
)
CAPABILITY_COMMANDS = frozenset(
    {
        "locklearn/profiles/import_dry_run",
        "locklearn/profiles/import_apply",
    }
)
PROFILE_GUARDED_COMMANDS = frozenset(
    {
        "locklearn/profiles/update",
        "locklearn/profiles/delete",
        "locklearn/profiles/export",
        "locklearn/profiles/share",
        "locklearn/profiles/members",
        "locklearn/profiles/share_targets",
        "locklearn/tracks/list",
        "locklearn/targets/list",
        "locklearn/tracks/create",
        "locklearn/content/report",
        "locklearn/content/report_question",
        "locklearn/progress/set_user_state",
        "locklearn/calibration/sample",
        "locklearn/stats/get",
        "locklearn/dashboard/get",
        "locklearn/difficulties/list",
        "locklearn/confusions/list",
        "locklearn/annotations/list",
        "locklearn/annotations/create",
        "locklearn/annotations/update",
        "locklearn/annotations/delete",
        "locklearn/leeches/reactivate",
        "locklearn/progress/undo_last",
        "locklearn/notifications/unrecorded_responses",
        "locklearn/scheduler/preview",
        "locklearn/session/start",
    }
)
TRACK_GUARDED_COMMANDS = frozenset(
    {
        "locklearn/tracks/update",
        "locklearn/tracks/delete",
        "locklearn/tracks/integrate_pack_update",
        "locklearn/tracks/preview_pack_update",
        "locklearn/tracks/plan_preview",
        "locklearn/tracks/plan_set",
    }
)
SESSION_GUARDED_COMMANDS = frozenset(
    {
        "locklearn/session/get",
        "locklearn/quiz/evaluate",
        "locklearn/quiz/answer",
        "locklearn/session/answer",
        "locklearn/session/pause",
        "locklearn/session/complete",
        "locklearn/session/undo",
        "locklearn/session/subscribe",
    }
)
ADMIN_GUARDED_COMMANDS = frozenset(
    {
        "locklearn/datasets/refresh",
        "locklearn/datasets/install",
        "locklearn/admin/rebuild_progress",
        "locklearn/admin/rebuild_stats",
        "locklearn/admin/recompute_progress",
        "locklearn/admin/storage/status",
    }
)
OPERATION_GUARDED_COMMANDS = frozenset(
    {
        "locklearn/operations/subscribe",
        "locklearn/operations/cancel",
    }
)

COMMAND_GROUPS = (
    AUTHENTICATED_COMMANDS,
    CAPABILITY_COMMANDS,
    PROFILE_GUARDED_COMMANDS,
    TRACK_GUARDED_COMMANDS,
    SESSION_GUARDED_COMMANDS,
    ADMIN_GUARDED_COMMANDS,
    OPERATION_GUARDED_COMMANDS,
)


def _command_blocks(source: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    starts = [match.start() for match in re.finditer(r"(?=@websocket_api\.websocket_command)", source)]
    starts.append(len(source))
    for index, start in enumerate(starts[:-1]):
        block = source[start : starts[index + 1]]
        command = re.search(r'vol\.Required\("type"\):\s*"([^"]+)"', block)
        if command is not None:
            blocks[command.group(1)] = block
    return blocks


def test_every_websocket_command_has_one_explicit_access_classification() -> None:
    source = WEBSOCKET_PATH.read_text(encoding="utf-8")
    blocks = _command_blocks(source)
    classified = set().union(*COMMAND_GROUPS)

    assert len(classified) == sum(len(group) for group in COMMAND_GROUPS)
    assert classified == set(blocks)


def test_every_protected_websocket_command_has_the_expected_guard() -> None:
    blocks = _command_blocks(WEBSOCKET_PATH.read_text(encoding="utf-8"))

    for command in PROFILE_GUARDED_COMMANDS:
        assert "_require_profile_permission(" in blocks[command], command
    for command in TRACK_GUARDED_COMMANDS:
        assert "_require_track_permission(" in blocks[command], command
    for command in SESSION_GUARDED_COMMANDS:
        assert "_authorized_session(" in blocks[command], command
    for command in ADMIN_GUARDED_COMMANDS:
        block = blocks[command]
        assert "_require_admin(" in block or "@websocket_api.require_admin" in block, command
    for command in OPERATION_GUARDED_COMMANDS:
        assert "_can_access_operation(" in blocks[command], command
    for command in CAPABILITY_COMMANDS:
        block = blocks[command]
        assert "connection.user.id" in block and "owner_user_id" in block, command


def test_critical_domain_logic_has_no_direct_wall_clock_dependency() -> None:
    forbidden = (
        re.compile(r"\bdatetime\.now\s*\("),
        re.compile(r"\bdatetime\.utcnow\s*\("),
        re.compile(r"\bdate\.today\s*\("),
        re.compile(r"\bdt_util\.now\s*\("),
        re.compile(r"\bdt_util\.utcnow\s*\("),
    )
    violations: list[str] = []
    for path in sorted(CORE_ROOT.rglob("*.py")):
        if path.name == "clock.py":
            continue
        source = path.read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in forbidden):
            violations.append(str(path.relative_to(ROOT)))

    assert violations == []
