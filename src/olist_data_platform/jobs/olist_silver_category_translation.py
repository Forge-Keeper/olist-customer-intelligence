from __future__ import annotations

import argparse
import json
from uuid import uuid4

from pyspark.sql import SparkSession

from olist_data_platform.domains.silver.olist.category_translation import (
    process_category_translation_snapshot,
)
from olist_data_platform.platform.delta.operations import ExecutionRunRepository
from olist_data_platform.platform.operations import ExecutionRunTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transform Olist Bronze Category Translation into Silver."
    )
    parser.add_argument("--source-table", required=True)
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--execution-runs-table", required=True)
    parser.add_argument("--quality-results-table", required=True)
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> tuple[str, int]:
    run_id = str(uuid4())
    execution_scope = json.dumps(
        {"source_table": args.source_table},
        sort_keys=True,
        separators=(",", ":"),
    )
    tracker = ExecutionRunTracker(
        ExecutionRunRepository(spark, args.execution_runs_table)
    )
    tracker.start(
        run_id=run_id,
        dataset="olist_product_category_name_translation",
        layer="silver",
        source_system="olist_bronze",
        target_table=args.target_table,
        execution_scope=execution_scope,
    )
    try:
        report = process_category_translation_snapshot(
            spark=spark,
            bronze=spark.table(args.source_table),
            target_table=args.target_table,
            quality_results_table=args.quality_results_table,
            run_id=run_id,
            evaluation_scope=execution_scope,
        )
        tracker.succeed(run_id)
        return run_id, report.row_count
    except Exception as exc:
        try:
            tracker.fail(run_id, exc)
        except Exception:
            pass
        raise


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    run_id, row_count = run(args=args, spark=spark)
    print(
        "olist_silver_category_translation_completed "
        f"run_id={run_id} rows={row_count}"
    )


if __name__ == "__main__":
    main()
