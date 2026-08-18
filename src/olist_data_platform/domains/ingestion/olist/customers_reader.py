from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


class OlistCustomersReader:
    """Read and validate the Olist customers CSV snapshot."""

    REQUIRED_COLUMNS = (
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    )

    def __init__(self, spark: SparkSession, source_path: str) -> None:
        if not isinstance(source_path, str):
            raise TypeError("source_path must be a string.")
        if not source_path.strip():
            raise ValueError("source_path cannot be empty.")

        self.spark = spark
        self.source_path = source_path

    def read(self) -> DataFrame:
        dataframe = (
            self.spark.read
            .option("header", True)
            .option("inferSchema", False)
            .csv(self.source_path)
            .select(
                "*",
                F.col("_metadata.file_path").alias("source_file"),
            )
        )

        self._validate_minimum_schema(dataframe)
        return dataframe

    def _validate_minimum_schema(self, dataframe: DataFrame) -> None:
        missing_columns = set(self.REQUIRED_COLUMNS) - set(dataframe.columns)
        if missing_columns:
            raise ValueError(
                "Olist customers source is missing required columns: "
                f"{sorted(missing_columns)}"
            )
