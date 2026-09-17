from datetime import datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

from olist_data_platform.platform.delta.operations.execution_run_repository import (
    ExecutionRunRepository,
)
from olist_data_platform.platform.delta.quality.result_writer import QualityResultWriter
from olist_data_platform.platform.operations.model import (
    ExecutionRun,
    ExecutionStage,
    ExecutionStatus,
    QualityRunStatus,
)
from olist_data_platform.platform.quality.model import QualityReport


def _execution_run() -> ExecutionRun:
    return ExecutionRun(
        run_id="run-1",
        dataset="olist_sellers",
        layer="silver",
        source_system="olist_bronze",
        target_table="dev.silver.olist_sellers",
        execution_scope="{}",
        started_at=datetime(2026, 9, 12),
        finished_at=None,
        status=ExecutionStatus.RUNNING,
        quality_status=QualityRunStatus.NOT_EVALUATED,
        records_extracted=None,
        records_evaluated=None,
        records_written=None,
        error_stage=None,
        error_type=None,
        error_message=None,
        orchestrator_run_id=None,
        last_stage=ExecutionStage.SOURCE,
    )


def test_execution_run_repository_skips_metadata_reconciliation() -> None:
    spark = Mock()
    dataframe = Mock()
    spark.createDataFrame.return_value = dataframe
    repository = ExecutionRunRepository(spark, "dev_admin.operations.execution_runs")
    repository.lifecycle = Mock()

    repository.upsert(_execution_run())

    repository.lifecycle.ensure.assert_called_once_with(reconcile_metadata=False)
    dataframe.createOrReplaceTempView.assert_called_once()
    spark.sql.assert_called_once()


def test_quality_result_writer_skips_metadata_reconciliation() -> None:
    spark = Mock()
    dataframe = Mock()
    spark.createDataFrame.return_value = dataframe
    writer = QualityResultWriter(spark, "dev_admin.quality.data_quality_results")
    writer.lifecycle = Mock()
    result = SimpleNamespace(
        run_id="run-1",
        dataset="olist_sellers",
        layer="silver",
        rule_id="DQ01",
        rule_version=1,
        category=SimpleNamespace(value="COMPLETENESS"),
        severity=SimpleNamespace(value="ERROR"),
        status=SimpleNamespace(value="PASS"),
        observed_value="{}",
        expected_condition="expected",
        evaluation_scope="{}",
        evaluated_at=datetime(2026, 9, 12),
    )
    report = cast(QualityReport, SimpleNamespace(results=[result]))

    writer.write(report)

    writer.lifecycle.ensure.assert_called_once_with(reconcile_metadata=False)
    dataframe.createOrReplaceTempView.assert_called_once()
    spark.sql.assert_called_once()
