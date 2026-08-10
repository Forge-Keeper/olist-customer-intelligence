from __future__ import annotations

from typing import Any

from pyspark.sql import Row, SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


class BronzeWeatherWriter:
    """
    Persist parsed Open-Meteo records into the Bronze layer.

    The Bronze layer stores structured records while preserving
    source-level values and ingestion metadata.
    """

    SCHEMA = StructType(
        [
            StructField("request_id", StringType(), False),
            StructField(
                "requested_latitude",
                DoubleType(),
                False,
            ),
            StructField(
                "requested_longitude",
                DoubleType(),
                False,
            ),
            StructField("date", StringType(), False),
            StructField(
                "temperature_2m_mean",
                DoubleType(),
                True,
            ),
            StructField(
                "temperature_2m_max",
                DoubleType(),
                True,
            ),
            StructField(
                "temperature_2m_min",
                DoubleType(),
                True,
            ),
            StructField(
                "rain_sum",
                DoubleType(),
                True,
            ),
            StructField(
                "wind_speed_10m_max",
                DoubleType(),
                True,
            ),
            StructField(
                "weather_latitude",
                DoubleType(),
                False,
            ),
            StructField(
                "weather_longitude",
                DoubleType(),
                False,
            ),
            StructField(
                "elevation",
                DoubleType(),
                True,
            ),
            StructField(
                "timezone",
                StringType(),
                False,
            ),
            StructField(
                "timezone_abbreviation",
                StringType(),
                True,
            ),
            StructField(
                "utc_offset_seconds",
                IntegerType(),
                True,
            ),
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
        records: list[dict[str, Any]],
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
    ) -> None:
        self._validate_records(records)
        self._validate_request_id(request_id)

        if not records:
            return

        enriched_records = [
            {
                "request_id": request_id,
                "requested_latitude": requested_latitude,
                "requested_longitude": requested_longitude,
                **record,
            }
            for record in records
        ]

        schema_without_timestamp = StructType(
            [
                field
                for field in self.SCHEMA.fields
                if field.name != "ingestion_timestamp"
            ]
        )

        spark_rows = [
            Row(**record)
            for record in enriched_records
        ]

        df = self.spark.createDataFrame(
            spark_rows,
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
    def _validate_records(
        records: list[dict[str, Any]],
    ) -> None:
        if not isinstance(records, list):
            raise TypeError(
                "records must be a list."
            )

        if not all(
            isinstance(record, dict)
            for record in records
        ):
            raise TypeError(
                "records must contain only dictionaries."
            )

    @staticmethod
    def _validate_target_table(
        target_table: str,
    ) -> None:
        if not isinstance(target_table, str):
            raise TypeError(
                "target_table must be a string."
            )

        if not target_table.strip():
            raise ValueError(
                "target_table cannot be empty."
            )

    @staticmethod
    def _validate_request_id(
        request_id: str,
    ) -> None:
        if not isinstance(request_id, str):
            raise TypeError(
                "request_id must be a string."
            )

        if not request_id.strip():
            raise ValueError(
                "request_id cannot be empty."
            )