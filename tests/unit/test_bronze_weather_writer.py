from datetime import date
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.domains.bronze.weather.bronze_weather_writer import (
    BronzeWeatherWriter,
)


def _record():
    return {
        "dt_base": date(2018, 1, 1),
        "payload": {
            "timezone": "America/Sao_Paulo",
            "daily": {"time": "2018-01-01", "temperature_2m_mean": 22.5},
        },
    }


def test_should_skip_empty_records():
    spark = Mock()
    writer = BronzeWeatherWriter(spark, "bronze.weather_daily")

    writer.write([], "request-1", -23.55, -46.63)

    spark.createDataFrame.assert_not_called()


def test_should_reject_record_without_date():
    writer = BronzeWeatherWriter(Mock(), "bronze.weather_daily")

    with pytest.raises(TypeError, match="dt_base"):
        writer.write(
            [{"payload": {}}],
            "request-1",
            -23.55,
            -46.63,
        )


def test_should_reject_record_without_payload():
    writer = BronzeWeatherWriter(Mock(), "bronze.weather_daily")

    with pytest.raises(TypeError, match="payload"):
        writer.write(
            [{"dt_base": date(2018, 1, 1)}],
            "request-1",
            -23.55,
            -46.63,
        )


@patch(
    "olist_data_platform.domains.bronze.weather.bronze_weather_writer.F.parse_json"
)
def test_should_build_variant_payload_and_delegate_to_generic_writer(mock_parse_json):
    spark = Mock()
    dataframe = Mock()
    with_payload = Mock()
    final_dataframe = Mock()

    spark.createDataFrame.return_value = dataframe
    dataframe.withColumn.return_value = with_payload
    with_payload.drop.return_value = final_dataframe
    mock_parse_json.return_value = Mock(name="variant_expression")

    writer = BronzeWeatherWriter(spark, "bronze.weather_daily")
    writer.writer = Mock()

    writer.write([_record()], "request-1", -23.55, -46.63)

    spark.createDataFrame.assert_called_once()
    mock_parse_json.assert_called_once_with("payload_json")
    writer.writer.write.assert_called_once_with(final_dataframe)


@patch(
    "olist_data_platform.domains.bronze.weather.bronze_weather_writer.F.parse_json"
)
def test_should_reprocess_explicit_scope_with_replace_where(mock_parse_json):
    spark = Mock()
    dataframe = Mock()
    with_payload = Mock()
    final_dataframe = Mock()

    spark.createDataFrame.return_value = dataframe
    dataframe.withColumn.return_value = with_payload
    with_payload.drop.return_value = final_dataframe
    mock_parse_json.return_value = Mock(name="variant_expression")

    writer = BronzeWeatherWriter(spark, "bronze.weather_daily")
    writer.writer = Mock()

    writer.reprocess(
        records=[_record()],
        request_id="request-1",
        requested_latitude=-23.55,
        requested_longitude=-46.63,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 31),
    )

    writer.writer.replace_where.assert_called_once_with(
        final_dataframe,
        "dt_base >= DATE '2018-01-01' AND dt_base <= DATE '2018-01-31' "
        "AND requested_latitude = -23.55 AND requested_longitude = -46.63",
    )


def test_should_reject_invalid_reprocess_range():
    writer = BronzeWeatherWriter(Mock(), "bronze.weather_daily")

    with pytest.raises(ValueError, match="start_date"):
        writer.reprocess(
            records=[_record()],
            request_id="request-1",
            requested_latitude=-23.55,
            requested_longitude=-46.63,
            start_date=date(2018, 2, 1),
            end_date=date(2018, 1, 1),
        )


def test_should_validate_coordinates():
    writer = BronzeWeatherWriter(Mock(), "bronze.weather_daily")

    with pytest.raises(ValueError, match="latitude"):
        writer.write([_record()], "request-1", 100.0, -46.63)
