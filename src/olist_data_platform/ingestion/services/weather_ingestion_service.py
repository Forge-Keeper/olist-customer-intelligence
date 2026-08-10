from __future__ import annotations

from collections.abc import Callable
from datetime import date
from uuid import uuid4

from olist_data_platform.ingestion.api.open_meteo_client import (
    OpenMeteoClient,
)
from olist_data_platform.ingestion.parsers.weather_response_parser import (
    WeatherResponseParser,
)
from olist_data_platform.ingestion.writers.bronze_weather_writer import (
    BronzeWeatherWriter,
)
from olist_data_platform.ingestion.writers.raw_weather_writer import (
    RawWeatherWriter,
)


class WeatherIngestionService:
    """
    Orchestrate historical weather ingestion.

    Responsibilities:
        - Generate a unique request identifier
        - Request historical weather data
        - Persist the original API response in RAW
        - Parse the API response
        - Persist structured weather records in Bronze

    The service does not implement HTTP, parsing, or Spark persistence
    logic itself. Those responsibilities are delegated to collaborators.
    """

    def __init__(
        self,
        client: OpenMeteoClient,
        raw_writer: RawWeatherWriter,
        bronze_writer: BronzeWeatherWriter,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.client = client
        self.raw_writer = raw_writer
        self.bronze_writer = bronze_writer
        self.request_id_factory = (
            request_id_factory
            if request_id_factory is not None
            else lambda: str(uuid4())
        )

    def ingest(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        daily_variables: list[str] | None = None,
        timezone: str = "auto",
        overwrite: bool = False,
    ) -> str:
        """
        Ingest historical weather data into RAW and Bronze.

        Returns:
            The request identifier associated with the ingestion.
        """

        request_id = self.request_id_factory()

        response = self.client.get_historical_weather(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            daily_variables=daily_variables,
            timezone=timezone,
        )

        self.raw_writer.write(
            request_id=request_id,
            requested_latitude=latitude,
            requested_longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            response=response,
            
        )

        records = WeatherResponseParser.parse(
            response
        )

        self.bronze_writer.write(
            records=records,
            request_id=request_id,
            requested_latitude=latitude,
            requested_longitude=longitude,
            overwrite=overwrite
        )

        return request_id

