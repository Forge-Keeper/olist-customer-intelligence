from __future__ import annotations

import json
from datetime import date
from typing import Any

from pyspark.sql import Row, SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


class RawWeatherWriter:
    """
    Persist raw Open-Meteo API responses.

    The RAW layer preserves the original API response and
    request metadata to support traceability and replay.
    """

    SCHEMA = StructType(
        [
            StructField("request_id", StringType(), False),
            StructField("requested_latitude", DoubleType(), False),
            StructField("requested_longitude", DoubleType(), False),
            StructField("start_date", StringType(), False),
            StructField("end_date", StringType(), False),
            StructField("response_json", StringType(), False),
            StructField(
                "ingestion_timestamp",
                TimestampType(),
                False,
            ),
        ]
    )

    def __init__(
        self,
        spark: SparkSession,
        target_table: str,
    ) -> None:
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

        row = {
            "request_id": request_id,
            "requested_latitude": requested_latitude,
            "requested_longitude": requested_longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "response_json": json.dumps(
                response,
                ensure_ascii=False,
            ),
        }

        schema_without_timestamp = StructType(
            [
                field
                for field in self.SCHEMA.fields
                if field.name != "ingestion_timestamp"
            ]
        )

        spark_row = Row(**row)

        df = self.spark.createDataFrame(
            [spark_row],
            schema=schema_without_timestamp,
        )

        df = df.withColumn(
            "ingestion_timestamp",
            current_timestamp(),
        )

        (
            df.write
            .format("delta")
            .mode("append")
            .saveAsTable(self.target_table)
        )

    @staticmethod
    def _validate_target_table(target_table: str) -> None:
        if not isinstance(target_table, str):
            raise TypeError(
                "target_table must be a string."
            )

        if not target_table.strip():
            raise ValueError(
                "target_table cannot be empty."
            )

    @staticmethod
    def _validate_request_id(request_id: str) -> None:
        if not isinstance(request_id, str):
            raise TypeError(
                "request_id must be a string."
            )

        if not request_id.strip():
            raise ValueError(
                "request_id cannot be empty."
            )