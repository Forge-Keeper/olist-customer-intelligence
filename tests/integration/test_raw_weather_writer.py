import json
from datetime import date, datetime

import pytest
from pyspark.sql.types import DoubleType, StringType, TimestampType

from olist_data_platform.domains.raw.weather.raw_weather_writer import (
    RawWeatherWriter,
)


@pytest.fixture
def weather_response() -> dict:
    return {
        "latitude": -23.514938,
        "longitude": -46.610504,
        "elevation": 758.0,
        "generationtime_ms": 8.47,
        "timezone": "America/Sao_Paulo",
        "timezone_abbreviation": "GMT-3",
        "utc_offset_seconds": -10800,
        "daily_units": {
            "time": "iso8601",
            "temperature_2m_mean": "°C",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "rain_sum": "mm",
            "wind_speed_10m_max": "km/h",
        },
        "daily": {
            "time": ["2018-01-01", "2018-01-02", "2018-01-03"],
            "temperature_2m_mean": [22.5, 22.2, 21.2],
            "temperature_2m_max": [25.7, 25.2, 23.8],
            "temperature_2m_min": [19.9, 20.1, 19.3],
            "rain_sum": [1.6, 1.1, 3.4],
            "wind_speed_10m_max": [20.2, 28.8, 24.5],
        },
    }


def _build(writer, weather_response):
    return writer._build_dataframe(
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 3),
        response=weather_response,
    )


def test_should_build_single_row_raw_dataframe(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    dataframe = _build(writer, weather_response)
    assert dataframe.count() == 1


def test_should_build_dataframe_with_expected_schema(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    dataframe = _build(writer, weather_response)
    assert dataframe.schema == RawWeatherWriter.SCHEMA


def test_should_preserve_request_metadata(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    row = _build(writer, weather_response).first()

    assert row is not None
    assert row.request_id == "request-123"
    assert row.requested_latitude == pytest.approx(-23.5505)
    assert row.requested_longitude == pytest.approx(-46.6333)
    assert row.start_date == "2018-01-01"
    assert row.end_date == "2018-01-03"


def test_should_serialize_original_response_as_json(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    row = _build(writer, weather_response).first()

    assert row is not None
    assert json.loads(row.response_json) == weather_response


def test_should_preserve_unicode_characters_in_response_json(
    spark,
    weather_response,
):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    row = _build(writer, weather_response).first()

    assert row is not None
    assert "°C" in row.response_json
    assert "\\u00b0C" not in row.response_json


def test_should_generate_ingestion_timestamp(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    row = _build(writer, weather_response).first()

    assert row is not None
    assert row.ingestion_timestamp is not None
    assert isinstance(row.ingestion_timestamp, datetime)


def test_should_create_expected_spark_data_types(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    dataframe = _build(writer, weather_response)

    schema = {
        field.name: field.dataType
        for field in dataframe.schema.fields
    }

    assert isinstance(schema["request_id"], StringType)
    assert isinstance(schema["requested_latitude"], DoubleType)
    assert isinstance(schema["requested_longitude"], DoubleType)
    assert isinstance(schema["start_date"], StringType)
    assert isinstance(schema["end_date"], StringType)
    assert isinstance(schema["response_json"], StringType)
    assert isinstance(schema["ingestion_timestamp"], TimestampType)


def test_should_preserve_complete_nested_response(spark, weather_response):
    writer = RawWeatherWriter(spark=spark, target_table="raw.open_meteo")
    row = _build(writer, weather_response).first()

    assert row is not None

    response = json.loads(row.response_json)

    assert response["daily"]["time"] == [
        "2018-01-01",
        "2018-01-02",
        "2018-01-03",
    ]
    assert response["daily"]["rain_sum"] == [1.6, 1.1, 3.4]
    assert response["daily_units"]["temperature_2m_mean"] == "°C"
