from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.ibge.bronze_municipalities_writer import (
    BronzeMunicipalitiesWriter,
)
from olist_data_platform.domains.ingestion.ibge.localities_client import LocalitiesClient
from olist_data_platform.domains.ingestion.ibge.municipalities_ingestion_service import (
    MunicipalitiesIngestionService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest IBGE municipalities into Bronze.")
    parser.add_argument("--target-table", required=True)
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> str:
    service = MunicipalitiesIngestionService(
        client=LocalitiesClient(),
        bronze_writer=BronzeMunicipalitiesWriter(
            spark=spark,
            target_table=args.target_table,
        ),
    )
    return service.ingest()


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    request_id = run(args=args, spark=spark)
    print(f"ibge_municipalities_ingestion_completed request_id={request_id}")


if __name__ == "__main__":
    main()
