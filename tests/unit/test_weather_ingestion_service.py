from datetime import date
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.ingestion.services.weather_ingestion_service import (
    WeatherIngestionService,
)


@pytest.fixture
def client() -> Mock:
    return Mock()


@pytest.fixture
def raw_writer() -> Mock:
    return Mock()


@pytest.fixture
def bronze_writer() -> Mock:
    return Mock()


@pytest.fixture
def weather_response() -> dict:
    return {
        "latitude": -23.514938,
        "longitude": -46.610504,
        "elevation": 758.0,
        "timezone": "America/Sao_Paulo",
        "timezone_abbreviation": "GMT-3",
        "utc_offset_seconds": -10800,
        "daily": {
            "time": [
                "2018-01-01",
                "2018-01-02",
            ],
            "temperature_2m_mean": [
                22.5,
                22.2,
            ],
            "temperature_2m_max": [
                25.7,
                25.2,
            ],
            "temperature_2m_min": [
                19.9,
                20.1,
            ],
            "rain_sum": [
                1.6,
                1.1,
            ],
            "wind_speed_10m_max": [
                20.2,
                28.8,
            ],
        },
    }


@pytest.fixture
def parsed_records() -> list[dict]:
    return [
        {
            "date": "2018-01-01",
            "temperature_2m_mean": 22.5,
        },
        {
            "date": "2018-01-02",
            "temperature_2m_mean": 22.2,
        },
    ]


@pytest.fixture
def service(
    client: Mock,
    raw_writer: Mock,
    bronze_writer: Mock,
) -> WeatherIngestionService:
    return WeatherIngestionService(
        client=client,
        raw_writer=raw_writer,
        bronze_writer=bronze_writer,
        request_id_factory=lambda: "request-123",
    )


def test_should_request_historical_weather(
    service: WeatherIngestionService,
    client: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

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


def test_should_forward_custom_daily_variables(
    service: WeatherIngestionService,
    client: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    variables = [
        "temperature_2m_mean",
        "rain_sum",
    ]

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        daily_variables=variables,
    )

    client.get_historical_weather.assert_called_once_with(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        daily_variables=variables,
        timezone="auto",
    )


def test_should_write_original_response_to_raw(
    service: WeatherIngestionService,
    client: Mock,
    raw_writer: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    raw_writer.write.assert_called_once_with(
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        response=weather_response,
    )


@patch(
    "olist_data_platform.ingestion.services."
    "weather_ingestion_service.WeatherResponseParser.parse"
)
def test_should_parse_api_response(
    mock_parse: Mock,
    service: WeatherIngestionService,
    client: Mock,
    weather_response: dict,
    parsed_records: list[dict],
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    mock_parse.return_value = parsed_records

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    mock_parse.assert_called_once_with(
        weather_response
    )


@patch(
    "olist_data_platform.ingestion.services."
    "weather_ingestion_service.WeatherResponseParser.parse"
)
def test_should_write_parsed_records_to_bronze(
    mock_parse: Mock,
    service: WeatherIngestionService,
    client: Mock,
    bronze_writer: Mock,
    weather_response: dict,
    parsed_records: list[dict],
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    mock_parse.return_value = parsed_records

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    bronze_writer.write.assert_called_once_with(
        records=parsed_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
        overwrite=False,
    )


@patch(
    "olist_data_platform.ingestion.services."
    "weather_ingestion_service.WeatherResponseParser.parse"
)
def test_should_forward_overwrite_to_bronze_writer(
    mock_parse: Mock,
    service: WeatherIngestionService,
    client: Mock,
    bronze_writer: Mock,
    weather_response: dict,
    parsed_records: list[dict],
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    mock_parse.return_value = parsed_records

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
        overwrite=True,
    )

    bronze_writer.write.assert_called_once_with(
        records=parsed_records,
        request_id="request-123",
        requested_latitude=-23.5505,
        requested_longitude=-46.6333,
        overwrite=True,
    )


def test_should_use_same_request_id_for_raw_and_bronze(
    service: WeatherIngestionService,
    client: Mock,
    raw_writer: Mock,
    bronze_writer: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    raw_request_id = (
        raw_writer.write
        .call_args.kwargs["request_id"]
    )

    bronze_request_id = (
        bronze_writer.write
        .call_args.kwargs["request_id"]
    )

    assert raw_request_id == "request-123"
    assert bronze_request_id == "request-123"
    assert raw_request_id == bronze_request_id


def test_should_return_generated_request_id(
    service: WeatherIngestionService,
    client: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    request_id = service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    assert request_id == "request-123"


def test_should_not_write_anything_when_api_request_fails(
    service: WeatherIngestionService,
    client: Mock,
    raw_writer: Mock,
    bronze_writer: Mock,
) -> None:
    client.get_historical_weather.side_effect = (
        RuntimeError("API unavailable")
    )

    with pytest.raises(
        RuntimeError,
        match="API unavailable",
    ):
        service.ingest(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 2),
        )

    raw_writer.write.assert_not_called()
    bronze_writer.write.assert_not_called()


@patch(
    "olist_data_platform.ingestion.services."
    "weather_ingestion_service.WeatherResponseParser.parse"
)
def test_should_not_write_bronze_when_parser_fails(
    mock_parse: Mock,
    service: WeatherIngestionService,
    client: Mock,
    raw_writer: Mock,
    bronze_writer: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    mock_parse.side_effect = ValueError(
        "Invalid weather response"
    )

    with pytest.raises(
        ValueError,
        match="Invalid weather response",
    ):
        service.ingest(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 2),
        )

    raw_writer.write.assert_called_once()
    bronze_writer.write.assert_not_called()


def test_should_stop_pipeline_when_raw_write_fails(
    service: WeatherIngestionService,
    client: Mock,
    raw_writer: Mock,
    bronze_writer: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    raw_writer.write.side_effect = RuntimeError(
        "RAW write failed"
    )

    with pytest.raises(
        RuntimeError,
        match="RAW write failed",
    ):
        service.ingest(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 2),
        )

    bronze_writer.write.assert_not_called()


def test_should_generate_request_id_when_factory_is_not_provided(
    client: Mock,
    raw_writer: Mock,
    bronze_writer: Mock,
    weather_response: dict,
) -> None:
    client.get_historical_weather.return_value = (
        weather_response
    )

    service = WeatherIngestionService(
        client=client,
        raw_writer=raw_writer,
        bronze_writer=bronze_writer,
    )

    request_id = service.ingest(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 2),
    )

    assert isinstance(request_id, str)
    assert request_id

