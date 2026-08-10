from __future__ import annotations

from typing import Any, ClassVar


class WeatherResponseParser:
    """
    Parse Open-Meteo daily weather responses into tabular records.

    Responsibilities:
        - Validate the expected Open-Meteo response structure
        - Validate daily arrays consistency
        - Convert column-oriented daily data into row-oriented records

    This class does not perform HTTP requests or Spark transformations.
    """

    REQUIRED_ROOT_FIELDS: ClassVar[tuple[str, ...]] = (
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
        cls._validate_response(response)

        daily = response["daily"]

        record_count = len(daily["time"])

        records = []

        for index in range(record_count):
            records.append(
                {
                    "date": daily["time"][index],
                    "temperature_2m_mean": (
                        daily["temperature_2m_mean"][index]
                    ),
                    "temperature_2m_max": (
                        daily["temperature_2m_max"][index]
                    ),
                    "temperature_2m_min": (
                        daily["temperature_2m_min"][index]
                    ),
                    "rain_sum": daily["rain_sum"][index],
                    "wind_speed_10m_max": (
                        daily["wind_speed_10m_max"][index]
                    ),
                    "weather_latitude": response["latitude"],
                    "weather_longitude": response["longitude"],
                    "elevation": response.get("elevation"),
                    "timezone": response["timezone"],
                    "timezone_abbreviation": response.get(
                        "timezone_abbreviation"
                    ),
                    "utc_offset_seconds": response.get(
                        "utc_offset_seconds"
                    ),
                }
            )

        return records

    @classmethod
    def _validate_response(
        cls,
        response: dict[str, Any],
    ) -> None:
        if not isinstance(response, dict):
            raise TypeError(
                "response must be a dictionary."
            )

        cls._validate_required_root_fields(response)

        daily = response["daily"]

        if not isinstance(daily, dict):
            raise TypeError(
                "response['daily'] must be a dictionary."
            )

        cls._validate_required_daily_fields(daily)
        cls._validate_daily_field_types(daily)
        cls._validate_daily_lengths(daily)

    @classmethod
    def _validate_required_root_fields(
        cls,
        response: dict[str, Any],
    ) -> None:
        missing_fields = [
            field
            for field in cls.REQUIRED_ROOT_FIELDS
            if field not in response
        ]

        if missing_fields:
            raise ValueError(
                "Missing required response fields: "
                f"{', '.join(missing_fields)}."
            )

    @classmethod
    def _validate_required_daily_fields(
        cls,
        daily: dict[str, Any],
    ) -> None:
        missing_fields = [
            field
            for field in cls.REQUIRED_DAILY_FIELDS
            if field not in daily
        ]

        if missing_fields:
            raise ValueError(
                "Missing required daily fields: "
                f"{', '.join(missing_fields)}."
            )

    @classmethod
    def _validate_daily_field_types(
        cls,
        daily: dict[str, Any],
    ) -> None:
        for field in cls.REQUIRED_DAILY_FIELDS:
            if not isinstance(daily[field], list):
                raise TypeError(
                    f"daily['{field}'] must be a list."
                )

    @classmethod
    def _validate_daily_lengths(
        cls,
        daily: dict[str, Any],
    ) -> None:
        lengths = {
            field: len(daily[field])
            for field in cls.REQUIRED_DAILY_FIELDS
        }

        if len(set(lengths.values())) != 1:
            raise ValueError(
                "All daily fields must contain the same "
                f"number of elements. Received: {lengths}"
            )