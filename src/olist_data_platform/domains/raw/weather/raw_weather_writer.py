from __future__ import annotations

import json
from datetime import date
from typing import Any, ClassVar

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RawWeatherWriter:
    """Persist raw Open-Meteo API responses into the RAW layer."""

    INGESTION_TIMESTAMP_COLUMN: ClassVar[str] = "ingestion_timestamp"

    SCHEMA: ClassVar[StructType] = StructType(
        [
            StructField("request_id", StringType(), False),
            StructField("requested_latitude", DoubleType(), False),
            StructField("requested_longitude", DoubleType(), False),
            StructField("start_date", StringType(), False),
            StructField("end_date", StringType(), False),
            StructField("response_json", StringType(), False),
            StructField(INGESTION_TIMESTAMP_COLUMN, TimestampType(), False),
        ]
    )

    def __init__(self, spark: SparkSession, target_table: str) -> None:
        self._validate_target_table(target_table)
        self.spark = spark
        self.target_table = target_table

    def write(
        self,
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
        start_date: date,
        end_date: date,
        response: dict[str, Any],
    ) -> None:
        self._validate_request_id(request_id)
        self._validate_coordinates(requested_latitude, requested_longitude)
        self._validate_date_range(start_date, end_date)
        self._validate_response(response)

        logger.info(
            "raw_weather_write_started | "
            "request_id=%s | target_table=%s | latitude=%s | "
            "longitude=%s | start_date=%s | end_date=%s",
            request_id,
            self.target_table,
            requested_latitude,
            requested_longitude,
            start_date,
            end_date,
        )

        dataframe = self._build_dataframe(
            request_id=request_id,
            requested_latitude=requested_latitude,
            requested_longitude=requested_longitude,
            start_date=start_date,
            end_date=end_date,
            response=response,
        )
        self._write_dataframe(dataframe=dataframe, request_id=request_id)

    def _build_dataframe(
        self,
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
        start_date: date,
        end_date: date,
        response: dict[str, Any],
    ) -> DataFrame:
        response_json = json.dumps(
            response,
            ensure_ascii=False,
        )

        logger.debug(
            "raw_weather_response_serialized | "
            "request_id=%s | "
            "response_size_bytes=%s",
            request_id,
            len(response_json.encode("utf-8")),
        )

        raw_record = {
            "request_id": request_id,
            "requested_latitude": requested_latitude,
            "requested_longitude": requested_longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "response_json": response_json,
        }

        spark_row = Row(**raw_record)

        dataframe = self.spark.createDataFrame(
            [spark_row],
            schema=self._schema_without_ingestion_timestamp(),
        )

        return dataframe.withColumn(
            self.INGESTION_TIMESTAMP_COLUMN,
            current_timestamp(),
        )

    def _write_dataframe(self, dataframe: DataFrame, request_id: str) -> None:
        (
            dataframe.write
            .format("delta")
            .mode("append")
            .saveAsTable(self.target_table)
        )

        logger.info(
            "raw_weather_write_completed | request_id=%s | target_table=%s",
            request_id,
            self.target_table,
        )

    @classmethod
    def _schema_without_ingestion_timestamp(cls) -> StructType:
        return StructType(
            [
                field
                for field in cls.SCHEMA.fields
                if field.name != cls.INGESTION_TIMESTAMP_COLUMN
            ]
        )

    @staticmethod
    def _validate_target_table(target_table: str) -> None:
        if not isinstance(target_table, str):
            raise TypeError("target_table must be a string.")
        if not target_table.strip():
            raise ValueError("target_table cannot be empty.")

    @staticmethod
    def _validate_request_id(request_id: str) -> None:
        if not isinstance(request_id, str):
            raise TypeError("request_id must be a string.")
        if not request_id.strip():
            raise ValueError("request_id cannot be empty.")

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        if not isinstance(latitude, (int, float)):
            raise TypeError("requested_latitude must be numeric.")
        if not isinstance(longitude, (int, float)):
            raise TypeError("requested_longitude must be numeric.")
        if not -90 <= latitude <= 90:
            raise ValueError("requested_latitude must be between -90 and 90.")
        if not -180 <= longitude <= 180:
            raise ValueError("requested_longitude must be between -180 and 180.")

    @staticmethod
    def _validate_date_range(start_date: date, end_date: date) -> None:
        if not isinstance(start_date, date):
            raise TypeError("start_date must be a date.")
        if not isinstance(end_date, date):
            raise TypeError("end_date must be a date.")
        if start_date > end_date:
            raise ValueError("start_date cannot be later than end_date.")

    @staticmethod
    def _validate_response(response: dict[str, Any]) -> None:
        if not isinstance(response, dict):
            raise TypeError("response must be a dictionary.")
