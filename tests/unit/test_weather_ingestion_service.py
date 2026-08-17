from datetime import date
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.domains.ingestion.weather.weather_ingestion_service import (
    WeatherIngestionService,
)


@pytest.fixture
def client() -> Mock:
    return Mock()


@pytest.fixture
def bronze_writer() -> Mock:
    return Mock()


@pytest.fixture
def weather_response() -> dict:
    return {
        "latitude": -23.514938,
        "longitude": -46.610504,
        "timezone": "America/Sao_Paulo",
        "daily": {
            "time": ["2018-01-01", "2018-01-02"],
            "temperature_2m_mean": [22.5, 22.2],
        },
    }


@pytest.fixture
def daily_records() -> list[dict]:
    return [
        {"dt_base": date(2018, 1, 1), "payload": {"daily": {"time": "2018-01-01"}}},
        {"dt_base": date(2018, 1, 2), "payload": {"daily": {"time": "2018-01-02"}}},
    ]


@pytest.fixture
def service(client: Mock, bronze_writer: Mock) -> WeatherIngestionService:
    return WeatherIngestionService(
        client=client,
        bronze_writer=bronze_writer,
        request_id_factory=lambda: "request-123",
    )


def test_should_request_historical_weather(service, client, weather_response):
    client.get_historical_weather.return_value = weather_response

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        timezone="America/Sao_Paulo",
    )

    client.get_historical_weather.assert_called_once_with(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        daily_variables=None,
        timezone="America/Sao_Paulo",
    )


@patch(
    "olist_data_platform.domains.ingestion.weather."
    "weather_ingestion_service.WeatherDailyExtractor.extract"
)
def test_should_extract_and_write_daily_bronze_records(
    mock_extract,
    service,
    client,
    bronze_writer,
    weather_response,
    daily_records,
):
    client.get_historical_weather.return_value = weather_response
    mock_extract.return_value = daily_records

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    mock_extract.assert_called_once_with(weather_response)
    bronze_writer.write.assert_called_once_with(
        records=daily_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
    )
    bronze_writer.reprocess.assert_not_called()


@patch(
    "olist_data_platform.domains.ingestion.weather."
    "weather_ingestion_service.WeatherDailyExtractor.extract"
)
def test_should_reprocess_explicit_weather_scope(
    mock_extract,
    service,
    client,
    bronze_writer,
    weather_response,
    daily_records,
):
    client.get_historical_weather.return_value = weather_response
    mock_extract.return_value = daily_records

    service.reprocess(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    bronze_writer.reprocess.assert_called_once_with(
        records=daily_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )
    bronze_writer.write.assert_not_called()


def test_should_return_generated_request_id(service, client, weather_response):
    client.get_historical_weather.return_value = weather_response

    request_id = service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    assert request_id == "request-123"


def test_should_not_write_when_api_request_fails(service, client, bronze_writer):
    client.get_historical_weather.side_effect = RuntimeError("API unavailable")

    with pytest.raises(RuntimeError, match="API unavailable"):
        service.ingest(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 2),
        )

    bronze_writer.write.assert_not_called()
    bronze_writer.reprocess.assert_not_called()


@patch(
    "olist_data_platform.domains.ingestion.weather."
    "weather_ingestion_service.WeatherDailyExtractor.extract"
)
def test_should_not_write_when_extraction_fails(
    mock_extract,
    service,
    client,
    bronze_writer,
    weather_response,
):
    client.get_historical_weather.return_value = weather_response
    mock_extract.side_effect = ValueError("Invalid weather response")

    with pytest.raises(ValueError, match="Invalid weather response"):
        service.ingest(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 2),
        )

    bronze_writer.write.assert_not_called()
    bronze_writer.reprocess.assert_not_called()


def test_should_generate_request_id_when_factory_is_not_provided(
    client,
    bronze_writer,
    weather_response,
):
    client.get_historical_weather.return_value = weather_response
    service = WeatherIngestionService(client=client, bronze_writer=bronze_writer)

    request_id = service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    assert isinstance(request_id, str)
    assert request_id
