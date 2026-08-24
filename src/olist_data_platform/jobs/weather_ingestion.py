from __future__ import annotations

import argparse
from datetime import date

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.weather.bronze_weather_writer import (
    BronzeWeatherWriter,
)
from olist_data_platform.domains.ingestion.weather.open_meteo_client import (
    OpenMeteoClient,
)
from olist_data_platform.domains.ingestion.weather.weather_ingestion_service import (
    WeatherIngestionService,
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid ISO date: {value!r}. Expected YYYY-MM-DD."
        ) from exc


def _parse_daily_variables(value: str | None) -> list[str] | None:
    if value is None:
        return None

    variables = [item.strip() for item in value.split(",") if item.strip()]
    if not variables:
        raise argparse.ArgumentTypeError(
            "daily-variables must contain at least one variable."
        )
    return variables


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest or explicitly reprocess Open-Meteo data into Bronze."
    )
    parser.add_argument(
        "--operation",
        choices=("ingest", "reprocess"),
        default="ingest",
    )
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--latitude", required=True, type=float)
    parser.add_argument("--longitude", required=True, type=float)
    parser.add_argument("--start-date", required=True, type=_parse_date)
    parser.add_argument("--end-date", required=True, type=_parse_date)
    parser.add_argument("--timezone", default="auto")
    parser.add_argument(
        "--daily-variables",
        help="Comma-separated Open-Meteo daily variables.",
    )
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> str:
    client = OpenMeteoClient()
    writer = BronzeWeatherWriter(
        spark=spark,
        target_table=args.target_table,
    )
    service = WeatherIngestionService(
        client=client,
        bronze_writer=writer,
    )

    kwargs = {
        "latitude": args.latitude,
        "longitude": args.longitude,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "daily_variables": _parse_daily_variables(args.daily_variables),
        "timezone": args.timezone,
    }

    if args.operation == "reprocess":
        return service.reprocess(**kwargs)

    return service.ingest(**kwargs)


def main() -> None:
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    request_id = run(args=args, spark=spark)
    print(f"weather_{args.operation}_completed request_id={request_id}")


if __name__ == "__main__":
    main()
