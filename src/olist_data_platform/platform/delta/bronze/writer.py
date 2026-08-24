from __future__ import annotations

from uuid import uuid4

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from olist_data_platform.platform.delta.bronze.config import (
    BronzeDatasetConfig,
    WriteStrategy,
)
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class BronzeWriter:
    """Persist Bronze batches according to declarative write semantics.

    The writer owns batch preparation, platform-managed ingestion timestamp
    injection, logical-key validation and MERGE/FULL_REPLACE/replaceWhere write
    behavior. Table lifecycle, schema evolution and governance reconciliation are
    being moved to the dedicated Delta lifecycle boundary and must not accumulate
    here as new responsibilities.
    """

    INGESTION_TIMESTAMP_COLUMN = "ingestion_timestamp"

    def __init__(
        self,
        spark: SparkSession,
        target_table: str,
        config: BronzeDatasetConfig,
    ) -> None:
        if not isinstance(target_table, str):
            raise TypeError("target_table must be a string.")
        if not target_table.strip():
            raise ValueError("target_table cannot be empty.")

        self.spark = spark
        self.target_table = target_table
        self.config = config

    def write(self, dataframe: DataFrame) -> None:
        """Persist one validated Bronze batch using the configured write strategy.

        The method adds the platform ingestion timestamp, validates logical key
        values/duplicates and then applies MERGE or FULL_REPLACE semantics. An
        empty FULL_REPLACE snapshot fails before replacing existing data.
        """
        prepared = self._prepare_dataframe(dataframe)

        logger.info(
            "bronze_write_started | target_table=%s | strategy=%s",
            self.target_table,
            self.config.write_strategy.value,
        )

        if self.config.write_strategy is WriteStrategy.FULL_REPLACE:
            self._validate_non_empty_snapshot(prepared)

        if not self.spark.catalog.tableExists(self.target_table):
            self._create_table(prepared)
        else:
            self._write_existing_table(prepared)

        logger.info(
            "bronze_write_completed | target_table=%s | strategy=%s",
            self.target_table,
            self.config.write_strategy.value,
        )

    def replace_where(self, dataframe: DataFrame, predicate: str) -> None:
        """Atomically replace one explicitly bounded Bronze scope.

        ``predicate`` is passed to Delta ``replaceWhere`` and must therefore be
        supplied deliberately by the caller; this method never infers the scope.
        Invalid/empty predicates fail before any persistence operation.
        """
        if not isinstance(predicate, str):
            raise TypeError("predicate must be a string.")
        if not predicate.strip():
            raise ValueError("predicate cannot be empty.")

        prepared = self._prepare_dataframe(dataframe)

        logger.info(
            "bronze_reprocess_started | target_table=%s | predicate=%s",
            self.target_table,
            predicate,
        )

        if not self.spark.catalog.tableExists(self.target_table):
            self._create_table(prepared)
        else:
            (
                prepared.write
                .format("delta")
                .mode("overwrite")
                .option("replaceWhere", predicate)
                .saveAsTable(self.target_table)
            )

        logger.info(
            "bronze_reprocess_completed | target_table=%s | predicate=%s",
            self.target_table,
            predicate,
        )

    def _prepare_dataframe(self, dataframe: DataFrame) -> DataFrame:
        self._validate_dataframe_contract(dataframe)

        prepared = dataframe.withColumn(
            self.INGESTION_TIMESTAMP_COLUMN,
            F.current_timestamp(),
        )

        self._validate_primary_key_values(prepared)
        return prepared

    def _validate_dataframe_contract(self, dataframe: DataFrame) -> None:
        columns = set(dataframe.columns)
        required = set(self.config.required_columns)
        missing = required - columns
        if missing:
            raise ValueError(
                "DataFrame is missing required Bronze columns: "
                f"{sorted(missing)}"
            )

        layout_columns = (
            set(self.config.clustering_columns)
            | set(self.config.partition_columns)
        )
        missing_layout = layout_columns - columns
        if missing_layout:
            raise ValueError(
                "DataFrame is missing configured layout columns: "
                f"{sorted(missing_layout)}"
            )

    def _validate_primary_key_values(self, dataframe: DataFrame) -> None:
        null_condition = None
        for column_name in self.config.primary_key_columns:
            condition = F.col(column_name).isNull()
            null_condition = (
                condition
                if null_condition is None
                else null_condition | condition
            )

        has_null_primary_key = (
            null_condition is not None
            and dataframe.where(null_condition).limit(1).count()
        )
        if has_null_primary_key:
            raise ValueError("Bronze primary key columns cannot contain null values.")

        duplicated = (
            dataframe.groupBy(*self.config.primary_key_columns)
            .count()
            .where(F.col("count") > 1)
            .limit(1)
            .count()
        )
        if duplicated:
            raise ValueError("Bronze batch contains duplicate primary keys.")

    @staticmethod
    def _validate_non_empty_snapshot(dataframe: DataFrame) -> None:
        if dataframe.limit(1).count() == 0:
            raise ValueError(
                "Bronze FULL_REPLACE snapshot cannot be empty; "
                "the existing target was preserved."
            )

    def _create_table(self, dataframe: DataFrame) -> None:
        writer = dataframe.write.format("delta").mode("overwrite")

        if self.config.clustering_columns:
            writer = writer.clusterBy(*self.config.clustering_columns)
        elif self.config.partition_columns:
            writer = writer.partitionBy(*self.config.partition_columns)

        writer.saveAsTable(self.target_table)

    def _write_existing_table(self, dataframe: DataFrame) -> None:
        if self.config.write_strategy is WriteStrategy.MERGE:
            self._merge(dataframe)
            return

        if self.config.write_strategy is WriteStrategy.FULL_REPLACE:
            self._full_replace(dataframe)
            return

        if self.config.write_strategy is WriteStrategy.REPLACE_WHERE:
            raise NotImplementedError(
                "REPLACE_WHERE normal-write strategy requires an explicit scope "
                "and is not implemented as an implicit write behavior."
            )

        raise ValueError(
            f"Unsupported Bronze write strategy: {self.config.write_strategy!r}"
        )

    def _full_replace(self, dataframe: DataFrame) -> None:
        (
            dataframe.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(self.target_table)
        )

    def _merge(self, dataframe: DataFrame) -> None:
        source_view = f"_bronze_source_{uuid4().hex}"
        dataframe.createOrReplaceTempView(source_view)

        merge_condition = " AND ".join(
            f"target.`{column}` = source.`{column}`"
            for column in self.config.primary_key_columns
        )

        try:
            self.spark.sql(
                f"""
                MERGE INTO {self.target_table} AS target
                USING {source_view} AS source
                ON {merge_condition}
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
                """
            )
        finally:
            self.spark.catalog.dropTempView(source_view)
