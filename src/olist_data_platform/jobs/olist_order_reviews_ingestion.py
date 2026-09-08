from __future__ import annotations

import argparse
import json
from uuid import uuid4

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.olist.order_reviews_bronze_config import (
    OLIST_ORDER_REVIEWS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.order_reviews_quality import (
    OLIST_ORDER_REVIEWS_QUALITY_CONTRACT,
)
from olist_data_platform.domains.ingestion.olist.csv_snapshot_reader import (
    OlistCsvSnapshotReader,
)
from olist_data_platform.domains.ingestion.olist.snapshot_ingestion_service import (
    OlistSnapshotIngestionService,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.delta.operations import ExecutionRunRepository
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.operations import ExecutionRunTracker
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    DataQualityRunner,
)

ORDER_REVIEWS_SOURCE_COLUMNS = (
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load the Olist order reviews CSV snapshot into Bronze."
    )
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--execution-runs-table", required=True)
    parser.add_argument("--quality-results-table", required=True)
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> tuple[str, int]:
    run_id = str(uuid4())
    execution_scope = json.dumps(
        {"source_path": args.source_path},
        sort_keys=True,
        separators=(",", ":"),
    )
    tracker = ExecutionRunTracker(
        ExecutionRunRepository(spark, args.execution_runs_table)
    )
    tracker.start(
        run_id=run_id,
        dataset="olist_order_reviews",
        layer="bronze",
        source_system="olist_csv",
        target_table=args.target_table,
        execution_scope=execution_scope,
    )

    reader = OlistCsvSnapshotReader(
        spark=spark,
        source_path=args.source_path,
        required_columns=ORDER_REVIEWS_SOURCE_COLUMNS,
        dataset_name="olist_order_reviews",
        multiline=True,
        escape='"',
    )
    writer = BronzeWriter(
        spark=spark,
        target_table=args.target_table,
        config=OLIST_ORDER_REVIEWS_BRONZE_CONFIG,
    )
    service = OlistSnapshotIngestionService(
        dataset_name="olist_order_reviews",
        reader=reader,
        bronze_writer=writer,
        quality_contract=OLIST_ORDER_REVIEWS_QUALITY_CONTRACT,
        quality_runner=DataQualityRunner(),
        quality_result_writer=QualityResultWriter(
            spark,
            args.quality_results_table,
        ),
        run_tracker=tracker,
    )

    try:
        row_count = service.ingest(
            run_id=run_id,
            evaluation_scope=execution_scope,
        )
        tracker.succeed(run_id)
        return run_id, row_count
    except DataQualityRejectedError:
        raise
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
    print(f"olist_order_reviews_ingestion_completed run_id={run_id} rows={row_count}")


if __name__ == "__main__":
    main()
