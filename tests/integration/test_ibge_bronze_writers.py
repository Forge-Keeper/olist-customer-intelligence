from datetime import date
from unittest.mock import Mock

from pyspark.sql.types import DateType, StringType, VariantType

from olist_data_platform.domains.bronze.ibge.bronze_municipalities_writer import (
    BronzeMunicipalitiesWriter,
)
from olist_data_platform.domains.bronze.ibge.bronze_municipality_population_writer import (
    BronzeMunicipalityPopulationWriter,
)


def test_municipalities_writer_preserves_source_payload_as_variant(spark):
    writer = BronzeMunicipalitiesWriter(spark, "bronze.ibge_municipalities")
    captured = Mock()
    writer.writer = captured

    writer.write(
        records=[
            {
                "municipality_code": "3550308",
                "dt_base": date(2026, 8, 19),
                "payload": {
                    "id": 3550308,
                    "nome": "São Paulo",
                    "campo-novo": {"nested": True},
                },
            }
        ],
        request_id="request-localidades",
    )

    dataframe = captured.write.call_args.args[0]
    row = dataframe.first()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    assert row is not None
    assert row.municipality_code == "3550308"
    assert row.dt_base == date(2026, 8, 19)
    assert row.request_id == "request-localidades"
    assert isinstance(schema["municipality_code"], StringType)
    assert isinstance(schema["dt_base"], DateType)
    assert isinstance(schema["payload"], VariantType)

    payload_json = dataframe.selectExpr("to_json(payload) AS payload_json").first()
    assert payload_json is not None
    assert "campo-novo" in payload_json.payload_json


def test_population_writer_preserves_sidra_payload_as_variant(spark):
    writer = BronzeMunicipalityPopulationWriter(
        spark,
        "bronze.ibge_municipality_population",
    )
    captured = Mock()
    writer.writer = captured

    writer.write(
        records=[
            {
                "municipality_code": "3550308",
                "reference_year": "2018",
                "variable_code": "9324",
                "dt_base": date(2018, 1, 1),
                "payload": {
                    "Município (Código)": "3550308",
                    "Ano": "2018",
                    "Variável (Código)": "9324",
                    "Valor": "12176866",
                    "Campo novo": {"nested": True},
                },
            }
        ],
        request_id="request-population",
    )

    dataframe = captured.write.call_args.args[0]
    row = dataframe.first()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    assert row is not None
    assert row.municipality_code == "3550308"
    assert row.reference_year == "2018"
    assert row.variable_code == "9324"
    assert row.dt_base == date(2018, 1, 1)
    assert row.request_id == "request-population"
    assert isinstance(schema["reference_year"], StringType)
    assert isinstance(schema["payload"], VariantType)

    payload_json = dataframe.selectExpr("to_json(payload) AS payload_json").first()
    assert payload_json is not None
    assert '"Valor":"12176866"' in payload_json.payload_json
    assert "Campo novo" in payload_json.payload_json
