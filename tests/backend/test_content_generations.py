"""P1.6 content schema, immutable generation, and stable-merge tests."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import threading
from pathlib import Path

import pytest

from custom_components.locklearn.const import CONTENT_SCHEMA_VERSION
from custom_components.locklearn.storage import (
    ContentActivationError,
    ContentGenerationError,
    ContentGenerationValidator,
    ContentValidationError,
    SQLiteStorage,
    StoragePaths,
)
from custom_components.locklearn.storage.schema import (
    CONTENT_REQUIRED_INDEXES,
    CONTENT_REQUIRED_TABLES,
)
from tests.backend.content_db_helpers import (
    ITEM_A,
    ITEM_B,
    card_identity,
    create_package,
    facet_ids,
)


@pytest.fixture
async def content_storage(tmp_path: Path):
    """Open storage with content generations under one isolated root."""
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    yield storage
    await storage.async_close()


def inspect_generation(path: Path) -> sqlite3.Connection:
    """Open one immutable generation read-only for assertions."""
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)


async def build_candidate(
    storage: SQLiteStorage,
    package: Path,
    generation_id: str,
) -> Path:
    """Build one named candidate in the manager's same-filesystem staging area."""
    candidate = storage.paths.content_staging_dir / f"{generation_id}.next.db"
    await storage.async_build_content_generation((package,), candidate, generation_id=generation_id)
    return candidate


async def test_fresh_content_schema_has_required_objects_and_integrity(
    content_storage: SQLiteStorage,
) -> None:
    """A fresh bootstrap generation is complete, versioned, and integral."""
    path = content_storage.content_generations.active_path
    with inspect_generation(path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute(
            "SELECT version FROM schema_version WHERE singleton = 1"
        ).fetchone() == (CONTENT_SCHEMA_VERSION,)
        objects = connection.execute(
            "SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index')"
        ).fetchall()
        tables = {name for object_type, name in objects if object_type == "table"}
        indexes = {name for object_type, name in objects if object_type == "index"}
        assert tables >= CONTENT_REQUIRED_TABLES
        assert indexes >= CONTENT_REQUIRED_INDEXES


async def test_unreleased_p0_content_cache_is_rebuilt_without_partial_switch(
    tmp_path: Path,
) -> None:
    """The exact provisional P0 cache shape is reconstructible upgrade input."""
    paths = StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    paths.content_db.parent.mkdir(parents=True)
    with sqlite3.connect(paths.content_db) as connection:
        connection.executescript(
            """CREATE TABLE schema_version(version INTEGER NOT NULL);
               INSERT INTO schema_version VALUES (1);
               CREATE TABLE card_definitions(
                   card_key TEXT PRIMARY KEY,
                   pack_version_id TEXT NOT NULL,
                   ordinal INTEGER NOT NULL
               );"""
        )
    storage = SQLiteStorage(paths)
    await storage.async_open()
    try:
        with inspect_generation(paths.content_db) as connection:
            assert connection.execute(
                "SELECT content_schema_version FROM generation_metadata"
            ).fetchone() == (CONTENT_SCHEMA_VERSION,)
        assert list(paths.content_staging_dir.glob("legacy-p0-*.db")) == []
    finally:
        await storage.async_close()


def test_content_schema_enforces_foreign_keys_and_semantic_uniqueness(tmp_path: Path) -> None:
    """Package builders cannot create dangling relations or duplicate facet keys."""
    package = create_package(tmp_path / "constraints.db", "constraints")
    with sqlite3.connect(package) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learning_item_concepts VALUES (?, 'locklearn:concept:missing')",
                (ITEM_A,),
            )
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO facets(
                       facet_id, learning_item_id, kind, facet_key, language_tag, script,
                       lifecycle_status, superseded_by_facet_id
                   ) VALUES (
                       'locklearn:facet:duplicate', ?, 'text', 'prompt',
                       'en', 'Latn', 'active', NULL
                   )""",
                (ITEM_A,),
            )


def test_package_validation_rejects_payload_outside_p1_3_contract(tmp_path: Path) -> None:
    """Persisted blocks are revalidated against the strict typed payload contract."""
    package = create_package(tmp_path / "invalid-block.db", "invalid-block")
    with sqlite3.connect(package) as connection:
        connection.execute('UPDATE content_blocks SET payload_json = \'{"html":"<script>"}\'')
        connection.commit()
    with pytest.raises(ContentValidationError, match="invalid content block payload"):
        ContentGenerationValidator().validate_package(package)


async def test_incomplete_released_id_migration_cannot_replace_active_generation(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Item/facet migrations must explicitly cover affected card IDs and keys."""
    package_v1 = create_package(tmp_path / "migration-v1.db", "migration-v1")
    candidate_v1 = await build_candidate(content_storage, package_v1, "migration-one")
    await content_storage.async_activate_content_generation(candidate_v1)

    package_v2 = create_package(
        tmp_path / "migration-v2.db", "migration-v2", active_item_ids=(ITEM_B,)
    )
    with sqlite3.connect(package_v2) as connection:
        connection.execute(
            """INSERT INTO stable_id_migrations VALUES (
                   'learning_item', ?, ?, ?, 'migration-v2', 'source identity correction'
               )""",
            ("locklearn:dataset:test", ITEM_A, ITEM_B),
        )
        connection.commit()
    candidate_v2 = content_storage.paths.content_staging_dir / "migration-two.next.db"
    with pytest.raises(ContentValidationError, match="must map every affected"):
        await content_storage.async_build_content_generation(
            (package_v2,), candidate_v2, generation_id="migration-two"
        )
    assert content_storage.content_generations.active_metadata.generation_id == "migration-one"
    assert not candidate_v2.exists()


async def test_build_is_independent_staged_and_bounded_to_one_attach(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """N+1 is a separate validated file and never becomes visible during build."""
    bootstrap = content_storage.content_generations.active_metadata.generation_id
    package = create_package(tmp_path / "v1.db", "v1")
    candidate = content_storage.paths.content_staging_dir / "content.next.db"

    result = await content_storage.async_build_content_generation(
        (package,), candidate, generation_id="generation-one"
    )

    assert result.metadata.generation_id == "generation-one"
    assert result.metadata.parent_generation_id == bootstrap
    assert result.active_item_count == 1
    assert result.active_card_count == 1
    assert result.max_database_count == 2
    assert candidate.exists()
    assert os.stat(candidate).st_ino != os.stat(content_storage.paths.content_db).st_ino
    assert content_storage.content_generations.active_metadata.generation_id == bootstrap


async def test_valid_activation_is_immutable_and_failed_activation_preserves_lkg(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Only a fully valid candidate replaces current; invalid staging is harmless."""
    package = create_package(tmp_path / "v1.db", "v1")
    candidate = await build_candidate(content_storage, package, "generation-one")
    activated = await content_storage.async_activate_content_generation(candidate)
    assert activated.generation_id == "generation-one"
    active_path = content_storage.content_generations.active_path
    assert os.stat(active_path).st_ino == os.stat(content_storage.paths.content_db).st_ino
    assert active_path.stat().st_mode & 0o222 == 0
    with pytest.raises(sqlite3.OperationalError), sqlite3.connect(active_path) as connection:
        connection.execute("DELETE FROM learning_items")

    invalid = content_storage.paths.content_staging_dir / "invalid.next.db"
    invalid.write_bytes(b"not sqlite")
    with pytest.raises(ContentValidationError):
        await content_storage.async_activate_content_generation(invalid)
    assert content_storage.content_generations.active_metadata.generation_id == "generation-one"
    with inspect_generation(content_storage.paths.content_db) as connection:
        assert connection.execute("SELECT generation_id FROM generation_metadata").fetchone() == (
            "generation-one",
        )


async def test_reader_drain_switch_and_previous_generation_cleanup(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Old SQLite readers finish; new readers wait and then see the new generation."""
    package_v1 = create_package(tmp_path / "v1.db", "v1")
    candidate_v1 = await build_candidate(content_storage, package_v1, "generation-one")
    await content_storage.async_activate_content_generation(candidate_v1)

    package_v2 = create_package(tmp_path / "v2.db", "v2", active_item_ids=())
    candidate_v2 = await build_candidate(content_storage, package_v2, "generation-two")
    old_lease = await content_storage.content_generations.acquire_reader()
    old_connection = inspect_generation(old_lease.path)
    activation = asyncio.create_task(
        content_storage.async_activate_content_generation(candidate_v2)
    )
    await asyncio.sleep(0.02)
    assert not activation.done()
    assert old_connection.execute(
        "SELECT lifecycle_status FROM learning_items WHERE learning_item_id = ?", (ITEM_A,)
    ).fetchone() == ("active",)

    waiting_reader = asyncio.create_task(content_storage.content_generations.acquire_reader())
    await asyncio.sleep(0.02)
    assert not waiting_reader.done()
    old_connection.close()
    await old_lease.release()
    await activation
    new_lease = await waiting_reader
    try:
        assert new_lease.generation_id == "generation-two"
        with inspect_generation(new_lease.path) as connection:
            assert connection.execute(
                "SELECT lifecycle_status FROM learning_items WHERE learning_item_id = ?",
                (ITEM_A,),
            ).fetchone() == ("removed",)
    finally:
        await new_lease.release()

    assert content_storage.content_generations.previous_generation_id == "generation-one"
    retained = {
        path.stem for path in content_storage.content_generations.generations_dir.glob("*.db")
    }
    assert retained == {"generation-one", "generation-two"}


async def test_rollback_reactivates_only_a_valid_retained_generation(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Rollback swaps to the validated previous file and retains the rolled-away file."""
    for version, generation_id, items in (
        ("v1", "generation-one", (ITEM_A,)),
        ("v2", "generation-two", ()),
    ):
        package = create_package(tmp_path / f"{version}.db", version, active_item_ids=items)
        candidate = await build_candidate(content_storage, package, generation_id)
        await content_storage.async_activate_content_generation(candidate)

    rolled_back = await content_storage.async_rollback_content_generation()
    assert rolled_back.generation_id == "generation-one"
    assert content_storage.content_generations.previous_generation_id == "generation-two"
    with inspect_generation(content_storage.paths.content_db) as connection:
        assert connection.execute(
            "SELECT lifecycle_status FROM learning_items WHERE learning_item_id = ?", (ITEM_A,)
        ).fetchone() == ("active",)


async def test_active_removed_active_reuses_exact_identity_and_records_history(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """A removed item comes back with identical item, facet, and card identities."""
    expected_card_id, expected_card_key = card_identity(ITEM_A)
    expected_facets = facet_ids(ITEM_A)
    versions = (
        ("v1", "generation-one", (ITEM_A,)),
        ("v2", "generation-two", ()),
        ("v3", "generation-three", (ITEM_A,)),
    )
    observed: list[tuple[str, tuple[str, str], str, str]] = []
    for version, generation_id, items in versions:
        package = create_package(tmp_path / f"{version}.db", version, active_item_ids=items)
        candidate = await build_candidate(content_storage, package, generation_id)
        await content_storage.async_activate_content_generation(candidate)
        with inspect_generation(content_storage.paths.content_db) as connection:
            item_status = connection.execute(
                "SELECT lifecycle_status FROM learning_items WHERE learning_item_id = ?",
                (ITEM_A,),
            ).fetchone()[0]
            facets = tuple(
                row[0]
                for row in connection.execute(
                    "SELECT facet_id FROM facets WHERE learning_item_id = ? ORDER BY facet_id",
                    (ITEM_A,),
                )
            )
            card_id, card_key = connection.execute(
                """SELECT card_definition_id, card_key FROM card_definitions
                   WHERE learning_item_id = ?""",
                (ITEM_A,),
            ).fetchone()
            observed.append((item_status, facets, card_id, card_key))
            if generation_id == "generation-two":
                assert connection.execute(
                    """SELECT lifecycle_status FROM tombstones
                       WHERE object_type = 'learning_item' AND stable_id = ?""",
                    (ITEM_A,),
                ).fetchone() == ("removed",)

    assert [row[0] for row in observed] == ["active", "removed", "active"]
    assert all(row[1] == tuple(sorted(expected_facets)) for row in observed)
    assert all(row[2:] == (expected_card_id, expected_card_key) for row in observed)
    with inspect_generation(content_storage.paths.content_db) as connection:
        assert (
            connection.execute("SELECT 1 FROM tombstones WHERE stable_id = ?", (ITEM_A,)).fetchone()
            is None
        )
        assert connection.execute(
            """SELECT generation_id, lifecycle_status FROM content_lifecycle_history
               WHERE object_type = 'learning_item' AND stable_id = ? ORDER BY generation_id""",
            (ITEM_A,),
        ).fetchall() == [
            ("generation-one", "active"),
            ("generation-three", "active"),
            ("generation-two", "removed"),
        ]


async def test_superseded_item_preserves_identity_and_points_to_replacement(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Supersession is explicit and does not delete the old stable row."""
    package_v1 = create_package(tmp_path / "v1.db", "v1")
    candidate_v1 = await build_candidate(content_storage, package_v1, "generation-one")
    await content_storage.async_activate_content_generation(candidate_v1)

    package_v2 = create_package(
        tmp_path / "v2.db",
        "v2",
        active_item_ids=(ITEM_B,),
        superseded=((ITEM_A, ITEM_B),),
    )
    candidate_v2 = await build_candidate(content_storage, package_v2, "generation-two")
    await content_storage.async_activate_content_generation(candidate_v2)

    with inspect_generation(content_storage.paths.content_db) as connection:
        assert connection.execute(
            """SELECT lifecycle_status, superseded_by_learning_item_id
               FROM learning_items WHERE learning_item_id = ?""",
            (ITEM_A,),
        ).fetchone() == ("superseded", ITEM_B)
        assert connection.execute(
            """SELECT lifecycle_status, replacement_id FROM tombstones
               WHERE object_type = 'learning_item' AND stable_id = ?""",
            (ITEM_A,),
        ).fetchone() == ("superseded", ITEM_B)
        assert connection.execute(
            "SELECT lifecycle_status FROM learning_items WHERE learning_item_id = ?", (ITEM_B,)
        ).fetchone() == ("active",)


async def test_parallel_real_sqlite_readers_survive_activation(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Multiple worker-thread readers complete before activation opens the new catalog."""
    package_v1 = create_package(tmp_path / "v1.db", "v1")
    candidate_v1 = await build_candidate(content_storage, package_v1, "generation-one")
    await content_storage.async_activate_content_generation(candidate_v1)
    package_v2 = create_package(tmp_path / "v2.db", "v2", active_item_ids=())
    candidate_v2 = await build_candidate(content_storage, package_v2, "generation-two")

    entered = asyncio.Event()
    release = asyncio.Event()
    reader_count = 4
    entered_count = 0
    lock = asyncio.Lock()

    async def reader() -> str:
        nonlocal entered_count
        lease = await content_storage.content_generations.acquire_reader()
        try:
            with inspect_generation(lease.path) as connection:
                assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                async with lock:
                    entered_count += 1
                    if entered_count == reader_count:
                        entered.set()
                await release.wait()
                return str(
                    connection.execute("SELECT generation_id FROM generation_metadata").fetchone()[
                        0
                    ]
                )
        finally:
            await lease.release()

    readers = [asyncio.create_task(reader()) for _ in range(reader_count)]
    await entered.wait()
    activation = asyncio.create_task(
        content_storage.async_activate_content_generation(candidate_v2)
    )
    await asyncio.sleep(0.02)
    assert not activation.done()
    release.set()
    assert await asyncio.gather(*readers) == ["generation-one"] * reader_count
    assert (await activation).generation_id == "generation-two"
    new_lease = await content_storage.content_generations.acquire_reader()
    try:
        assert new_lease.generation_id == "generation-two"
    finally:
        await new_lease.release()


def test_package_validation_rejects_cross_dataset_rows(tmp_path: Path) -> None:
    """Every dataset-scoped row in one package belongs to the declared dataset."""
    package = create_package(tmp_path / "cross-dataset.db", "cross-dataset")
    with sqlite3.connect(package) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("INSERT INTO datasets VALUES ('locklearn:dataset:other')")
        connection.execute(
            "UPDATE terms SET dataset_id = 'locklearn:dataset:other' WHERE term_id = ?",
            ("locklearn:term:test",),
        )
        connection.commit()
    with pytest.raises(ContentValidationError, match="exactly its declared dataset"):
        ContentGenerationValidator().validate_package(package)


async def test_stale_candidate_parent_cannot_replace_newer_generation(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Activation is a generation CAS and rejects candidates built from stale parents."""
    package_b = create_package(tmp_path / "b.db", "b")
    package_c = create_package(tmp_path / "c.db", "c", active_item_ids=())
    candidate_b = await build_candidate(content_storage, package_b, "generation-b")
    candidate_c = await build_candidate(content_storage, package_c, "generation-c")

    await content_storage.async_activate_content_generation(candidate_b)
    with pytest.raises(ContentActivationError, match="parent generation"):
        await content_storage.async_activate_content_generation(candidate_c)

    assert content_storage.content_generations.active_metadata.generation_id == "generation-b"
    with inspect_generation(content_storage.paths.content_db) as connection:
        assert connection.execute("SELECT generation_id FROM generation_metadata").fetchone() == (
            "generation-b",
        )


async def test_cancelled_activation_finishes_switch_before_reopening_reader_gate(
    content_storage: SQLiteStorage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancellation cannot expose a switched inode with stale in-memory generation state."""
    package = create_package(tmp_path / "cancel.db", "cancel")
    candidate = await build_candidate(content_storage, package, "generation-cancel")
    manager = content_storage.content_generations
    original_activate_sync = manager._activate_sync
    entered = threading.Event()
    release = threading.Event()

    def delayed_activate_sync(path: Path, previous_id: str | None):
        entered.set()
        if not release.wait(timeout=5):
            raise RuntimeError("timed out waiting to release activation")
        return original_activate_sync(path, previous_id)

    monkeypatch.setattr(manager, "_activate_sync", delayed_activate_sync)
    activation = asyncio.create_task(content_storage.async_activate_content_generation(candidate))
    assert await asyncio.to_thread(entered.wait, 2)
    activation.cancel()
    await asyncio.sleep(0)
    waiting_reader = asyncio.create_task(manager.acquire_reader())
    await asyncio.sleep(0.02)
    assert not waiting_reader.done()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await activation
    lease = await waiting_reader
    try:
        assert lease.generation_id == "generation-cancel"
        assert manager.active_metadata.generation_id == "generation-cancel"
        with inspect_generation(content_storage.paths.content_db) as connection:
            assert connection.execute(
                "SELECT generation_id FROM generation_metadata"
            ).fetchone() == ("generation-cancel",)
    finally:
        await lease.release()


async def test_close_waits_for_inflight_activation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HA unload cannot shut executors down underneath an atomic content switch."""
    storage = SQLiteStorage(
        StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    )
    await storage.async_open()
    package = create_package(tmp_path / "close.db", "close")
    candidate = await build_candidate(storage, package, "generation-close")
    manager = storage.content_generations
    original_activate_sync = manager._activate_sync
    entered = threading.Event()
    release = threading.Event()

    def delayed_activate_sync(path: Path, previous_id: str | None):
        entered.set()
        if not release.wait(timeout=5):
            raise RuntimeError("timed out waiting to release activation")
        return original_activate_sync(path, previous_id)

    monkeypatch.setattr(manager, "_activate_sync", delayed_activate_sync)
    activation = asyncio.create_task(storage.async_activate_content_generation(candidate))
    assert await asyncio.to_thread(entered.wait, 2)
    closing = asyncio.create_task(storage.async_close())
    await asyncio.sleep(0.02)
    assert not closing.done()

    release.set()
    assert (await activation).generation_id == "generation-close"
    await closing
    with pytest.raises(ContentGenerationError, match="closed"):
        await manager.acquire_reader()


async def test_rollback_restart_recovers_previous_from_switch_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crash boundary after rollback pointer swap can recover the rolled-away generation."""
    paths = StoragePaths(tmp_path / "state" / "state.db", tmp_path / "content" / "current.db")
    storage = SQLiteStorage(paths)
    await storage.async_open()
    try:
        for version, generation_id, items in (
            ("journal-v1", "journal-one", ("locklearn:item:a",)),
            ("journal-v2", "journal-two", ()),
        ):
            package = create_package(tmp_path / f"{version}.db", version, active_item_ids=items)
            candidate = await build_candidate(storage, package, generation_id)
            await storage.async_activate_content_generation(candidate)

        manager = storage.content_generations

        def fail_catalog(*_args: object, **_kwargs: object) -> None:
            raise OSError("simulated catalog persistence failure")

        monkeypatch.setattr(manager, "_write_catalog", fail_catalog)
        rolled_back = await storage.async_rollback_content_generation()
        assert rolled_back.generation_id == "journal-one"
        assert manager.switch_journal_path.exists()
    finally:
        await storage.async_close()

    reopened = SQLiteStorage(paths)
    await reopened.async_open()
    try:
        assert reopened.content_generations.active_metadata.generation_id == "journal-one"
        assert reopened.content_generations.previous_generation_id == "journal-two"
        assert not reopened.content_generations.switch_journal_path.exists()
    finally:
        await reopened.async_close()


async def test_migration_targets_must_match_migrated_card_tuple(
    content_storage: SQLiteStorage, tmp_path: Path
) -> None:
    """Complete-looking mappings cannot redirect progress to a semantically different card."""
    item_c = "locklearn:item:c"
    package_v1 = create_package(tmp_path / "semantic-v1.db", "semantic-v1")
    candidate_v1 = await build_candidate(content_storage, package_v1, "semantic-one")
    await content_storage.async_activate_content_generation(candidate_v1)

    package_v2 = create_package(
        tmp_path / "semantic-v2.db",
        "semantic-v2",
        active_item_ids=("locklearn:item:b", item_c),
    )
    old_prompt, old_answer = facet_ids("locklearn:item:a")
    new_prompt, new_answer = facet_ids("locklearn:item:b")
    old_card_id, old_card_key = card_identity("locklearn:item:a")
    wrong_card_id, wrong_card_key = card_identity(item_c)
    with sqlite3.connect(package_v2) as connection:
        migrations = (
            ("learning_item", "locklearn:item:a", "locklearn:item:b"),
            ("facet", old_prompt, new_prompt),
            ("facet", old_answer, new_answer),
            ("card_definition", old_card_id, wrong_card_id),
            ("card_key", old_card_key, wrong_card_key),
        )
        connection.executemany(
            """INSERT INTO stable_id_migrations(
                   object_type, dataset_id, old_id, new_id, introduced_in_version, reason
               ) VALUES (?, 'locklearn:dataset:test', ?, ?, 'semantic-v2', 'test mapping')""",
            migrations,
        )
        connection.commit()

    candidate_v2 = content_storage.paths.content_staging_dir / "semantic-two.next.db"
    with pytest.raises(ContentValidationError, match="migrated tuple"):
        await content_storage.async_build_content_generation(
            (package_v2,), candidate_v2, generation_id="semantic-two"
        )
    assert content_storage.content_generations.active_metadata.generation_id == "semantic-one"


def test_package_requires_provenance_for_every_declared_source(tmp_path: Path) -> None:
    """A declared source cannot enter an official-shaped package without a snapshot trail."""
    package = create_package(tmp_path / "missing-provenance.db", "missing-provenance")
    with sqlite3.connect(package) as connection:
        connection.execute("DELETE FROM provenance_records")
        connection.commit()
    with pytest.raises(ContentValidationError, match="no provenance-backed source snapshot"):
        ContentGenerationValidator().validate_package(package)


def test_package_rejects_provenance_target_from_wrong_dataset(tmp_path: Path) -> None:
    """Object provenance must resolve inside the dataset that declares it."""
    package = create_package(tmp_path / "wrong-target.db", "wrong-target")
    with sqlite3.connect(package) as connection:
        connection.execute(
            """UPDATE provenance_records
               SET object_type = 'learning_item', object_id = 'locklearn:item:missing'"""
        )
        connection.commit()
    with pytest.raises(ContentValidationError, match="target does not exist"):
        ContentGenerationValidator().validate_package(package)


def test_package_rejects_invalid_source_snapshot_hash(tmp_path: Path) -> None:
    """Snapshot identity includes a lowercase canonical SHA-256 digest."""
    package = create_package(tmp_path / "bad-snapshot.db", "bad-snapshot")
    with sqlite3.connect(package) as connection:
        connection.execute("UPDATE source_snapshots SET sha256 = ?", ("A" * 64,))
        connection.commit()
    with pytest.raises(ContentValidationError, match="invalid SHA-256"):
        ContentGenerationValidator().validate_package(package)
