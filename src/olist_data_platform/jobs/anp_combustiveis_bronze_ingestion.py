from __future__ import annotations

import argparse
from datetime import date

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.anp import ANP_COMBUSTIVEIS_BRONZE_CONFIG
from olist_data_platform.domains.ingestion.anp import (
    AnpCombustiveisPostgresReader,
    AnpCombustiveisReadRequest,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.jdbc import JdbcConfig, JdbcReader


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected YYYY-MM-DD."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load ANP fuel prices from PostgreSQL into Databricks Bronze."
    )
    parser.add_argument("--start-date", type=_parse_date, required=True)
    parser.add_argument("--end-date", type=_parse_date, required=True)
    parser.add_argument("--target-table", required=True)
    return parser


def _build_replace_where_predicate(start_date: date, end_date: date) -> str:
    return (
        f"dt_base >= DATE '{start_date.isoformat()}' "
        f"AND dt_base <= DATE '{end_date.isoformat()}'"
    )


def run(
    args: argparse.Namespace,
    spark: SparkSession,
    jdbc_config: JdbcConfig | None = None,
) -> int:
    request = AnpCombustiveisReadRequest(
        start_date=args.start_date,
        end_date=args.end_date,
    )
    jdbc_reader = JdbcReader(
        spark=spark,
        config=jdbc_config or JdbcConfig.from_env(),
    )
    reader = AnpCombustiveisPostgresReader(jdbc_reader)
    dataframe = reader.read(request)

    row_count = dataframe.count()
    if row_count == 0:
        raise ValueError(
            "ANP PostgreSQL source returned no rows for the requested interval."
        )

    writer = BronzeWriter(
        spark=spark,
        target_table=args.target_table,
        config=ANP_COMBUSTIVEIS_BRONZE_CONFIG,
    )
    writer.replace_where(
        dataframe=dataframe,
        predicate=_build_replace_where_predicate(
            start_date=request.start_date,
            end_date=request.end_date,
        ),
    )
    return row_count


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    row_count = run(args=args, spark=spark)
    print(
        "anp_combustiveis_bronze_ingestion_completed "
        f"rows={row_count} "
        f"target_table={args.target_table} "
        f"start_date={args.start_date.isoformat()} "
        f"end_date={args.end_date.isoformat()}"
    )


if __name__ == "__main__":
    main()
