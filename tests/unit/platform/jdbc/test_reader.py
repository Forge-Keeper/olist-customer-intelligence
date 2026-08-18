from typing import Any, cast

import pytest
from pyspark.sql import SparkSession

from olist_data_platform.platform.jdbc import JdbcConfig, JdbcReader


def _reader() -> JdbcReader:
    spark = cast(SparkSession, cast(Any, object()))
    config = JdbcConfig(
        host="localhost",
        port=5432,
        database="olist",
        user="reader",
        password="secret",
    )
    return JdbcReader(spark=spark, config=config)


def test_read_table_rejects_empty_table() -> None:
    with pytest.raises(ValueError, match="table cannot be empty"):
        _reader().read_table("")


def test_read_table_rejects_non_string_table() -> None:
    with pytest.raises(TypeError, match="table must be a string"):
        _reader().read_table(cast(Any, 123))
