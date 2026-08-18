from unittest.mock import Mock

from olist_data_platform.domains.ingestion.olist.customers_ingestion_service import (
    OlistCustomersIngestionService,
)


def test_should_read_snapshot_write_bronze_and_return_row_count():
    reader = Mock()
    bronze_writer = Mock()
    dataframe = Mock()
    dataframe.count.return_value = 3
    dataframe.columns = ["customer_id", "source_file"]
    reader.read.return_value = dataframe
    reader.source_path = "/Volumes/source.csv"
    bronze_writer.target_table = "prd.bronze.olist_customers"

    service = OlistCustomersIngestionService(reader, bronze_writer)

    row_count = service.ingest()

    reader.read.assert_called_once_with()
    bronze_writer.write.assert_called_once_with(dataframe)
    assert row_count == 3
