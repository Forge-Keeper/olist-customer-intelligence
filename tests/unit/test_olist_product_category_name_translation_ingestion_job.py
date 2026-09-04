from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.jobs import (
    olist_product_category_name_translation_ingestion as job_module,
)


def test_parser_should_require_control_plane_arguments():
    with pytest.raises(SystemExit):
        job_module.build_parser().parse_args(
            [
                "--source-path",
                "/test/category_translation.csv",
                "--target-table",
                "test_catalog.bronze.olist_product_category_name_translation",
            ]
        )


def test_parser_should_accept_explicit_runtime_arguments():
    args = job_module.build_parser().parse_args(
        [
            "--source-path",
            "/test/category_translation.csv",
            "--target-table",
            "test_catalog.bronze.olist_product_category_name_translation",
            "--execution-runs-table",
            "test_admin.operations.execution_runs",
            "--quality-results-table",
            "test_admin.quality.data_quality_results",
        ]
    )

    assert args.source_path == "/test/category_translation.csv"
    assert args.target_table == (
        "test_catalog.bronze.olist_product_category_name_translation"
    )


@patch.object(job_module, "QualityResultWriter")
@patch.object(job_module, "DataQualityRunner")
@patch.object(job_module, "OlistSnapshotIngestionService")
@patch.object(job_module, "BronzeWriter")
@patch.object(job_module, "OlistCsvSnapshotReader")
@patch.object(job_module, "ExecutionRunTracker")
@patch.object(job_module, "ExecutionRunRepository")
@patch.object(job_module, "uuid4")
def test_run_should_compose_first_class_category_translation_ingestion(
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
        source_path="/test/category_translation.csv",
        target_table="test_catalog.bronze.olist_product_category_name_translation",
        execution_runs_table="test_admin.operations.execution_runs",
        quality_results_table="test_admin.quality.data_quality_results",
    )
    uuid_factory.return_value = "run-1"
    service_class.return_value.ingest.return_value = 71

    run_id, row_count = job_module.run(args=args, spark=spark)

    assert run_id == "run-1"
    assert row_count == 71
    reader_class.assert_called_once_with(
        spark=spark,
        source_path=args.source_path,
        required_columns=job_module.CATEGORY_TRANSLATION_SOURCE_COLUMNS,
        dataset_name="olist_product_category_name_translation",
    )
    writer_class.assert_called_once()
    quality_runner_class.assert_called_once_with()
    quality_result_writer_class.assert_called_once_with(
        spark,
        args.quality_results_table,
    )
    service_class.return_value.ingest.assert_called_once()
    tracker_class.return_value.succeed.assert_called_once_with("run-1")
