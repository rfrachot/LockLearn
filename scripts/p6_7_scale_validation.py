"""P6.7 reference-hardware performance, scale, and storage qualification."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import shutil
import sqlite3
import sys
import tempfile
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import custom_components.locklearn.const as locklearn_const  # noqa: E402
import custom_components.locklearn.datasets.storage_budget as storage_budget  # noqa: E402
import custom_components.locklearn.observability as observability  # noqa: E402
import custom_components.locklearn.storage as locklearn_storage  # noqa: E402
import custom_components.locklearn.storage.schema as storage_schema  # noqa: E402
import scripts.p5_9_performance as p5_9_performance  # noqa: E402
import tests.backend.content_db_helpers as content_db_helpers  # noqa: E402

REFERENCE_CARD_COUNT = 60_000
STATE_DAYS = 1_826
STANDARD_NEW_CARDS_PER_DAY = 8
STANDARD_REVIEW_CAPACITY_PER_DAY = 80
STANDARD_SESSION_CARDS = 20
STANDARD_SESSIONS_PER_DAY = STANDARD_REVIEW_CAPACITY_PER_DAY // STANDARD_SESSION_CARDS
STANDARD_NOTIFICATION_SLOTS_PER_DAY = 6
AUDIT_EVENTS_PER_DAY = 2


def _hardware() -> dict[str, Any]:
    memory_bytes: int | None = None
    with suppress(AttributeError, OSError, TypeError, ValueError):
        memory_bytes = int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "logical_cpu_count": os.cpu_count(),
        "memory_bytes": memory_bytes,
    }


def _initialize_state_projection(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(storage_schema.STATE_SCHEMA)
    connection.execute(
        "INSERT INTO schema_version(version) VALUES (?)",
        (locklearn_const.DB_SCHEMA_VERSION,),
    )
    return connection


def _project_five_year_state(path: Path, *, days: int) -> dict[str, Any]:
    started = perf_counter()
    connection = _initialize_state_projection(path)
    profile_id = "p6-7-profile"
    track_id = "p6-7-track"
    target_id = "p6-7-target"
    start = datetime(2026, 1, 1, tzinfo=UTC)
    try:
        connection.execute(
            """INSERT INTO profiles(
                   profile_id, name, preset, timezone, status, settings_json,
                   created_at_utc, updated_at_utc
               ) VALUES (
                   ?, 'P6.7 reference', 'standard', 'Europe/Paris', 'active',
                   '{}', ?, ?
               )""",
            (profile_id, start.isoformat(), start.isoformat()),
        )
        connection.execute(
            """INSERT INTO tracks(
                   track_id, profile_id, name, status, priority, settings_json,
                   created_at_utc, updated_at_utc
               ) VALUES (?, ?, 'P6.7 track', 'active', 1, '{}', ?, ?)""",
            (track_id, profile_id, start.isoformat(), start.isoformat()),
        )
        connection.execute(
            """INSERT INTO notification_targets(
                   target_id, profile_id, device_registry_id, platform,
                   friendly_name, capabilities_json, shared_device,
                   lockscreen_visibility, enabled, created_at_utc, updated_at_utc
               ) VALUES (
                   ?, ?, 'p6-7-device', 'android', 'P6.7 target', '{}',
                   0, 'private', 1, ?, ?
               )""",
            (target_id, profile_id, start.isoformat(), start.isoformat()),
        )

        progress_count = days * STANDARD_NEW_CARDS_PER_DAY
        connection.executemany(
            """INSERT INTO progress(
                   profile_id, track_id, card_key, state, mastery, box,
                   seen_count, verified_correct_count, verified_wrong_count,
                   next_due_at_utc, dataset_generation, updated_at_utc
               ) VALUES (
                   ?, ?, ?, 'review', 0.72, 3, 12, 9, 3, ?,
                   'p6-7-generation', ?
               )""",
            (
                (
                    profile_id,
                    track_id,
                    f"p6-7-card-{index}",
                    (start + timedelta(days=index % days)).isoformat(),
                    (start + timedelta(days=index % days)).isoformat(),
                )
                for index in range(progress_count)
            ),
        )

        review_count = 0
        session_item_count = 0
        notification_count = 0
        for day_index in range(days):
            current = start + timedelta(days=day_index)
            local_date = current.date().isoformat()
            timestamp = current.replace(hour=12).isoformat()
            day_session_ids: list[str] = []
            for session_index in range(STANDARD_SESSIONS_PER_DAY):
                session_id = f"p6-7-session-{day_index}-{session_index}"
                day_session_ids.append(session_id)
                connection.execute(
                    """INSERT INTO sessions(
                           id, profile_id, track_id, type, strategy, status,
                           version, current_position, started_at_utc,
                           last_activity_at_utc, completed_at_utc,
                           question_count, settings_json
                       ) VALUES (
                           ?, ?, ?, 'learn', 'default', 'completed', 21, 20,
                           ?, ?, ?, 20, '{}'
                       )""",
                    (
                        session_id,
                        profile_id,
                        track_id,
                        timestamp,
                        timestamp,
                        timestamp,
                    ),
                )

                item_rows: list[tuple[Any, ...]] = []
                answer_rows: list[tuple[Any, ...]] = []
                for item_index in range(STANDARD_SESSION_CARDS):
                    review_index = session_index * STANDARD_SESSION_CARDS + item_index
                    global_card = (
                        day_index * STANDARD_REVIEW_CAPACITY_PER_DAY
                        + review_index
                    ) % progress_count
                    card_key = f"p6-7-card-{global_card}"
                    question_id = f"p6-7-q-{day_index}-{session_index}-{item_index}"
                    item_rows.append(
                        (
                            session_id,
                            item_index,
                            question_id,
                            card_key,
                            f"p6-7-item-{global_card}",
                            f"p6-7-prompt-{global_card}",
                            f"p6-7-answer-{global_card}",
                            "answered",
                            '{"selection":{"reason":"review_due"}}',
                        )
                    )
                    answer_rows.append(
                        (
                            session_id,
                            question_id,
                            '{"kind":"benchmark","choice":1}',
                            item_index + 2,
                            timestamp,
                        )
                    )
                connection.executemany(
                    """INSERT INTO session_items(
                           session_id, position, question_id, card_key,
                           learning_item_id, prompt_facet_id, answer_facet_id,
                           status, payload_json
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    item_rows,
                )
                connection.executemany(
                    """INSERT INTO session_answers(
                           session_id, question_id, answer_json,
                           resulting_version, created_at_utc
                       ) VALUES (?, ?, ?, ?, ?)""",
                    answer_rows,
                )
                session_item_count += STANDARD_SESSION_CARDS

            event_rows: list[tuple[Any, ...]] = []
            for review_index in range(STANDARD_REVIEW_CAPACITY_PER_DAY):
                global_card = (
                    day_index * STANDARD_REVIEW_CAPACITY_PER_DAY + review_index
                ) % progress_count
                card_key = f"p6-7-card-{global_card}"
                result = "wrong" if review_index % 10 == 0 else "correct"
                snapshot = json.dumps(
                    {
                        "profile_id": profile_id,
                        "track_id": track_id,
                        "card_key": card_key,
                        "state": "review",
                        "box": 3,
                        "mastery": 0.72,
                        "seen_count": 12,
                        "verified_correct_count": 9,
                        "verified_wrong_count": 3,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
                event_rows.append(
                    (
                        f"p6-7-review-{day_index}-{review_index}",
                        profile_id,
                        track_id,
                        f"p6-7-item-{global_card}",
                        f"p6-7-prompt-{global_card}",
                        f"p6-7-answer-{global_card}",
                        card_key,
                        "panel",
                        "mcq",
                        result,
                        0,
                        1,
                        "verified",
                        1,
                        "p6-7-generation",
                        snapshot,
                        snapshot,
                        day_session_ids[review_index // STANDARD_SESSION_CARDS],
                        timestamp,
                        local_date,
                        "Europe/Paris",
                        60,
                    )
                )
            connection.executemany(
                """INSERT INTO review_events(
                       id, profile_id, track_id, learning_item_id,
                       prompt_facet_id, answer_facet_id, card_key, mode,
                       question_type, result, hint_used, retrieval_occurred,
                       signal_quality, policy_version, dataset_generation,
                       pre_state_snapshot, post_state_snapshot, session_id,
                       created_at_utc, local_date, timezone_name,
                       utc_offset_minutes
                   ) VALUES (
                       ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?
                   )""",
                event_rows,
            )
            review_count += STANDARD_REVIEW_CAPACITY_PER_DAY

            connection.execute(
                """INSERT INTO stats_daily(
                       profile_id, track_id, local_date, timezone_name,
                       utc_offset_minutes, policy_version, learning_exposures,
                       verified_retrievals, verified_correct, verified_wrong,
                       quiz_total, new_cards, reviewed_cards, active_seconds
                   ) VALUES (
                       ?, ?, ?, 'Europe/Paris', 60, 1, 8, 80, 72, 8,
                       80, 8, 72, 1200
                   )""",
                (profile_id, track_id, local_date),
            )

            slot_rows: list[tuple[Any, ...]] = []
            interaction_rows: list[tuple[Any, ...]] = []
            receptivity_rows: list[tuple[Any, ...]] = []
            for slot_index in range(STANDARD_NOTIFICATION_SLOTS_PER_DAY):
                slot_id = f"p6-7-slot-{day_index}-{slot_index}"
                slot_time = current.replace(hour=8 + slot_index * 2).isoformat()
                slot_rows.append(
                    (
                        slot_id,
                        profile_id,
                        track_id,
                        target_id,
                        "learning",
                        slot_time,
                        "consumed",
                        1,
                        f"p6-7-seed-{day_index}",
                        slot_time,
                        slot_time,
                    )
                )
                interaction_rows.append(
                    (
                        f"p6-7-interaction-{day_index}-{slot_index}",
                        f"p6-7-token-{day_index}-{slot_index}",
                        profile_id,
                        track_id,
                        target_id,
                        "answered",
                        "consumed",
                        slot_time,
                        current.replace(hour=23, minute=59).isoformat(),
                        slot_time,
                        "KNOWN",
                        '{"kind":"benchmark"}',
                    )
                )
                receptivity_rows.append(
                    (
                        slot_id,
                        profile_id,
                        target_id,
                        slot_time,
                        current.weekday(),
                        8 + slot_index * 2,
                        1,
                        0,
                        1,
                        2500,
                        slot_time,
                    )
                )
            connection.executemany(
                """INSERT INTO scheduled_slots(
                       slot_id, profile_id, track_id, target_id, slot_type,
                       scheduled_for_utc, status, scheduler_config_version,
                       seed, created_at_utc, updated_at_utc
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                slot_rows,
            )
            connection.executemany(
                """INSERT INTO notification_interactions(
                       interaction_id, token, profile_id, track_id, target_id,
                       stage, status, created_at_utc, expires_at_utc,
                       consumed_at_utc, action_id, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                interaction_rows,
            )
            connection.executemany(
                """INSERT INTO receptivity_samples(
                       slot_id, profile_id, target_id, delivered_at_utc,
                       timezone_name, weekday, local_hour, delivered, cleared,
                       answered, delivery_to_action_ms, updated_at_utc
                   ) VALUES (
                       ?, ?, ?, ?, 'Europe/Paris', ?, ?, ?, ?, ?, ?, ?
                   )""",
                receptivity_rows,
            )
            notification_count += STANDARD_NOTIFICATION_SLOTS_PER_DAY

            connection.executemany(
                """INSERT INTO audit_events(
                       event_type, actor_user_id, profile_id, payload_json,
                       created_at_utc
                   ) VALUES ('benchmark_action', NULL, ?, '{}', ?)""",
                ((profile_id, timestamp) for _ in range(AUDIT_EVENTS_PER_DAY)),
            )

        connection.commit()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        row_counts = {
            table: int(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            )
            for table in (
                "progress",
                "review_events",
                "sessions",
                "session_items",
                "session_answers",
                "scheduled_slots",
                "notification_interactions",
                "receptivity_samples",
                "stats_daily",
                "audit_events",
            )
        }
    finally:
        connection.close()

    file_bytes = path.stat().st_size
    bytes_per_day = file_bytes / days
    return {
        "assumptions": {
            "days": days,
            "standard_new_cards_per_day": STANDARD_NEW_CARDS_PER_DAY,
            "standard_review_capacity_per_day": STANDARD_REVIEW_CAPACITY_PER_DAY,
            "standard_session_cards": STANDARD_SESSION_CARDS,
            "standard_sessions_per_day": STANDARD_SESSIONS_PER_DAY,
            "standard_notification_slots_per_day": STANDARD_NOTIFICATION_SLOTS_PER_DAY,
            "audit_events_per_day": AUDIT_EVENTS_PER_DAY,
            "review_capacity_source": "P3.14 standard quality-bench assumption",
        },
        "integrity_check": integrity,
        "foreign_key_violation_count": len(foreign_keys),
        "file_bytes": file_bytes,
        "page_count": page_count,
        "page_size": page_size,
        "bytes_per_day": round(bytes_per_day, 2),
        "mib_per_year": round(bytes_per_day * 365 / (1024 * 1024), 3),
        "row_counts": row_counts,
        "elapsed_s": round(perf_counter() - started, 3),
        "derived_counts": {
            "progress_cards": progress_count,
            "review_events": review_count,
            "session_items": session_item_count,
            "notification_slots": notification_count,
        },
    }


async def _content_scale(root: Path, *, card_count: int) -> dict[str, Any]:
    item_ids = tuple(f"locklearn:item:p6-7-{index:05d}" for index in range(card_count))
    package = content_db_helpers.create_package(
        root / "p6-7-scale-package.db",
        "p6-7-scale",
        active_item_ids=item_ids,
    )
    package_bytes = package.stat().st_size
    storage = locklearn_storage.SQLiteStorage(
        locklearn_storage.StoragePaths(
            root / "state" / "state.db",
            root / "content" / "current.db",
        )
    )
    await storage.async_open()
    try:
        candidate = storage.paths.content_staging_dir / "p6-7-scale.next.db"
        free_before = shutil.disk_usage(storage.paths.content_root).free
        build_started = perf_counter()
        result = await storage.async_build_content_generation(
            (package,),
            candidate,
            generation_id="p6-7-scale",
        )
        build_s = perf_counter() - build_started
        candidate_bytes = candidate.stat().st_size
        required_free = storage_budget.activation_required_free_disk(candidate_bytes)
        activation_started = perf_counter()
        await storage.async_activate_content_generation(candidate)
        activation_s = perf_counter() - activation_started
        scale = max(1, card_count / 10_000)
        return {
            "card_count": card_count,
            "package_bytes": package_bytes,
            "candidate_bytes": candidate_bytes,
            "active_content_bytes": storage.content_generations.active_path.stat().st_size,
            "build_s": round(build_s, 3),
            "activation_s": round(activation_s, 3),
            "build_ms_per_10k_cards": round(build_s * 1000 / scale, 3),
            "activation_ms_per_10k_cards": round(activation_s * 1000 / scale, 3),
            "active_item_count": result.active_item_count,
            "active_card_count": result.active_card_count,
            "max_database_count": result.max_database_count,
            "free_bytes_before": free_before,
            "required_free_disk_bytes": required_free,
            "free_space_gate_pass": free_before >= required_free,
        }
    finally:
        await storage.async_close()


async def _run(card_count: int, state_days: int) -> dict[str, Any]:
    observability.INTERNAL_METRICS.clear()
    hot_paths = await p5_9_performance._run()
    with tempfile.TemporaryDirectory(prefix="locklearn-p6-7-") as temporary:
        root = Path(temporary)
        state_projection = _project_five_year_state(
            root / "projection" / "state.db",
            days=state_days,
        )
        content_scale = await _content_scale(root / "content-scale", card_count=card_count)
        filesystem = shutil.disk_usage(root)
    return {
        "hardware": _hardware(),
        "filesystem": {
            "total_bytes": filesystem.total,
            "free_bytes": filesystem.free,
        },
        "normative_budgets": {
            "session_answer_p95_ms": p5_9_performance.SESSION_ANSWER_P95_BUDGET_MS,
            "next_card_p95_ms": p5_9_performance.NEXT_CARD_P95_BUDGET_MS,
            "scheduler_day_p95_ms": p5_9_performance.SCHEDULER_DAY_P95_BUDGET_MS,
            "official_dataset_artifact_default_max_bytes": (
                storage_budget.OFFICIAL_DATASET_ARTIFACT_DEFAULT_MAX_BYTES
            ),
            "dataset_cache_warning_default_bytes": storage_budget.DATASET_CACHE_WARNING_DEFAULT_BYTES,
            "activation_safety_margin_bytes": storage_budget.ACTIVATION_SAFETY_MARGIN_DEFAULT_BYTES,
            "activation_policy": "free >= 2x generated content + configured safety margin",
        },
        "hot_paths": hot_paths,
        "content_scale": content_scale,
        "state_projection": state_projection,
        "internal_metrics": observability.INTERNAL_METRICS.snapshot(),
    }


def _passes(result: dict[str, Any]) -> bool:
    hot = result["hot_paths"]
    content = result["content_scale"]
    state = result["state_projection"]
    return (
        float(hot["session_answer_p95_ms"])
        < p5_9_performance.SESSION_ANSWER_P95_BUDGET_MS
        and float(hot["next_card_p95_ms"])
        < p5_9_performance.NEXT_CARD_P95_BUDGET_MS
        and float(hot["scheduler_day_p95_ms"])
        < p5_9_performance.SCHEDULER_DAY_P95_BUDGET_MS
        and bool(content["free_space_gate_pass"])
        and state["integrity_check"] == "ok"
        and int(state["foreign_key_violation_count"]) == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--card-count", type=int, default=REFERENCE_CARD_COUNT)
    parser.add_argument("--state-days", type=int, default=STATE_DAYS)
    args = parser.parse_args()
    if args.card_count <= 0 or args.state_days <= 0:
        parser.error("--card-count and --state-days must be positive")
    result = asyncio.run(_run(args.card_count, args.state_days))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if _passes(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
