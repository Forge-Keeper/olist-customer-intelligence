from datetime import date
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.ingestion.api.open_meteo_client import (
    OpenMeteoClient,
)

# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------


def test_should_create_open_meteo_client_with_default_configuration():
    client = OpenMeteoClient()

    assert client.base_url == "https://archive-api.open-meteo.com"
    assert client.timeout == 30
    assert client.max_retries == 3
    assert client.backoff_factor == 1.0


def test_should_create_open_meteo_client_with_custom_configuration():
    client = OpenMeteoClient(
        timeout=60,
        max_retries=5,
        backoff_factor=2.0,
    )

    assert client.timeout == 60
    assert client.max_retries == 5
    assert client.backoff_factor == 2.0


def test_should_have_expected_default_daily_variables():
    assert OpenMeteoClient.DEFAULT_DAILY_VARIABLES == (
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "rain_sum",
        "wind_speed_10m_max",
    )


# ---------------------------------------------------------------------------
# Historical weather request
# ---------------------------------------------------------------------------


def test_should_request_historical_weather_with_default_parameters():
    client = OpenMeteoClient()

    expected_response = {
        "latitude": -26.3045,
        "longitude": -48.8487,
        "daily": {
            "time": ["2024-01-01"],
            "temperature_2m_mean": [25.3],
        },
    }

    client.get = Mock(return_value=expected_response)

    response = client.get_historical_weather(
        latitude=-26.3045,
        longitude=-48.8487,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    assert response == expected_response

    client.get.assert_called_once_with(
        endpoint="/v1/archive",
        params={
            "latitude": -26.3045,
            "longitude": -48.8487,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "daily": (
                "temperature_2m_mean,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "rain_sum,"
                "wind_speed_10m_max"
            ),
            "timezone": "auto",
        },
    )


def test_should_request_historical_weather_with_custom_variables():
    client = OpenMeteoClient()

    client.get = Mock(return_value={})

    variables = [
        "temperature_2m_mean",
        "precipitation_sum",
    ]

    client.get_historical_weather(
        latitude=-26.3045,
        longitude=-48.8487,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        daily_variables=variables,
    )

    client.get.assert_called_once_with(
        endpoint="/v1/archive",
        params={
            "latitude": -26.3045,
            "longitude": -48.8487,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "auto",
        },
    )


def test_should_accept_tuple_as_custom_variables():
    client = OpenMeteoClient()

    client.get = Mock(return_value={})

    variables = (
        "temperature_2m_mean",
        "rain_sum",
    )

    client.get_historical_weather(
        latitude=-26.3045,
        longitude=-48.8487,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        daily_variables=variables, # ty: ignore[invalid-argument-type]
    )

    client.get.assert_called_once()

    request = client.get.call_args.kwargs

    assert (
        request["params"]["daily"]
        == "temperature_2m_mean,rain_sum"
    )


def test_should_request_historical_weather_with_custom_timezone():
    client = OpenMeteoClient()

    client.get = Mock(return_value={})

    client.get_historical_weather(
        latitude=-26.3045,
        longitude=-48.8487,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        timezone="America/Sao_Paulo",
    )

    client.get.assert_called_once()

    request = client.get.call_args.kwargs

    assert request["params"]["timezone"] == "America/Sao_Paulo"


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------


def test_should_return_dictionary_response():
    client = OpenMeteoClient()

    expected_response = {
        "latitude": -26.3045,
        "longitude": -48.8487,
    }

    client.get = Mock(return_value=expected_response)

    response = client.get_historical_weather(
        latitude=-26.3045,
        longitude=-48.8487,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )

    assert response == expected_response
    assert isinstance(response, dict)


def test_should_reject_unexpected_list_response():
    client = OpenMeteoClient()

    client.get = Mock(return_value=[])

    with pytest.raises(
        TypeError,
        match="Open-Meteo historical response must be a dictionary",
    ):
        client.get_historical_weather(
            latitude=-26.3045,
            longitude=-48.8487,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )


# ---------------------------------------------------------------------------
# Coordinate validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "latitude",
    [
        -90.0,
        0.0,
        90.0,
    ],
)
def test_should_accept_valid_latitude(latitude):
    client = OpenMeteoClient()
    client.get = Mock(return_value={})

    client.get_historical_weather(
        latitude=latitude,
        longitude=0.0,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )

    client.get.assert_called_once()


@pytest.mark.parametrize(
    "latitude",
    [
        -90.1,
        90.1,
    ],
)
def test_should_reject_invalid_latitude(latitude):
    client = OpenMeteoClient()

    with pytest.raises(ValueError):
        client.get_historical_weather(
            latitude=latitude,
            longitude=0.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )


@pytest.mark.parametrize(
    "longitude",
    [
        -180.0,
        0.0,
        180.0,
    ],
)
def test_should_accept_valid_longitude(longitude):
    client = OpenMeteoClient()
    client.get = Mock(return_value={})

    client.get_historical_weather(
        latitude=0.0,
        longitude=longitude,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )

    client.get.assert_called_once()


@pytest.mark.parametrize(
    "longitude",
    [
        -180.1,
        180.1,
    ],
)
def test_should_reject_invalid_longitude(longitude):
    client = OpenMeteoClient()

    with pytest.raises(ValueError):
        client.get_historical_weather(
            latitude=0.0,
            longitude=longitude,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------


def test_should_accept_same_start_and_end_date():
    client = OpenMeteoClient()
    client.get = Mock(return_value={})

    client.get_historical_weather(
        latitude=0.0,
        longitude=0.0,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )

    client.get.assert_called_once()


def test_should_reject_start_date_after_end_date():
    client = OpenMeteoClient()

    with pytest.raises(
        ValueError,
        match="start_date cannot be later than end_date",
    ):
        client.get_historical_weather(
            latitude=0.0,
            longitude=0.0,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 1, 1),
        )


# ---------------------------------------------------------------------------
# Timezone validation
# ---------------------------------------------------------------------------


def test_should_accept_valid_timezone():
    client = OpenMeteoClient()
    client.get = Mock(return_value={})

    client.get_historical_weather(
        latitude=0.0,
        longitude=0.0,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        timezone="America/Sao_Paulo",
    )

    client.get.assert_called_once()


@pytest.mark.parametrize(
    "timezone",
    [
        "",
        " ",
    ],
)
def test_should_reject_empty_timezone(timezone):
    client = OpenMeteoClient()

    with pytest.raises(ValueError):
        client.get_historical_weather(
            latitude=0.0,
            longitude=0.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            timezone=timezone,
        )


def test_should_reject_invalid_timezone_type():
    client = OpenMeteoClient()

    with pytest.raises(TypeError):
        client.get_historical_weather(
            latitude=0.0,
            longitude=0.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            timezone=None,  # ty: ignore[invalid-argument-type]
        )


# ---------------------------------------------------------------------------
# Daily variables validation
# ---------------------------------------------------------------------------


def test_should_use_default_variables_when_none_is_provided():
    client = OpenMeteoClient()
    client.get = Mock(return_value={})

    client.get_historical_weather(
        latitude=0.0,
        longitude=0.0,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        daily_variables=None,
    )

    request = client.get.call_args.kwargs

    assert request["params"]["daily"] == (
        "temperature_2m_mean,"
        "temperature_2m_max,"
        "temperature_2m_min,"
        "rain_sum,"
        "wind_speed_10m_max"
    )


def test_should_reject_empty_daily_variables():
    client = OpenMeteoClient()

    with pytest.raises(ValueError):
        client.get_historical_weather(
            latitude=0.0,
            longitude=0.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            daily_variables=[],
        )


def test_should_reject_invalid_daily_variables_argument_type():
    client = OpenMeteoClient()

    with pytest.raises(TypeError):
        client.get_historical_weather(
            latitude=0.0,
            longitude=0.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            daily_variables="temperature_2m_mean",  # ty: ignore[invalid-argument-type]
        )


def test_should_reject_non_string_daily_variable():
    client = OpenMeteoClient()

    invalid_variables = [
        "temperature_2m_mean",
        123,
    ]

    with pytest.raises(TypeError):
        client.get_historical_weather(
            latitude=0.0,
            longitude=0.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            daily_variables=invalid_variables,  # ty: ignore[invalid-argument-type]
        )

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


@patch(
    "olist_data_platform.ingestion.api."
    "open_meteo_client.logger"
)
def test_should_log_debug_for_historical_weather_request(
    mock_logger,
):
    client = OpenMeteoClient()

    client.get = Mock(
        return_value={
            "latitude": -26.3045,
            "longitude": -48.8487,
            "daily": {},
        }
    )

    client.get_historical_weather(
        latitude=-26.3045,
        longitude=-48.8487,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        timezone="America/Sao_Paulo",
    )

    assert mock_logger.debug.call_count == 2

