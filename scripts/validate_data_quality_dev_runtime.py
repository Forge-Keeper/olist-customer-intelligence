from __future__ import annotations

import argparse
import json
from datetime import date
from uuid import uuid4

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from olist_data_platform.domains.bronze.ibge.bronze_municipality_gdp_writer import (
    BronzeMunicipalityGdpWriter,
)
from olist_data_platform.domains.ingestion.ibge.datasets import MUNICIPALITY_GDP
from olist_data_platform.platform.delta.operations import ExecutionRunRepository
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.operations import ExecutionRunTracker
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    DataQualityRunner,
    QualitySeverity,
    QualityStatus,
)

EXPECTED_2018_ROWS = 33_420
EXPECTED_RULE_COUNT = 8
GDP_KEY_COLUMNS = ("municipality_code", "reference_year", "variable_code")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--success-run-id", required=True)
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--execution-runs-table", required=True)
    parser.add_argument("--quality-results-table", required=True)
    parser.add_argument("--temp-table", required=True)
    return parser


def _single_row(dataframe, *, message: str):
    rows = dataframe.collect()
    if len(rows) != 1:
        raise AssertionError(f"{message}: expected 1 row, found {len(rows)}")
    return rows[0]


def _assert_success_evidence(
    spark: SparkSession,
    *,
    success_run_id: str,
    target_table: str,
    execution_runs_table: str,
    quality_results_table: str,
) -> None:
    execution = _single_row(
        spark.table(execution_runs_table).where(F.col("run_id") == success_run_id),
        message="successful execution evidence",
    )
    if execution.status != "SUCCEEDED":
        raise AssertionError(f"expected SUCCEEDED, found {execution.status}")
    if execution.quality_status not in {"PASSED", "PASSED_WITH_WARNINGS"}:
        raise AssertionError(
            f"expected successful quality status, found {execution.quality_status}"
        )
    for field_name in (
        "records_extracted",
        "records_evaluated",
        "records_written",
    ):
        value = int(execution[field_name])
        if value != EXPECTED_2018_ROWS:
            raise AssertionError(
                f"{field_name}: expected {EXPECTED_2018_ROWS}, found {value}"
            )

    quality_rows = (
        spark.table(quality_results_table)
        .where(F.col("run_id") == success_run_id)
        .collect()
    )
    if len(quality_rows) != EXPECTED_RULE_COUNT:
        raise AssertionError(
            f"expected {EXPECTED_RULE_COUNT} quality results, found {len(quality_rows)}"
        )
    blocking_failures = [
        row.rule_id
        for row in quality_rows
        if row.status == QualityStatus.FAIL.value
        and row.severity == QualitySeverity.ERROR.value
    ]
    if blocking_failures:
        raise AssertionError(
            "successful execution contains blocking DQ failures: "
            + ", ".join(blocking_failures)
        )

    bronze_2018 = spark.table(target_table).where(F.col("reference_year") == "2018")
    row_count = bronze_2018.count()
    distinct_key_count = bronze_2018.select(*GDP_KEY_COLUMNS).distinct().count()
    combination_count = (
        bronze_2018.select("reference_year", "variable_code").distinct().count()
    )
    if row_count != EXPECTED_2018_ROWS:
        raise AssertionError(
            f"2018 Bronze row count: expected {EXPECTED_2018_ROWS}, found {row_count}"
        )
    if distinct_key_count != EXPECTED_2018_ROWS:
        raise AssertionError(
            "2018 Bronze natural keys are not unique: "
            f"rows={row_count}, distinct_keys={distinct_key_count}"
        )
    if combination_count != len(MUNICIPALITY_GDP.variables):
        raise AssertionError(
            "2018 Bronze variable coverage mismatch: "
            f"expected {len(MUNICIPALITY_GDP.variables)}, found {combination_count}"
        )

    print(
        "dq_runtime_success_evidence "
        + json.dumps(
            {
                "run_id": success_run_id,
                "execution_status": execution.status,
                "quality_status": execution.quality_status,
                "quality_rule_count": len(quality_rows),
                "bronze_2018_rows": row_count,
                "bronze_2018_distinct_keys": distinct_key_count,
                "bronze_2018_variable_combinations": combination_count,
            },
            sort_keys=True,
        )
    )


def _build_validation_records() -> list[dict[str, object]]:
    return [
        {
            "municipality_code": "9999999",
            "reference_year": "2018",
            "variable_code": variable_code,
            "dt_base": date(2018, 1, 1),
            "payload": {"Valor": "1", "validation": "dq_runtime"},
        }
        for variable_code in MUNICIPALITY_GDP.variables
    ]


def _assert_blocking_gate(
    spark: SparkSession,
    *,
    execution_runs_table: str,
    quality_results_table: str,
    temp_table: str,
) -> None:
    spark.sql(f"DROP TABLE IF EXISTS {temp_table}")
    repository = ExecutionRunRepository(spark, execution_runs_table)
    tracker = ExecutionRunTracker(repository)
    runner = DataQualityRunner()
    result_writer = QualityResultWriter(spark, quality_results_table)
    writer = BronzeMunicipalityGdpWriter(
        spark,
        temp_table,
        quality_runner=runner,
        quality_result_writer=result_writer,
        run_tracker=tracker,
    )
    valid_run_id = f"dq-runtime-valid-{uuid4()}"
    rejected_run_id = f"dq-runtime-rejected-{uuid4()}"
    periods = ("2018",)
    scope = json.dumps(
        {"periods": list(periods), "validation": "blocking_gate"},
        sort_keys=True,
        separators=(",", ":"),
    )
    valid_records = _build_validation_records()

    try:
        tracker.start(
            run_id=valid_run_id,
            dataset="ibge_municipality_gdp_runtime_validation",
            layer="bronze",
            source_system="runtime_validation",
            target_table=temp_table,
            execution_scope=scope,
        )
        writer.write(valid_records, valid_run_id, periods)
        tracker.succeed(valid_run_id)
        baseline_count = spark.table(temp_table).count()
        if baseline_count != len(valid_records):
            raise AssertionError(
                f"validation baseline expected {len(valid_records)} rows, "
                f"found {baseline_count}"
            )

        tracker.start(
            run_id=rejected_run_id,
            dataset="ibge_municipality_gdp_runtime_validation",
            layer="bronze",
            source_system="runtime_validation",
            target_table=temp_table,
            execution_scope=scope,
        )
        invalid_records = [*valid_records, valid_records[0]]
        try:
            writer.write(invalid_records, rejected_run_id, periods)
        except DataQualityRejectedError:
            pass
        else:
            raise AssertionError("duplicate-key batch was not rejected by Data Quality")

        after_rejection_count = spark.table(temp_table).count()
        if after_rejection_count != baseline_count:
            raise AssertionError(
                "Bronze validation table mutated after a rejected batch: "
                f"before={baseline_count}, after={after_rejection_count}"
            )

        rejected_execution = _single_row(
            spark.table(execution_runs_table).where(F.col("run_id") == rejected_run_id),
            message="rejected execution evidence",
        )
        if rejected_execution.status != "REJECTED":
            raise AssertionError(
                f"expected rejected execution status, found {rejected_execution.status}"
            )
        if rejected_execution.quality_status != "FAILED":
            raise AssertionError(
                "expected rejected quality status FAILED, found "
                f"{rejected_execution.quality_status}"
            )
        if int(rejected_execution.records_written or 0) != 0:
            raise AssertionError(
                "rejected execution must record zero written rows, found "
                f"{rejected_execution.records_written}"
            )

        duplicate_rule = _single_row(
            spark.table(quality_results_table).where(
                (F.col("run_id") == rejected_run_id)
                & (F.col("rule_id") == "GDP-DQ03")
            ),
            message="duplicate-key DQ evidence",
        )
        if duplicate_rule.status != "FAIL" or duplicate_rule.severity != "ERROR":
            raise AssertionError(
                "GDP-DQ03 must be a blocking failure for the duplicate-key batch"
            )

        print(
            "dq_runtime_blocking_gate_evidence "
            + json.dumps(
                {
                    "valid_run_id": valid_run_id,
                    "rejected_run_id": rejected_run_id,
                    "baseline_rows": baseline_count,
                    "rows_after_rejection": after_rejection_count,
                    "rejected_status": rejected_execution.status,
                    "rejected_quality_status": rejected_execution.quality_status,
                    "rejected_records_written": int(
                        rejected_execution.records_written or 0
                    ),
                    "blocking_rule": duplicate_rule.rule_id,
                    "blocking_rule_status": duplicate_rule.status,
                    "blocking_rule_severity": duplicate_rule.severity,
                },
                sort_keys=True,
            )
        )
    finally:
        spark.sql(f"DROP TABLE IF EXISTS {temp_table}")


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    _assert_success_evidence(
        spark,
        success_run_id=args.success_run_id,
        target_table=args.target_table,
        execution_runs_table=args.execution_runs_table,
        quality_results_table=args.quality_results_table,
    )
    _assert_blocking_gate(
        spark,
        execution_runs_table=args.execution_runs_table,
        quality_results_table=args.quality_results_table,
        temp_table=args.temp_table,
    )
    print("dq_runtime_validation_completed")


if __name__ == "__main__":
    main()
