"""Notification event counters must not deserialize the complete history."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from custom_components.locklearn.storage import SQLiteStorage, StoragePaths


async def test_notification_counters_preserve_reverse_event_semantics(tmp_path: Path) -> None:
    storage = SQLiteStorage(StoragePaths(tmp_path / "state.db", tmp_path / "content" / "current.db"))
    await storage.async_open()
    try:
        def seed(connection: object) -> None:
            from sqlite3 import Connection
            assert isinstance(connection, Connection)
            for index, (result, session) in enumerate(
                (
                    ("correct", "session-1"),
                    ("wrong", "session-1"),
                    ("correct", "session-1"),
                    ("known", None),
                    ("correct", "session-1"),
                    ("correct", "session-2"),
                )
            ):
                connection.execute(
                    """INSERT INTO review_events(
                        id, profile_id, track_id, learning_item_id,
                        prompt_facet_id, answer_facet_id, card_key,
                        mode, question_type, result, hint_used,
                        retrieval_occurred, signal_quality, policy_version,
                        dataset_generation, normalization_version,
                        pre_state_snapshot, post_state_snapshot,
                        session_id, created_at_utc, local_date,
                        timezone_name, utc_offset_minutes
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        f"event-{index}", "p", "t", "item", "prompt", "answer", "card",
                        "verified_mcq", "mcq", result, 0, 1, "medium", 1,
                        "generation", 1, "{}", "{}", session,
                        datetime(2026, 10, 10, 10, index, tzinfo=UTC).isoformat(),
                        "2026-10-10", "UTC", 0,
                    ),
                )
            connection.commit()
        await storage._async_writer(seed)
        results = await storage.repositories.review_events.async_notification_result_counters(
            profile_id="p", track_id="t", session_id="session-1"
        )
        assert results == {
            "consecutive_correct": 4,
            "consecutive_wrong": 0,
            "session_accuracy": 0.75,
        }
        missing = await storage.repositories.review_events.async_notification_result_counters(
            profile_id="p", track_id="missing", session_id=None
        )
        assert missing == {
            "consecutive_correct": 0,
            "consecutive_wrong": 0,
            "session_accuracy": None,
        }
    finally:
        await storage.async_close()
