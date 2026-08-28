from __future__ import annotations

from uuid import uuid4

from pyspark.sql import Row, SparkSession

from olist_data_platform.platform.delta.contract import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle
from olist_data_platform.platform.quality.model import QualityReport


DATA_QUALITY_RESULT_CONTRACT = DatasetContract(
    columns=(
        ColumnContract(
            "run_id",
            "string",
            False,
            "Platform execution identifier.",
        ),
        ColumnContract(
            "dataset",
            "string",
            False,
            "Logical dataset evaluated.",
        ),
        ColumnContract(
            "layer",
            "string",
            False,
            "Data layer evaluated.",
        ),
        ColumnContract(
            "rule_id",
            "string",
            False,
            "Stable Data Quality rule identifier.",
        ),
        ColumnContract(
            "rule_version",
            "bigint",
            False,
            "Version of the evaluated rule.",
        ),
        ColumnContract(
            "category",
            "string",
            False,
            "Data Quality rule category.",
        ),
        ColumnContract(
            "severity",
            "string",
            False,
            "Configured rule severity.",
        ),
        ColumnContract(
            "status",
            "string",
            False,
            "PASS or FAIL evaluation result.",
        ),
        ColumnContract(
            "observed_value",
            "string",
            False,
            "Canonical JSON observation produced by the rule.",
        ),
        ColumnContract(
            "expected_condition",
            "string",
            False,
            "Human-readable expected rule condition.",
        ),
        ColumnContract(
            "evaluation_scope",
            "string",
            False,
            "Canonical JSON scope for the evaluation.",
        ),
        ColumnContract(
            "evaluated_at",
            "timestamp",
            False,
            "Timestamp when the rule was evaluated.",
        ),
    ),
    key_columns=(
        "run_id",
        "dataset",
        "rule_id",
        "rule_version",
        "evaluation_scope",
    ),
    write_strategy=WriteStrategy.MERGE,
    metadata=TableMetadata(
        description=(
            "Persisted Data Quality results correlated with platform execution runs."
        ),
        tags={"managed_by": "olist_data_platform"},
    ),
)


class QualityResultWriter:
    """Persist Data Quality results idempotently in a managed Delta table."""

    def __init__(self, spark: SparkSession, target_table: str) -> None:
        self.spark = spark
        self.target_table = target_table
        self.lifecycle = DeltaTableLifecycle(
            spark,
            target_table,
            DATA_QUALITY_RESULT_CONTRACT,
        )

    def write(self, report: QualityReport) -> None:
        if not report.results:
            raise ValueError("QualityReport must contain at least one result.")
        rows = [
            Row(
                run_id=result.run_id,
                dataset=result.dataset,
                layer=result.layer,
                rule_id=result.rule_id,
                rule_version=result.rule_version,
                category=result.category.value,
                severity=result.severity.value,
                status=result.status.value,
                observed_value=result.observed_value,
                expected_condition=result.expected_condition,
                evaluation_scope=result.evaluation_scope,
                evaluated_at=result.evaluated_at,
            )
            for result in report.results
        ]
        dataframe = self.spark.createDataFrame(
            rows,
            schema=DATA_QUALITY_RESULT_CONTRACT.to_struct_type(),
        )
        self.lifecycle.ensure()
        source_view = f"_quality_results_{uuid4().hex}"
        dataframe.createOrReplaceTempView(source_view)
        try:
            self.spark.sql(
                f"""
                MERGE INTO {self.target_table} AS target
                USING {source_view} AS source
                ON target.run_id = source.run_id
                   AND target.dataset = source.dataset
                   AND target.rule_id = source.rule_id
                   AND target.rule_version = source.rule_version
                   AND target.evaluation_scope = source.evaluation_scope
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
                """
            )
        finally:
            self.spark.catalog.dropTempView(source_view)
