from __future__ import annotations

from collections.abc import Sequence

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


class OlistCsvSnapshotReader:
    """Read an Olist CSV snapshot while preserving source values as strings."""

    def __init__(
        self,
        spark: SparkSession,
        source_path: str,
        required_columns: Sequence[str],
        dataset_name: str,
    ) -> None:
        if not isinstance(source_path, str):
            raise TypeError("source_path must be a string.")
        if not source_path.strip():
            raise ValueError("source_path cannot be empty.")
        if not required_columns:
            raise ValueError("required_columns cannot be empty.")
        if not dataset_name.strip():
            raise ValueError("dataset_name cannot be empty.")

        self.spark = spark
        self.source_path = source_path
        self.required_columns = tuple(required_columns)
        self.dataset_name = dataset_name

    def read(self) -> DataFrame:
        dataframe = (
            self.spark.read.option("header", True)
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
        missing_columns = set(self.required_columns) - set(dataframe.columns)
        if missing_columns:
            raise ValueError(
                f"{self.dataset_name} source is missing required columns: "
                f"{sorted(missing_columns)}"
            )
