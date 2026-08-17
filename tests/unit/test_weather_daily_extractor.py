from datetime import date

import pytest

from olist_data_platform.domains.ingestion.weather.weather_daily_extractor import (
    WeatherDailyExtractor,
)


def _response() -> dict:
    return {
        "latitude": -23.5,
        "longitude": -46.6,
        "timezone": "America/Sao_Paulo",
        "daily_units": {"temperature_2m_mean": "°C"},
        "daily": {
            "time": ["2018-01-01", "2018-01-02"],
            "temperature_2m_mean": [22.5, 22.2],
            "rain_sum": [1.6, 1.1],
        },
    }


def test_should_extract_one_record_per_day() -> None:
    records = WeatherDailyExtractor.extract(_response())

    assert [record["dt_base"] for record in records] == [
        date(2018, 1, 1),
        date(2018, 1, 2),
    ]
    assert records[0]["payload"]["daily"]["temperature_2m_mean"] == 22.5
    assert records[1]["payload"]["daily"]["temperature_2m_mean"] == 22.2


def test_should_preserve_top_level_payload_fields() -> None:
    records = WeatherDailyExtractor.extract(_response())

    assert records[0]["payload"]["timezone"] == "America/Sao_Paulo"
    assert records[0]["payload"]["daily_units"] == {
        "temperature_2m_mean": "°C"
    }


def test_should_preserve_new_daily_columns() -> None:
    response = _response()
    response["daily"]["new_metric"] = [10, 20]

    records = WeatherDailyExtractor.extract(response)

    assert records[0]["payload"]["daily"]["new_metric"] == 10
    assert records[1]["payload"]["daily"]["new_metric"] == 20


def test_should_reject_inconsistent_daily_list_lengths() -> None:
    response = _response()
    response["daily"]["rain_sum"] = [1.6]

    with pytest.raises(ValueError, match="same number of values"):
        WeatherDailyExtractor.extract(response)


def test_should_reject_missing_daily_time() -> None:
    response = _response()
    del response["daily"]["time"]

    with pytest.raises(ValueError, match="daily.time"):
        WeatherDailyExtractor.extract(response)


def test_should_reject_invalid_date() -> None:
    response = _response()
    response["daily"]["time"][0] = "not-a-date"

    with pytest.raises(ValueError, match="Invalid daily.time value"):
        WeatherDailyExtractor.extract(response)
