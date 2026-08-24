from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any


class WeatherDailyExtractor:
    """Split a multi-day Open-Meteo response into daily Bronze records."""

    @classmethod
    def extract(cls, response: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(response, dict):
            raise TypeError("response must be a dictionary.")

        daily = response.get("daily")
        if not isinstance(daily, dict):
            raise ValueError("response must contain a daily object.")

        times = daily.get("time")
        if not isinstance(times, list) or not times:
            raise ValueError("daily.time must be a non-empty list.")

        for field_name, values in daily.items():
            if isinstance(values, list) and len(values) != len(times):
                raise ValueError(
                    "All daily list fields must contain the same number of values: "
                    f"field={field_name}"
                )

        base_payload = {
            key: deepcopy(value)
            for key, value in response.items()
            if key != "daily"
        }

        records: list[dict[str, Any]] = []
        for index, raw_date in enumerate(times):
            if not isinstance(raw_date, str):
                raise TypeError("daily.time values must be ISO date strings.")

            try:
                dt_base = date.fromisoformat(raw_date)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid daily.time value: {raw_date!r}."
                ) from exc

            daily_payload: dict[str, Any] = {}
            for field_name, values in daily.items():
                if isinstance(values, list):
                    daily_payload[field_name] = deepcopy(values[index])
                else:
                    daily_payload[field_name] = deepcopy(values)

            payload = deepcopy(base_payload)
            payload["daily"] = daily_payload

            records.append(
                {
                    "dt_base": dt_base,
                    "payload": payload,
                }
            )

        return records
