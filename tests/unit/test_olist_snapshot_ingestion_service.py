from unittest.mock import Mock

from olist_data_platform.domains.ingestion.olist.snapshot_ingestion_service import (
    OlistSnapshotIngestionService,
)


def test_should_read_count_write_and_return_row_count():
    dataframe = Mock()
    dataframe.count.return_value = 42
    dataframe.columns = ["id", "source_file"]

    reader = Mock()
    reader.source_path = "/Volumes/source.csv"
    reader.read.return_value = dataframe

    writer = Mock()
    writer.target_table = "test_catalog.bronze.test"

    service = OlistSnapshotIngestionService(
        dataset_name="olist_test",
        reader=reader,
        bronze_writer=writer,
    )

    result = service.ingest()

    assert result == 42
    reader.read.assert_called_once_with()
    writer.write.assert_called_once_with(dataframe)
