from datetime import date

import pytest

from olist_data_platform.domains.ingestion.ibge.municipality_population_extractor import (
    MunicipalityPopulationExtractor,
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
    }


def test_extract_types_population_contract() -> None:
    [record] = MunicipalityPopulationExtractor.extract([_row()])
    assert record["municipality_code"] == "3550308"
    assert record["reference_year"] == 2018
    assert record["value"] == 11904961
    assert record["dt_base"] == date(2018, 1, 1)


def test_extract_rejects_special_population_value() -> None:
    with pytest.raises(ValueError, match="numeric string"):
        MunicipalityPopulationExtractor.extract([_row("...")])
