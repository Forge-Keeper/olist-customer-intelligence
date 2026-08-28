from __future__ import annotations

import argparse
import json
from uuid import uuid4

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.olist import (
    marketing_qualified_leads_bronze_config as mql_config,
)
from olist_data_platform.domains.bronze.olist.marketing_qualified_leads_quality import (
    OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT,
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

MQL_SOURCE_COLUMNS = (
    "mql_id",
    "first_contact_date",
    "landing_page_id",
    "origin",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load the Olist marketing qualified leads snapshot into Bronze."
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
        dataset="olist_marketing_qualified_leads",
        layer="bronze",
        source_system="olist_csv",
        target_table=args.target_table,
        execution_scope=execution_scope,
    )

    reader = OlistCsvSnapshotReader(
        spark=spark,
        source_path=args.source_path,
        required_columns=MQL_SOURCE_COLUMNS,
        dataset_name="olist_marketing_qualified_leads",
    )
    writer = BronzeWriter(
        spark=spark,
        target_table=args.target_table,
        config=mql_config.OLIST_MARKETING_QUALIFIED_LEADS_BRONZE_CONFIG,
    )
    service = OlistSnapshotIngestionService(
        dataset_name="olist_marketing_qualified_leads",
        reader=reader,
        bronze_writer=writer,
        quality_contract=OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT,
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
        "olist_marketing_qualified_leads_ingestion_completed "
        f"run_id={run_id} rows={row_count}"
    )


if __name__ == "__main__":
    main()
