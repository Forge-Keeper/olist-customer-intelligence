from __future__ import annotations

from datetime import date
from typing import Any


class MunicipalitiesExtractor:
    """Prepare the current IBGE Localidades snapshot for AS-IS Bronze landing."""

    @classmethod
    def extract(
        cls,
        payload: list[dict[str, Any]],
        snapshot_date: date,
    ) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            raise TypeError("Localidades payload must be a list.")
        if not all(isinstance(item, dict) for item in payload):
            raise TypeError("Localidades payload must contain only dictionaries.")
        if not isinstance(snapshot_date, date):
            raise TypeError("snapshot_date must be a date.")

        return [cls._prepare(municipality, snapshot_date) for municipality in payload]

    @staticmethod
    def _prepare(
        municipality: dict[str, Any],
        snapshot_date: date,
    ) -> dict[str, Any]:
        municipality_code = str(municipality["id"])
        if not municipality_code.strip():
            raise ValueError("Municipality code cannot be empty.")

        return {
            "municipality_code": municipality_code,
            "dt_base": snapshot_date,
            "payload": dict(municipality),
        }
