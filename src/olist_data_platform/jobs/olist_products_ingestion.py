from __future__ import annotations

import argparse
import json
from uuid import uuid4

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.olist.products_bronze_config import (
    OLIST_PRODUCTS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.products_quality import (
    OLIST_PRODUCTS_QUALITY_CONTRACT,
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

PRODUCTS_SOURCE_COLUMNS = (
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
)


def build_parser() -> argparse.ArgumentParser:
    """Build explicit runtime arguments for the Products Bronze job."""
    parser = argparse.ArgumentParser(
        description="Load the Olist products CSV snapshot into Bronze."
    )
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--execution-runs-table", required=True)
    parser.add_argument("--quality-results-table", required=True)
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> tuple[str, int]:
    """Execute one Products snapshot ingestion with Control Plane evidence."""
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
        dataset="olist_products",
        layer="bronze",
        source_system="olist_csv",
        target_table=args.target_table,
        execution_scope=execution_scope,
    )

    reader = OlistCsvSnapshotReader(
        spark=spark,
        source_path=args.source_path,
        required_columns=PRODUCTS_SOURCE_COLUMNS,
        dataset_name="olist_products",
    )
    writer = BronzeWriter(
        spark=spark,
        target_table=args.target_table,
        config=OLIST_PRODUCTS_BRONZE_CONFIG,
    )
    service = OlistSnapshotIngestionService(
        dataset_name="olist_products",
        reader=reader,
        bronze_writer=writer,
        quality_contract=OLIST_PRODUCTS_QUALITY_CONTRACT,
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
    """Run the Products Bronze job in the active Spark session."""
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    run_id, row_count = run(args=args, spark=spark)
    print(f"olist_products_ingestion_completed run_id={run_id} rows={row_count}")


if __name__ == "__main__":
    main()
