"""Backend-owned card presentation contract for P5.3 Learn UI."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..storage.database import SQLiteStorage


class PresentationError(ValueError):
    """Raised when an active CardDefinition cannot be rendered unambiguously."""


class CardPresentationService:
    """Resolve CardDefinition facets to validated ContentBlocks without UI guessing."""

    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

    async def async_for_card(self, *, track_id: str, card_key: str) -> dict[str, Any]:
        """Return one direction-aware presentation for an enabled active card."""

        def read(connection: sqlite3.Connection) -> dict[str, Any]:
            row = connection.execute(
                """SELECT card.learning_item_id, item.content_type,
                          prompt.facet_id, prompt.kind, prompt.facet_key,
                          prompt.language_tag, prompt.script,
                          answer.facet_id, answer.kind, answer.facet_key,
                          answer.language_tag, answer.script
                   FROM track_card_rules AS rule
                   JOIN content.card_definitions AS card
                     ON card.card_key = rule.card_key
                    AND card.lifecycle_status = 'active'
                   JOIN content.learning_items AS item
                     ON item.learning_item_id = card.learning_item_id
                    AND item.lifecycle_status = 'active'
                   JOIN content.facets AS prompt
                     ON prompt.facet_id = card.prompt_facet_id
                    AND prompt.lifecycle_status = 'active'
                   JOIN content.facets AS answer
                     ON answer.facet_id = card.answer_facet_id
                    AND answer.lifecycle_status = 'active'
                   WHERE rule.track_id = ? AND rule.card_key = ?
                     AND rule.enabled = 1
                   LIMIT 1""",
                (track_id, card_key),
            ).fetchone()
            if row is None:
                raise PresentationError("card is not enabled in track")

            learning_item_id = str(row[0])
            content_type = str(row[1])
            prompt = self._facet_meta(row[2:7])
            answer = self._facet_meta(row[7:12])

            raw_blocks = connection.execute(
                """SELECT content_block_id, position, kind, role, reveals_answer,
                          mask_strategy, payload_json
                   FROM content.content_blocks
                   WHERE learning_item_id = ?
                   ORDER BY position, content_block_id""",
                (learning_item_id,),
            ).fetchall()
            blocks = tuple(self._block(block_row) for block_row in raw_blocks)
            if not blocks:
                raise PresentationError("learning item has no renderable content blocks")

            terms = tuple(
                {
                    "text": str(term_row[0]),
                    "language_tag": str(term_row[1]),
                    "script": None if term_row[2] is None else str(term_row[2]),
                }
                for term_row in connection.execute(
                    """SELECT DISTINCT term.text, term.language_tag, term.script
                       FROM content.learning_item_concepts AS item_concept
                       JOIN content.concept_terms AS relation
                         ON relation.concept_id = item_concept.concept_id
                       JOIN content.terms AS term ON term.term_id = relation.term_id
                       WHERE item_concept.learning_item_id = ?
                       ORDER BY term.term_id""",
                    (learning_item_id,),
                ).fetchall()
            )

            prompt_view = self._resolve_facet(prompt, blocks, terms)
            answer_view = self._resolve_facet(answer, blocks, terms)
            context_rows = connection.execute(
                """SELECT facet.facet_id, facet.kind, facet.facet_key,
                          facet.language_tag, facet.script
                   FROM content.card_context_hints AS hint
                   JOIN content.facets AS facet ON facet.facet_id = hint.facet_id
                   WHERE hint.card_definition_id = (
                       SELECT card_definition_id
                       FROM content.card_definitions
                       WHERE card_key = ?
                       LIMIT 1
                   )
                     AND facet.lifecycle_status = 'active'
                   ORDER BY hint.position""",
                (card_key,),
            ).fetchall()
            context = tuple(
                self._resolve_facet(self._facet_meta(context_row), blocks, terms)
                for context_row in context_rows
            )

            annotated = tuple(self._annotate_block(block, terms) for block in blocks)
            return {
                "card_key": card_key,
                "learning_item_id": learning_item_id,
                "content_type": content_type,
                "prompt": prompt_view,
                "answer": answer_view,
                "context": list(context),
                "introduction_blocks": list(annotated),
                "hint_blocks": [block for block in annotated if block["role"] == "hint"],
                "mnemonic_blocks": [block for block in annotated if block["role"] == "mnemonic"],
                "example_blocks": [block for block in annotated if block["role"] == "example"],
            }

        return await self._storage._async_reader(read)

    @staticmethod
    def _facet_meta(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "facet_id": str(row[0]),
            "kind": str(row[1]),
            "facet_key": str(row[2]),
            "language_tag": str(row[3]),
            "script": None if row[4] is None else str(row[4]),
        }

    @staticmethod
    def _block(row: tuple[Any, ...]) -> dict[str, Any]:
        payload = json.loads(str(row[6]))
        if not isinstance(payload, dict):
            raise PresentationError("content block payload must be an object")
        return {
            "content_block_id": str(row[0]),
            "position": int(row[1]),
            "kind": str(row[2]),
            "role": str(row[3]),
            "reveals_answer": bool(row[4]),
            "mask_strategy": str(row[5]),
            "payload": payload,
        }

    @classmethod
    def _resolve_facet(
        cls,
        facet: dict[str, Any],
        blocks: tuple[dict[str, Any], ...],
        terms: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        if facet["kind"] != "text":
            raise PresentationError(
                f"P5.3 Learn renderer does not yet support facet kind {facet['kind']!r}"
            )
        accepted_texts = {
            term["text"]
            for term in terms
            if term["language_tag"] == facet["language_tag"]
            and (
                facet["script"] is None
                or term["script"] is None
                or term["script"] == facet["script"]
            )
        }
        matches = [
            block
            for block in blocks
            if block["kind"] == "text"
            and isinstance(block["payload"].get("text"), str)
            and block["payload"]["text"] in accepted_texts
        ]
        if not matches:
            matches = [
                block
                for block in blocks
                if block["kind"] == "text" and block["role"] == facet["facet_key"]
            ]
        if len(matches) != 1:
            raise PresentationError(
                "facet-to-content mapping is ambiguous; explicit content mapping is required"
            )
        view = dict(facet)
        view["blocks"] = [cls._annotate_block(matches[0], terms)]
        return view

    @staticmethod
    def _annotate_block(
        block: dict[str, Any],
        terms: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        annotated = dict(block)
        text = block["payload"].get("text")
        if isinstance(text, str):
            matching = [term for term in terms if term["text"] == text]
            if len(matching) == 1:
                annotated["language_tag"] = matching[0]["language_tag"]
                annotated["script"] = matching[0]["script"]
        return annotated
