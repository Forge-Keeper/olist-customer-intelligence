from __future__ import annotations

import re

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    if not _IDENTIFIER.fullmatch(normalized):
        raise ValueError(
            f"{label} must be a simple Unity Catalog identifier: {value!r}."
        )
    return normalized


def qualified_table_name(*, catalog: str, schema: str, table: str) -> str:
    """Build a fully qualified Unity Catalog table name from explicit inputs.

    Environment selection belongs to deployment/runtime configuration. This helper
    only validates and composes identifiers; it never infers dev/stg/prd.
    """
    return ".".join(
        (
            _validate_identifier(catalog, label="catalog"),
            _validate_identifier(schema, label="schema"),
            _validate_identifier(table, label="table"),
        )
    )
