from datetime import date

import pytest

from olist_data_platform.domains.ingestion.ibge.municipality_gdp_extractor import (
    MunicipalityGdpExtractor,
)


def test_extract_preserves_sidra_gdp_payload_and_technical_grain() -> None:
    source_row = {
        "Município (Código)": "3550308",
        "Município": "São Paulo (SP)",
        "Variável (Código)": "37",
        "Variável": "Produto Interno Bruto a preços correntes",
        "Ano": "2018",
        "Unidade de Medida": "Mil Reais",
        "Valor": "714683362",
        "Campo novo": "preservar",
    }

    [record] = MunicipalityGdpExtractor.extract([source_row])

    assert record["municipality_code"] == "3550308"
    assert record["reference_year"] == "2018"
    assert record["variable_code"] == "37"
    assert record["dt_base"] == date(2018, 1, 1)
    assert record["payload"] == source_row
    assert record["payload"]["Valor"] == "714683362"


def test_extract_preserves_special_sidra_value_marker() -> None:
    source_row = {
        "Município (Código)": "3550308",
        "Variável (Código)": "6575",
        "Ano": "2018",
        "Valor": "...",
    }

    [record] = MunicipalityGdpExtractor.extract([source_row])

    assert record["payload"]["Valor"] == "..."


def test_extract_rejects_non_numeric_reference_year() -> None:
    with pytest.raises(ValueError, match="Reference year"):
        MunicipalityGdpExtractor.extract(
            [
                {
                    "Município (Código)": "3550308",
                    "Variável (Código)": "37",
                    "Ano": "last",
                    "Valor": "1",
                }
            ]
        )
