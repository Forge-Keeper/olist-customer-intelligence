import pytest

from olist_data_platform.domains.ingestion.ibge.sidra_parser import SidraParser


PAYLOAD = [
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
        "D3C": "2025",
        "D3N": "2025",
        "MC": "45",
        "MN": "Pessoas",
        "NC": "6",
        "NN": "Município",
        "V": "11904961",
    },
]


def test_split_separates_header_from_rows() -> None:
    header, rows = SidraParser.split(PAYLOAD)

    assert header["D1C"] == "Município (Código)"
    assert len(rows) == 1
    assert rows[0]["D1C"] == "3550308"


def test_decode_uses_header_as_dynamic_mapping() -> None:
    rows = SidraParser.decode(PAYLOAD)

    assert rows == [
        {
            "Município (Código)": "3550308",
            "Município": "São Paulo (SP)",
            "Variável (Código)": "9324",
            "Variável": "População residente estimada",
            "Ano (Código)": "2025",
            "Ano": "2025",
            "Unidade de Medida (Código)": "45",
            "Unidade de Medida": "Pessoas",
            "Nível Territorial (Código)": "6",
            "Nível Territorial": "Município",
            "Valor": "11904961",
        }
    ]


def test_decode_preserves_unknown_keys() -> None:
    payload = [
        {"D1C": "Território (Código)"},
        {"D1C": "1", "EXTRA": "value"},
    ]

    assert SidraParser.decode(payload) == [
        {"Território (Código)": "1", "EXTRA": "value"}
    ]


def test_split_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="payload cannot be empty"):
        SidraParser.split([])
