"""P6.10 release packaging, versioning and upgrade readiness contracts."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from custom_components.locklearn.const import (
    CONFIG_ENTRY_VERSION,
    DB_SCHEMA_VERSION,
    INTEGRATION_VERSION,
)
from custom_components.locklearn.storage import SQLiteStorage, StoragePaths

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "custom_components" / "locklearn" / "manifest.json"
HACS_PATH = ROOT / "hacs.json"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_PATH = ROOT / "RELEASE.md"
FRONTEND_PACKAGE_PATH = ROOT / "frontend" / "package.json"
RELEASE_SMOKE_PATH = ROOT / "scripts" / "p6_10_release_smoke.py"

PREVIOUS_SUPPORTED_RELEASE = "0.0.2"
V1_RELEASE_CANDIDATE = "1.0.0-beta.1"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

# Exact state schema shipped by the real v0.0.2 GitHub release.
_V0_0_2_STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    track_id TEXT,
    status TEXT NOT NULL,
    version INTEGER NOT NULL,
    current_position INTEGER NOT NULL,
    started_at_utc TEXT NOT NULL,
    last_activity_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_profile_status_activity
ON sessions(profile_id, status, last_activity_at_utc);

CREATE TABLE IF NOT EXISTS session_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    resulting_version INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    UNIQUE(session_id, resulting_version)
);

CREATE TABLE IF NOT EXISTS progress (
    profile_id TEXT NOT NULL,
    track_id TEXT NOT NULL,
    card_key TEXT NOT NULL,
    state TEXT NOT NULL,
    next_due_at_utc TEXT,
    PRIMARY KEY(profile_id, track_id, card_key)
);

CREATE INDEX IF NOT EXISTS progress_due
ON progress(profile_id, track_id, state, next_due_at_utc);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_user_id TEXT,
    profile_id TEXT,
    payload_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);
"""


def _version_tuple(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(version)
    assert match is not None, version
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def test_v1_candidate_uses_one_authoritative_runtime_version() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["version"] == INTEGRATION_VERSION == V1_RELEASE_CANDIDATE
    assert _version_tuple(INTEGRATION_VERSION) > _version_tuple(PREVIOUS_SUPPORTED_RELEASE)
    assert CONFIG_ENTRY_VERSION == 1

    frontend_package = json.loads(FRONTEND_PACKAGE_PATH.read_text(encoding="utf-8"))
    assert frontend_package["private"] is True
    release_doc = RELEASE_PATH.read_text(encoding="utf-8")
    assert "frontend/package.json" in release_doc
    assert "not the LockLearn product version" in release_doc


def test_hacs_floor_and_tested_patch_are_deliberately_distinct() -> None:
    hacs = json.loads(HACS_PATH.read_text(encoding="utf-8"))
    assert hacs["homeassistant"] == "2025.2.0"

    ci = CI_PATH.read_text(encoding="utf-8")
    assert 'home_assistant: "2025.2.5"' in ci
    assert "homeassistant==2026.9.4" in ci

    release_doc = RELEASE_PATH.read_text(encoding="utf-8")
    assert "2025.2.0" in release_doc
    assert "2025.2.5" in release_doc


def test_release_payload_smoke_is_permanent_ci_gate() -> None:
    assert RELEASE_SMOKE_PATH.is_file()
    ci = CI_PATH.read_text(encoding="utf-8")
    assert "tests/backend/test_p6_10_release_readiness.py" in ci
    assert ci.count("python scripts/p6_10_release_smoke.py") >= 3

    completed = subprocess.run(
        [sys.executable, str(RELEASE_SMOKE_PATH)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "P6.10 release payload smoke: PASS" in completed.stdout


async def test_real_v0_0_2_state_upgrades_to_v1_candidate_without_data_loss(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state" / "state.db"
    state_path.parent.mkdir(parents=True)
    connection = sqlite3.connect(state_path)
    try:
        connection.executescript(_V0_0_2_STATE_SCHEMA)
        connection.execute("INSERT INTO schema_version(version) VALUES (1)")
        connection.execute(
            """INSERT INTO sessions VALUES (
                   'release-session', 'release-profile', NULL, 'active', 1, 0,
                   '2026-09-21T20:00:00+00:00', '2026-09-21T20:00:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO session_answers(
                   session_id, question_id, answer_json, resulting_version, created_at_utc
               ) VALUES (
                   'release-session', 'q1', '{"choice":"known"}', 2,
                   '2026-09-21T20:01:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO progress VALUES (
                   'release-profile', 'release-track', 'release-card', 'review',
                   '2026-09-22T20:00:00+00:00'
               )"""
        )
        connection.execute(
            """INSERT INTO audit_events(
                   event_type, actor_user_id, profile_id, payload_json, created_at_utc
               ) VALUES (
                   'release-probe', 'release-user', 'release-profile', '{}',
                   '2026-09-21T20:02:00+00:00'
               )"""
        )
        connection.commit()
    finally:
        connection.close()

    storage = SQLiteStorage(
        StoragePaths(
            state_path,
            tmp_path / "content" / "current.db",
        )
    )
    await storage.async_open()
    try:
        migrated = sqlite3.connect(state_path)
        try:
            assert migrated.execute("SELECT version FROM schema_version").fetchone() == (
                DB_SCHEMA_VERSION,
            )
            assert migrated.execute(
                "SELECT id, profile_id, type, strategy FROM sessions"
            ).fetchone() == (
                "release-session",
                "release-profile",
                "learn",
                "default",
            )
            assert migrated.execute(
                "SELECT profile_id, track_id, card_key, state FROM progress"
            ).fetchone() == (
                "release-profile",
                "release-track",
                "release-card",
                "review",
            )
            assert migrated.execute("SELECT COUNT(*) FROM session_answers").fetchone() == (1,)
            assert migrated.execute("SELECT COUNT(*) FROM audit_events").fetchone() == (1,)
        finally:
            migrated.close()

        backup = state_path.with_name("state.db.pre-migration-v1.bak")
        assert backup.is_file()
        previous = sqlite3.connect(backup)
        try:
            assert previous.execute("SELECT version FROM schema_version").fetchone() == (1,)
            assert previous.execute("SELECT COUNT(*) FROM sessions").fetchone() == (1,)
            assert previous.execute("SELECT COUNT(*) FROM progress").fetchone() == (1,)
        finally:
            previous.close()
    finally:
        await storage.async_close()
