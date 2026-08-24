from __future__ import annotations

from datetime import date
from typing import Any


class MunicipalityGdpExtractor:
    """Prepare decoded SIDRA municipal GDP rows for AS-IS Bronze landing."""

    @classmethod
    def extract(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            raise TypeError("SIDRA rows must be a list.")
        if not all(isinstance(row, dict) for row in rows):
            raise TypeError("SIDRA rows must contain only dictionaries.")

        return [cls._prepare(row) for row in rows]

    @staticmethod
    def _prepare(row: dict[str, Any]) -> dict[str, Any]:
        municipality_code = str(row["Município (Código)"])
        reference_year = str(row["Ano"])
        variable_code = str(row["Variável (Código)"])

        if not municipality_code.strip():
            raise ValueError("Municipality code cannot be empty.")
        if not reference_year.isdigit():
            raise ValueError("Reference year must be a numeric string.")
        if not variable_code.strip():
            raise ValueError("Variable code cannot be empty.")

        return {
            "municipality_code": municipality_code,
            "reference_year": reference_year,
            "variable_code": variable_code,
            "dt_base": date(int(reference_year), 1, 1),
            "payload": dict(row),
        }
