from __future__ import annotations

from uuid import uuid4

from pyspark.sql import Row, SparkSession

from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.contract import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle
from olist_data_platform.platform.operations.model import ExecutionRun

EXECUTION_RUN_CONTRACT = DatasetContract(
    columns=(
        ColumnContract(
            "run_id",
            "string",
            False,
            "Unique platform execution identifier.",
        ),
        ColumnContract(
            "dataset",
            "string",
            False,
            "Logical dataset processed by the execution.",
        ),
        ColumnContract(
            "layer",
            "string",
            False,
            "Data layer targeted by the execution.",
        ),
        ColumnContract(
            "source_system",
            "string",
            False,
            "Source system associated with the execution.",
        ),
        ColumnContract(
            "target_table",
            "string",
            False,
            "Fully qualified data-plane target table.",
        ),
        ColumnContract(
            "execution_scope",
            "string",
            False,
            "Canonical JSON execution scope.",
        ),
        ColumnContract(
            "started_at",
            "timestamp",
            False,
            "Execution start timestamp.",
        ),
        ColumnContract(
            "finished_at",
            "timestamp",
            True,
            "Execution completion timestamp when terminal.",
        ),
        ColumnContract(
            "status",
            "string",
            False,
            "Execution lifecycle status.",
        ),
        ColumnContract(
            "quality_status",
            "string",
            False,
            "Data-quality outcome for the execution.",
        ),
        ColumnContract(
            "records_extracted",
            "bigint",
            True,
            "Records extracted from the source when known.",
        ),
        ColumnContract(
            "records_evaluated",
            "bigint",
            True,
            "Records evaluated by data quality when known.",
        ),
        ColumnContract(
            "records_written",
            "bigint",
            True,
            "Records submitted to the target write when known.",
        ),
        ColumnContract(
            "error_stage",
            "string",
            True,
            "Execution stage that produced the terminal error.",
        ),
        ColumnContract(
            "error_type",
            "string",
            True,
            "Error class or stable operational classification.",
        ),
        ColumnContract(
            "error_message",
            "string",
            True,
            "Sanitized operational error message.",
        ),
        ColumnContract(
            "orchestrator_run_id",
            "string",
            True,
            "External orchestrator run identifier when available.",
        ),
        ColumnContract(
            "last_stage",
            "string",
            False,
            "Last coarse execution stage reached.",
        ),
    ),
    key_columns=("run_id",),
    write_strategy=WriteStrategy.MERGE,
    metadata=TableMetadata(
        description="Operational execution history for Olist Data Platform workloads.",
        tags={"managed_by": "olist_data_platform"},
    ),
)


class ExecutionRunRepository:
    """Persist execution-run state idempotently in a managed Delta table."""

    def __init__(self, spark: SparkSession, target_table: str) -> None:
        self.spark = spark
        self.target_table = target_table
        self.lifecycle = DeltaTableLifecycle(
            spark,
            target_table,
            EXECUTION_RUN_CONTRACT,
        )

    def upsert(self, run: ExecutionRun) -> None:
        dataframe = self.spark.createDataFrame(
            [
                Row(
                    run_id=run.run_id,
                    dataset=run.dataset,
                    layer=run.layer,
                    source_system=run.source_system,
                    target_table=run.target_table,
                    execution_scope=run.execution_scope,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    status=run.status.value,
                    quality_status=run.quality_status.value,
                    records_extracted=run.records_extracted,
                    records_evaluated=run.records_evaluated,
                    records_written=run.records_written,
                    error_stage=run.error_stage,
                    error_type=run.error_type,
                    error_message=run.error_message,
                    orchestrator_run_id=run.orchestrator_run_id,
                    last_stage=run.last_stage.value,
                )
            ],
            schema=EXECUTION_RUN_CONTRACT.to_struct_type(),
        )
        self.lifecycle.ensure()
        source_view = f"_execution_run_{uuid4().hex}"
        dataframe.createOrReplaceTempView(source_view)
        try:
            self.spark.sql(
                f"""
                MERGE INTO {self.target_table} AS target
                USING {source_view} AS source
                ON target.run_id = source.run_id
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
                """
            )
        finally:
            self.spark.catalog.dropTempView(source_view)
