from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.olist.customers_bronze_config import (
    OLIST_CUSTOMERS_BRONZE_CONFIG,
)
from olist_data_platform.domains.ingestion.olist.csv_snapshot_reader import (
    OlistCsvSnapshotReader,
)
from olist_data_platform.domains.ingestion.olist.snapshot_ingestion_service import (
    OlistSnapshotIngestionService,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter

DEFAULT_SOURCE_PATH = (
    "/Volumes/prd/bronze/raw_storage/raw/olist/"
    "e_commerce/olist_customers_dataset.csv"
)
CUSTOMERS_SOURCE_COLUMNS = (
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load the Olist customers CSV snapshot into Bronze."
    )
    parser.add_argument("--source-path", default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--target-table", required=True)
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> int:
    reader = OlistCsvSnapshotReader(
        spark=spark,
        source_path=args.source_path,
        required_columns=CUSTOMERS_SOURCE_COLUMNS,
        dataset_name="olist_customers",
    )
    writer = BronzeWriter(
        spark=spark,
        target_table=args.target_table,
        config=OLIST_CUSTOMERS_BRONZE_CONFIG,
    )
    service = OlistSnapshotIngestionService(
        dataset_name="olist_customers",
        reader=reader,
        bronze_writer=writer,
    )
    return service.ingest()


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    row_count = run(args=args, spark=spark)
    print(f"olist_customers_ingestion_completed rows={row_count}")


if __name__ == "__main__":
    main()
