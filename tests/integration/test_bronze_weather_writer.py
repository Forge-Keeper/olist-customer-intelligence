from datetime import date, datetime

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    TimestampType,
)

from olist_data_platform.ingestion.writers.bronze_weather_writer import (
    BronzeWeatherWriter,
)


@pytest.fixture
def weather_records() -> list[dict]:
    return [
        {
            "dt_base": date(2018, 1, 1),
            "temperature_2m_mean": 22.5,
            "temperature_2m_max": 25.7,
            "temperature_2m_min": 19.9,
            "rain_sum": 1.6,
            "wind_speed_10m_max": 20.2,
            "weather_latitude": -23.514938,
            "weather_longitude": -46.610504,
            "elevation": 758.0,
            "timezone": "America/Sao_Paulo",
            "timezone_abbreviation": "GMT-3",
            "utc_offset_seconds": -10800,
        },
        {
            "dt_base": date(2018, 1, 2),
            "temperature_2m_mean": 22.2,
            "temperature_2m_max": 25.2,
            "temperature_2m_min": 20.1,
            "rain_sum": 1.1,
            "wind_speed_10m_max": 28.8,
            "weather_latitude": -23.514938,
            "weather_longitude": -46.610504,
            "elevation": 758.0,
            "timezone": "America/Sao_Paulo",
            "timezone_abbreviation": "GMT-3",
            "utc_offset_seconds": -10800,
        },
    ]


def test_should_build_real_bronze_dataframe(
    spark: SparkSession,
    weather_records: list[dict],
) -> None:
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    dataframe = writer._build_dataframe(
        records=weather_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
    )

    assert dataframe.count() == 2


def test_should_build_dataframe_with_expected_schema(
    spark: SparkSession,
    weather_records: list[dict],
) -> None:
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    dataframe = writer._build_dataframe(
        records=weather_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
    )

    assert (
        dataframe.schema
        == BronzeWeatherWriter.SCHEMA
    )


def test_should_preserve_weather_record_values(
    spark: SparkSession,
    weather_records: list[dict],
) -> None:
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    first_row = (
        writer
        ._build_dataframe(
            records=weather_records,
            request_id="request-123",
            requested_latitude=-23.5505,
            requested_longitude=-46.6333,
        )
        .orderBy("dt_base")
        .first()
    )

    assert first_row is not None

    assert first_row.dt_base == date(
        2018,
        1,
        1,
    )
    assert (
        first_row.temperature_2m_mean
        == 22.5
    )
    assert (
        first_row.temperature_2m_max
        == 25.7
    )
    assert (
        first_row.temperature_2m_min
        == 19.9
    )
    assert first_row.rain_sum == 1.6
    assert (
        first_row.wind_speed_10m_max
        == 20.2
    )


def test_should_add_request_metadata_to_every_record(
    spark: SparkSession,
    weather_records: list[dict],
) -> None:
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    rows = (
        writer
        ._build_dataframe(
            records=weather_records,
            request_id="request-123",
            requested_latitude=-23.5505,
            requested_longitude=-46.6333,
        )
        .collect()
    )

    for row in rows:
        assert (
            row.request_id
            == "request-123"
        )
        assert row.requested_latitude == (
            pytest.approx(-23.5505)
        )
        assert row.requested_longitude == (
            pytest.approx(-46.6333)
        )


def test_should_generate_ingestion_timestamp(
    spark: SparkSession,
    weather_records: list[dict],
) -> None:
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    rows = (
        writer
        ._build_dataframe(
            records=weather_records,
            request_id="request-123",
            requested_latitude=-23.5505,
            requested_longitude=-46.6333,
        )
        .collect()
    )

    for row in rows:
        assert (
            row.ingestion_timestamp
            is not None
        )
        assert isinstance(
            row.ingestion_timestamp,
            datetime,
        )


def test_should_create_expected_spark_data_types(
    spark: SparkSession,
    weather_records: list[dict],
) -> None:
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    dataframe = writer._build_dataframe(
        records=weather_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
    )

    schema = {
        field.name: field.dataType
        for field in dataframe.schema.fields
    }

    assert isinstance(
        schema["request_id"],
        StringType,
    )
    assert isinstance(
        schema["requested_latitude"],
        DoubleType,
    )
    assert isinstance(
        schema["requested_longitude"],
        DoubleType,
    )
    assert isinstance(
        schema["dt_base"],
        DateType,
    )
    assert isinstance(
        schema["temperature_2m_mean"],
        DoubleType,
    )
    assert isinstance(
        schema["utc_offset_seconds"],
        IntegerType,
    )
    assert isinstance(
        schema["ingestion_timestamp"],
        TimestampType,
    )


def test_should_keep_nullable_weather_values(
    spark: SparkSession,
) -> None:
    records = [
        {
            "dt_base": date(2018, 1, 1),
            "temperature_2m_mean": None,
            "temperature_2m_max": None,
            "temperature_2m_min": None,
            "rain_sum": None,
            "wind_speed_10m_max": None,
            "weather_latitude": -23.514938,
            "weather_longitude": -46.610504,
            "elevation": None,
            "timezone": "America/Sao_Paulo",
            "timezone_abbreviation": None,
            "utc_offset_seconds": None,
        }
    ]

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    row = (
        writer
        ._build_dataframe(
            records=records,
            request_id="request-123",
            requested_latitude=-23.5505,
            requested_longitude=-46.6333,
        )
        .first()
    )

    assert row is not None
    assert (
        row.temperature_2m_mean
        is None
    )
    assert (
        row.temperature_2m_max
        is None
    )
    assert (
        row.temperature_2m_min
        is None
    )
    assert row.rain_sum is None
    assert (
        row.wind_speed_10m_max
        is None
    )
    assert row.elevation is None
    assert (
        row.timezone_abbreviation
        is None
    )
    assert (
        row.utc_offset_seconds
        is None
    )
