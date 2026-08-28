from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.jobs.olist_closed_deals_ingestion import (
    CLOSED_DEALS_SOURCE_COLUMNS,
    build_parser,
    run,
)


def test_parser_should_require_control_plane_arguments():
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "--source-path",
                "/test/closed_deals.csv",
                "--target-table",
                "test_catalog.bronze.closed_deals",
            ]
        )


def test_parser_should_accept_explicit_runtime_arguments():
    args = build_parser().parse_args(
        [
            "--source-path",
            "/test/closed_deals.csv",
            "--target-table",
            "test_catalog.bronze.closed_deals",
            "--execution-runs-table",
            "test_admin.operations.execution_runs",
            "--quality-results-table",
            "test_admin.quality.data_quality_results",
        ]
    )

    assert args.source_path == "/test/closed_deals.csv"
    assert args.target_table == "test_catalog.bronze.closed_deals"


@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.QualityResultWriter")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.DataQualityRunner")
@patch(
    "olist_data_platform.jobs.olist_closed_deals_ingestion."
    "OlistSnapshotIngestionService"
)
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.BronzeWriter")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.OlistCsvSnapshotReader")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.ExecutionRunTracker")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.ExecutionRunRepository")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.uuid4")
def test_run_should_compose_first_class_closed_deals_ingestion(
    uuid_factory: Mock,
    repository_class: Mock,
    tracker_class: Mock,
    reader_class: Mock,
    writer_class: Mock,
    service_class: Mock,
    quality_runner_class: Mock,
    quality_result_writer_class: Mock,
):
    spark = Mock()
    args = Namespace(
        source_path="/test/closed_deals.csv",
        target_table="test_catalog.bronze.olist_closed_deals",
        execution_runs_table="test_admin.operations.execution_runs",
        quality_results_table="test_admin.quality.data_quality_results",
    )
    uuid_factory.return_value = "run-1"
    service_class.return_value.ingest.return_value = 842

    run_id, row_count = run(args=args, spark=spark)

    assert run_id == "run-1"
    assert row_count == 842
    reader_class.assert_called_once_with(
        spark=spark,
        source_path=args.source_path,
        required_columns=CLOSED_DEALS_SOURCE_COLUMNS,
        dataset_name="olist_closed_deals",
    )
    writer_class.assert_called_once()
    quality_runner_class.assert_called_once_with()
    quality_result_writer_class.assert_called_once_with(
        spark,
        args.quality_results_table,
    )
    service_class.return_value.ingest.assert_called_once()
    tracker_class.return_value.succeed.assert_called_once_with("run-1")
