"""Reviewed P1.10 Japanese Starter recipe using only LockLearn-authored content."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping

from custom_components.locklearn.core.content import (
    derive_card_definition_id,
    derive_card_key,
    make_stable_id,
)
from datasets.adapters import NormalizedRecord
from datasets.pipeline import BuildContext, DatasetBuildError

DATASET_ID = "locklearn:dataset:japanese-starter"
PACK_ID = "locklearn:pack:japanese-starter"
PACK_VERSION_ID = "locklearn:pack-version:japanese-starter-1.0.0"
CURATION_POLICY_ID = "locklearn:curation:japanese-default"


class JapaneseStarterRecipe:
    """Materialize the tiny offline first-run Japanese demonstration pack."""

    recipe_id = "locklearn:japanese-starter"
    recipe_version = "1"

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        if context.dataset_id != DATASET_ID:
            raise DatasetBuildError("Japanese Starter recipe received the wrong dataset_id")

        _insert_tags(connection)
        connection.execute(
            "INSERT INTO packs(pack_id, dataset_id, name) VALUES (?, ?, ?)",
            (PACK_ID, DATASET_ID, "Japanese Starter"),
        )
        connection.execute(
            """INSERT INTO pack_versions(
                   pack_version_id, pack_id, version, curation_policy_id
               ) VALUES (?, ?, '1.0.0', ?)""",
            (PACK_VERSION_ID, PACK_ID, CURATION_POLICY_ID),
        )

        item_count = 0
        card_count = 0
        pack_record = None
        for record in context.iter_records("locklearn:original"):
            if record.kind == "pack_metadata":
                pack_record = record
                continue
            if record.kind == "kana":
                cards = _materialize_kana(connection, context, record, item_count)
            elif record.kind == "word_reading":
                cards = _materialize_word(connection, context, record, item_count)
            else:
                raise DatasetBuildError(f"unsupported Japanese Starter record kind: {record.kind}")
            item_count += 1
            card_count += cards

        if pack_record is None:
            raise DatasetBuildError("Japanese Starter source is missing pack metadata")
        context.insert_provenance(
            connection,
            record=pack_record,
            object_type="pack",
            object_id=PACK_ID,
            license_scope="editorial",
            attribution_text="LockLearn contributors — CC BY-SA 4.0",
        )
        if item_count != 120 or card_count != 240:
            raise DatasetBuildError(
                f"Japanese Starter expected 120 items/240 cards, got {item_count}/{card_count}"
            )
        return {
            "learning_items": item_count,
            "cards": card_count,
            "packs": 1,
            "pack_versions": 1,
        }


def _materialize_kana(
    connection: sqlite3.Connection,
    context: BuildContext,
    record: NormalizedRecord,
    position: int,
) -> int:
    glyph = _payload_string(record.payload, "glyph")
    romaji = _payload_string(record.payload, "romaji")
    script = _payload_string(record.payload, "script")
    group = _payload_string(record.payload, "group")
    return _materialize_pair(
        connection,
        context,
        record=record,
        position=position,
        left_text=glyph,
        left_key="glyph",
        left_language="ja",
        left_script=script,
        right_text=romaji,
        right_key="romaji",
        right_language="ja-Latn",
        right_script="Latn",
        concept_type="pedagogical",
        content_type="custom",
        tag_ids=("locklearn:tag:kana", f"locklearn:tag:{group}"),
    )


def _materialize_word(
    connection: sqlite3.Connection,
    context: BuildContext,
    record: NormalizedRecord,
    position: int,
) -> int:
    written = _payload_string(record.payload, "written")
    reading = _payload_string(record.payload, "reading")
    return _materialize_pair(
        connection,
        context,
        record=record,
        position=position,
        left_text=written,
        left_key="term",
        left_language="ja",
        left_script="Jpan",
        right_text=reading,
        right_key="reading",
        right_language="ja",
        right_script="Hira",
        concept_type="lexical",
        content_type="vocabulary",
        tag_ids=("locklearn:tag:vocabulary", "locklearn:tag:contextual-reading"),
    )


def _materialize_pair(
    connection: sqlite3.Connection,
    context: BuildContext,
    *,
    record: NormalizedRecord,
    position: int,
    left_text: str,
    left_key: str,
    left_language: str,
    left_script: str,
    right_text: str,
    right_key: str,
    right_language: str,
    right_script: str,
    concept_type: str,
    content_type: str,
    tag_ids: tuple[str, ...],
) -> int:
    item_id = make_stable_id("locklearn", "starter-item", record.source_record_id)
    concept_id = make_stable_id("locklearn", "starter-concept", record.source_record_id)
    left_term_id = make_stable_id("locklearn", "starter-term", record.source_record_id, left_key)
    right_term_id = make_stable_id("locklearn", "starter-term", record.source_record_id, right_key)
    left_facet_id = make_stable_id("locklearn", "starter-facet", record.source_record_id, left_key)
    right_facet_id = make_stable_id(
        "locklearn", "starter-facet", record.source_record_id, right_key
    )

    connection.execute(
        """INSERT INTO concepts(
               concept_id, dataset_id, source_id, source_record_id, source_sense_id, concept_type
           ) VALUES (?, ?, 'locklearn:original', ?, NULL, ?)""",
        (concept_id, DATASET_ID, record.source_record_id, concept_type),
    )
    connection.executemany(
        """INSERT INTO terms(
               term_id, dataset_id, language_tag, script, text,
               normalized_text, normalization_version
           ) VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (
            (left_term_id, DATASET_ID, left_language, left_script, left_text, left_text),
            (right_term_id, DATASET_ID, right_language, right_script, right_text, right_text),
        ),
    )
    connection.executemany(
        "INSERT INTO concept_terms(concept_id, term_id) VALUES (?, ?)",
        ((concept_id, left_term_id), (concept_id, right_term_id)),
    )
    connection.execute(
        """INSERT INTO learning_items(
               learning_item_id, dataset_id, content_type, register,
               lifecycle_status, superseded_by_learning_item_id
           ) VALUES (?, ?, ?, NULL, 'active', NULL)""",
        (item_id, DATASET_ID, content_type),
    )
    connection.execute(
        "INSERT INTO learning_item_concepts(learning_item_id, concept_id) VALUES (?, ?)",
        (item_id, concept_id),
    )
    connection.executemany(
        """INSERT INTO facets(
               facet_id, learning_item_id, kind, facet_key, language_tag, script,
               lifecycle_status, superseded_by_facet_id
           ) VALUES (?, ?, 'text', ?, ?, ?, 'active', NULL)""",
        (
            (left_facet_id, item_id, left_key, left_language, left_script),
            (right_facet_id, item_id, right_key, right_language, right_script),
        ),
    )

    cards = (
        _insert_card(connection, item_id, left_facet_id, right_facet_id),
        _insert_card(connection, item_id, right_facet_id, left_facet_id),
    )
    left_block_id = make_stable_id(
        "locklearn", "starter-block", record.source_record_id, "prompt"
    )
    right_block_id = make_stable_id(
        "locklearn", "starter-block", record.source_record_id, "answer"
    )
    connection.executemany(
        """INSERT INTO content_blocks(
               content_block_id, learning_item_id, position, kind, role,
               reveals_answer, mask_strategy, payload_json
           ) VALUES (?, ?, ?, 'text', ?, ?, 'none', ?)""",
        (
            (
                left_block_id,
                item_id,
                0,
                "prompt",
                0,
                json.dumps({"text": left_text}, ensure_ascii=False, separators=(",", ":")),
            ),
            (
                right_block_id,
                item_id,
                1,
                "answer",
                1,
                json.dumps({"text": right_text}, ensure_ascii=False, separators=(",", ":")),
            ),
        ),
    )
    for tag_id in tag_ids:
        connection.execute(
            "INSERT INTO learning_item_tags(learning_item_id, tag_id) VALUES (?, ?)",
            (item_id, tag_id),
        )
    connection.execute(
        "INSERT INTO pack_items(pack_version_id, learning_item_id, position) VALUES (?, ?, ?)",
        (PACK_VERSION_ID, item_id, position),
    )
    connection.executemany(
        """INSERT INTO pack_item_card_defaults(
               pack_version_id, learning_item_id, card_key, enabled_by_default
           ) VALUES (?, ?, ?, 1)""",
        ((PACK_VERSION_ID, item_id, card_key) for _card_id, card_key in cards),
    )

    for object_type, object_id in (
        ("concept", concept_id),
        ("term", left_term_id),
        ("term", right_term_id),
        ("learning_item", item_id),
        ("content_block", left_block_id),
        ("content_block", right_block_id),
    ):
        context.insert_provenance(
            connection,
            record=record,
            object_type=object_type,
            object_id=object_id,
            license_scope="editorial",
            attribution_text="LockLearn contributors — CC BY-SA 4.0",
        )
    return len(cards)


def _insert_card(
    connection: sqlite3.Connection,
    item_id: str,
    prompt_facet_id: str,
    answer_facet_id: str,
) -> tuple[str, str]:
    card_id = derive_card_definition_id(item_id, prompt_facet_id, answer_facet_id)
    card_key = derive_card_key(item_id, prompt_facet_id, answer_facet_id)
    connection.execute(
        """INSERT INTO card_definitions(
               card_definition_id, card_key, learning_item_id,
               prompt_facet_id, answer_facet_id, answer_semantics,
               grading_policy_kind, grading_policy_version,
               lifecycle_status, superseded_by_card_definition_id
           ) VALUES (?, ?, ?, ?, ?, 'single_value', 'exact', 1, 'active', NULL)""",
        (card_id, card_key, item_id, prompt_facet_id, answer_facet_id),
    )
    return card_id, card_key


def _insert_tags(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT INTO tags(tag_id, label) VALUES (?, ?)",
        (
            ("locklearn:tag:kana", "Kana"),
            ("locklearn:tag:hiragana", "Hiragana"),
            ("locklearn:tag:katakana", "Katakana"),
            ("locklearn:tag:yoon", "Yōon"),
            ("locklearn:tag:vocabulary", "Vocabulary"),
            ("locklearn:tag:contextual-reading", "Contextual reading"),
        ),
    )


def _payload_string(payload: Mapping[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise DatasetBuildError(f"Japanese Starter field {field} must be a non-empty string")
    return value
