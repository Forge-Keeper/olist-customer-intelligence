from argparse import Namespace
from unittest.mock import Mock, patch

from olist_data_platform.jobs.olist_closed_deals_ingestion import (
    CLOSED_DEALS_SOURCE_COLUMNS,
    DEFAULT_SOURCE_PATH,
    build_parser,
    run,
)


def test_parser_should_use_default_source_path():
    args = build_parser().parse_args(
        ["--target-table", "test_catalog.bronze.closed_deals"]
    )

    assert args.source_path == DEFAULT_SOURCE_PATH
    assert args.target_table == "test_catalog.bronze.closed_deals"


@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.OlistSnapshotIngestionService")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.BronzeWriter")
@patch("olist_data_platform.jobs.olist_closed_deals_ingestion.OlistCsvSnapshotReader")
def test_run_should_compose_closed_deals_ingestion(
    reader_class: Mock,
    writer_class: Mock,
    service_class: Mock,
):
    spark = Mock()
    args = Namespace(
        source_path="/Volumes/closed_deals.csv",
        target_table="test_catalog.bronze.closed_deals",
    )
    service_class.return_value.ingest.return_value = 842

    result = run(args=args, spark=spark)

    assert result == 842
    reader_class.assert_called_once_with(
        spark=spark,
        source_path=args.source_path,
        required_columns=CLOSED_DEALS_SOURCE_COLUMNS,
        dataset_name="olist_closed_deals",
    )
    writer_class.assert_called_once()
    service_class.return_value.ingest.assert_called_once_with()
