from datetime import date
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


@pytest.fixture
def bronze_metadata():
    return {
        "min_date": date(2018, 1, 1),
        "max_date": date(2018, 1, 3),
        "latitude": -23.5505,
        "longitude": -46.6333,
    }


@pytest.fixture
def existing_data_condition() -> Mock:
    return Mock(name="existing_data_condition")


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


@patch.object(BronzeWeatherWriter, "_write_dataframe")
@patch.object(BronzeWeatherWriter, "_build_dataframe")
def test_should_write_bronze_records_as_delta(
    mock_build_dataframe,
    mock_write_dataframe,
):
    spark = Mock()
    dataframe = Mock()

    mock_build_dataframe.return_value = dataframe

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

    mock_build_dataframe.assert_called_once_with(
        records=[_weather_record()],
        request_id="request-123",
        requested_latitude=-23.55,
        requested_longitude=-46.63,
    )

    mock_write_dataframe.assert_called_once_with(
        dataframe=dataframe,
        overwrite=False,
    )


def test_should_build_replace_where_condition():
    replace_where = BronzeWeatherWriter._build_replace_where(
        min_date=date(2018, 1, 1),
        max_date=date(2018, 1, 3),
        latitude=-23.5505,
        longitude=-46.6333,
    )

    assert replace_where == (
        "date >= DATE '2018-01-01' "
        "AND date <= DATE '2018-01-03' "
        "AND requested_latitude = -23.5505 "
        "AND requested_longitude = -46.6333"
    )


@patch.object(BronzeWeatherWriter, "_build_existing_data_condition")
@patch.object(BronzeWeatherWriter, "_build_replace_where")
@patch.object(BronzeWeatherWriter, "_get_dataframe_metadata")
def test_should_write_when_target_table_does_not_exist(
    mock_get_metadata,
    mock_build_replace_where,
    mock_build_condition,
    bronze_metadata,
    existing_data_condition,
):
    spark = Mock()
    dataframe = Mock()

    mock_get_metadata.return_value = bronze_metadata
    mock_build_condition.return_value = existing_data_condition
    mock_build_replace_where.return_value = "date >= DATE '2018-01-01'"
    spark.catalog.tableExists.return_value = False

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )

    writer._write_dataframe(
        dataframe=dataframe,
        overwrite=False,
    )

    spark.catalog.tableExists.assert_called_once_with(
        "prd.bronze.weather_daily"
    )

    mock_build_condition.assert_called_once_with(
        min_date=date(2018, 1, 1),
        max_date=date(2018, 1, 3),
        latitude=-23.5505,
        longitude=-46.6333,
    )

    mock_build_replace_where.assert_called_once_with(
        min_date=date(2018, 1, 1),
        max_date=date(2018, 1, 3),
        latitude=-23.5505,
        longitude=-46.6333,
    )

    dataframe.write.format.assert_called_once_with("delta")
    dataframe.write.format.return_value.mode.assert_called_once_with(
        "overwrite"
    )
    (
        dataframe.write
        .format.return_value
        .mode.return_value
        .option.assert_called_once_with(
            "replaceWhere",
            "date >= DATE '2018-01-01'",
        )
    )
    (
        dataframe.write
        .format.return_value
        .mode.return_value
        .option.return_value
        .partitionBy.assert_called_once_with("date")
    )
    (
        dataframe.write
        .format.return_value
        .mode.return_value
        .option.return_value
        .partitionBy.return_value
        .saveAsTable.assert_called_once_with("prd.bronze.weather_daily")
    )


@patch.object(BronzeWeatherWriter, "_build_existing_data_condition")
@patch.object(BronzeWeatherWriter, "_get_dataframe_metadata")
def test_should_raise_when_data_exists_and_overwrite_is_false(
    mock_get_metadata,
    mock_build_condition,
    bronze_metadata,
    existing_data_condition,
):
    spark = Mock()
    dataframe = Mock()
    target_dataframe = Mock()
    filtered_dataframe = Mock()

    mock_get_metadata.return_value = bronze_metadata
    mock_build_condition.return_value = existing_data_condition
    spark.catalog.tableExists.return_value = True
    spark.table.return_value = target_dataframe
    target_dataframe.where.return_value = filtered_dataframe
    filtered_dataframe.isEmpty.return_value = False

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )

    with pytest.raises(
        ValueError,
        match="Bronze weather data already exists",
    ):
        writer._write_dataframe(
            dataframe=dataframe,
            overwrite=False,
        )

    target_dataframe.where.assert_called_once_with(
        existing_data_condition
    )
    dataframe.write.format.assert_not_called()


@patch.object(BronzeWeatherWriter, "_build_existing_data_condition")
@patch.object(BronzeWeatherWriter, "_build_replace_where")
@patch.object(BronzeWeatherWriter, "_get_dataframe_metadata")
def test_should_replace_existing_data_when_overwrite_is_true(
    mock_get_metadata,
    mock_build_replace_where,
    mock_build_condition,
    bronze_metadata,
    existing_data_condition,
):
    spark = Mock()
    dataframe = Mock()
    target_dataframe = Mock()
    filtered_dataframe = Mock()

    mock_get_metadata.return_value = bronze_metadata
    mock_build_condition.return_value = existing_data_condition
    mock_build_replace_where.return_value = (
        "date >= DATE '2018-01-01' "
        "AND date <= DATE '2018-01-03' "
        "AND requested_latitude = -23.5505 "
        "AND requested_longitude = -46.6333"
    )
    spark.catalog.tableExists.return_value = True
    spark.table.return_value = target_dataframe
    target_dataframe.where.return_value = filtered_dataframe
    filtered_dataframe.isEmpty.return_value = False

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )

    writer._write_dataframe(
        dataframe=dataframe,
        overwrite=True,
    )

    target_dataframe.where.assert_called_once_with(
        existing_data_condition
    )
    dataframe.write.format.assert_called_once_with("delta")
    dataframe.write.format.return_value.mode.assert_called_once_with(
        "overwrite"
    )
    (
        dataframe.write
        .format.return_value
        .mode.return_value
        .option.assert_called_once_with(
            "replaceWhere",
            mock_build_replace_where.return_value,
        )
    )


@patch.object(BronzeWeatherWriter, "_build_existing_data_condition")
@patch.object(BronzeWeatherWriter, "_build_replace_where")
@patch.object(BronzeWeatherWriter, "_get_dataframe_metadata")
def test_should_write_when_table_exists_but_data_does_not(
    mock_get_metadata,
    mock_build_replace_where,
    mock_build_condition,
    bronze_metadata,
    existing_data_condition,
):
    spark = Mock()
    dataframe = Mock()
    target_dataframe = Mock()
    filtered_dataframe = Mock()

    mock_get_metadata.return_value = bronze_metadata
    mock_build_condition.return_value = existing_data_condition
    mock_build_replace_where.return_value = "date >= DATE '2018-01-01'"
    spark.catalog.tableExists.return_value = True
    spark.table.return_value = target_dataframe
    target_dataframe.where.return_value = filtered_dataframe
    filtered_dataframe.isEmpty.return_value = True

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )

    writer._write_dataframe(
        dataframe=dataframe,
        overwrite=False,
    )

    target_dataframe.where.assert_called_once_with(
        existing_data_condition
    )
    dataframe.write.format.assert_called_once_with("delta")


@patch.object(BronzeWeatherWriter, "_build_existing_data_condition")
@patch.object(BronzeWeatherWriter, "_build_replace_where")
@patch.object(BronzeWeatherWriter, "_get_dataframe_metadata")
def test_should_not_raise_when_data_exists_and_overwrite_is_true(
    mock_get_metadata,
    mock_build_replace_where,
    mock_build_condition,
    bronze_metadata,
    existing_data_condition,
):
    spark = Mock()
    dataframe = Mock()
    target_dataframe = Mock()
    filtered_dataframe = Mock()

    mock_get_metadata.return_value = bronze_metadata
    mock_build_condition.return_value = existing_data_condition
    mock_build_replace_where.return_value = "date >= DATE '2018-01-01'"
    spark.catalog.tableExists.return_value = True
    spark.table.return_value = target_dataframe
    target_dataframe.where.return_value = filtered_dataframe
    filtered_dataframe.isEmpty.return_value = False

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )

    writer._write_dataframe(
        dataframe=dataframe,
        overwrite=True,
    )

    dataframe.write.format.assert_called_once_with("delta")


@patch.object(BronzeWeatherWriter, "_write_dataframe")
@patch.object(BronzeWeatherWriter, "_build_dataframe")
def test_should_forward_overwrite_to_write_dataframe(
    mock_build_dataframe,
    mock_write_dataframe,
):
    spark = Mock()
    dataframe = Mock()

    mock_build_dataframe.return_value = dataframe

    writer = BronzeWeatherWriter(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )

    writer.write(
        records=[_weather_record()],
        request_id="request-123",
        requested_latitude=-23.55,
        requested_longitude=-46.63,
        overwrite=True,
    )

    mock_write_dataframe.assert_called_once_with(
        dataframe=dataframe,
        overwrite=True,
    )
