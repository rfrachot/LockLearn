"""Immutable content generations, validation, activation, and reader leases."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import uuid
from collections.abc import Iterable
from concurrent.futures import Executor
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..const import CONTENT_SCHEMA_VERSION
from ..core.content import derive_card_definition_id, derive_card_key, validate_stable_id
from ..core.content_blocks import (
    ContentBlock,
    ContentBlockKind,
    ContentPayload,
    ContentRole,
    MaskStrategy,
    MediaReference,
    RubySegment,
    TextContent,
    parse_rich_text_ast,
)
from .schema import (
    CONTENT_REQUIRED_INDEXES,
    CONTENT_REQUIRED_TABLES,
    CONTENT_SCHEMA,
)

_GENERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ContentGenerationError(RuntimeError):
    """Base error for generated content catalogs."""


class ContentValidationError(ContentGenerationError):
    """Raised when a package or candidate generation is not safe to use."""


class ContentActivationError(ContentGenerationError):
    """Raised when a generation cannot be activated atomically."""


@dataclass(frozen=True, slots=True)
class GenerationMetadata:
    """Immutable identity and build facts stored inside one generation."""

    generation_id: str
    content_schema_version: int
    built_at_utc: str
    parent_generation_id: str | None
    package_count: int
    package_set_hash: str


@dataclass(frozen=True, slots=True)
class PackageMetadata:
    """The one dataset package declared by a package database."""

    package_id: str
    dataset_id: str
    dataset_version_id: str
    built_at_utc: str
    canonical_content_hash: str
    path: Path


@dataclass(frozen=True, slots=True)
class ContentBuildResult:
    """Observable result of a complete validated generation build."""

    path: Path
    metadata: GenerationMetadata
    active_item_count: int
    active_card_count: int
    max_database_count: int


def _read_only_uri(path: Path, *, immutable: bool = False) -> str:
    query = "mode=ro"
    if immutable:
        query += "&immutable=1"
    return f"{path.resolve().as_uri()}?{query}"


def initialize_content_database(path: Path) -> None:
    """Create an empty normalized package/catalog database for build tooling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(CONTENT_SCHEMA)
        connection.execute(
            "INSERT OR REPLACE INTO schema_version(singleton, version) VALUES (1, ?)",
            (CONTENT_SCHEMA_VERSION,),
        )
        connection.commit()
    finally:
        connection.close()


class ContentGenerationValidator:
    """Validate schema, integrity, lifecycle, and stable card identities."""

    def validate_package(self, path: Path) -> PackageMetadata:
        """Validate one normalized prebuilt dataset package."""
        with sqlite3.connect(_read_only_uri(path, immutable=True), uri=True) as connection:
            self._validate_common(connection, path)
            if connection.execute("SELECT COUNT(*) FROM generation_metadata").fetchone()[0] != 0:
                raise ContentValidationError("a dataset package cannot declare generation metadata")
            rows = connection.execute(
                """SELECT package_id, dataset_id, dataset_version_id, built_at_utc,
                          canonical_content_hash
                   FROM dataset_packages"""
            ).fetchall()
            if len(rows) != 1:
                raise ContentValidationError("a package database must declare exactly one dataset")
            row = rows[0]
            dataset_id = str(row[1])
            mismatched = connection.execute(
                "SELECT COUNT(*) FROM learning_items WHERE dataset_id != ?",
                (dataset_id,),
            ).fetchone()[0]
            if mismatched:
                raise ContentValidationError("package learning items must belong to its dataset")
            self._validate_cards(connection)
            self._validate_stable_ids(connection)
            self._validate_id_migrations(connection, require_card_coverage=False)
            self._validate_content_blocks(connection)
            self._validate_tombstones(connection)
            return PackageMetadata(
                package_id=str(row[0]),
                dataset_id=dataset_id,
                dataset_version_id=str(row[2]),
                built_at_utc=str(row[3]),
                canonical_content_hash=str(row[4]),
                path=path,
            )

    def validate_generation(
        self, path: Path, *, expected_generation_id: str | None = None
    ) -> GenerationMetadata:
        """Validate a complete candidate before it may become active."""
        with sqlite3.connect(_read_only_uri(path, immutable=True), uri=True) as connection:
            self._validate_common(connection, path)
            rows = connection.execute(
                """SELECT generation_id, content_schema_version, built_at_utc,
                          parent_generation_id, package_count, package_set_hash
                   FROM generation_metadata"""
            ).fetchall()
            if len(rows) != 1:
                raise ContentValidationError("a generated catalog needs one metadata row")
            row = rows[0]
            metadata = GenerationMetadata(
                generation_id=str(row[0]),
                content_schema_version=int(row[1]),
                built_at_utc=str(row[2]),
                parent_generation_id=None if row[3] is None else str(row[3]),
                package_count=int(row[4]),
                package_set_hash=str(row[5]),
            )
            _validate_generation_id(metadata.generation_id)
            if (
                expected_generation_id is not None
                and metadata.generation_id != expected_generation_id
            ):
                raise ContentValidationError("candidate generation_id does not match its target")
            if metadata.content_schema_version != CONTENT_SCHEMA_VERSION:
                raise ContentValidationError(
                    "generation metadata has an unsupported schema version"
                )
            package_count = connection.execute("SELECT COUNT(*) FROM dataset_packages").fetchone()[
                0
            ]
            if package_count != metadata.package_count:
                raise ContentValidationError("generation package_count does not match its catalog")
            package_rows = connection.execute(
                """SELECT dataset_id, dataset_version_id, canonical_content_hash
                   FROM dataset_packages ORDER BY dataset_id"""
            ).fetchall()
            if _package_rows_hash(package_rows) != metadata.package_set_hash:
                raise ContentValidationError(
                    "generation package_set_hash does not match its catalog"
                )
            self._validate_cards(connection)
            self._validate_stable_ids(connection)
            self._validate_id_migrations(connection, require_card_coverage=True)
            self._validate_content_blocks(connection)
            self._validate_tombstones(connection)
            self._validate_preaggregates(connection)
            return metadata

    @staticmethod
    def _validate_common(connection: sqlite3.Connection, path: Path) -> None:
        try:
            integrity = [str(row[0]) for row in connection.execute("PRAGMA integrity_check")]
        except sqlite3.DatabaseError as err:
            raise ContentValidationError(f"invalid SQLite content database: {path}") from err
        if integrity != ["ok"]:
            raise ContentValidationError(f"content integrity_check failed: {integrity!r}")
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_keys:
            raise ContentValidationError("content database has foreign-key violations")
        row = connection.execute(
            "SELECT version FROM schema_version WHERE singleton = 1"
        ).fetchone()
        if row is None or int(row[0]) != CONTENT_SCHEMA_VERSION:
            found = None if row is None else row[0]
            raise ContentValidationError(f"unsupported content schema version: {found!r}")
        objects = connection.execute(
            "SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index')"
        ).fetchall()
        tables = {str(name) for object_type, name in objects if object_type == "table"}
        indexes = {str(name) for object_type, name in objects if object_type == "index"}
        if missing := CONTENT_REQUIRED_TABLES - tables:
            raise ContentValidationError(f"content database is missing tables: {sorted(missing)!r}")
        if missing := CONTENT_REQUIRED_INDEXES - indexes:
            raise ContentValidationError(
                f"content database is missing indexes: {sorted(missing)!r}"
            )

    @staticmethod
    def _validate_cards(connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            """SELECT card_definition_id, card_key, learning_item_id,
                      prompt_facet_id, answer_facet_id
               FROM card_definitions"""
        )
        for card_id, card_key, item_id, prompt_id, answer_id in rows:
            if str(card_key) != derive_card_key(str(item_id), str(prompt_id), str(answer_id)):
                raise ContentValidationError(f"invalid stable card_key: {card_key}")
            if str(card_id) != derive_card_definition_id(
                str(item_id), str(prompt_id), str(answer_id)
            ):
                raise ContentValidationError(f"invalid card_definition_id: {card_id}")
        cross_item = connection.execute(
            """SELECT COUNT(*)
               FROM card_definitions AS card
               JOIN facets AS prompt ON prompt.facet_id = card.prompt_facet_id
               JOIN facets AS answer ON answer.facet_id = card.answer_facet_id
               WHERE prompt.learning_item_id != card.learning_item_id
                  OR answer.learning_item_id != card.learning_item_id"""
        ).fetchone()[0]
        if cross_item:
            raise ContentValidationError("card facets must belong to their LearningItem")

    @staticmethod
    def _validate_stable_ids(connection: sqlite3.Connection) -> None:
        fields = (
            ("sources", "source_id"),
            ("datasets", "dataset_id"),
            ("dataset_versions", "dataset_version_id"),
            ("dataset_packages", "package_id"),
            ("concepts", "concept_id"),
            ("terms", "term_id"),
            ("learning_items", "learning_item_id"),
            ("facets", "facet_id"),
            ("card_definitions", "card_definition_id"),
            ("card_definitions", "card_key"),
            ("content_blocks", "content_block_id"),
            ("tags", "tag_id"),
            ("packs", "pack_id"),
            ("pack_versions", "pack_version_id"),
            ("confusable_groups", "confusable_group_id"),
            ("stable_id_migrations", "old_id"),
            ("stable_id_migrations", "new_id"),
        )
        for table, column in fields:
            for (value,) in connection.execute(f"SELECT {column} FROM {table}"):
                try:
                    validate_stable_id(str(value), field=column)
                except ValueError as err:
                    raise ContentValidationError(
                        f"invalid stable ID in {table}.{column}: {value!r}"
                    ) from err

    @staticmethod
    def _validate_id_migrations(
        connection: sqlite3.Connection, *, require_card_coverage: bool
    ) -> None:
        targets = {
            "concept": ("concepts", "concept_id"),
            "term": ("terms", "term_id"),
            "learning_item": ("learning_items", "learning_item_id"),
            "facet": ("facets", "facet_id"),
            "card_definition": ("card_definitions", "card_definition_id"),
            "card_key": ("card_definitions", "card_key"),
        }
        rows = connection.execute(
            "SELECT object_type, old_id, new_id FROM stable_id_migrations"
        ).fetchall()
        edges: dict[tuple[str, str], str] = {}
        for raw_type, raw_old, raw_new in rows:
            object_type, old_id, new_id = str(raw_type), str(raw_old), str(raw_new)
            table, column = targets[object_type]
            if (
                connection.execute(
                    f"SELECT 1 FROM {table} WHERE {column} = ?", (new_id,)
                ).fetchone()
                is None
            ):
                raise ContentValidationError(
                    f"ID migration target does not exist for {object_type}: {new_id}"
                )
            edges[(object_type, old_id)] = new_id
        for object_type, old_id in edges:
            visited = {old_id}
            current = old_id
            while (object_type, current) in edges:
                current = edges[(object_type, current)]
                if current in visited:
                    raise ContentValidationError(
                        f"cyclic stable ID migration for {object_type}: {old_id}"
                    )
                visited.add(current)

        if not require_card_coverage:
            return
        changed_items = {
            old_id
            for (object_type, old_id), _new in edges.items()
            if object_type == "learning_item"
        }
        changed_facets = {
            old_id for (object_type, old_id), _new in edges.items() if object_type == "facet"
        }
        if not changed_items and not changed_facets:
            return
        affected_cards: set[tuple[str, str]] = set()
        for item_id in changed_items:
            affected_cards.update(
                (str(card_id), str(card_key))
                for card_id, card_key in connection.execute(
                    """SELECT card_definition_id, card_key FROM card_definitions
                       WHERE learning_item_id = ?""",
                    (item_id,),
                )
            )
        for facet_id in changed_facets:
            affected_cards.update(
                (str(card_id), str(card_key))
                for card_id, card_key in connection.execute(
                    """SELECT card_definition_id, card_key FROM card_definitions
                       WHERE prompt_facet_id = ? OR answer_facet_id = ?""",
                    (facet_id, facet_id),
                )
            )
        for card_id, card_key in affected_cards:
            if ("card_definition", card_id) not in edges or ("card_key", card_key) not in edges:
                raise ContentValidationError(
                    "LearningItem/Facet ID migrations must map every affected "
                    "card_definition_id and card_key"
                )

    @staticmethod
    def _validate_content_blocks(connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            """SELECT content_block_id, learning_item_id, position, kind, role,
                      reveals_answer, mask_strategy, payload_json
               FROM content_blocks"""
        )
        for row in rows:
            block_id, item_id, position, raw_kind, raw_role, reveals, raw_mask, raw_payload = row
            try:
                payload_data = json.loads(str(raw_payload))
                if not isinstance(payload_data, dict):
                    raise ValueError("content payload must be an object")
                kind = ContentBlockKind(str(raw_kind))
                payload: ContentPayload
                if kind is ContentBlockKind.TEXT:
                    allowed = {"text", "reading", "furigana", "ruby_segments"}
                    if not set(payload_data) <= allowed or "text" not in payload_data:
                        raise ValueError("invalid text payload fields")
                    if not isinstance(payload_data["text"], str):
                        raise ValueError("text payload text must be a string")
                    for optional_field in ("reading", "furigana"):
                        optional_value = payload_data.get(optional_field)
                        if optional_value is not None and not isinstance(optional_value, str):
                            raise ValueError(f"{optional_field} must be a string or null")
                    raw_segments = payload_data.get("ruby_segments", [])
                    if not isinstance(raw_segments, list):
                        raise ValueError("ruby_segments must be an array")
                    segments = tuple(
                        RubySegment(
                            text=segment["text"],
                            reading=segment.get("reading"),
                        )
                        for segment in raw_segments
                        if isinstance(segment, dict)
                        and set(segment) <= {"text", "reading"}
                        and "text" in segment
                        and isinstance(segment["text"], str)
                        and (
                            segment.get("reading") is None
                            or isinstance(segment.get("reading"), str)
                        )
                    )
                    if len(segments) != len(raw_segments):
                        raise ValueError("invalid ruby segment fields")
                    payload = TextContent(
                        text=payload_data["text"],
                        reading=payload_data.get("reading"),
                        furigana=payload_data.get("furigana"),
                        ruby_segments=segments,
                    )
                elif kind is ContentBlockKind.RICH_TEXT:
                    payload = parse_rich_text_ast(payload_data)
                else:
                    if set(payload_data) != {"asset_id"} or not isinstance(
                        payload_data["asset_id"], str
                    ):
                        raise ValueError("media payload must contain only asset_id")
                    payload = MediaReference(payload_data["asset_id"])
                ContentBlock(
                    content_block_id=str(block_id),
                    learning_item_id=str(item_id),
                    position=int(position),
                    kind=kind,
                    role=ContentRole(str(raw_role)),
                    reveals_answer=bool(reveals),
                    mask_strategy=MaskStrategy(str(raw_mask)),
                    payload=payload,
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as err:
                raise ContentValidationError(f"invalid content block payload: {block_id}") from err

    @staticmethod
    def _validate_tombstones(connection: sqlite3.Connection) -> None:
        missing = connection.execute(
            """SELECT tombstone.object_type, tombstone.stable_id
               FROM tombstones AS tombstone
               LEFT JOIN learning_items AS item
                 ON tombstone.object_type = 'learning_item'
                AND item.learning_item_id = tombstone.stable_id
               LEFT JOIN facets AS facet
                 ON tombstone.object_type = 'facet' AND facet.facet_id = tombstone.stable_id
               LEFT JOIN card_definitions AS card
                 ON tombstone.object_type = 'card_definition'
                AND card.card_definition_id = tombstone.stable_id
               WHERE item.learning_item_id IS NULL
                 AND facet.facet_id IS NULL
                 AND card.card_definition_id IS NULL"""
        ).fetchone()
        if missing is not None:
            raise ContentValidationError(f"tombstone has no preserved identity row: {missing!r}")
        inconsistent = connection.execute(
            """SELECT COUNT(*) FROM (
                   SELECT tombstone.stable_id
                   FROM tombstones AS tombstone
                   JOIN learning_items AS item
                     ON tombstone.object_type = 'learning_item'
                    AND item.learning_item_id = tombstone.stable_id
                   WHERE item.lifecycle_status != tombstone.lifecycle_status
                      OR item.superseded_by_learning_item_id IS NOT tombstone.replacement_id
                   UNION ALL
                   SELECT tombstone.stable_id
                   FROM tombstones AS tombstone
                   JOIN facets AS facet
                     ON tombstone.object_type = 'facet' AND facet.facet_id = tombstone.stable_id
                   WHERE facet.lifecycle_status != tombstone.lifecycle_status
                      OR facet.superseded_by_facet_id IS NOT tombstone.replacement_id
                   UNION ALL
                   SELECT tombstone.stable_id
                   FROM tombstones AS tombstone
                   JOIN card_definitions AS card
                     ON tombstone.object_type = 'card_definition'
                    AND card.card_definition_id = tombstone.stable_id
                   WHERE card.lifecycle_status != tombstone.lifecycle_status
                      OR card.superseded_by_card_definition_id IS NOT tombstone.replacement_id
               )"""
        ).fetchone()[0]
        if inconsistent:
            raise ContentValidationError("tombstone lifecycle does not match its identity row")
        missing_tombstone = connection.execute(
            """SELECT stable_id FROM (
                   SELECT 'learning_item' AS object_type,
                          learning_item_id AS stable_id FROM learning_items
                   WHERE lifecycle_status != 'active'
                   UNION ALL
                   SELECT 'facet', facet_id FROM facets WHERE lifecycle_status != 'active'
                   UNION ALL
                   SELECT 'card_definition', card_definition_id FROM card_definitions
                   WHERE lifecycle_status != 'active'
               ) AS inactive
               WHERE NOT EXISTS (
                   SELECT 1 FROM tombstones
                   WHERE tombstones.object_type = inactive.object_type
                     AND tombstones.stable_id = inactive.stable_id
               ) LIMIT 1"""
        ).fetchone()
        if missing_tombstone is not None:
            raise ContentValidationError(
                f"inactive identity has no tombstone: {missing_tombstone[0]}"
            )

    @staticmethod
    def _validate_preaggregates(connection: sqlite3.Connection) -> None:
        expected = connection.execute(
            """SELECT pack.pack_version_id,
                      COUNT(DISTINCT CASE WHEN item.lifecycle_status = 'active'
                                          THEN item.learning_item_id END),
                      COUNT(DISTINCT CASE WHEN item.lifecycle_status = 'active'
                                               AND card.lifecycle_status = 'active'
                                          THEN card.card_key END)
               FROM pack_versions AS pack
               LEFT JOIN pack_items AS member ON member.pack_version_id = pack.pack_version_id
               LEFT JOIN learning_items AS item
                 ON item.learning_item_id = member.learning_item_id
               LEFT JOIN card_definitions AS card
                 ON card.learning_item_id = item.learning_item_id
               GROUP BY pack.pack_version_id"""
        ).fetchall()
        actual = connection.execute(
            "SELECT pack_version_id, total_items, total_cards FROM pack_version_stats"
        ).fetchall()
        if sorted(expected) != sorted(actual):
            raise ContentValidationError("pack pre-aggregates do not match active content")
        expected_types = connection.execute(
            """SELECT member.pack_version_id, item.content_type,
                      COUNT(DISTINCT item.learning_item_id)
               FROM pack_items AS member
               JOIN learning_items AS item ON item.learning_item_id = member.learning_item_id
               WHERE item.lifecycle_status = 'active'
               GROUP BY member.pack_version_id, item.content_type"""
        ).fetchall()
        actual_types = connection.execute(
            """SELECT pack_version_id, content_type, item_count
               FROM pack_version_content_type_counts"""
        ).fetchall()
        expected_tags = connection.execute(
            """SELECT member.pack_version_id, tagged.tag_id,
                      COUNT(DISTINCT item.learning_item_id)
               FROM pack_items AS member
               JOIN learning_items AS item ON item.learning_item_id = member.learning_item_id
               JOIN learning_item_tags AS tagged
                 ON tagged.learning_item_id = item.learning_item_id
               WHERE item.lifecycle_status = 'active'
               GROUP BY member.pack_version_id, tagged.tag_id"""
        ).fetchall()
        actual_tags = connection.execute(
            "SELECT pack_version_id, tag_id, item_count FROM pack_version_tag_counts"
        ).fetchall()
        if sorted(expected_types) != sorted(actual_types):
            raise ContentValidationError("content-type pre-aggregates do not match active content")
        if sorted(expected_tags) != sorted(actual_tags):
            raise ContentValidationError("tag pre-aggregates do not match active content")


@dataclass(frozen=True, slots=True)
class _TableMerge:
    name: str
    key_columns: tuple[str, ...]
    update_columns: tuple[str, ...] = ()


_MERGES = (
    _TableMerge("licenses", ("license_id",)),
    _TableMerge("sources", ("source_id",), ("name", "provider", "license_id")),
    _TableMerge("datasets", ("dataset_id",)),
    _TableMerge("dataset_sources", ("dataset_id", "source_id")),
    _TableMerge("dataset_licenses", ("dataset_id", "license_id")),
    _TableMerge("dataset_versions", ("dataset_version_id",)),
    _TableMerge(
        "dataset_packages",
        ("package_id",),
        ("dataset_id", "dataset_version_id", "built_at_utc", "canonical_content_hash"),
    ),
    _TableMerge(
        "concepts",
        ("concept_id",),
        ("source_record_id", "source_sense_id", "concept_type"),
    ),
    _TableMerge(
        "terms",
        ("term_id",),
        ("language_tag", "script", "text", "normalized_text", "normalization_version"),
    ),
    _TableMerge("concept_terms", ("concept_id", "term_id")),
    _TableMerge("tags", ("tag_id",), ("label",)),
    _TableMerge(
        "learning_items",
        ("learning_item_id",),
        ("content_type", "register", "lifecycle_status", "superseded_by_learning_item_id"),
    ),
    _TableMerge("learning_item_concepts", ("learning_item_id", "concept_id")),
    _TableMerge("learning_item_requirements", ("learning_item_id", "required_learning_item_id")),
    _TableMerge("learning_item_tags", ("learning_item_id", "tag_id")),
    _TableMerge(
        "facets",
        ("facet_id",),
        (
            "kind",
            "facet_key",
            "language_tag",
            "script",
            "lifecycle_status",
            "superseded_by_facet_id",
        ),
    ),
    _TableMerge(
        "card_definitions",
        ("card_definition_id",),
        (
            "card_key",
            "answer_semantics",
            "grading_policy_kind",
            "grading_policy_version",
            "lifecycle_status",
            "superseded_by_card_definition_id",
        ),
    ),
    _TableMerge("card_context_hints", ("card_definition_id", "facet_id"), ("position",)),
    _TableMerge(
        "content_blocks",
        ("content_block_id",),
        (
            "learning_item_id",
            "position",
            "kind",
            "role",
            "reveals_answer",
            "mask_strategy",
            "payload_json",
        ),
    ),
    _TableMerge("packs", ("pack_id",), ("name",)),
    _TableMerge("pack_versions", ("pack_version_id",)),
    _TableMerge("pack_items", ("pack_version_id", "learning_item_id"), ("position",)),
    _TableMerge(
        "pack_item_prerequisites",
        ("pack_version_id", "learning_item_id", "prerequisite_card_key"),
    ),
    _TableMerge(
        "pack_item_unlock_conditions",
        ("pack_version_id", "learning_item_id", "position"),
        ("metric", "minimum"),
    ),
    _TableMerge(
        "pack_item_card_defaults",
        ("pack_version_id", "learning_item_id", "card_key"),
        ("enabled_by_default",),
    ),
    _TableMerge("confusable_groups", ("confusable_group_id",), ("min_intro_gap_days",)),
    _TableMerge("confusable_group_items", ("confusable_group_id", "learning_item_id")),
    _TableMerge("stable_id_migrations", ("object_type", "old_id")),
)


class ContentGenerationBuilder:
    """Build a complete catalog while attaching at most one package at a time."""

    def __init__(self, validator: ContentGenerationValidator | None = None) -> None:
        self.validator = validator or ContentGenerationValidator()

    def build(
        self,
        packages: Iterable[Path],
        destination: Path,
        *,
        generation_id: str,
        built_at_utc: str,
        previous_generation: Path | None = None,
    ) -> ContentBuildResult:
        """Build and validate a generation without changing the active pointer."""
        _validate_generation_id(generation_id)
        package_metadata = sorted(
            (self.validator.validate_package(path) for path in packages),
            key=lambda package: package.dataset_id,
        )
        dataset_ids = [package.dataset_id for package in package_metadata]
        if len(dataset_ids) != len(set(dataset_ids)):
            raise ContentValidationError("a generation may contain one package per dataset")
        if previous_generation is not None:
            previous = self.validator.validate_generation(previous_generation)
            parent_generation_id = previous.generation_id
        else:
            parent_generation_id = None

        destination.parent.mkdir(parents=True, exist_ok=True)
        work = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.building")
        max_database_count = 1
        try:
            if previous_generation is None:
                initialize_content_database(work)
            else:
                _copy_database(previous_generation, work)
                os.chmod(work, 0o600)
            # uri=True is required on Python 3.13's sqlite3 connection for URI
            # query parameters on later ATTACH statements to be honored.
            with sqlite3.connect(work, uri=True) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                self._prepare_previous_lifecycle(connection)
                connection.execute("DELETE FROM generation_metadata")
                connection.execute("DELETE FROM dataset_packages")
                connection.execute("DELETE FROM pack_version_stats")
                connection.execute("DELETE FROM pack_version_content_type_counts")
                connection.execute("DELETE FROM pack_version_tag_counts")
                connection.commit()
                for package in package_metadata:
                    connection.execute(
                        "ATTACH DATABASE ? AS package",
                        (_read_only_uri(package.path, immutable=True),),
                    )
                    try:
                        database_count = [
                            row
                            for row in connection.execute("PRAGMA database_list").fetchall()
                            if row[1] != "temp"
                        ]
                        max_database_count = max(max_database_count, len(database_count))
                        if len(database_count) > 2:
                            raise ContentGenerationError(
                                "content merge attached more than one package database"
                            )
                        self._validate_stable_conflicts(connection)
                        self._merge_attached_package(connection, generation_id)
                        connection.commit()
                    except Exception:
                        connection.rollback()
                        raise
                    finally:
                        connection.execute("DETACH DATABASE package")
                self._synchronize_lifecycle(connection, generation_id)
                self._build_preaggregates(connection)
                package_set_hash = _package_set_hash(package_metadata)
                connection.execute(
                    """INSERT INTO generation_metadata(
                           singleton, generation_id, content_schema_version, built_at_utc,
                           parent_generation_id, package_count, package_set_hash
                       ) VALUES (1, ?, ?, ?, ?, ?, ?)""",
                    (
                        generation_id,
                        CONTENT_SCHEMA_VERSION,
                        built_at_utc,
                        parent_generation_id,
                        len(package_metadata),
                        package_set_hash,
                    ),
                )
                foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
                if foreign_keys:
                    raise ContentValidationError(
                        f"merged generation has foreign-key violations: {foreign_keys[:3]!r}"
                    )
                connection.commit()
            metadata = self.validator.validate_generation(
                work, expected_generation_id=generation_id
            )
            with sqlite3.connect(_read_only_uri(work, immutable=True), uri=True) as connection:
                active_items = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM learning_items WHERE lifecycle_status = 'active'"
                    ).fetchone()[0]
                )
                active_cards = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM card_definitions WHERE lifecycle_status = 'active'"
                    ).fetchone()[0]
                )
            os.replace(work, destination)
            _fsync_directory(destination.parent)
            return ContentBuildResult(
                path=destination,
                metadata=metadata,
                active_item_count=active_items,
                active_card_count=active_cards,
                max_database_count=max_database_count,
            )
        except Exception:
            work.unlink(missing_ok=True)
            raise

    @staticmethod
    def _prepare_previous_lifecycle(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TEMP TABLE previous_lifecycle(
                   object_type TEXT NOT NULL,
                   stable_id TEXT NOT NULL,
                   lifecycle_status TEXT NOT NULL,
                   replacement_id TEXT,
                   PRIMARY KEY(object_type, stable_id)
               )"""
        )
        connection.execute(
            """INSERT INTO previous_lifecycle
               SELECT 'learning_item', learning_item_id, lifecycle_status,
                      superseded_by_learning_item_id FROM learning_items
               UNION ALL
               SELECT 'facet', facet_id, lifecycle_status, superseded_by_facet_id FROM facets
               UNION ALL
               SELECT 'card_definition', card_definition_id, lifecycle_status,
                      superseded_by_card_definition_id FROM card_definitions"""
        )
        connection.execute(
            """UPDATE learning_items SET lifecycle_status = 'removed',
                   superseded_by_learning_item_id = NULL WHERE lifecycle_status = 'active'"""
        )
        connection.execute(
            """UPDATE facets SET lifecycle_status = 'removed',
                   superseded_by_facet_id = NULL WHERE lifecycle_status = 'active'"""
        )
        connection.execute(
            """UPDATE card_definitions SET lifecycle_status = 'removed',
                   superseded_by_card_definition_id = NULL WHERE lifecycle_status = 'active'"""
        )

    @staticmethod
    def _validate_stable_conflicts(connection: sqlite3.Connection) -> None:
        checks = (
            ("concepts", "concept_id", ("dataset_id", "source_id")),
            ("terms", "term_id", ("dataset_id",)),
            ("learning_items", "learning_item_id", ("dataset_id",)),
            ("facets", "facet_id", ("learning_item_id",)),
            (
                "card_definitions",
                "card_definition_id",
                ("card_key", "learning_item_id", "prompt_facet_id", "answer_facet_id"),
            ),
            ("packs", "pack_id", ("dataset_id",)),
            ("pack_versions", "pack_version_id", ("pack_id", "version")),
            (
                "dataset_versions",
                "dataset_version_id",
                ("dataset_id", "version", "canonical_content_hash"),
            ),
        )
        for table, key, immutable_columns in checks:
            differences = " OR ".join(
                f"target.{column} IS NOT incoming.{column}" for column in immutable_columns
            )
            row = connection.execute(
                f"""SELECT incoming.{key} FROM package.{table} AS incoming
                    JOIN main.{table} AS target ON target.{key} = incoming.{key}
                    WHERE {differences} LIMIT 1"""
            ).fetchone()
            if row is not None:
                raise ContentValidationError(f"stable identity conflict in {table} for {row[0]!r}")

    @staticmethod
    def _merge_attached_package(connection: sqlite3.Connection, generation_id: str) -> None:
        for merge in _MERGES:
            columns = tuple(
                str(row[1]) for row in connection.execute(f"PRAGMA main.table_info({merge.name})")
            )
            column_list = ", ".join(columns)
            conflict = ", ".join(merge.key_columns)
            if merge.update_columns:
                assignments = ", ".join(
                    f"{column} = excluded.{column}" for column in merge.update_columns
                )
                action = f"DO UPDATE SET {assignments}"
            else:
                action = "DO NOTHING"
            connection.execute(
                f"""INSERT INTO main.{merge.name}({column_list})
                    SELECT {column_list} FROM package.{merge.name} WHERE true
                    ON CONFLICT({conflict}) {action}"""
            )

        package_tombstones = connection.execute(
            """SELECT object_type, stable_id, dataset_id, lifecycle_status, replacement_id
               FROM package.tombstones"""
        ).fetchall()
        for object_type, stable_id, dataset_id, status, replacement_id in package_tombstones:
            connection.execute(
                """INSERT INTO tombstones(
                       object_type, stable_id, dataset_id, lifecycle_status,
                       replacement_id, status_since_generation_id
                   ) VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(object_type, stable_id) DO UPDATE SET
                       dataset_id = excluded.dataset_id,
                       lifecycle_status = excluded.lifecycle_status,
                       replacement_id = excluded.replacement_id,
                       status_since_generation_id = CASE
                           WHEN tombstones.lifecycle_status = excluded.lifecycle_status
                            AND tombstones.replacement_id IS excluded.replacement_id
                           THEN tombstones.status_since_generation_id
                           ELSE excluded.status_since_generation_id
                       END""",
                (object_type, stable_id, dataset_id, status, replacement_id, generation_id),
            )
            _apply_tombstone_to_identity(
                connection, str(object_type), str(stable_id), str(status), replacement_id
            )

    @staticmethod
    def _synchronize_lifecycle(connection: sqlite3.Connection, generation_id: str) -> None:
        lifecycle_sources = (
            (
                "learning_item",
                "learning_items",
                "learning_item_id",
                "superseded_by_learning_item_id",
                "dataset_id",
            ),
            (
                "facet",
                "facets",
                "facet_id",
                "superseded_by_facet_id",
                "(SELECT dataset_id FROM learning_items WHERE learning_item_id = facets.learning_item_id)",
            ),
            (
                "card_definition",
                "card_definitions",
                "card_definition_id",
                "superseded_by_card_definition_id",
                "(SELECT dataset_id FROM learning_items WHERE learning_item_id = card_definitions.learning_item_id)",
            ),
        )
        for (
            object_type,
            table,
            id_column,
            replacement_column,
            dataset_expression,
        ) in lifecycle_sources:
            connection.execute(
                f"""DELETE FROM tombstones
                    WHERE object_type = ? AND stable_id IN (
                        SELECT {id_column} FROM {table} WHERE lifecycle_status = 'active'
                    )""",
                (object_type,),
            )
            inactive = connection.execute(
                f"""SELECT {id_column}, {dataset_expression}, lifecycle_status,
                            {replacement_column}
                     FROM {table} WHERE lifecycle_status != 'active'"""
            ).fetchall()
            for stable_id, dataset_id, status, replacement_id in inactive:
                previous_tombstone = connection.execute(
                    """SELECT lifecycle_status, replacement_id, status_since_generation_id
                       FROM tombstones WHERE object_type = ? AND stable_id = ?""",
                    (object_type, stable_id),
                ).fetchone()
                status_since = generation_id
                if previous_tombstone is not None and (
                    previous_tombstone[0],
                    previous_tombstone[1],
                ) == (status, replacement_id):
                    status_since = str(previous_tombstone[2])
                connection.execute(
                    """INSERT INTO tombstones(
                           object_type, stable_id, dataset_id, lifecycle_status,
                           replacement_id, status_since_generation_id
                       ) VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(object_type, stable_id) DO UPDATE SET
                           dataset_id = excluded.dataset_id,
                           lifecycle_status = excluded.lifecycle_status,
                           replacement_id = excluded.replacement_id,
                           status_since_generation_id = excluded.status_since_generation_id""",
                    (
                        object_type,
                        stable_id,
                        dataset_id,
                        status,
                        replacement_id,
                        status_since,
                    ),
                )
            connection.execute(
                f"""INSERT INTO content_lifecycle_history(
                       object_type, stable_id, generation_id, lifecycle_status, replacement_id
                   )
                   SELECT ?, current.{id_column}, ?, current.lifecycle_status,
                          current.{replacement_column}
                   FROM {table} AS current
                   LEFT JOIN previous_lifecycle AS previous
                     ON previous.object_type = ? AND previous.stable_id = current.{id_column}
                   WHERE previous.stable_id IS NULL
                      OR previous.lifecycle_status != current.lifecycle_status
                      OR previous.replacement_id IS NOT current.{replacement_column}""",
                (object_type, generation_id, object_type),
            )

    @staticmethod
    def _build_preaggregates(connection: sqlite3.Connection) -> None:
        connection.execute(
            """INSERT INTO pack_version_stats(pack_version_id, total_items, total_cards)
               SELECT pack.pack_version_id,
                      COUNT(DISTINCT CASE WHEN item.lifecycle_status = 'active'
                                          THEN item.learning_item_id END),
                      COUNT(DISTINCT CASE WHEN item.lifecycle_status = 'active'
                                               AND card.lifecycle_status = 'active'
                                          THEN card.card_key END)
               FROM pack_versions AS pack
               LEFT JOIN pack_items AS member ON member.pack_version_id = pack.pack_version_id
               LEFT JOIN learning_items AS item
                 ON item.learning_item_id = member.learning_item_id
               LEFT JOIN card_definitions AS card
                 ON card.learning_item_id = item.learning_item_id
               GROUP BY pack.pack_version_id"""
        )
        connection.execute(
            """INSERT INTO pack_version_content_type_counts(
                   pack_version_id, content_type, item_count
               )
               SELECT member.pack_version_id, item.content_type, COUNT(DISTINCT item.learning_item_id)
               FROM pack_items AS member
               JOIN learning_items AS item ON item.learning_item_id = member.learning_item_id
               WHERE item.lifecycle_status = 'active'
               GROUP BY member.pack_version_id, item.content_type"""
        )
        connection.execute(
            """INSERT INTO pack_version_tag_counts(pack_version_id, tag_id, item_count)
               SELECT member.pack_version_id, tagged.tag_id,
                      COUNT(DISTINCT item.learning_item_id)
               FROM pack_items AS member
               JOIN learning_items AS item ON item.learning_item_id = member.learning_item_id
               JOIN learning_item_tags AS tagged
                 ON tagged.learning_item_id = item.learning_item_id
               WHERE item.lifecycle_status = 'active'
               GROUP BY member.pack_version_id, tagged.tag_id"""
        )


def _apply_tombstone_to_identity(
    connection: sqlite3.Connection,
    object_type: str,
    stable_id: str,
    status: str,
    replacement_id: Any,
) -> None:
    mappings = {
        "learning_item": (
            "learning_items",
            "learning_item_id",
            "superseded_by_learning_item_id",
        ),
        "facet": ("facets", "facet_id", "superseded_by_facet_id"),
        "card_definition": (
            "card_definitions",
            "card_definition_id",
            "superseded_by_card_definition_id",
        ),
    }
    try:
        table, id_column, replacement_column = mappings[object_type]
    except KeyError as err:
        raise ContentValidationError(f"unsupported tombstone object type: {object_type}") from err
    cursor = connection.execute(
        f"""UPDATE {table} SET lifecycle_status = ?, {replacement_column} = ?
            WHERE {id_column} = ?""",
        (status, replacement_id, stable_id),
    )
    if cursor.rowcount != 1:
        raise ContentValidationError(f"tombstone identity is not preserved: {stable_id}")


class ContentReaderLease:
    """A generation pin held until one reader has closed its SQLite connection."""

    def __init__(self, manager: ContentGenerationManager, path: Path, generation_id: str) -> None:
        self._manager = manager
        self.path = path
        self.generation_id = generation_id
        self._released = False

    async def __aenter__(self) -> ContentReaderLease:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.release()

    async def release(self) -> None:
        """Release this lease exactly once."""
        if not self._released:
            self._released = True
            await self._manager._release_reader(self.generation_id)


class ContentGenerationManager:
    """Serialize validated activation with reader drain and one-step rollback."""

    def __init__(self, current_path: Path, executor: Executor) -> None:
        self.current_path = current_path
        self.root = current_path.parent
        self.generations_dir = self.root / "generations"
        self.staging_dir = self.root / "staging"
        self.catalog_path = self.root / "catalog.json"
        self._executor = executor
        self._validator = ContentGenerationValidator()
        self._condition = asyncio.Condition()
        self._leases: dict[str, int] = {}
        self._active: GenerationMetadata | None = None
        self._active_path: Path | None = None
        self._previous_id: str | None = None
        self._switching = False
        self._closed = False

    @property
    def active_metadata(self) -> GenerationMetadata:
        """Return the validated active generation."""
        if self._active is None:
            raise ContentGenerationError("content generation manager is not open")
        return self._active

    @property
    def active_path(self) -> Path:
        """Return the immutable active generation path, not the mutable pointer."""
        if self._active_path is None:
            raise ContentGenerationError("content generation manager is not open")
        return self._active_path

    @property
    def previous_generation_id(self) -> str | None:
        """Return the retained rollback generation, if one exists."""
        return self._previous_id

    async def async_open(self, *, built_at_utc: str) -> None:
        """Discover a valid active generation or create an empty bootstrap one."""
        loop = asyncio.get_running_loop()
        active, active_path, previous_id = await loop.run_in_executor(
            self._executor, self._open_sync, built_at_utc
        )
        self._active = active
        self._active_path = active_path
        self._previous_id = previous_id

    def _open_sync(self, built_at_utc: str) -> tuple[GenerationMetadata, Path, str | None]:
        self.generations_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        if self.current_path.exists() and _is_p0_content_database(self.current_path):
            legacy = self.staging_dir / f"legacy-p0-{uuid.uuid4().hex}.db"
            os.replace(self.current_path, legacy)
            try:
                active = self._create_bootstrap_sync(built_at_utc)
            except Exception:
                os.replace(legacy, self.current_path)
                raise
            legacy.unlink()
            return active
        if not self.current_path.exists():
            return self._create_bootstrap_sync(built_at_utc)

        metadata = self._validator.validate_generation(self.current_path)
        generation_path = self.generations_dir / f"{metadata.generation_id}.db"
        if not generation_path.exists():
            os.link(self.current_path, generation_path)
        previous_id = self._read_catalog_previous(metadata.generation_id)
        if previous_id is None:
            previous_id = metadata.parent_generation_id
        if previous_id is not None:
            previous_path = self.generations_dir / f"{previous_id}.db"
            try:
                self._validator.validate_generation(
                    previous_path, expected_generation_id=previous_id
                )
            except (ContentGenerationError, OSError):
                previous_id = None
        os.chmod(generation_path, 0o444)
        self._write_catalog(metadata.generation_id, previous_id)
        return metadata, generation_path, previous_id

    def _create_bootstrap_sync(
        self, built_at_utc: str
    ) -> tuple[GenerationMetadata, Path, str | None]:
        generation_id = f"bootstrap-{uuid.uuid4().hex}"
        candidate = self.staging_dir / "content.next.db"
        result = ContentGenerationBuilder(self._validator).build(
            (), candidate, generation_id=generation_id, built_at_utc=built_at_utc
        )
        return self._activate_sync(result.path, previous_id=None)

    async def acquire_reader(self) -> ContentReaderLease:
        """Wait out a switch and pin the currently active immutable file."""
        async with self._condition:
            while self._switching and not self._closed:
                await self._condition.wait()
            if self._closed:
                raise ContentGenerationError("content generation manager is closed")
            metadata = self.active_metadata
            path = self.active_path
            self._leases[metadata.generation_id] = self._leases.get(metadata.generation_id, 0) + 1
            return ContentReaderLease(self, path, metadata.generation_id)

    async def _release_reader(self, generation_id: str) -> None:
        async with self._condition:
            count = self._leases.get(generation_id, 0)
            if count <= 1:
                self._leases.pop(generation_id, None)
            else:
                self._leases[generation_id] = count - 1
            self._condition.notify_all()

    async def async_activate(self, candidate: Path) -> GenerationMetadata:
        """Drain readers, validate again, then atomically switch current.db."""
        async with self._condition:
            if self._closed:
                raise ContentActivationError("content generation manager is closed")
            while self._switching:
                await self._condition.wait()
            self._switching = True
            while self._leases:
                await self._condition.wait()
        old_active = self.active_metadata
        try:
            loop = asyncio.get_running_loop()
            metadata, path, previous_id = await loop.run_in_executor(
                self._executor,
                self._activate_sync,
                candidate,
                old_active.generation_id,
            )
            self._active = metadata
            self._active_path = path
            self._previous_id = previous_id
            return metadata
        finally:
            async with self._condition:
                self._switching = False
                self._condition.notify_all()

    async def async_rollback(self) -> GenerationMetadata:
        """Atomically reactivate the retained validated previous generation."""
        async with self._condition:
            if self._closed:
                raise ContentActivationError("content generation manager is closed")
            while self._switching:
                await self._condition.wait()
            if self._previous_id is None:
                raise ContentActivationError("no previous generation is available")
            self._switching = True
            while self._leases:
                await self._condition.wait()
        rolled_away = self.active_metadata.generation_id
        target_id = self._previous_id
        target = self.generations_dir / f"{target_id}.db"
        try:
            loop = asyncio.get_running_loop()
            metadata = await loop.run_in_executor(
                self._executor, self._switch_existing_sync, target, rolled_away
            )
            self._active = metadata
            self._active_path = target
            self._previous_id = rolled_away
            return metadata
        finally:
            async with self._condition:
                self._switching = False
                self._condition.notify_all()

    def _activate_sync(
        self, candidate: Path, previous_id: str | None
    ) -> tuple[GenerationMetadata, Path, str | None]:
        metadata = self._validator.validate_generation(candidate)
        target = self.generations_dir / f"{metadata.generation_id}.db"
        if target.exists():
            raise ContentActivationError(f"generation already exists: {metadata.generation_id}")
        os.replace(candidate, target)
        os.chmod(target, 0o444)
        _fsync_directory(self.generations_dir)
        self._replace_current_link(target)
        self._finish_switch(metadata.generation_id, previous_id)
        return metadata, target, previous_id

    def _switch_existing_sync(self, target: Path, previous_id: str) -> GenerationMetadata:
        metadata = self._validator.validate_generation(target)
        self._replace_current_link(target)
        self._finish_switch(metadata.generation_id, previous_id)
        return metadata

    def _finish_switch(self, active_id: str, previous_id: str | None) -> None:
        """Best-effort bookkeeping after current.db has already switched."""
        # current.db is the crash-safe source of truth; startup reconstructs
        # the previous pointer from generation metadata when needed.
        with suppress(OSError):
            self._write_catalog(active_id, previous_id)
        # An extra immutable generation is safe and may be pruned later.
        with suppress(OSError):
            self._cleanup_generations({active_id, previous_id})

    def _replace_current_link(self, target: Path) -> None:
        temporary = self.root / f".current.{uuid.uuid4().hex}.tmp"
        try:
            os.link(target, temporary)
            os.replace(temporary, self.current_path)
            _fsync_directory(self.root)
        finally:
            temporary.unlink(missing_ok=True)

    def _cleanup_generations(self, retained: set[str | None]) -> None:
        retained.discard(None)
        for path in self.generations_dir.glob("*.db"):
            if path.stem not in retained:
                path.unlink()
        _fsync_directory(self.generations_dir)

    def _write_catalog(self, active_id: str, previous_id: str | None) -> None:
        temporary = self.root / f".catalog.{uuid.uuid4().hex}.tmp"
        payload = json.dumps(
            {
                "catalog_version": 1,
                "active_generation_id": active_id,
                "previous_generation_id": previous_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.catalog_path)
            _fsync_directory(self.root)
        finally:
            temporary.unlink(missing_ok=True)

    def _read_catalog_previous(self, active_id: str) -> str | None:
        try:
            data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if data.get("catalog_version") != 1 or data.get("active_generation_id") != active_id:
            return None
        previous = data.get("previous_generation_id")
        return previous if isinstance(previous, str) else None

    async def async_close(self) -> None:
        """Prevent new readers and drain every in-flight lease."""
        async with self._condition:
            self._closed = True
            self._switching = True
            while self._leases:
                await self._condition.wait()
            self._condition.notify_all()


def _copy_database(source_path: Path, target_path: Path) -> None:
    target_path.unlink(missing_ok=True)
    source = sqlite3.connect(_read_only_uri(source_path, immutable=True), uri=True)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def _is_p0_content_database(path: Path) -> bool:
    """Recognize only the unreleased three-column P0 benchmark cache."""
    try:
        with sqlite3.connect(_read_only_uri(path, immutable=True), uri=True) as connection:
            schema_columns = [
                str(row[1]) for row in connection.execute("PRAGMA table_info(schema_version)")
            ]
            card_columns = [
                str(row[1]) for row in connection.execute("PRAGMA table_info(card_definitions)")
            ]
            generation_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'generation_metadata'"
            ).fetchone()
    except sqlite3.DatabaseError:
        return False
    return (
        schema_columns == ["version"]
        and card_columns == ["card_key", "pack_version_id", "ordinal"]
        and generation_table is None
    )


def _package_set_hash(packages: Iterable[PackageMetadata]) -> str:
    return _package_rows_hash(
        [
            (package.dataset_id, package.dataset_version_id, package.canonical_content_hash)
            for package in packages
        ]
    )


def _package_rows_hash(rows: Iterable[tuple[Any, Any, Any]]) -> str:
    digest = hashlib.sha256()
    for dataset_id, dataset_version_id, canonical_content_hash in rows:
        digest.update(str(dataset_id).encode())
        digest.update(b"\x1f")
        digest.update(str(dataset_version_id).encode())
        digest.update(b"\x1f")
        digest.update(str(canonical_content_hash).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _validate_generation_id(generation_id: str) -> None:
    if not _GENERATION_ID_RE.fullmatch(generation_id):
        raise ContentValidationError(f"invalid generation_id: {generation_id!r}")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
