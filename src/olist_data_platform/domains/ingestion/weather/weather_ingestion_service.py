from __future__ import annotations

from collections.abc import Callable
from datetime import date
from uuid import uuid4

from olist_data_platform.domains.bronze.weather.bronze_weather_writer import (
    BronzeWeatherWriter,
)
from olist_data_platform.domains.ingestion.weather.open_meteo_client import (
    OpenMeteoClient,
)
from olist_data_platform.domains.ingestion.weather.weather_daily_extractor import (
    WeatherDailyExtractor,
)
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class WeatherIngestionService:
    """Orchestrate idempotent historical weather ingestion into Bronze."""

    def __init__(
        self,
        client: OpenMeteoClient,
        bronze_writer: BronzeWeatherWriter,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.client = client
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
    ) -> str:
        request_id = self.request_id_factory()

        logger.info(
            "weather_ingestion_started | request_id=%s | latitude=%s | "
            "longitude=%s | start_date=%s | end_date=%s",
            request_id,
            latitude,
            longitude,
            start_date,
            end_date,
        )

        try:
            response = self.client.get_historical_weather(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                daily_variables=daily_variables,
                timezone=timezone,
            )

            logger.info(
                "weather_api_request_completed | request_id=%s",
                request_id,
            )

            records = WeatherDailyExtractor.extract(response)

            logger.info(
                "weather_daily_records_extracted | request_id=%s | "
                "record_count=%s",
                request_id,
                len(records),
            )

            self.bronze_writer.write(
                records=records,
                request_id=request_id,
                requested_latitude=latitude,
                requested_longitude=longitude,
            )

            logger.info(
                "weather_ingestion_completed | request_id=%s | record_count=%s",
                request_id,
                len(records),
            )

            return request_id

        except Exception:
            logger.exception(
                "weather_ingestion_failed | request_id=%s | latitude=%s | "
                "longitude=%s | start_date=%s | end_date=%s",
                request_id,
                latitude,
                longitude,
                start_date,
                end_date,
            )
            raise
