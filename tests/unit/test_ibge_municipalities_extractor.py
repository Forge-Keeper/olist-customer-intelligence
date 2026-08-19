from datetime import date

from olist_data_platform.domains.ingestion.ibge.municipalities_extractor import (
    MunicipalitiesExtractor,
)


def _municipality(code: int = 3550308) -> dict:
    return {
        "id": code,
        "nome": "São Paulo",
        "microrregiao": {
            "id": 35061,
            "nome": "São Paulo",
            "mesorregiao": {"id": 3515, "nome": "Metropolitana de São Paulo"},
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
                    "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                },
            },
        },
    }


def test_extract_materializes_three_reference_years() -> None:
    records = MunicipalitiesExtractor.extract([_municipality()])
    assert [record["dt_base"] for record in records] == [
        date(2016, 1, 1),
        date(2017, 1, 1),
        date(2018, 1, 1),
    ]
    assert {record["municipality_code"] for record in records} == {"3550308"}


def test_extract_excludes_boa_esperanca_do_norte_from_olist_period() -> None:
    records = MunicipalitiesExtractor.extract([_municipality(5101837)])
    assert records == []
