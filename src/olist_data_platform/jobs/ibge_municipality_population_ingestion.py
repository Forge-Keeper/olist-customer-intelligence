from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.ibge import (
    bronze_municipality_population_writer as population_writer,
)
from olist_data_platform.domains.ingestion.ibge import (
    municipality_population_ingestion_service as population_service,
)
from olist_data_platform.domains.ingestion.ibge.sidra_client import SidraClient


def _parse_periods(value: str) -> tuple[str, ...]:
    periods = tuple(item.strip() for item in value.split(",") if item.strip())
    if not periods:
        raise argparse.ArgumentTypeError("periods must contain at least one year.")
    return periods


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest IBGE municipality population into Bronze."
    )
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--periods", default="2016,2017,2018")
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> str:
    service = population_service.MunicipalityPopulationIngestionService(
        client=SidraClient(),
        bronze_writer=population_writer.BronzeMunicipalityPopulationWriter(
            spark=spark,
            target_table=args.target_table,
        ),
    )
    return service.ingest(periods=_parse_periods(args.periods))


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    request_id = run(args=args, spark=spark)
    print(f"ibge_population_ingestion_completed request_id={request_id}")


if __name__ == "__main__":
    main()
