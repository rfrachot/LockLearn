"""Strict pack content-filter schema and parameterized SQL compiler."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

_MAX_FILTER_TERMS = 64
_MAX_IN_VALUES = 256

_FIELD_SQL = {
    "content_type": "item.content_type",
    "register": "item.register",
    "dataset_id": "item.dataset_id",
}
_ALLOWED_OPERATORS = frozenset({"eq", "in"})


class PackFilterError(ValueError):
    """Raised when a pack content filter leaves the closed V1 grammar."""


@dataclass(frozen=True, slots=True)
class CompiledPackFilter:
    """One SQL fragment whose values are always separate bound parameters."""

    where_sql: str
    parameters: tuple[object, ...]


def _non_empty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PackFilterError(f"{field} must be a non-empty string")
    return value


def _compile_term(value: object) -> tuple[str, tuple[object, ...]]:
    if not isinstance(value, Mapping):
        raise PackFilterError("content filter terms must be objects")
    term = dict(value)
    if set(term) != {"field", "op", "value"}:
        raise PackFilterError("content filter term keys must be exactly field/op/value")

    field = _non_empty_string(term["field"], "field")
    operator = _non_empty_string(term["op"], "op")
    column = _FIELD_SQL.get(field)
    if column is None:
        raise PackFilterError(f"unsupported content filter field: {field}")
    if operator not in _ALLOWED_OPERATORS:
        raise PackFilterError(f"unsupported content filter operator: {operator}")

    raw_value = term["value"]
    if operator == "eq":
        return f"{column} = ?", (_non_empty_string(raw_value, "value"),)

    if not isinstance(raw_value, list) or not raw_value or len(raw_value) > _MAX_IN_VALUES:
        raise PackFilterError(
            f"in filter value must be a non-empty array of at most {_MAX_IN_VALUES} strings"
        )
    values = tuple(_non_empty_string(item, "value[]") for item in raw_value)
    placeholders = ",".join("?" for _ in values)
    return f"{column} IN ({placeholders})", values


def compile_pack_content_filter(value: object) -> CompiledPackFilter:
    """Compile the closed JSON-like filter grammar into parameterized SQLite SQL.

    Grammar:
      {"all": [{"field": <allowlisted>, "op": "eq"|"in", "value": ...}, ...]}

    SQL identifiers and operators come only from module constants. User/package
    values are returned separately and must be bound by sqlite3.
    """
    if not isinstance(value, Mapping):
        raise PackFilterError("content_filters must be an object")
    document = dict(value)
    if set(document) != {"all"}:
        raise PackFilterError("content_filters keys must be exactly ['all']")
    terms = document["all"]
    if not isinstance(terms, list) or len(terms) > _MAX_FILTER_TERMS:
        raise PackFilterError(
            f"content_filters.all must be an array of at most {_MAX_FILTER_TERMS} terms"
        )

    clauses = ["item.lifecycle_status = 'active'"]
    parameters: list[object] = []
    for term in terms:
        clause, values = _compile_term(term)
        clauses.append(clause)
        parameters.extend(values)
    return CompiledPackFilter(
        where_sql=" AND ".join(clauses),
        parameters=tuple(parameters),
    )
