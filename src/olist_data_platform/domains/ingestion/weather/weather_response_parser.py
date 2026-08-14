from __future__ import annotations

from datetime import date
from typing import Any, ClassVar


class WeatherResponseParser:
    """
    Parse and validate Open-Meteo historical weather responses.
    """

    REQUIRED_RESPONSE_FIELDS: ClassVar[tuple[str, ...]] = (
        "latitude",
        "longitude",
        "timezone",
        "daily",
    )

    REQUIRED_DAILY_FIELDS: ClassVar[tuple[str, ...]] = (
        "time",
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "rain_sum",
        "wind_speed_10m_max",
    )

    @classmethod
    def parse(
        cls,
        response: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(response, dict):
            raise TypeError(
                "Open-Meteo response must be a dictionary."
            )

        missing_response_fields = [
            field
            for field in cls.REQUIRED_RESPONSE_FIELDS
            if field not in response
        ]

        if missing_response_fields:
            raise ValueError(
                "Missing required response fields: "
                f"{missing_response_fields}"
            )

        daily = response["daily"]

        if not isinstance(daily, dict):
            raise TypeError(
                "response['daily'] must be a dictionary."
            )

        missing_daily_fields = [
            field
            for field in cls.REQUIRED_DAILY_FIELDS
            if field not in daily
        ]

        if missing_daily_fields:
            raise ValueError(
                "Missing required daily fields: "
                f"{missing_daily_fields}"
            )

        for field in cls.REQUIRED_DAILY_FIELDS:
            if not isinstance(daily[field], list):
                raise TypeError(
                    f"daily['{field}'] must be a list."
                )

        lengths = {
            len(daily[field])
            for field in cls.REQUIRED_DAILY_FIELDS
        }

        if len(lengths) != 1:
            raise ValueError(
                "All daily fields must contain the same "
                "number of values."
            )

        record_count = len(daily["time"])
        records: list[dict[str, Any]] = []

        for index in range(record_count):
            records.append(
                {
                    "dt_base": date.fromisoformat(daily["time"][index]),
                    "temperature_2m_mean": daily["temperature_2m_mean"][index],
                    "temperature_2m_max": daily["temperature_2m_max"][index],
                    "temperature_2m_min": daily["temperature_2m_min"][index],
                    "rain_sum": daily["rain_sum"][index],
                    "wind_speed_10m_max": daily["wind_speed_10m_max"][index],
                    "weather_latitude": response["latitude"],
                    "weather_longitude": response["longitude"],
                    "elevation": response.get("elevation"),
                    "timezone": response["timezone"],
                    "timezone_abbreviation": response.get("timezone_abbreviation"),
                    "utc_offset_seconds": response.get("utc_offset_seconds"),
                }
            )

        return records
