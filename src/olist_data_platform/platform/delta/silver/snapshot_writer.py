from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.contract import DatasetContract
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.quality import (
    DataQualityContract,
    DataQualityRunner,
    QualityReport,
)


class SilverSnapshotWriter:
    """Persist one protected Silver FULL_REPLACE snapshot.

    This API intentionally differs from BronzeWriter.write_checked.
    Bronze accepts an already evaluated QualityCheckedBatch so it can reuse
    key-integrity evidence produced by callers. Silver owns the repeated
    evaluate -> persist quality evidence -> blocking gate -> empty guard ->
    lifecycle -> full-replace protocol observed across the delivered snapshot
    processors, so write_checked accepts the transformed DataFrame directly.
    """

    def __init__(
        self,
        spark: SparkSession,
        target_table: str,
        dataset_contract: DatasetContract,
        quality_contract: DataQualityContract,
        quality_results_table: str,
        *,
        empty_snapshot_message: str | None = None,
    ) -> None:
        if not isinstance(target_table, str):
            raise TypeError("target_table must be a string.")
        if not target_table.strip():
            raise ValueError("target_table cannot be empty.")
        if not isinstance(quality_results_table, str):
            raise TypeError("quality_results_table must be a string.")
        if not quality_results_table.strip():
            raise ValueError("quality_results_table cannot be empty.")
        if dataset_contract.write_strategy is not WriteStrategy.FULL_REPLACE:
            raise ValueError(
                "SilverSnapshotWriter requires DatasetContract.write_strategy "
                "to be FULL_REPLACE."
            )
        if empty_snapshot_message is not None:
            if not isinstance(empty_snapshot_message, str):
                raise TypeError("empty_snapshot_message must be a string or None.")
            if not empty_snapshot_message.strip():
                raise ValueError("empty_snapshot_message cannot be empty.")

        self.spark = spark
        self.target_table = target_table
        self.dataset_contract = dataset_contract
        self.quality_contract = quality_contract
        self.quality_results_table = quality_results_table
        self.empty_snapshot_message = empty_snapshot_message

    def write_checked(
        self,
        dataframe: DataFrame,
        *,
        run_id: str,
        evaluation_scope: str,
    ) -> QualityReport:
        """Evaluate, record and persist one protected Silver snapshot.

        Unlike BronzeWriter.write_checked, callers pass the transformed
        DataFrame rather than a pre-evaluated batch. Data Quality evaluation and
        result persistence are part of this writer's contract because that exact
        correctness-sensitive sequence is the shared Silver snapshot behavior.
        """
        checked = DataQualityRunner().evaluate(
            dataframe=dataframe,
            contract=self.quality_contract,
            run_id=run_id,
            evaluation_scope=evaluation_scope,
        )
        QualityResultWriter(
            self.spark,
            self.quality_results_table,
        ).write(checked.report)
        checked.report.raise_for_blocking_failures()

        if checked.report.row_count == 0:
            raise ValueError(
                self.empty_snapshot_message
                or (
                    "Silver FULL_REPLACE snapshot cannot be empty; "
                    f"target_table={self.target_table}; "
                    "the existing target was preserved."
                )
            )

        DeltaTableLifecycle(
            self.spark,
            self.target_table,
            self.dataset_contract,
        ).ensure()
        (
            checked.dataframe.select(*self.dataset_contract.required_columns)
            .write.format("delta")
            .mode("overwrite")
            .saveAsTable(self.target_table)
        )
        return checked.report
