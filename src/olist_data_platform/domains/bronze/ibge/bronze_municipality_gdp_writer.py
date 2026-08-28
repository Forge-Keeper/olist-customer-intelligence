from __future__ import annotations

import json
from typing import Any

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, StringType, StructField, StructType

from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.operations import (
    ExecutionRunTracker,
    ExecutionStage,
    QualityRunStatus,
)
from olist_data_platform.platform.quality import DataQualityRunner, QualityOutcome

from .municipality_gdp_bronze_config import IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG
from .municipality_gdp_quality import build_municipality_gdp_quality_contract


class BronzeMunicipalityGdpWriter:
    """Adapt IBGE SIDRA GDP records, evaluate DQ and persist Bronze data.

    Source-specific DataFrame construction remains in this domain adapter.
    Generic quality evaluation, audit-result persistence and Bronze Delta write
    semantics remain delegated to platform collaborators.
    """

    INPUT_SCHEMA = StructType(
        [
            StructField("municipality_code", StringType(), False),
            StructField("reference_year", StringType(), False),
            StructField("variable_code", StringType(), False),
            StructField("dt_base", DateType(), False),
            StructField("payload_json", StringType(), False),
            StructField("request_id", StringType(), False),
        ]
    )

    def __init__(
        self,
        spark: SparkSession,
        target_table: str,
        *,
        quality_runner: DataQualityRunner | None = None,
        quality_result_writer: QualityResultWriter | None = None,
        run_tracker: ExecutionRunTracker | None = None,
    ) -> None:
        if (quality_runner is None) != (quality_result_writer is None):
            raise ValueError(
                "quality_runner and quality_result_writer must be configured together."
            )
        self.spark = spark
        self.writer = BronzeWriter(
            spark=spark,
            target_table=target_table,
            config=IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
        )
        self.quality_runner = quality_runner
        self.quality_result_writer = quality_result_writer
        self.run_tracker = run_tracker

    def write(
        self,
        records: list[dict[str, Any]],
        request_id: str,
        periods: tuple[str, ...] | None = None,
    ) -> None:
        """Persist one GDP batch, using first-class Data Quality when configured."""
        quality_enabled = self.quality_runner is not None
        if not records and not quality_enabled:
            return

        dataframe = self._build_dataframe(records=records, request_id=request_id)
        if not quality_enabled:
            self.writer.write(dataframe)
            return
        if periods is None or not periods:
            raise ValueError("periods are required when GDP Data Quality is enabled.")
        if self.quality_result_writer is None:
            raise RuntimeError(
                "quality_result_writer is required when Data Quality is enabled."
            )

        scope = json.dumps(
            {"periods": list(periods)},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if self.run_tracker is not None:
            self.run_tracker.update_metrics(
                request_id,
                records_extracted=len(records),
            )
            self.run_tracker.set_stage(request_id, ExecutionStage.QUALITY)

        checked = self.quality_runner.evaluate(
            dataframe=dataframe,
            contract=build_municipality_gdp_quality_contract(periods),
            run_id=request_id,
            evaluation_scope=scope,
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
                request_id,
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
                    request_id,
                    error_message=(
                        "Blocking Data Quality rules failed: " f"{failed_rules}"
                    ),
                )
            checked.report.raise_for_blocking_failures()

        if self.run_tracker is not None:
            self.run_tracker.set_stage(request_id, ExecutionStage.WRITE)
        self.writer.write_checked(checked)
        if self.run_tracker is not None:
            self.run_tracker.update_metrics(
                request_id,
                records_written=checked.report.row_count,
            )

    def _build_dataframe(
        self,
        *,
        records: list[dict[str, Any]],
        request_id: str,
    ) -> DataFrame:
        rows = [
            Row(
                municipality_code=str(record["municipality_code"]),
                reference_year=str(record["reference_year"]),
                variable_code=str(record["variable_code"]),
                dt_base=record["dt_base"],
                payload_json=json.dumps(
                    record["payload"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                request_id=request_id,
            )
            for record in records
        ]
        dataframe = self.spark.createDataFrame(rows, schema=self.INPUT_SCHEMA)
        return dataframe.withColumn("payload", F.parse_json("payload_json")).drop(
            "payload_json"
        )
