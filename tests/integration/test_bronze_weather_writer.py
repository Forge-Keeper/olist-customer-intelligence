from datetime import date
from unittest.mock import Mock

from pyspark.sql.types import DateType, DoubleType, StringType, VariantType

from olist_data_platform.domains.bronze.weather.bronze_weather_writer import (
    BronzeWeatherWriter,
)


def test_should_build_daily_variant_bronze_dataframe(spark):
    writer = BronzeWeatherWriter(spark, "bronze.weather_daily")
    captured = Mock()
    writer.writer = captured

    writer.write(
        records=[
            {
                "dt_base": date(2018, 1, 1),
                "payload": {
                    "timezone": "America/Sao_Paulo",
                    "daily": {
                        "time": "2018-01-01",
                        "temperature_2m_mean": 22.5,
                        "unexpected_new_field": {"nested": True},
                    },
                },
            }
        ],
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
    )

    dataframe = captured.write.call_args.args[0]
    row = dataframe.first()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    assert row is not None
    assert row.dt_base == date(2018, 1, 1)
    assert row.request_id == "request-123"
    assert row.requested_latitude == -23.5505
    assert row.requested_longitude == -46.6333

    assert isinstance(schema["dt_base"], DateType)
    assert isinstance(schema["payload"], VariantType)
    assert isinstance(schema["request_id"], StringType)
    assert isinstance(schema["requested_latitude"], DoubleType)
    assert isinstance(schema["requested_longitude"], DoubleType)

    payload_json = dataframe.selectExpr("to_json(payload) AS payload_json").first()
    assert payload_json is not None
    assert "unexpected_new_field" in payload_json.payload_json
