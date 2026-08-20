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
        "campo-novo": {"preserve": True},
    }


def test_extract_preserves_single_source_snapshot() -> None:
    snapshot_date = date(2026, 8, 19)
    source = _municipality()

    records = MunicipalitiesExtractor.extract([source], snapshot_date=snapshot_date)

    assert len(records) == 1
    assert records[0]["municipality_code"] == "3550308"
    assert records[0]["dt_base"] == snapshot_date
    assert records[0]["payload"] == source
    assert records[0]["payload"]["campo-novo"] == {"preserve": True}


def test_extract_does_not_apply_historical_exclusions() -> None:
    snapshot_date = date(2026, 8, 19)

    records = MunicipalitiesExtractor.extract(
        [_municipality(5101837)],
        snapshot_date=snapshot_date,
    )

    assert len(records) == 1
    assert records[0]["municipality_code"] == "5101837"
