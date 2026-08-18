from argparse import Namespace
from unittest.mock import Mock, patch

from olist_data_platform.jobs.olist_customers_ingestion import (
    DEFAULT_SOURCE_PATH,
    build_parser,
    run,
)


def test_should_default_source_path():
    args = build_parser().parse_args(
        ["--target-table", "prd.bronze.olist_customers"]
    )

    assert args.source_path == DEFAULT_SOURCE_PATH
    assert args.target_table == "prd.bronze.olist_customers"


@patch("olist_data_platform.jobs.olist_customers_ingestion.BronzeWriter")
@patch("olist_data_platform.jobs.olist_customers_ingestion.OlistCustomersReader")
@patch(
    "olist_data_platform.jobs.olist_customers_ingestion."
    "OlistCustomersIngestionService"
)
def test_should_compose_and_run_ingestion(
    mock_service_class,
    mock_reader_class,
    mock_writer_class,
):
    spark = Mock()
    args = Namespace(
        source_path="/Volumes/source.csv",
        target_table="prd.bronze.olist_customers",
    )
    service = mock_service_class.return_value
    service.ingest.return_value = 99441

    result = run(args=args, spark=spark)

    mock_reader_class.assert_called_once_with(
        spark=spark,
        source_path="/Volumes/source.csv",
    )
    mock_writer_class.assert_called_once()
    mock_service_class.assert_called_once_with(
        reader=mock_reader_class.return_value,
        bronze_writer=mock_writer_class.return_value,
    )
    assert result == 99441
