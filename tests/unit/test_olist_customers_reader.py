from unittest.mock import Mock

import pytest
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from olist_data_platform.domains.ingestion.olist.customers_reader import (
    OlistCustomersReader,
)


def _dataframe_with_schema(fields: list[StructField]) -> Mock:
    dataframe = Mock()
    dataframe.schema = StructType(fields)
    return dataframe


def test_should_accept_expected_minimum_schema():
    reader = OlistCustomersReader(Mock(), "/Volumes/source.csv")
    dataframe = _dataframe_with_schema(
        [
            StructField("customer_id", StringType()),
            StructField("customer_unique_id", StringType()),
            StructField("customer_zip_code_prefix", IntegerType()),
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
            StructField("customer_zip_code_prefix", IntegerType()),
            StructField("customer_city", StringType()),
        ]
    )

    with pytest.raises(ValueError, match="missing required columns"):
        reader._validate_minimum_schema(dataframe)


def test_should_reject_incompatible_required_source_type():
    reader = OlistCustomersReader(Mock(), "/Volumes/source.csv")
    dataframe = _dataframe_with_schema(
        [
            StructField("customer_id", StringType()),
            StructField("customer_unique_id", StringType()),
            StructField("customer_zip_code_prefix", StringType()),
            StructField("customer_city", StringType()),
            StructField("customer_state", StringType()),
        ]
    )

    with pytest.raises(ValueError, match="incompatible required-column types"):
        reader._validate_minimum_schema(dataframe)
