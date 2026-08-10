import pytest

from olist_data_platform.ingestion.parsers.weather_response_parser import (
    WeatherResponseParser,
)


@pytest.fixture
def valid_weather_response():
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
                "2018-01-03",
            ],
            "temperature_2m_mean": [
                22.5,
                22.2,
                21.2,
            ],
            "temperature_2m_max": [
                25.7,
                25.2,
                23.8,
            ],
            "temperature_2m_min": [
                19.9,
                20.1,
                19.3,
            ],
            "rain_sum": [
                1.6,
                1.1,
                3.4,
            ],
            "wind_speed_10m_max": [
                20.2,
                28.8,
                24.5,
            ],
        },
    }


# ---------------------------------------------------------------------------
# Successful parsing
# ---------------------------------------------------------------------------


def test_should_parse_weather_response_into_records(
    valid_weather_response,
):
    records = WeatherResponseParser.parse(
        valid_weather_response
    )

    assert len(records) == 3


def test_should_parse_first_weather_record_correctly(
    valid_weather_response,
):
    records = WeatherResponseParser.parse(
        valid_weather_response
    )

    assert records[0] == {
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


def test_should_preserve_weather_coordinates(
    valid_weather_response,
):
    records = WeatherResponseParser.parse(
        valid_weather_response
    )

    assert records[0]["weather_latitude"] == -23.514938
    assert records[0]["weather_longitude"] == -46.610504


# ---------------------------------------------------------------------------
# Optional metadata
# ---------------------------------------------------------------------------


def test_should_accept_missing_optional_metadata(
    valid_weather_response,
):
    valid_weather_response.pop("elevation")
    valid_weather_response.pop("timezone_abbreviation")
    valid_weather_response.pop("utc_offset_seconds")

    records = WeatherResponseParser.parse(
        valid_weather_response
    )

    assert records[0]["elevation"] is None
    assert records[0]["timezone_abbreviation"] is None
    assert records[0]["utc_offset_seconds"] is None


# ---------------------------------------------------------------------------
# Root response validation
# ---------------------------------------------------------------------------


def test_should_reject_non_dictionary_response():
    with pytest.raises(TypeError):
        WeatherResponseParser.parse(
            []  # ty: ignore[invalid-argument-type]
        )


@pytest.mark.parametrize(
    "missing_field",
    [
        "latitude",
        "longitude",
        "timezone",
        "daily",
    ],
)
def test_should_reject_missing_required_root_field(
    valid_weather_response,
    missing_field,
):
    valid_weather_response.pop(missing_field)

    with pytest.raises(
        ValueError,
        match="Missing required response fields",
    ):
        WeatherResponseParser.parse(
            valid_weather_response
        )


def test_should_reject_non_dictionary_daily(
    valid_weather_response,
):
    valid_weather_response["daily"] = []

    with pytest.raises(
        TypeError,
        match=r"response\['daily'\] must be a dictionary",
    ):
        WeatherResponseParser.parse(
            valid_weather_response
        )


# ---------------------------------------------------------------------------
# Daily field validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing_field",
    [
        "time",
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "rain_sum",
        "wind_speed_10m_max",
    ],
)
def test_should_reject_missing_required_daily_field(
    valid_weather_response,
    missing_field,
):
    valid_weather_response["daily"].pop(
        missing_field
    )

    with pytest.raises(
        ValueError,
        match="Missing required daily fields",
    ):
        WeatherResponseParser.parse(
            valid_weather_response
        )


def test_should_reject_non_list_daily_field(
    valid_weather_response,
):
    valid_weather_response["daily"][
        "rain_sum"
    ] = "1.6"

    with pytest.raises(
        TypeError,
        match=r"daily\['rain_sum'\] must be a list",
    ):
        WeatherResponseParser.parse(
            valid_weather_response
        )


# ---------------------------------------------------------------------------
# Array consistency
# ---------------------------------------------------------------------------


def test_should_reject_different_daily_field_lengths(
    valid_weather_response,
):
    valid_weather_response["daily"][
        "rain_sum"
    ] = [1.6, 1.1]

    with pytest.raises(
        ValueError,
        match="All daily fields must contain the same",
    ):
        WeatherResponseParser.parse(
            valid_weather_response
        )


def test_should_accept_empty_daily_arrays(
    valid_weather_response,
):
    for field in (
        WeatherResponseParser.REQUIRED_DAILY_FIELDS
    ):
        valid_weather_response["daily"][field] = []

    records = WeatherResponseParser.parse(
        valid_weather_response
    )

    assert records == []