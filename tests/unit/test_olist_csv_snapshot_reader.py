from unittest.mock import Mock

import pytest
from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.ingestion.olist.csv_snapshot_reader import (
    OlistCsvSnapshotReader,
)


def _dataframe_with_columns(columns: tuple[str, ...]) -> Mock:
    dataframe = Mock()
    dataframe.schema = StructType(
        [StructField(column, StringType()) for column in columns]
    )
    dataframe.columns = list(columns)
    return dataframe


def test_should_accept_required_and_extra_columns():
    reader = OlistCsvSnapshotReader(
        Mock(),
        "/Volumes/source.csv",
        required_columns=("id", "name"),
        dataset_name="test_dataset",
    )
    dataframe = _dataframe_with_columns(("id", "name", "extra", "source_file"))

    reader._validate_minimum_schema(dataframe)


def test_should_reject_missing_required_column():
    reader = OlistCsvSnapshotReader(
        Mock(),
        "/Volumes/source.csv",
        required_columns=("id", "name"),
        dataset_name="test_dataset",
    )
    dataframe = _dataframe_with_columns(("id", "source_file"))

    with pytest.raises(ValueError, match="missing required columns"):
        reader._validate_minimum_schema(dataframe)


def test_should_reject_empty_required_columns():
    with pytest.raises(ValueError, match="required_columns cannot be empty"):
        OlistCsvSnapshotReader(
            Mock(),
            "/Volumes/source.csv",
            required_columns=(),
            dataset_name="test_dataset",
        )
