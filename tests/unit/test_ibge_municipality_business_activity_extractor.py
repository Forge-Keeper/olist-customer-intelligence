from datetime import date

import pytest

from olist_data_platform.domains.ingestion.ibge import (
    municipality_business_activity_extractor as cempre_extractor,
)


def test_extract_preserves_cempre_payload_and_derives_keys() -> None:
    row = {
        "Município (Código)": "3550308",
        "Ano": "2016",
        "Variável (Código)": "367",
        "Valor": "...",
    }

    [record] = cempre_extractor.MunicipalityBusinessActivityExtractor.extract([row])

    assert record["municipality_code"] == "3550308"
    assert record["reference_year"] == "2016"
    assert record["variable_code"] == "367"
    assert record["dt_base"] == date(2016, 1, 1)
    assert record["payload"] == row


def test_extract_rejects_non_numeric_reference_year() -> None:
    with pytest.raises(ValueError, match="Reference year"):
        cempre_extractor.MunicipalityBusinessActivityExtractor.extract(
            [
                {
                    "Município (Código)": "3550308",
                    "Ano": "latest",
                    "Variável (Código)": "367",
                }
            ]
        )
