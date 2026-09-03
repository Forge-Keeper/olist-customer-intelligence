from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.jobs.olist_sellers_ingestion import (
    SELLERS_SOURCE_COLUMNS,
    build_parser,
    run,
)


def test_parser_should_require_control_plane_arguments():
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "--source-path",
                "/test/sellers.csv",
                "--target-table",
                "test_catalog.bronze.olist_sellers",
            ]
        )


def test_parser_should_accept_explicit_runtime_arguments():
    args = build_parser().parse_args(
        [
            "--source-path",
            "/test/sellers.csv",
            "--target-table",
            "test_catalog.bronze.olist_sellers",
            "--execution-runs-table",
            "test_admin.operations.execution_runs",
            "--quality-results-table",
            "test_admin.quality.data_quality_results",
        ]
    )

    assert args.source_path == "/test/sellers.csv"
    assert args.target_table == "test_catalog.bronze.olist_sellers"


@patch("olist_data_platform.jobs.olist_sellers_ingestion.QualityResultWriter")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.DataQualityRunner")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.OlistSnapshotIngestionService")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.BronzeWriter")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.OlistCsvSnapshotReader")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.ExecutionRunTracker")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.ExecutionRunRepository")
@patch("olist_data_platform.jobs.olist_sellers_ingestion.uuid4")
def test_run_should_compose_first_class_sellers_ingestion(
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
        source_path="/test/sellers.csv",
        target_table="test_catalog.bronze.olist_sellers",
        execution_runs_table="test_admin.operations.execution_runs",
        quality_results_table="test_admin.quality.data_quality_results",
    )
    uuid_factory.return_value = "run-1"
    service_class.return_value.ingest.return_value = 3095

    run_id, row_count = run(args=args, spark=spark)

    assert run_id == "run-1"
    assert row_count == 3095
    reader_class.assert_called_once_with(
        spark=spark,
        source_path=args.source_path,
        required_columns=SELLERS_SOURCE_COLUMNS,
        dataset_name="olist_sellers",
    )
    writer_class.assert_called_once()
    quality_runner_class.assert_called_once_with()
    quality_result_writer_class.assert_called_once_with(
        spark,
        args.quality_results_table,
    )
    service_class.return_value.ingest.assert_called_once()
    tracker_class.return_value.succeed.assert_called_once_with("run-1")
