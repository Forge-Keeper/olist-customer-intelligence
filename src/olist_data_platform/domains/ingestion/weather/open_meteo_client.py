from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, ClassVar

from olist_data_platform.platform.logging import LoggerFactory
from olist_data_platform.platform.http.api_client import APIClient

logger = LoggerFactory.get_logger(__name__)


class OpenMeteoClient(APIClient):
    """
    Client for interacting with the Open-Meteo Historical Weather API.

    This class contains Open-Meteo-specific logic while delegating
    generic HTTP behavior to APIClient.
    """

    DEFAULT_BASE_URL: ClassVar[str] = "https://archive-api.open-meteo.com"

    HISTORICAL_ENDPOINT: ClassVar[str] = "/v1/archive"

    DEFAULT_DAILY_VARIABLES: ClassVar[tuple[str, ...]] = (
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "rain_sum",
        "wind_speed_10m_max",
    )

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        super().__init__(
            base_url=self.DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

    def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        daily_variables: list[str] | None = None,
        timezone: str = "auto",
    ) -> dict[str, Any]:
        """
        Retrieve historical daily weather data from Open-Meteo.
        """

        self._validate_coordinates(latitude, longitude)
        self._validate_date_range(start_date, end_date)
        self._validate_timezone(timezone)

        variables = (
            daily_variables
            if daily_variables is not None
            else list(self.DEFAULT_DAILY_VARIABLES)
        )

        self._validate_daily_variables(variables)

        logger.debug(
            "open_meteo_historical_weather_requested | "
            "latitude=%s | "
            "longitude=%s | "
            "start_date=%s | "
            "end_date=%s | "
            "timezone=%s | "
            "daily_variables=%s",
            latitude,
            longitude,
            start_date,
            end_date,
            timezone,
            variables,
        )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": ",".join(variables),
            "timezone": timezone,
        }

        response = self.get(
            endpoint=self.HISTORICAL_ENDPOINT,
            params=params,
        )

        if not isinstance(response, dict):
            raise TypeError(
                "Open-Meteo historical response "
                "must be a dictionary."
            )

        logger.debug(
            "open_meteo_historical_weather_received | "
            "latitude=%s | "
            "longitude=%s | "
            "start_date=%s | "
            "end_date=%s",
            latitude,
            longitude,
            start_date,
            end_date,
        )

        return response

    @staticmethod
    def _validate_coordinates(
        latitude: float,
        longitude: float,
    ) -> None:
        if not -90 <= latitude <= 90:
            raise ValueError(
                "latitude must be between -90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "longitude must be between -180 and 180."
            )

    @staticmethod
    def _validate_date_range(
        start_date: date,
        end_date: date,
    ) -> None:
        if start_date > end_date:
            raise ValueError(
                "start_date cannot be later than end_date."
            )

    @staticmethod
    def _validate_timezone(timezone: str) -> None:
        if not isinstance(timezone, str):
            raise TypeError(
                "timezone must be a string."
            )

        if not timezone.strip():
            raise ValueError(
                "timezone cannot be empty."
            )

    @staticmethod
    def _validate_daily_variables(
        daily_variables: Sequence[str],
    ) -> None:
        if isinstance(daily_variables, (str, bytes)):
            raise TypeError(
                "daily_variables must be a sequence of strings, "
                "not a single string."
            )

        if not daily_variables:
            raise ValueError(
                "daily_variables cannot be empty."
            )

        if not all(
            isinstance(variable, str)
            for variable in daily_variables
        ):
            raise TypeError(
                "daily_variables must contain only strings."
            )
