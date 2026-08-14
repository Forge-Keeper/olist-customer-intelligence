from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col as C
from pyspark.sql.functions import current_timestamp
from pyspark.sql.functions import lit as L
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class BronzeWeatherWriter:
    """
    Persist parsed Open-Meteo records into the Bronze layer.

    Responsibilities:
        - Validate input records and writer configuration
        - Enrich parsed records with request metadata
        - Build a Spark DataFrame using an explicit schema
        - Add technical ingestion metadata
        - Persist the DataFrame as a Delta table
        - Create the table using liquid clustering

    Business transformations should not be performed in this layer.
    """

    INGESTION_TIMESTAMP_COLUMN: ClassVar[str] = (
        "ingestion_timestamp"
    )

    CLUSTERING_COLUMNS: ClassVar[tuple[str, ...]] = (
        "dt_base",
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
                "dt_base",
                DateType(),
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
        overwrite: bool = False,
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
            logger.warning(
                "bronze_weather_write_skipped | "
                "target_table=%s | "
                "reason=no_records | "
                "request_id=%s",
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

        self._write_dataframe(
            dataframe=dataframe,
            overwrite=overwrite,
        )

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

    @staticmethod
    def _build_replace_where(
        min_dt_base: date,
        max_dt_base: date,
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"dt_base >= DATE '{min_dt_base.isoformat()}' "
            f"AND dt_base <= DATE '{max_dt_base.isoformat()}' "
            f"AND requested_latitude = {latitude} "
            f"AND requested_longitude = {longitude}"
        )

    def _get_dataframe_metadata(
        self,
        dataframe: DataFrame,
    ) -> dict[str, Any] | None:
        metadata = (
            dataframe
            .select(
                F.min("dt_base").alias(
                    "min_dt_base"
                ),
                F.max("dt_base").alias(
                    "max_dt_base"
                ),
                F.first(
                    "requested_latitude"
                ).alias("latitude"),
                F.first(
                    "requested_longitude"
                ).alias("longitude"),
            )
            .first()
        )

        if metadata is None:
            return None

        return {
            "min_dt_base": metadata[
                "min_dt_base"
            ],
            "max_dt_base": metadata[
                "max_dt_base"
            ],
            "latitude": metadata[
                "latitude"
            ],
            "longitude": metadata[
                "longitude"
            ],
        }

    @staticmethod
    def _build_existing_data_condition(
        min_dt_base: date,
        max_dt_base: date,
        latitude: float,
        longitude: float,
    ):
        return (
            C("dt_base").between(
                L(min_dt_base),
                L(max_dt_base),
            )
            & (
                C("requested_latitude")
                == L(latitude)
            )
            & (
                C("requested_longitude")
                == L(longitude)
            )
        )

    def _write_dataframe(
        self,
        dataframe: DataFrame,
        overwrite: bool = False,
    ) -> None:
        metadata = self._get_dataframe_metadata(
            dataframe
        )

        if metadata is None:
            logger.warning(
                "bronze_weather_write_skipped | "
                "target_table=%s | "
                "reason=empty_dataframe",
                self.target_table,
            )
            return

        min_dt_base = metadata[
            "min_dt_base"
        ]
        max_dt_base = metadata[
            "max_dt_base"
        ]
        latitude = metadata["latitude"]
        longitude = metadata["longitude"]

        logger.info(
            "bronze_weather_write_started | "
            "target_table=%s | "
            "latitude=%s | "
            "longitude=%s | "
            "min_dt_base=%s | "
            "max_dt_base=%s | "
            "overwrite=%s",
            self.target_table,
            latitude,
            longitude,
            min_dt_base,
            max_dt_base,
            overwrite,
        )

        condition = self._build_existing_data_condition(
            min_dt_base=min_dt_base,
            max_dt_base=max_dt_base,
            latitude=latitude,
            longitude=longitude,
        )

        table_exists = (
            self.spark.catalog.tableExists(
                self.target_table
            )
        )

        if table_exists:
            existing_data = (
                self.spark
                .table(self.target_table)
                .where(condition)
            )

            if (
                not existing_data.isEmpty()
                and not overwrite
            ):
                logger.warning(
                    "bronze_weather_data_already_exists | "
                    "target_table=%s | "
                    "latitude=%s | "
                    "longitude=%s | "
                    "min_dt_base=%s | "
                    "max_dt_base=%s | "
                    "overwrite=%s",
                    self.target_table,
                    latitude,
                    longitude,
                    min_dt_base,
                    max_dt_base,
                    overwrite,
                )

                raise ValueError(
                    "Bronze weather data already exists for "
                    f"latitude={latitude}, "
                    f"longitude={longitude}, "
                    f"period={min_dt_base} to "
                    f"{max_dt_base}. "
                    "Use overwrite=True to reprocess."
                )

        replace_where = self._build_replace_where(
            min_dt_base=min_dt_base,
            max_dt_base=max_dt_base,
            latitude=latitude,
            longitude=longitude,
        )

        logger.debug(
            "bronze_weather_replace_where_built | "
            "target_table=%s | "
            "predicate=%s",
            self.target_table,
            replace_where,
        )

        writer = (
            dataframe.write
            .format("delta")
            .mode("overwrite")
            .option(
                "replaceWhere",
                replace_where,
            )
        )

        # Liquid clustering is a table-layout property.
        # Define it only when the managed Delta table is created.
        # Subsequent writes preserve the table's clustering config.
        if not table_exists:
            writer = writer.clusterBy(
                *self.CLUSTERING_COLUMNS
            )

        writer.saveAsTable(
            self.target_table
        )

        logger.info(
            "bronze_weather_write_completed | "
            "target_table=%s | "
            "latitude=%s | "
            "longitude=%s | "
            "min_dt_base=%s | "
            "max_dt_base=%s | "
            "overwrite=%s",
            self.target_table,
            latitude,
            longitude,
            min_dt_base,
            max_dt_base,
            overwrite,
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
        if not isinstance(
            latitude,
            (int, float),
        ):
            raise TypeError(
                "requested_latitude must be numeric."
            )

        if not isinstance(
            longitude,
            (int, float),
        ):
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
