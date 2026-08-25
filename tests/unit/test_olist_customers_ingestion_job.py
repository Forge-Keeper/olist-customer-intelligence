from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from olist_data_platform.jobs.olist_customers_ingestion import (
    CUSTOMERS_SOURCE_COLUMNS,
    build_parser,
    run,
)


def test_should_require_source_path():
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["--target-table", "test_catalog.bronze.olist_customers"]
        )


def test_should_parse_explicit_source_and_target():
    args = build_parser().parse_args(
        [
            "--source-path",
            "/test/olist_customers_dataset.csv",
            "--target-table",
            "test_catalog.bronze.olist_customers",
        ]
    )

    assert args.source_path == "/test/olist_customers_dataset.csv"
    assert args.target_table == "test_catalog.bronze.olist_customers"


@patch("olist_data_platform.jobs.olist_customers_ingestion.OlistSnapshotIngestionService")
@patch("olist_data_platform.jobs.olist_customers_ingestion.BronzeWriter")
@patch("olist_data_platform.jobs.olist_customers_ingestion.OlistCsvSnapshotReader")
def test_should_compose_and_run_ingestion(
    mock_reader_class: Mock,
    mock_writer_class: Mock,
    mock_service_class: Mock,
):
    spark = Mock()
    args = Namespace(
        source_path="/test/source.csv",
        target_table="test_catalog.bronze.olist_customers",
    )
    mock_service_class.return_value.ingest.return_value = 99441

    result = run(args=args, spark=spark)

    mock_reader_class.assert_called_once_with(
        spark=spark,
        source_path="/test/source.csv",
        required_columns=CUSTOMERS_SOURCE_COLUMNS,
        dataset_name="olist_customers",
    )
    mock_writer_class.assert_called_once()
    mock_service_class.assert_called_once_with(
        dataset_name="olist_customers",
        reader=mock_reader_class.return_value,
        bronze_writer=mock_writer_class.return_value,
    )
    assert result == 99441
