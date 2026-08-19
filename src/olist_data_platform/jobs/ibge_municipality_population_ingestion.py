from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.ibge.bronze_municipality_population_writer import (
    BronzeMunicipalityPopulationWriter,
)
from olist_data_platform.domains.ingestion.ibge.municipality_population_ingestion_service import (
    MunicipalityPopulationIngestionService,
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
    service = MunicipalityPopulationIngestionService(
        client=SidraClient(),
        bronze_writer=BronzeMunicipalityPopulationWriter(
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
