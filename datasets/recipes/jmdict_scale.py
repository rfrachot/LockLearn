"""Qualification recipe for a bounded, source-native JMdict vocabulary corpus."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

from custom_components.locklearn.core.content import (
    derive_card_definition_id,
    derive_card_key,
    make_stable_id,
)
from datasets.adapters import NormalizedRecord
from datasets.pipeline import BuildContext, DatasetBuildError

DATASET_ID = "locklearn:dataset:jmdict-scale"
PACK_ID = "locklearn:pack:jmdict-scale"
PACK_VERSION_ID = "locklearn:pack:jmdict-scale:version:2026.09"
MAX_LEARNING_ITEMS = 20_000


class JMdictScaleRecipe:
    """Materialize a reproducible, bounded JMdict qualification pack.

    One LearningItem represents one JMdict entry/sense pair.  JMdict's
    ``ent_seq`` identifies an entry, so the source sense index is part of the
    source-native identity used by this recipe; display text never participates
    in a stable ID.
    """

    recipe_id = "locklearn:jmdict-scale"
    recipe_version = "1"

    def materialize(
        self,
        connection: sqlite3.Connection,
        context: BuildContext,
    ) -> Mapping[str, int]:
        if context.dataset_id != DATASET_ID:
            raise DatasetBuildError("JMdict scale recipe received the wrong dataset_id")

        connection.executemany(
            "INSERT INTO tags(tag_id, label) VALUES (?, ?)",
            (
                ("locklearn:tag:jmdict", "JMdict"),
                ("locklearn:tag:japanese-vocabulary", "Japanese vocabulary"),
            ),
        )
        connection.execute(
            "INSERT INTO packs(pack_id, dataset_id, name) VALUES (?, ?, ?)",
            (PACK_ID, DATASET_ID, "JMdict Scale Qualification"),
        )
        connection.execute(
            """INSERT INTO pack_versions(
                   pack_version_id, pack_id, version, curation_policy_id
               ) VALUES (?, ?, '2026.09', NULL)""",
            (PACK_VERSION_ID, PACK_ID),
        )

        counts = {
            "concepts": 0,
            "terms": 0,
            "learning_items": 0,
            "facets": 0,
            "cards": 0,
        }
        first_record: NormalizedRecord | None = None
        for record in context.iter_records("edrdg:jmdict"):
            if counts["learning_items"] >= MAX_LEARNING_ITEMS:
                break
            if record.kind != "jmdict_sense":
                raise DatasetBuildError(f"unsupported JMdict record kind: {record.kind}")
            if first_record is None:
                first_record = record
            sense_index = _payload_int(record.payload, "sense_metadata", "sense_index")
            identity = f"{record.source_record_id}-sense-{sense_index}"
            materialized = _materialize_item(
                connection,
                context,
                record=record,
                identity=identity,
                position=counts["learning_items"],
            )
            for key, value in materialized.items():
                counts[key] += value

        if first_record is None or counts["learning_items"] == 0:
            raise DatasetBuildError("JMdict scale source produced no materializable senses")
        context.insert_provenance(
            connection,
            record=first_record,
            object_type="pack",
            object_id=PACK_ID,
            license_scope="dataset",
            attribution_text="JMdict/EDRDG contributors — CC BY-SA 4.0",
        )
        counts.update({"packs": 1, "pack_versions": 1})
        return counts


def _materialize_item(
    connection: sqlite3.Connection,
    context: BuildContext,
    *,
    record: NormalizedRecord,
    identity: str,
    position: int,
) -> dict[str, int]:
    forms = _payload_strings(record.payload, "japanese_forms")
    readings = _payload_strings(record.payload, "readings")
    glosses = _payload_strings(record.payload, "english_glosses")
    japanese = forms[0] if forms else readings[0] if readings else ""
    reading = readings[0] if readings else ""
    meaning = " · ".join(glosses)
    if not japanese or not reading or not meaning:
        raise DatasetBuildError(f"JMdict sense is missing required content: {identity}")

    concept_id = make_stable_id("edrdg", "jmdict-concept", identity)
    item_id = make_stable_id("edrdg", "jmdict-item", identity)
    japanese_term_id = make_stable_id("edrdg", "jmdict-term", identity, "japanese")
    meaning_term_id = make_stable_id("edrdg", "jmdict-term", identity, "meaning-en")
    japanese_facet_id = make_stable_id("edrdg", "jmdict-facet", identity, "japanese")
    meaning_facet_id = make_stable_id("edrdg", "jmdict-facet", identity, "meaning-en")

    connection.execute(
        """INSERT INTO concepts(
               concept_id, dataset_id, source_id, source_record_id,
               source_sense_id, concept_type
           ) VALUES (?, ?, 'edrdg:jmdict', ?, ?, 'lexical')""",
        (
            concept_id,
            DATASET_ID,
            record.source_record_id,
            str(_payload_int(record.payload, "sense_metadata", "sense_index")),
        ),
    )
    connection.executemany(
        """INSERT INTO terms(
               term_id, dataset_id, language_tag, script, text,
               normalized_text, normalization_version
           ) VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (
            (japanese_term_id, DATASET_ID, "ja", "Jpan", japanese, japanese),
            (meaning_term_id, DATASET_ID, "en", "Latn", meaning, meaning),
        ),
    )
    connection.executemany(
        "INSERT INTO concept_terms(concept_id, term_id) VALUES (?, ?)",
        ((concept_id, japanese_term_id), (concept_id, meaning_term_id)),
    )
    connection.execute(
        """INSERT INTO learning_items(
               learning_item_id, dataset_id, content_type, register,
               lifecycle_status, superseded_by_learning_item_id
           ) VALUES (?, ?, 'vocabulary', NULL, 'active', NULL)""",
        (item_id, DATASET_ID),
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
            (japanese_facet_id, item_id, "japanese", "ja", "Jpan"),
            (meaning_facet_id, item_id, "meaning-en", "en", "Latn"),
        ),
    )

    cards = (
        _insert_card(connection, item_id, japanese_facet_id, meaning_facet_id),
        _insert_card(connection, item_id, meaning_facet_id, japanese_facet_id),
    )
    block_prefix = make_stable_id("edrdg", "jmdict-block", identity)
    connection.executemany(
        """INSERT INTO content_blocks(
               content_block_id, learning_item_id, position, kind, role,
               reveals_answer, mask_strategy, payload_json
           ) VALUES (?, ?, ?, 'text', ?, ?, 'none', ?)""",
        (
            (
                f"{block_prefix}:japanese",
                item_id,
                0,
                "prompt",
                0,
                json.dumps(
                    {"text": japanese, "reading": reading},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            ),
            (
                f"{block_prefix}:meaning-en",
                item_id,
                1,
                "answer",
                1,
                json.dumps({"text": meaning}, ensure_ascii=False, separators=(",", ":")),
            ),
        ),
    )
    connection.execute(
        "INSERT INTO learning_item_tags(learning_item_id, tag_id) VALUES (?, ?)",
        (item_id, "locklearn:tag:jmdict"),
    )
    connection.execute(
        "INSERT INTO learning_item_tags(learning_item_id, tag_id) VALUES (?, ?)",
        (item_id, "locklearn:tag:japanese-vocabulary"),
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

    provenance_objects = (
        ("concept", concept_id),
        ("term", japanese_term_id),
        ("term", meaning_term_id),
        ("learning_item", item_id),
        ("content_block", f"{block_prefix}:japanese"),
        ("content_block", f"{block_prefix}:meaning-en"),
    )
    for object_type, object_id in provenance_objects:
        context.insert_provenance(
            connection,
            record=record,
            object_type=object_type,
            object_id=object_id,
            license_scope="dataset",
            attribution_text="JMdict/EDRDG contributors — CC BY-SA 4.0",
        )
    return {
        "concepts": 1,
        "terms": 2,
        "learning_items": 1,
        "facets": 2,
        "cards": 2,
    }


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


def _payload_strings(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise DatasetBuildError(f"JMdict payload field {key} must be a non-empty string list")
    return tuple(value)


def _payload_int(payload: Mapping[str, Any], parent_key: str, key: str) -> int:
    parent = payload.get(parent_key)
    if not isinstance(parent, Mapping):
        raise DatasetBuildError(f"JMdict payload field {parent_key} must be an object")
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DatasetBuildError(f"JMdict payload field {parent_key}.{key} must be positive")
    return value
