from __future__ import annotations

from datetime import date
from typing import Any, ClassVar


class MunicipalitiesExtractor:
    """Normalize current IBGE Localidades payload for analytical reference years."""

    REFERENCE_YEARS: ClassVar[tuple[int, ...]] = (2016, 2017, 2018)
    NOT_YET_EXISTING_BY_YEAR: ClassVar[dict[int, frozenset[str]]] = {
        2016: frozenset({"5101837"}),
        2017: frozenset({"5101837"}),
        2018: frozenset({"5101837"}),
    }

    @classmethod
    def extract(cls, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            raise TypeError("Localidades payload must be a list.")
        if not all(isinstance(item, dict) for item in payload):
            raise TypeError("Localidades payload must contain only dictionaries.")

        records: list[dict[str, Any]] = []
        for year in cls.REFERENCE_YEARS:
            excluded = cls.NOT_YET_EXISTING_BY_YEAR.get(year, frozenset())
            dt_base = date(year, 1, 1)
            for municipality in payload:
                municipality_code = str(municipality.get("id", ""))
                if not municipality_code or municipality_code in excluded:
                    continue
                records.append(cls._normalize(municipality, dt_base))
        return records

    @staticmethod
    def _normalize(municipality: dict[str, Any], dt_base: date) -> dict[str, Any]:
        immediate = municipality.get("regiao-imediata") or {}
        intermediate = immediate.get("regiao-intermediaria") or {}
        micro = municipality.get("microrregiao") or {}
        meso = micro.get("mesorregiao") or {}
        state = intermediate.get("UF") or meso.get("UF") or {}
        region = state.get("regiao") or {}

        return {
            "municipality_code": str(municipality["id"]),
            "municipality_name": str(municipality["nome"]),
            "state_code": str(state.get("id", "")),
            "state_abbreviation": str(state.get("sigla", "")),
            "state_name": str(state.get("nome", "")),
            "region_code": str(region.get("id", "")),
            "region_abbreviation": str(region.get("sigla", "")),
            "region_name": str(region.get("nome", "")),
            "immediate_region_code": str(immediate.get("id", "")),
            "immediate_region_name": str(immediate.get("nome", "")),
            "intermediate_region_code": str(intermediate.get("id", "")),
            "intermediate_region_name": str(intermediate.get("nome", "")),
            "microregion_code": str(micro.get("id", "")),
            "microregion_name": str(micro.get("nome", "")),
            "mesoregion_code": str(meso.get("id", "")),
            "mesoregion_name": str(meso.get("nome", "")),
            "dt_base": dt_base,
        }
