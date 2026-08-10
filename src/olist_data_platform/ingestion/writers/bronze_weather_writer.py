from __future__ import annotations

from typing import Any, ClassVar

from pyspark.sql import DataFrame, Row, SparkSession
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

    Responsibilities:
        - Validate input records and writer configuration
        - Enrich parsed records with request metadata
        - Build a Spark DataFrame using an explicit schema
        - Add technical ingestion metadata
        - Persist the DataFrame as a Delta table

    Business transformations should not be performed in this layer.
    """

    INGESTION_TIMESTAMP_COLUMN: ClassVar[str] = (
        "ingestion_timestamp"
    )

    SCHEMA: ClassVar[StructType] = StructType(
        [
            StructField(
                "request_id",
                StringType(),
                False,
            ),
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
            StructField(
                "date",
                StringType(),
                False,
            ),
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
                INGESTION_TIMESTAMP_COLUMN,
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
        """
        Build and persist Bronze weather records.

        Empty record collections are ignored.
        """

        self._validate_records(records)
        self._validate_request_id(request_id)
        self._validate_coordinates(
            requested_latitude,
            requested_longitude,
        )

        if not records:
            return

        dataframe = self._build_dataframe(
            records=records,
            request_id=request_id,
            requested_latitude=requested_latitude,
            requested_longitude=requested_longitude,
        )

        self._write_dataframe(dataframe)

    def _build_dataframe(
        self,
        records: list[dict[str, Any]],
        request_id: str,
        requested_latitude: float,
        requested_longitude: float,
    ) -> DataFrame:
        """
        Convert parsed weather records into a Spark DataFrame.

        Request-level metadata is added to every weather record.
        """

        enriched_records = [
            {
                "request_id": request_id,
                "requested_latitude": requested_latitude,
                "requested_longitude": requested_longitude,
                **record,
            }
            for record in records
        ]

        spark_rows = [
            Row(**record)
            for record in enriched_records
        ]

        dataframe = self.spark.createDataFrame(
            spark_rows,
            schema=self._schema_without_ingestion_timestamp(),
        )

        return dataframe.withColumn(
            self.INGESTION_TIMESTAMP_COLUMN,
            current_timestamp(),
        )

    def _write_dataframe(
        self,
        dataframe: DataFrame,
    ) -> None:
        """
        Persist a Spark DataFrame as a Delta table.
        """

        (
            dataframe.write
            .format("delta")
            .mode("append")
            .saveAsTable(self.target_table)
        )

    @classmethod
    def _schema_without_ingestion_timestamp(
        cls,
    ) -> StructType:
        """
        Return the Bronze schema excluding the generated
        ingestion timestamp column.
        """

        return StructType(
            [
                field
                for field in cls.SCHEMA.fields
                if field.name
                != cls.INGESTION_TIMESTAMP_COLUMN
            ]
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

    @staticmethod
    def _validate_coordinates(
        latitude: float,
        longitude: float,
    ) -> None:
        if not isinstance(latitude, (int, float)):
            raise TypeError(
                "requested_latitude must be numeric."
            )

        if not isinstance(longitude, (int, float)):
            raise TypeError(
                "requested_longitude must be numeric."
            )

        if not -90 <= latitude <= 90:
            raise ValueError(
                "requested_latitude must be between "
                "-90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "requested_longitude must be between "
                "-180 and 180."
            )

