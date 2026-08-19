from __future__ import annotations

from datetime import date
from typing import Any


class MunicipalityPopulationExtractor:
    """Normalize decoded SIDRA municipality population rows for Bronze."""

    @classmethod
    def extract(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            raise TypeError("SIDRA rows must be a list.")
        if not all(isinstance(row, dict) for row in rows):
            raise TypeError("SIDRA rows must contain only dictionaries.")

        return [cls._normalize(row) for row in rows]

    @staticmethod
    def _normalize(row: dict[str, Any]) -> dict[str, Any]:
        reference_year = int(row["Ano"])
        value = row["Valor"]
        if not isinstance(value, str) or not value.isdigit():
            raise ValueError(
                "Population value must be a numeric string for this dataset."
            )

        return {
            "municipality_code": str(row["Município (Código)"]),
            "municipality_name": str(row["Município"]),
            "variable_code": str(row["Variável (Código)"]),
            "variable_name": str(row["Variável"]),
            "reference_year": reference_year,
            "unit_code": str(row["Unidade de Medida (Código)"]),
            "unit_name": str(row["Unidade de Medida"]),
            "territorial_level_code": str(row["Nível Territorial (Código)"]),
            "territorial_level_name": str(row["Nível Territorial"]),
            "value": int(value),
            "dt_base": date(reference_year, 1, 1),
        }
