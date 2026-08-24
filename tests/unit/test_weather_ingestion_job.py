from argparse import ArgumentTypeError, Namespace
from datetime import date
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.jobs.weather_ingestion import (
    _parse_daily_variables,
    _parse_date,
    run,
)


def test_should_parse_iso_date():
    assert _parse_date("2018-01-02") == date(2018, 1, 2)


def test_should_reject_invalid_date():
    with pytest.raises(ArgumentTypeError, match="Invalid ISO date"):
        _parse_date("2018-99-99")


def test_should_parse_daily_variables():
    assert _parse_daily_variables("temperature_2m_mean, rain_sum") == [
        "temperature_2m_mean",
        "rain_sum",
    ]


def _args(operation: str) -> Namespace:
    return Namespace(
        operation=operation,
        target_table="prd.bronze.weather_daily",
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        timezone="America/Sao_Paulo",
        daily_variables="temperature_2m_mean,rain_sum",
    )


@patch("olist_data_platform.jobs.weather_ingestion.WeatherIngestionService")
@patch("olist_data_platform.jobs.weather_ingestion.BronzeWeatherWriter")
@patch("olist_data_platform.jobs.weather_ingestion.OpenMeteoClient")
def test_should_execute_ingestion(
    mock_client_class,
    mock_writer_class,
    mock_service_class,
):
    spark = Mock()
    service = Mock()
    service.ingest.return_value = "request-123"
    mock_service_class.return_value = service

    result = run(args=_args("ingest"), spark=spark)

    mock_client_class.assert_called_once_with()
    mock_writer_class.assert_called_once_with(
        spark=spark,
        target_table="prd.bronze.weather_daily",
    )
    service.ingest.assert_called_once_with(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        daily_variables=["temperature_2m_mean", "rain_sum"],
        timezone="America/Sao_Paulo",
    )
    service.reprocess.assert_not_called()
    assert result == "request-123"


@patch("olist_data_platform.jobs.weather_ingestion.WeatherIngestionService")
@patch("olist_data_platform.jobs.weather_ingestion.BronzeWeatherWriter")
@patch("olist_data_platform.jobs.weather_ingestion.OpenMeteoClient")
def test_should_execute_explicit_reprocess(
    mock_client_class,
    mock_writer_class,
    mock_service_class,
):
    spark = Mock()
    service = Mock()
    service.reprocess.return_value = "request-456"
    mock_service_class.return_value = service

    result = run(args=_args("reprocess"), spark=spark)

    service.reprocess.assert_called_once()
    service.ingest.assert_not_called()
    assert result == "request-456"
