from unittest.mock import Mock, patch

import pytest

from olist_data_platform.ingestion.writers.bronze_weather_writer import (
    BronzeWeatherWriter,
)


def _weather_record():
    return {
        "date": "2018-01-01",
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
    }


def test_should_create_bronze_writer():
    spark = Mock()

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    assert writer.spark == spark
    assert writer.target_table == "bronze.weather_daily"


def test_should_not_write_when_records_are_empty():
    spark = Mock()

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    writer.write(
        records=[],
        request_id="request-123",
        requested_latitude=-23.55,
        requested_longitude=-46.63,
    )

    spark.createDataFrame.assert_not_called()


def test_should_reject_invalid_records_type():
    writer = BronzeWeatherWriter(
        spark=Mock(),
        target_table="bronze.weather_daily",
    )

    with pytest.raises(TypeError):
        writer.write(
            records={},  # ty: ignore[invalid-argument-type]
            request_id="request-123",
            requested_latitude=-23.55,
            requested_longitude=-46.63,
        )


def test_should_reject_non_dictionary_records():
    writer = BronzeWeatherWriter(
        spark=Mock(),
        target_table="bronze.weather_daily",
    )

    with pytest.raises(TypeError):
        writer.write(
            records=[
                _weather_record(),
                "invalid-record",
            ],  # ty: ignore[invalid-argument-type]
            request_id="request-123",
            requested_latitude=-23.55,
            requested_longitude=-46.63,
        )


@patch(
    "olist_data_platform.ingestion.writers."
    "bronze_weather_writer.current_timestamp"
)
def test_should_write_bronze_records_as_delta(
    mock_current_timestamp,
):
    spark = Mock()
    dataframe = Mock()
    timestamp_column = Mock()

    mock_current_timestamp.return_value = timestamp_column

    spark.createDataFrame.return_value = dataframe
    dataframe.withColumn.return_value = dataframe

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="bronze.weather_daily",
    )

    writer.write(
        records=[_weather_record()],
        request_id="request-123",
        requested_latitude=-23.55,
        requested_longitude=-46.63,
    )

    spark.createDataFrame.assert_called_once()

    mock_current_timestamp.assert_called_once_with()

    dataframe.withColumn.assert_called_once_with(
        "ingestion_timestamp",
        timestamp_column,
    )

    dataframe.write.format.assert_called_once_with(
        "delta"
    )

    dataframe.write.format.return_value.mode.assert_called_once_with(
        "append"
    )

    (
        dataframe.write
        .format.return_value
        .mode.return_value
        .saveAsTable
        .assert_called_once_with(
            "bronze.weather_daily"
        )
    )