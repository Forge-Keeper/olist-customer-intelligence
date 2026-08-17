from __future__ import annotations

import json
from datetime import date
from typing import Any

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DoubleType,
    StringType,
    StructField,
    StructType,
)

from olist_data_platform.domains.bronze.weather.weather_bronze_config import (
    WEATHER_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class BronzeWeatherWriter:
    """Persist daily Open-Meteo landing records into Bronze."""

    INPUT_SCHEMA = StructType(
        [
            StructField("dt_base", DateType(), False),
            StructField("payload_json", StringType(), False),
            StructField("request_id", StringType(), False),
            StructField("requested_latitude", DoubleType(), False),
            StructField("requested_longitude", DoubleType(), False),
        ]
    )

    def __init__(self, spark: SparkSession, target_table: str) -> None:
        self.spark = spark
        self.target_table = target_table
        self.writer = BronzeWriter(
            spark=spark,
            target_table=target_table,
            config=WEATHER_BRONZE_CONFIG,
        )

    def write(
        self,
        records: list[dict[str, Any]],
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
    ) -> None:
        if not records:
            self._validate_common_inputs(
                records,
                request_id,
                requested_latitude,
                requested_longitude,
            )
            logger.warning(
                "bronze_weather_write_skipped | target_table=%s | "
                "reason=no_records | request_id=%s",
                self.target_table,
                request_id,
            )
            return

        dataframe = self._build_dataframe(
            records=records,
            request_id=request_id,
            requested_latitude=requested_latitude,
            requested_longitude=requested_longitude,
        )
        self.writer.write(dataframe)

    def reprocess(
        self,
        records: list[dict[str, Any]],
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
        start_date: date,
        end_date: date,
    ) -> None:
        if start_date > end_date:
            raise ValueError("start_date cannot be later than end_date.")

        dataframe = self._build_dataframe(
            records=records,
            request_id=request_id,
            requested_latitude=requested_latitude,
            requested_longitude=requested_longitude,
        )

        predicate = self._build_reprocess_predicate(
            start_date=start_date,
            end_date=end_date,
            latitude=requested_latitude,
            longitude=requested_longitude,
        )
        self.writer.replace_where(dataframe, predicate)

    def _build_dataframe(
        self,
        records: list[dict[str, Any]],
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
    ) -> DataFrame:
        self._validate_common_inputs(
            records,
            request_id,
            requested_latitude,
            requested_longitude,
        )
        if not records:
            raise ValueError("records cannot be empty when building a Bronze DataFrame.")

        rows = [
            Row(
                dt_base=self._extract_dt_base(record),
                payload_json=json.dumps(
                    self._extract_payload(record),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                request_id=request_id,
                requested_latitude=float(requested_latitude),
                requested_longitude=float(requested_longitude),
            )
            for record in records
        ]

        dataframe = self.spark.createDataFrame(rows, schema=self.INPUT_SCHEMA)
        return dataframe.withColumn("payload", F.parse_json("payload_json")).drop(
            "payload_json"
        )

    @staticmethod
    def _build_reprocess_predicate(
        start_date: date,
        end_date: date,
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"dt_base >= DATE '{start_date.isoformat()}' "
            f"AND dt_base <= DATE '{end_date.isoformat()}' "
            f"AND requested_latitude = {latitude!r} "
            f"AND requested_longitude = {longitude!r}"
        )

    @classmethod
    def _validate_common_inputs(
        cls,
        records: list[dict[str, Any]],
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
    ) -> None:
        cls._validate_records(records)
        cls._validate_request_id(request_id)
        cls._validate_coordinates(requested_latitude, requested_longitude)

    @staticmethod
    def _extract_dt_base(record: dict[str, Any]) -> date:
        dt_base = record.get("dt_base")
        if not isinstance(dt_base, date):
            raise TypeError("record dt_base must be a date.")
        return dt_base

    @staticmethod
    def _extract_payload(record: dict[str, Any]) -> dict[str, Any]:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            raise TypeError("record payload must be a dictionary.")
        return payload

    @staticmethod
    def _validate_records(records: list[dict[str, Any]]) -> None:
        if not isinstance(records, list):
            raise TypeError("records must be a list.")
        if not all(isinstance(record, dict) for record in records):
            raise TypeError("records must contain only dictionaries.")

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
