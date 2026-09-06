from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from .config import JdbcConfig


class JdbcReader:
    def __init__(self, spark: SparkSession, config: JdbcConfig) -> None:
        self._spark = spark
        self._config = config

    def read_table(self, table: str) -> DataFrame:
        if not isinstance(table, str):
            raise TypeError("table must be a string")
        if not table.strip():
            raise ValueError("table cannot be empty")

        return (
            self._spark.read.format("jdbc")
            .options(**self._config.options)
            .option("dbtable", table)
            .load()
        )
