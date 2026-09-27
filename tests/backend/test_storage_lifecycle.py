"""P6.2 storage lifecycle, recovery, and uninstall policy tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from custom_components.locklearn.const import DB_SCHEMA_VERSION
from custom_components.locklearn.storage import SQLiteStorage, StateIntegrityError, StoragePaths
from custom_components.locklearn.storage import database as storage_database
from custom_components.locklearn.storage.database import validate_state_database_file
from custom_components.locklearn.storage.lifecycle import (
    StorageLifecycleManager,
    UninstallDataPolicy,
)


async def test_ha_backup_publishes_valid_coherent_recovery_snapshot(tmp_path: Path) -> None:
    """The HA hook snapshots committed state while holding the user-write gate."""
    paths = StoragePaths(
        tmp_path / "state" / "state.db",
        tmp_path / "content" / "current.db",
    )
    storage = SQLiteStorage(paths)
    await storage.async_open()
    try:
        await storage.async_create_session("backup-session", "profile", None)
        await storage.async_prepare_ha_backup()
        try:
            assert paths.ha_backup_snapshot.is_file()
            assert validate_state_database_file(paths.ha_backup_snapshot) == DB_SCHEMA_VERSION
            snapshot = sqlite3.connect(paths.ha_backup_snapshot)
            try:
                assert snapshot.execute(
                    "SELECT id FROM sessions WHERE id = 'backup-session'"
                ).fetchone() == ("backup-session",)
            finally:
                snapshot.close()
        finally:
            await storage.async_finish_ha_backup()
    finally:
        await storage.async_close()


async def test_corrupt_existing_state_is_rejected_without_writer_mutation(
    tmp_path: Path,
) -> None:
    """Integrity failure is detected read-only before LockLearn opens its writer."""
    paths = StoragePaths(
        tmp_path / "state" / "state.db",
        tmp_path / "content" / "current.db",
    )
    paths.state_db.parent.mkdir(parents=True)
    original = b"not-a-sqlite-database"
    paths.state_db.write_bytes(original)

    storage = SQLiteStorage(paths)
    with pytest.raises(StateIntegrityError):
        await storage.async_open()

    assert paths.state_db.read_bytes() == original
    assert storage.writer_thread_id is None


async def test_recovery_snapshot_restore_preserves_failed_live_copy(
    tmp_path: Path,
) -> None:
    """Recovery is explicit, validated, and quarantines the replaced live files."""
    paths = StoragePaths(
        tmp_path / "state" / "state.db",
        tmp_path / "content" / "current.db",
    )
    storage = SQLiteStorage(paths)
    await storage.async_open()
    await storage.async_create_session("recover-me", "profile", None)
    await storage.async_prepare_ha_backup()
    await storage.async_finish_ha_backup()
    await storage.async_close()

    paths.state_db.write_bytes(b"corrupted-live-copy")
    manager = StorageLifecycleManager(paths)
    snapshots = await manager.async_valid_recovery_snapshots()
    assert [snapshot.name for snapshot in snapshots] == [paths.ha_backup_snapshot.name]

    restored = await manager.async_restore_snapshot(paths.ha_backup_snapshot.name)
    assert restored.schema_version == DB_SCHEMA_VERSION
    assert validate_state_database_file(paths.state_db) == DB_SCHEMA_VERSION

    connection = sqlite3.connect(paths.state_db)
    try:
        assert connection.execute(
            "SELECT id FROM sessions WHERE id = 'recover-me'"
        ).fetchone() == ("recover-me",)
    finally:
        connection.close()

    quarantines = list(paths.state_snapshots_dir.glob("pre-recovery-*"))
    assert len(quarantines) == 1
    assert (quarantines[0] / "state.db").read_bytes() == b"corrupted-live-copy"


@pytest.mark.parametrize(
    ("policy", "state_kept", "content_kept"),
    (
        (UninstallDataPolicy.KEEP_USER_DATA, True, True),
        (UninstallDataPolicy.DELETE_USER_STATE, False, True),
        (UninstallDataPolicy.DELETE_CONTENT_CACHE, True, False),
        (UninstallDataPolicy.DELETE_EVERYTHING, False, False),
    ),
)
async def test_uninstall_policy_deletes_only_explicitly_selected_roots(
    tmp_path: Path,
    policy: UninstallDataPolicy,
    state_kept: bool,
    content_kept: bool,
) -> None:
    """No user state or reconstructible cache is purged implicitly."""
    paths = StoragePaths(
        tmp_path / "state" / "state.db",
        tmp_path / "content" / "current.db",
    )
    paths.state_db.parent.mkdir(parents=True)
    paths.state_db.write_bytes(b"state")
    paths.content_db.parent.mkdir(parents=True)
    paths.content_db.write_bytes(b"content")

    manager = StorageLifecycleManager(paths)
    await manager.async_apply_uninstall_policy(policy)

    assert paths.state_root.exists() is state_kept
    assert paths.content_root.exists() is content_kept


async def test_storage_usage_surfaces_state_cache_assets_and_backup_policy(
    tmp_path: Path,
) -> None:
    """The lifecycle UI can report byte budgets without exposing user rows."""
    paths = StoragePaths(
        tmp_path / "state" / "state.db",
        tmp_path / "content" / "current.db",
    )
    paths.state_db.parent.mkdir(parents=True)
    paths.state_db.write_bytes(b"1234567890")
    Path(f"{paths.state_db}-wal").write_bytes(b"wal")
    paths.content_db.parent.mkdir(parents=True)
    paths.content_db.write_bytes(b"content")
    assets = paths.content_root / "assets"
    assets.mkdir()
    (assets / "asset.bin").write_bytes(b"asset")
    paths.state_snapshots_dir.mkdir()
    paths.ha_backup_snapshot.write_bytes(b"snap")

    usage = await StorageLifecycleManager(paths).async_usage()

    assert usage.state_bytes >= 13
    assert usage.content_cache_bytes >= 12
    assert usage.asset_bytes == 5
    assert usage.recovery_snapshot_bytes >= 4
    assert usage.backup_policy == (
        "state_coherent_content_included_at_ha_2025_2_floor"
    )


async def test_failed_backup_prepare_releases_write_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed snapshot cannot leave LockLearn permanently write-locked."""
    paths = StoragePaths(
        tmp_path / "state" / "state.db",
        tmp_path / "content" / "current.db",
    )
    storage = SQLiteStorage(paths)
    await storage.async_open()
    original = storage_database._create_atomic_state_snapshot

    def fail_snapshot(connection: sqlite3.Connection, destination: Path) -> Path:
        del connection, destination
        raise RuntimeError("injected snapshot failure")

    monkeypatch.setattr(
        storage_database,
        "_create_atomic_state_snapshot",
        fail_snapshot,
    )
    try:
        with pytest.raises(RuntimeError, match="injected snapshot failure"):
            await storage.async_prepare_ha_backup()
        assert (await storage.async_diagnostic_status())["backup_active"] is False

        monkeypatch.setattr(
            storage_database,
            "_create_atomic_state_snapshot",
            original,
        )
        session = await storage.async_create_session("after-failure", "profile", None)
        assert session["id"] == "after-failure"
    finally:
        await storage.async_close()
