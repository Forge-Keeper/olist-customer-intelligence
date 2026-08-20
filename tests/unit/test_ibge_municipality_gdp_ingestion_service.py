from __future__ import annotations

from typing import Any

from olist_data_platform.domains.ingestion.ibge.datasets import MUNICIPALITY_GDP
from olist_data_platform.domains.ingestion.ibge import (
    municipality_gdp_ingestion_service as gdp_service,
)
from olist_data_platform.domains.ingestion.ibge.sidra_query import SidraQuery


class _SidraClient:
    def __init__(self) -> None:
        self.slices: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def get_values(self, query: SidraQuery) -> list[Any]:
        self.slices.append((query.periods, query.variables))
        [period] = query.periods
        [variable] = query.variables
        value = "..." if variable == "6575" else "1000"
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
                "D2C": variable,
                "D2N": f"Variável {variable}",
                "D3C": period,
                "D3N": period,
                "MC": "1029",
                "MN": "Mil Reais",
                "NC": "6",
                "NN": "Município",
                "V": value,
            },
        ]


class _Writer:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.request_id = ""

    def write(self, records: list[dict[str, Any]], request_id: str) -> None:
        self.records = records
        self.request_id = request_id


def test_gdp_service_partitions_requests_by_period_and_variable() -> None:
    writer = _Writer()
    client = _SidraClient()
    service = gdp_service.MunicipalityGdpIngestionService(
        client=client,
        bronze_writer=writer,
        request_id_factory=lambda: "req-gdp",
    )

    request_id = service.ingest()

    assert request_id == "req-gdp"
    assert len(client.slices) == 18
    assert client.slices[0] == (("2016",), ("37",))
    assert client.slices[-1] == (("2018",), ("6575",))
    assert len(writer.records) == 18
    assert {record["reference_year"] for record in writer.records} == {
        "2016",
        "2017",
        "2018",
    }
    assert {record["variable_code"] for record in writer.records} == set(
        MUNICIPALITY_GDP.variables
    )
    assert any(record["payload"]["Valor"] == "..." for record in writer.records)
    assert writer.request_id == request_id
