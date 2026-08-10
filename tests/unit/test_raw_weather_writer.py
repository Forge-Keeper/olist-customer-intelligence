from datetime import date
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.ingestion.writers.raw_weather_writer import (
    RawWeatherWriter,
)


def test_should_create_raw_weather_writer():
    spark = Mock()

    writer = RawWeatherWriter(
        spark=spark,
        target_table="raw.open_meteo",
    )

    assert writer.spark == spark
    assert writer.target_table == "raw.open_meteo"


@pytest.mark.parametrize(
    "target_table",
    [
        "",
        " ",
    ],
)
def test_should_reject_empty_target_table(
    target_table,
):
    with pytest.raises(ValueError):
        RawWeatherWriter(
            spark=Mock(),
            target_table=target_table,
        )


def test_should_reject_invalid_target_table_type():
    with pytest.raises(TypeError):
        RawWeatherWriter(
            spark=Mock(),
            target_table=None,  # ty: ignore[invalid-argument-type]
        )


@pytest.mark.parametrize(
    "request_id",
    [
        "",
        " ",
    ],
)
def test_should_reject_empty_request_id(
    request_id,
):
    writer = RawWeatherWriter(
        spark=Mock(),
        target_table="raw.open_meteo",
    )

    with pytest.raises(ValueError):
        writer.write(
            request_id=request_id,
            requested_latitude=-23.55,
            requested_longitude=-46.63,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 3),
            response={},
        )


@patch(
    "olist_data_platform.ingestion.writers."
    "raw_weather_writer.current_timestamp"
)
def test_should_write_raw_response_as_delta(
    mock_current_timestamp,
):
    spark = Mock()
    dataframe = Mock()
    timestamp_column = Mock()

    mock_current_timestamp.return_value = timestamp_column

    spark.createDataFrame.return_value = dataframe
    dataframe.withColumn.return_value = dataframe

    writer = RawWeatherWriter(
        spark=spark,
        target_table="raw.open_meteo",
    )

    response = {
        "latitude": -23.51,
        "longitude": -46.61,
    }

    writer.write(
        request_id="request-123",
        requested_latitude=-23.55,
        requested_longitude=-46.63,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 3),
        response=response,
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
            "raw.open_meteo"
        )
    )