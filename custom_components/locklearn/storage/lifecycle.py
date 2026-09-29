"""Storage lifecycle, recovery, and uninstall policy helpers."""

from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
import sqlite3
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .database import (
    StoragePaths,
    _read_only_uri,
    _unlink_sqlite_files,
    validate_state_database_file,
)


class StorageLifecycleError(RuntimeError):
    """Raised when a storage lifecycle operation cannot complete safely."""


class UninstallDataPolicy(StrEnum):
    """Explicit data-retention choices applied when the Config Entry is removed."""

    KEEP_USER_DATA = "keep_user_data"
    DELETE_USER_STATE = "delete_user_state"
    DELETE_CONTENT_CACHE = "delete_content_cache"
    DELETE_EVERYTHING = "delete_everything"


@dataclass(frozen=True, slots=True)
class StorageUsage:
    """Non-sensitive byte counts and the effective HA backup policy."""

    state_bytes: int
    content_cache_bytes: int
    asset_bytes: int
    recovery_snapshot_bytes: int
    backup_policy: str


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    """One validated coherent state snapshot available for explicit recovery."""

    name: str
    path: Path
    schema_version: int
    size_bytes: int


def _path_size(path: Path) -> int:
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    if not path.is_dir():
        return 0
    total = 0
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        try:
            total += candidate.stat().st_size
        except OSError:
            continue
    return total


def _sqlite_live_size(path: Path) -> int:
    return sum(
        _path_size(candidate) for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm"))
    )


def _safe_remove_tree(path: Path) -> None:
    """Remove one known storage root without following an arbitrary symlink tree."""
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    shutil.rmtree(path)


class StorageLifecycleManager:
    """Inspect and mutate LockLearn storage only through explicit lifecycle choices."""

    BACKUP_POLICY = "state_coherent_content_included_at_ha_2025_2_floor"
    MAX_RECOVERY_QUARANTINES = 2

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    async def async_usage(self) -> StorageUsage:
        """Return non-sensitive storage byte counts off the HA event loop."""
        return await asyncio.to_thread(self._usage_sync)

    def _usage_sync(self) -> StorageUsage:
        migration_snapshots = sum(
            _path_size(path)
            for path in self.paths.state_root.glob(
                f"{self.paths.state_db.name}.pre-migration-v*.bak"
            )
        )
        recovery_bytes = _path_size(self.paths.state_snapshots_dir) + migration_snapshots
        return StorageUsage(
            state_bytes=_sqlite_live_size(self.paths.state_db),
            content_cache_bytes=_path_size(self.paths.content_root),
            asset_bytes=_path_size(self.paths.content_root / "assets"),
            recovery_snapshot_bytes=recovery_bytes,
            backup_policy=self.BACKUP_POLICY,
        )

    def _candidate_snapshot_paths(self) -> tuple[Path, ...]:
        candidates = list(
            self.paths.state_root.glob(f"{self.paths.state_db.name}.pre-migration-v*.bak")
        )
        if self.paths.ha_backup_snapshot.is_file():
            candidates.append(self.paths.ha_backup_snapshot)
        return tuple(sorted(candidates, key=lambda path: path.name))

    async def async_backup_cache_anomaly_bytes(self) -> int:
        """Return reconstructible cache bytes found unexpectedly under state storage."""
        return await asyncio.to_thread(self._backup_cache_anomaly_bytes_sync)

    def _backup_cache_anomaly_bytes_sync(self) -> int:
        candidates: set[Path] = set()
        try:
            self.paths.content_root.relative_to(self.paths.state_root)
        except ValueError:
            pass
        else:
            candidates.add(self.paths.content_root)

        for name in ("content.db", "packages", "assets", "content-cache", "cache"):
            candidate = self.paths.state_root / name
            if candidate == self.paths.state_db:
                continue
            candidates.add(candidate)

        return sum(_path_size(path) for path in candidates)

    async def async_valid_recovery_snapshots(self) -> tuple[RecoverySnapshot, ...]:
        """Return only snapshots that pass read-only SQLite validation."""
        return await asyncio.to_thread(self._valid_recovery_snapshots_sync)

    def _valid_recovery_snapshots_sync(self) -> tuple[RecoverySnapshot, ...]:
        valid: list[RecoverySnapshot] = []
        for path in self._candidate_snapshot_paths():
            try:
                schema_version = validate_state_database_file(path)
                size_bytes = path.stat().st_size
            except (OSError, RuntimeError, sqlite3.DatabaseError):
                continue
            valid.append(
                RecoverySnapshot(
                    name=path.name,
                    path=path,
                    schema_version=schema_version,
                    size_bytes=size_bytes,
                )
            )
        return tuple(valid)

    async def async_restore_snapshot(self, snapshot_name: str) -> RecoverySnapshot:
        """Explicitly restore one validated snapshot while preserving the current copy."""
        return await asyncio.to_thread(self._restore_snapshot_sync, snapshot_name)

    def _restore_snapshot_sync(self, snapshot_name: str) -> RecoverySnapshot:
        matches = [
            snapshot
            for snapshot in self._valid_recovery_snapshots_sync()
            if snapshot.name == snapshot_name
        ]
        if len(matches) != 1:
            raise StorageLifecycleError(
                f"Recovery snapshot is unavailable or ambiguous: {snapshot_name}"
            )
        snapshot = matches[0]

        self.paths.state_root.mkdir(parents=True, exist_ok=True)
        candidate = self.paths.state_root / (
            f".{self.paths.state_db.name}.restore-{uuid.uuid4().hex}.tmp"
        )
        _unlink_sqlite_files(candidate)
        try:
            source = sqlite3.connect(_read_only_uri(snapshot.path), uri=True)
            try:
                target = sqlite3.connect(candidate)
                try:
                    source.backup(target)
                finally:
                    target.close()
            finally:
                source.close()
            validate_state_database_file(candidate)
        except BaseException:
            _unlink_sqlite_files(candidate)
            raise

        quarantine: Path | None = None
        moved: list[tuple[Path, Path]] = []
        live_files = (
            self.paths.state_db,
            Path(f"{self.paths.state_db}-wal"),
            Path(f"{self.paths.state_db}-shm"),
        )
        if any(path.exists() for path in live_files):
            try:
                quarantine = self.paths.state_snapshots_dir / (f"pre-recovery-{uuid.uuid4().hex}")
                quarantine.mkdir(parents=True, exist_ok=False)
                for live in live_files:
                    if not live.exists():
                        continue
                    preserved = quarantine / live.name
                    os.replace(live, preserved)
                    moved.append((live, preserved))
            except BaseException:
                for live, preserved in reversed(moved):
                    if preserved.exists() and not live.exists():
                        os.replace(preserved, live)
                if quarantine is not None:
                    with contextlib.suppress(OSError):
                        quarantine.rmdir()
                _unlink_sqlite_files(candidate)
                raise

        try:
            os.replace(candidate, self.paths.state_db)
            validate_state_database_file(self.paths.state_db)
        except Exception:
            _unlink_sqlite_files(self.paths.state_db)
            for live, preserved in moved:
                if preserved.exists():
                    os.replace(preserved, live)
            if quarantine is not None:
                with contextlib.suppress(OSError):
                    quarantine.rmdir()
            raise
        finally:
            _unlink_sqlite_files(candidate)

        self._prune_recovery_quarantines()
        return snapshot

    def _prune_recovery_quarantines(self) -> None:
        root = self.paths.state_snapshots_dir
        if not root.is_dir():
            return
        quarantines = [path for path in root.glob("pre-recovery-*") if path.is_dir()]
        quarantines.sort(
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        for stale in quarantines[self.MAX_RECOVERY_QUARANTINES :]:
            shutil.rmtree(stale, ignore_errors=True)

    async def async_delete_content_cache(self) -> None:
        """Delete only reconstructible content; the next setup rebuilds starter content."""
        await asyncio.to_thread(_safe_remove_tree, self.paths.content_root)

    async def async_apply_uninstall_policy(self, policy: UninstallDataPolicy) -> None:
        """Apply an explicit Config Entry removal policy off the event loop."""
        if policy is UninstallDataPolicy.KEEP_USER_DATA:
            return
        await asyncio.to_thread(self._apply_uninstall_policy_sync, policy)

    def _apply_uninstall_policy_sync(self, policy: UninstallDataPolicy) -> None:
        if policy in {
            UninstallDataPolicy.DELETE_USER_STATE,
            UninstallDataPolicy.DELETE_EVERYTHING,
        }:
            _safe_remove_tree(self.paths.state_root)
        if policy in {
            UninstallDataPolicy.DELETE_CONTENT_CACHE,
            UninstallDataPolicy.DELETE_EVERYTHING,
        }:
            _safe_remove_tree(self.paths.content_root)
