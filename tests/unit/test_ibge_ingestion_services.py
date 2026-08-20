from __future__ import annotations

from datetime import date
from typing import Any

from olist_data_platform.domains.ingestion.ibge import (
    municipalities_ingestion_service as municipalities_service,
)
from olist_data_platform.domains.ingestion.ibge import (
    municipality_population_ingestion_service as population_service,
)
from olist_data_platform.domains.ingestion.ibge.sidra_query import SidraQuery


class _LocalitiesClient:
    def get_municipalities(self) -> list[dict[str, Any]]:
        return [
            {
                "id": 3550308,
                "nome": "São Paulo",
                "microrregiao": {
                    "id": 35061,
                    "nome": "São Paulo",
                    "mesorregiao": {
                        "id": 3515,
                        "nome": "Metropolitana de São Paulo",
                    },
                },
                "regiao-imediata": {
                    "id": 350001,
                    "nome": "São Paulo",
                    "regiao-intermediaria": {
                        "id": 3501,
                        "nome": "São Paulo",
                        "UF": {
                            "id": 35,
                            "sigla": "SP",
                            "nome": "São Paulo",
                            "regiao": {
                                "id": 3,
                                "sigla": "SE",
                                "nome": "Sudeste",
                            },
                        },
                    },
                },
            }
        ]


class _SidraClient:
    def get_values(self, query: SidraQuery) -> list[Any]:
        assert query.periods == ("2016", "2017", "2018")
        return [
            {
                "D1C": "Município (Código)",
                "D1N": "Município",
                "D2C": "Variável (Código)",
                "D2N": "Variável",
                "D3C": "Ano (Código)",
                "D3N": "Ano",
                "MC": "Unidade de Medida (Código)",
                "MN": "Unidade de Medida",
                "NC": "Nível Territorial (Código)",
                "NN": "Nível Territorial",
                "V": "Valor",
            },
            {
                "D1C": "3550308",
                "D1N": "São Paulo (SP)",
                "D2C": "9324",
                "D2N": "População residente estimada",
                "D3C": "2018",
                "D3N": "2018",
                "MC": "45",
                "MN": "Pessoas",
                "NC": "6",
                "NN": "Município",
                "V": "12176866",
            },
        ]


class _Writer:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.request_id = ""

    def write(self, records: list[dict[str, Any]], request_id: str) -> None:
        self.records = records
        self.request_id = request_id


def test_municipalities_service_writes_single_source_snapshot() -> None:
    writer = _Writer()
    snapshot_date = date(2026, 8, 19)
    service = municipalities_service.MunicipalitiesIngestionService(
        client=_LocalitiesClient(),
        bronze_writer=writer,
        request_id_factory=lambda: "req-municipalities",
        snapshot_date_factory=lambda: snapshot_date,
    )

    request_id = service.ingest()

    assert request_id == "req-municipalities"
    assert len(writer.records) == 1
    assert writer.records[0]["dt_base"] == snapshot_date
    assert writer.records[0]["payload"]["nome"] == "São Paulo"
    assert writer.request_id == request_id


def test_population_service_builds_period_query_and_writes_records() -> None:
    writer = _Writer()
    service = population_service.MunicipalityPopulationIngestionService(
        client=_SidraClient(),
        bronze_writer=writer,
        request_id_factory=lambda: "req-population",
    )

    request_id = service.ingest()

    assert request_id == "req-population"
    assert len(writer.records) == 1
    assert writer.records[0]["reference_year"] == "2018"
    assert writer.records[0]["payload"]["Valor"] == "12176866"
    assert writer.request_id == request_id
