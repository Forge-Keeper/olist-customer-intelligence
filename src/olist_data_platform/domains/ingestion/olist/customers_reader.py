from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


class OlistCustomersReader:
    """Read and validate the Olist customers CSV snapshot."""

    EXPECTED_TYPES = {
        "customer_id": "string",
        "customer_unique_id": "string",
        "customer_zip_code_prefix": "int",
        "customer_city": "string",
        "customer_state": "string",
    }

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
            .option("inferSchema", True)
            .csv(self.source_path)
            .select(
                "*",
                F.col("_metadata.file_path").alias("source_file"),
            )
        )

        self._validate_minimum_schema(dataframe)
        return dataframe

    def _validate_minimum_schema(self, dataframe: DataFrame) -> None:
        actual_types = {
            field.name: field.dataType.simpleString()
            for field in dataframe.schema.fields
        }

        missing_columns = set(self.EXPECTED_TYPES) - set(actual_types)
        if missing_columns:
            raise ValueError(
                "Olist customers source is missing required columns: "
                f"{sorted(missing_columns)}"
            )

        incompatible_types = {
            column: (actual_types[column], expected_type)
            for column, expected_type in self.EXPECTED_TYPES.items()
            if actual_types[column] != expected_type
        }
        if incompatible_types:
            details = ", ".join(
                f"{column}: actual={actual}, expected={expected}"
                for column, (actual, expected) in incompatible_types.items()
            )
            raise ValueError(
                "Olist customers source has incompatible required-column types: "
                f"{details}"
            )
