from __future__ import annotations

import argparse
import json
from uuid import uuid4

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.ibge import (
    bronze_municipality_gdp_writer as gdp_writer,
)
from olist_data_platform.domains.ingestion.ibge import (
    municipality_gdp_ingestion_service as gdp_service,
)
from olist_data_platform.domains.ingestion.ibge.sidra_client import SidraClient
from olist_data_platform.platform.delta.operations import ExecutionRunRepository
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.operations import ExecutionRunTracker
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    DataQualityRunner,
)


def _parse_periods(value: str) -> tuple[str, ...]:
    periods = tuple(item.strip() for item in value.split(",") if item.strip())
    if not periods:
        raise argparse.ArgumentTypeError("periods must contain at least one year.")
    return periods


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest IBGE municipality GDP/VAB indicators into Bronze."
    )
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--execution-runs-table", required=True)
    parser.add_argument("--quality-results-table", required=True)
    parser.add_argument("--periods", default="2016,2017,2018")
    return parser


def run(args: argparse.Namespace, spark: SparkSession) -> str:
    periods = _parse_periods(args.periods)
    run_id = str(uuid4())
    tracker = ExecutionRunTracker(
        ExecutionRunRepository(spark, args.execution_runs_table)
    )
    tracker.start(
        run_id=run_id,
        dataset="ibge_municipality_gdp",
        layer="bronze",
        source_system="ibge_sidra",
        target_table=args.target_table,
        execution_scope=json.dumps(
            {"periods": list(periods)},
            sort_keys=True,
            separators=(",", ":"),
        ),
    )

    service = gdp_service.MunicipalityGdpIngestionService(
        client=SidraClient(),
        bronze_writer=gdp_writer.BronzeMunicipalityGdpWriter(
            spark=spark,
            target_table=args.target_table,
            quality_runner=DataQualityRunner(),
            quality_result_writer=QualityResultWriter(
                spark,
                args.quality_results_table,
            ),
            run_tracker=tracker,
        ),
        request_id_factory=lambda: run_id,
    )
    try:
        service.ingest(periods=periods)
        tracker.succeed(run_id)
        return run_id
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
    run_id = run(args=args, spark=spark)
    print(f"ibge_gdp_ingestion_completed run_id={run_id}")


if __name__ == "__main__":
    main()
