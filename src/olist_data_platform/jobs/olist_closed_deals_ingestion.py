from __future__ import annotations

import argparse
import json
from uuid import uuid4

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.olist.closed_deals_bronze_config import (
    OLIST_CLOSED_DEALS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.closed_deals_quality import (
    OLIST_CLOSED_DEALS_QUALITY_CONTRACT,
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

CLOSED_DEALS_SOURCE_COLUMNS = (
    "mql_id",
    "seller_id",
    "sdr_id",
    "sr_id",
    "won_date",
    "business_segment",
    "lead_type",
    "lead_behaviour_profile",
    "has_company",
    "has_gtin",
    "average_stock",
    "business_type",
    "declared_product_catalog_size",
    "declared_monthly_revenue",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load the Olist closed deals CSV snapshot into Bronze."
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
        dataset="olist_closed_deals",
        layer="bronze",
        source_system="olist_csv",
        target_table=args.target_table,
        execution_scope=execution_scope,
    )

    reader = OlistCsvSnapshotReader(
        spark=spark,
        source_path=args.source_path,
        required_columns=CLOSED_DEALS_SOURCE_COLUMNS,
        dataset_name="olist_closed_deals",
    )
    writer = BronzeWriter(
        spark=spark,
        target_table=args.target_table,
        config=OLIST_CLOSED_DEALS_BRONZE_CONFIG,
    )
    service = OlistSnapshotIngestionService(
        dataset_name="olist_closed_deals",
        reader=reader,
        bronze_writer=writer,
        quality_contract=OLIST_CLOSED_DEALS_QUALITY_CONTRACT,
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
    print(
        "olist_closed_deals_ingestion_completed "
        f"run_id={run_id} rows={row_count}"
    )


if __name__ == "__main__":
    main()
