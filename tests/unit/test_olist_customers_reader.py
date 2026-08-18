from unittest.mock import Mock

import pytest
from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.ingestion.olist.customers_reader import (
    OlistCustomersReader,
)


def _dataframe_with_schema(fields: list[StructField]) -> Mock:
    dataframe = Mock()
    dataframe.schema = StructType(fields)
    dataframe.columns = [field.name for field in fields]
    return dataframe


def test_should_accept_expected_minimum_schema_and_extra_columns():
    reader = OlistCustomersReader(Mock(), "/Volumes/source.csv")
    dataframe = _dataframe_with_schema(
        [
            StructField("customer_id", StringType()),
            StructField("customer_unique_id", StringType()),
            StructField("customer_zip_code_prefix", StringType()),
            StructField("customer_city", StringType()),
            StructField("customer_state", StringType()),
            StructField("extra_column", StringType()),
            StructField("source_file", StringType()),
        ]
    )

    reader._validate_minimum_schema(dataframe)


def test_should_reject_missing_required_source_column():
    reader = OlistCustomersReader(Mock(), "/Volumes/source.csv")
    dataframe = _dataframe_with_schema(
        [
            StructField("customer_id", StringType()),
            StructField("customer_unique_id", StringType()),
            StructField("customer_zip_code_prefix", StringType()),
            StructField("customer_city", StringType()),
        ]
    )

    with pytest.raises(ValueError, match="missing required columns"):
        reader._validate_minimum_schema(dataframe)
