from datetime import date

import pytest

from olist_data_platform.domains.ingestion.ibge import (
    municipality_population_extractor as population_extractor,
)


def _row(value: str = "11904961") -> dict:
    return {
        "Município (Código)": "3550308",
        "Município": "São Paulo (SP)",
        "Variável (Código)": "9324",
        "Variável": "População residente estimada",
        "Ano": "2018",
        "Unidade de Medida (Código)": "45",
        "Unidade de Medida": "Pessoas",
        "Nível Territorial (Código)": "6",
        "Nível Territorial": "Município",
        "Valor": value,
        "Campo novo": {"nested": True},
    }


def test_extract_preserves_population_source_payload() -> None:
    source = _row()
    [record] = population_extractor.MunicipalityPopulationExtractor.extract([source])

    assert record["municipality_code"] == "3550308"
    assert record["reference_year"] == "2018"
    assert record["variable_code"] == "9324"
    assert record["dt_base"] == date(2018, 1, 1)
    assert record["payload"] == source
    assert record["payload"]["Valor"] == "11904961"
    assert record["payload"]["Campo novo"] == {"nested": True}


def test_extract_rejects_non_numeric_reference_year() -> None:
    row = _row()
    row["Ano"] = "unknown"

    with pytest.raises(ValueError, match="Reference year"):
        population_extractor.MunicipalityPopulationExtractor.extract([row])
