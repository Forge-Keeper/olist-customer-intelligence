from __future__ import annotations

from typing import Protocol

from pyspark.sql import DataFrame

from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.logging import LoggerFactory
from olist_data_platform.platform.operations import (
    ExecutionRunTracker,
    ExecutionStage,
    QualityRunStatus,
)
from olist_data_platform.platform.quality import (
    DataQualityContract,
    QualityCheckedBatch,
    QualityOutcome,
    QualityReport,
)

logger = LoggerFactory.get_logger(__name__)


class SnapshotReader(Protocol):
    source_path: str

    def read(self) -> DataFrame: ...


class QualityEvaluator(Protocol):
    def evaluate(
        self,
        *,
        dataframe: DataFrame,
        contract: DataQualityContract,
        run_id: str,
        evaluation_scope: str,
    ) -> QualityCheckedBatch: ...


class QualityResultSink(Protocol):
    def write(self, report: QualityReport) -> None: ...


class OlistSnapshotIngestionService:
    """Load an authoritative Olist snapshot into Bronze.

    First-class Data Quality is optional so existing Olist snapshots can keep the
    legacy write path while newly migrated datasets reuse the same reader/service
    boundary and persist checked-batch evidence before the protected write.
    """

    def __init__(
        self,
        dataset_name: str,
        reader: SnapshotReader,
        bronze_writer: BronzeWriter,
        *,
        quality_contract: DataQualityContract | None = None,
        quality_runner: QualityEvaluator | None = None,
        quality_result_writer: QualityResultSink | None = None,
        run_tracker: ExecutionRunTracker | None = None,
    ) -> None:
        if not dataset_name.strip():
            raise ValueError("dataset_name cannot be empty.")

        quality_components = (
            quality_contract,
            quality_runner,
            quality_result_writer,
        )
        if any(component is not None for component in quality_components) and not all(
            component is not None for component in quality_components
        ):
            raise ValueError(
                "quality_contract, quality_runner and quality_result_writer "
                "must be configured together."
            )
        if quality_contract is not None and quality_contract.dataset != dataset_name:
            raise ValueError(
                "quality_contract.dataset must match dataset_name: "
                f"{quality_contract.dataset!r} != {dataset_name!r}."
            )

        self.dataset_name = dataset_name
        self.reader = reader
        self.bronze_writer = bronze_writer
        self.quality_contract = quality_contract
        self.quality_runner = quality_runner
        self.quality_result_writer = quality_result_writer
        self.run_tracker = run_tracker

    @property
    def quality_enabled(self) -> bool:
        return self.quality_contract is not None

    def ingest(
        self,
        *,
        run_id: str | None = None,
        evaluation_scope: str = "{}",
    ) -> int:
        if (self.quality_enabled or self.run_tracker is not None) and not run_id:
            raise ValueError(
                "run_id is required when Data Quality or execution tracking is enabled."
            )

        logger.info(
            "%s_ingestion_started | source_path=%s | target_table=%s",
            self.dataset_name,
            self.reader.source_path,
            self.bronze_writer.target_table,
        )
        try:
            dataframe = self.reader.read()
            row_count = dataframe.count()
            logger.info(
                "%s_snapshot_read | source_path=%s | row_count=%s | column_count=%s",
                self.dataset_name,
                self.reader.source_path,
                row_count,
                len(dataframe.columns),
            )

            if self.run_tracker is not None and run_id is not None:
                self.run_tracker.update_metrics(
                    run_id,
                    records_extracted=row_count,
                )

            if not self.quality_enabled:
                if self.run_tracker is not None and run_id is not None:
                    self.run_tracker.set_stage(run_id, ExecutionStage.WRITE)
                self.bronze_writer.write(dataframe)
                if self.run_tracker is not None and run_id is not None:
                    self.run_tracker.update_metrics(
                        run_id,
                        records_written=row_count,
                    )
                return row_count

            if (
                self.quality_contract is None
                or self.quality_runner is None
                or self.quality_result_writer is None
                or run_id is None
            ):
                raise RuntimeError("Incomplete first-class Data Quality configuration.")

            if self.run_tracker is not None:
                self.run_tracker.set_stage(run_id, ExecutionStage.QUALITY)

            checked = self.quality_runner.evaluate(
                dataframe=dataframe,
                contract=self.quality_contract,
                run_id=run_id,
                evaluation_scope=evaluation_scope,
            )
            self.quality_result_writer.write(checked.report)

            if self.run_tracker is not None:
                outcome_mapping = {
                    QualityOutcome.PASSED: QualityRunStatus.PASSED,
                    QualityOutcome.PASSED_WITH_WARNINGS: (
                        QualityRunStatus.PASSED_WITH_WARNINGS
                    ),
                    QualityOutcome.FAILED: QualityRunStatus.FAILED,
                }
                self.run_tracker.update_quality(
                    run_id,
                    outcome_mapping[checked.report.outcome],
                    records_evaluated=checked.report.row_count,
                )

            if checked.report.has_blocking_failures:
                if self.run_tracker is not None:
                    failed_rules = ", ".join(
                        result.rule_id
                        for result in checked.report.results
                        if result.status.value == "FAIL"
                        and result.severity.value == "ERROR"
                    )
                    self.run_tracker.reject(
                        run_id,
                        error_message=(
                            "Blocking Data Quality rules failed: "
                            f"{failed_rules}"
                        ),
                    )
                checked.report.raise_for_blocking_failures()

            if self.run_tracker is not None:
                self.run_tracker.set_stage(run_id, ExecutionStage.WRITE)
            self.bronze_writer.write_checked(checked)
            if self.run_tracker is not None:
                self.run_tracker.update_metrics(
                    run_id,
                    records_written=checked.report.row_count,
                )

            logger.info(
                "%s_ingestion_completed | target_table=%s | row_count=%s",
                self.dataset_name,
                self.bronze_writer.target_table,
                row_count,
            )
            return row_count
        except Exception:
            logger.exception(
                "%s_ingestion_failed | source_path=%s | target_table=%s",
                self.dataset_name,
                self.reader.source_path,
                self.bronze_writer.target_table,
            )
            raise
