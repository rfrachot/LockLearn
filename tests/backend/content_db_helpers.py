"""Small normalized content-package fixtures for storage tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from custom_components.locklearn.core.content import (
    derive_card_definition_id,
    derive_card_key,
)
from custom_components.locklearn.storage import initialize_content_database

DATASET_ID = "locklearn:dataset:test"
SOURCE_ID = "locklearn:source:test"
CONCEPT_ID = "locklearn:concept:test"
TERM_ID = "locklearn:term:test"
TAG_ID = "locklearn:tag:level-one"
PACK_ID = "locklearn:pack:test"
ITEM_A = "locklearn:item:a"
ITEM_B = "locklearn:item:b"


def facet_ids(item_id: str) -> tuple[str, str]:
    """Return stable prompt/answer facet IDs for a fixture item."""
    suffix = item_id.rsplit(":", 1)[-1]
    return f"locklearn:facet:{suffix}:prompt", f"locklearn:facet:{suffix}:answer"


def card_identity(item_id: str) -> tuple[str, str]:
    """Return card_definition_id and card_key for a fixture item."""
    prompt_id, answer_id = facet_ids(item_id)
    return (
        derive_card_definition_id(item_id, prompt_id, answer_id),
        derive_card_key(item_id, prompt_id, answer_id),
    )


def create_package(
    path: Path,
    version: str,
    *,
    active_item_ids: tuple[str, ...] = (ITEM_A,),
    superseded: tuple[tuple[str, str], ...] = (),
) -> Path:
    """Create one tiny self-contained package using the normalized content schema."""
    initialize_content_database(path)
    dataset_version_id = f"locklearn:dataset-version:{version}"
    package_id = f"locklearn:package:{version}"
    pack_version_id = f"locklearn:pack-version:{version}"
    all_item_ids = tuple(dict.fromkeys((*active_item_ids, *(old for old, _ in superseded))))

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """INSERT INTO licenses VALUES (
                   'CC-BY-SA-4.0', 'CC-BY-SA-4.0',
                   'Creative Commons Attribution-ShareAlike 4.0 International', '4.0',
                   1, 1, 1, 1, 'https://creativecommons.org/licenses/by-sa/4.0/',
                   'Synthetic test license'
               )"""
        )
        connection.execute(
            """INSERT INTO sources VALUES (
                   ?, 'Test source', 'LockLearn tests', 'https://example.invalid/source',
                   'CC-BY-SA-4.0', 'Test source attribution', 'test_adapter',
                   'release-driven', 1, 'Synthetic source'
               )""",
            (SOURCE_ID,),
        )
        connection.execute(
            """INSERT INTO source_snapshots VALUES (
                   ?, ?, ?, NULL, '2026-09-22T10:00:00+00:00',
                   'https://example.invalid/source/snapshot', ?, '1.0.0'
               )""",
            (
                f"locklearn:snapshot:{version}",
                SOURCE_ID,
                version,
                "0" * 64,
            ),
        )
        connection.execute("INSERT INTO datasets VALUES (?)", (DATASET_ID,))
        connection.execute("INSERT INTO dataset_sources VALUES (?, ?)", (DATASET_ID, SOURCE_ID))
        connection.execute(
            "INSERT INTO dataset_licenses VALUES (?, 'CC-BY-SA-4.0', 'dataset')",
            (DATASET_ID,),
        )
        connection.execute(
            "INSERT INTO dataset_versions VALUES (?, ?, ?, ?, ?)",
            (dataset_version_id, DATASET_ID, version, "2026-09-22T12:00:00+00:00", version * 8),
        )
        connection.execute(
            "INSERT INTO dataset_packages VALUES (?, ?, ?, ?, ?)",
            (
                package_id,
                DATASET_ID,
                dataset_version_id,
                "2026-09-22T12:00:00+00:00",
                version * 8,
            ),
        )
        connection.execute(
            """INSERT INTO provenance_records VALUES (
                   ?, ?, 'dataset', ?, ?, 'CC-BY-SA-4.0', 'dataset',
                   NULL, NULL, NULL, 1, 'Synthetic dataset provenance'
               )""",
            (
                "locklearn:provenance:test-dataset-source",
                DATASET_ID,
                DATASET_ID,
                f"locklearn:snapshot:{version}",
            ),
        )
        connection.execute(
            "INSERT INTO concepts VALUES (?, ?, ?, 'record-1', NULL, 'lexical')",
            (CONCEPT_ID, DATASET_ID, SOURCE_ID),
        )
        connection.execute(
            "INSERT INTO terms VALUES (?, ?, 'en', 'Latn', ?, ?, 1)",
            (TERM_ID, DATASET_ID, f"term-{version}", f"term-{version}"),
        )
        connection.execute("INSERT INTO concept_terms VALUES (?, ?)", (CONCEPT_ID, TERM_ID))
        connection.execute("INSERT INTO tags VALUES (?, 'Level one')", (TAG_ID,))

        for item_id in all_item_ids:
            connection.execute(
                """INSERT INTO learning_items(
                       learning_item_id, dataset_id, content_type, register,
                       lifecycle_status, superseded_by_learning_item_id
                   ) VALUES (?, ?, 'vocabulary', NULL, 'active', NULL)""",
                (item_id, DATASET_ID),
            )
            connection.execute(
                "INSERT INTO learning_item_concepts VALUES (?, ?)", (item_id, CONCEPT_ID)
            )

        for item_id in active_item_ids:
            prompt_id, answer_id = facet_ids(item_id)
            card_id, card_key = card_identity(item_id)
            connection.executemany(
                """INSERT INTO facets(
                       facet_id, learning_item_id, kind, facet_key, language_tag, script,
                       lifecycle_status, superseded_by_facet_id
                   ) VALUES (?, ?, 'text', ?, 'en', 'Latn', 'active', NULL)""",
                ((prompt_id, item_id, "prompt"), (answer_id, item_id, "answer")),
            )
            connection.execute(
                """INSERT INTO card_definitions(
                       card_definition_id, card_key, learning_item_id,
                       prompt_facet_id, answer_facet_id, answer_semantics,
                       grading_policy_kind, grading_policy_version,
                       lifecycle_status, superseded_by_card_definition_id
                   ) VALUES (?, ?, ?, ?, ?, 'single_value', 'exact', 1, 'active', NULL)""",
                (card_id, card_key, item_id, prompt_id, answer_id),
            )
            connection.execute(
                """INSERT INTO content_blocks VALUES (
                       ?, ?, 0, 'text', 'prompt', 0, 'none', ?
                   )""",
                (f"locklearn:block:{item_id.rsplit(':', 1)[-1]}", item_id, '{"text":"prompt"}'),
            )
            connection.execute("INSERT INTO learning_item_tags VALUES (?, ?)", (item_id, TAG_ID))

        connection.execute("INSERT INTO packs VALUES (?, ?, 'Test pack')", (PACK_ID, DATASET_ID))
        connection.execute(
            "INSERT INTO pack_versions VALUES (?, ?, ?, NULL)",
            (pack_version_id, PACK_ID, version),
        )
        connection.executemany(
            "INSERT INTO pack_items VALUES (?, ?, ?)",
            (
                (pack_version_id, item_id, position)
                for position, item_id in enumerate(active_item_ids)
            ),
        )
        for old_id, replacement_id in superseded:
            connection.execute(
                """UPDATE learning_items
                   SET lifecycle_status = 'superseded',
                       superseded_by_learning_item_id = ?
                   WHERE learning_item_id = ?""",
                (replacement_id, old_id),
            )
            connection.execute(
                """INSERT INTO tombstones(
                       object_type, stable_id, dataset_id, lifecycle_status,
                       replacement_id, status_since_generation_id
                   ) VALUES ('learning_item', ?, ?, 'superseded', ?, 'package')""",
                (old_id, DATASET_ID, replacement_id),
            )
        connection.commit()
    return path
