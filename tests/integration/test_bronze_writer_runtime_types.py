from datetime import date
from decimal import Decimal

import pytest
from pyspark.sql.types import (
    DateType,
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter


def _contract() -> DatasetContract:
    return DatasetContract(
        columns=(
            ColumnContract("id", "long", False, "Logical identifier."),
            ColumnContract("amount", "decimal(18,2)", False, "Monetary amount."),
            ColumnContract("dt_base", "date", False, "Logical reference date."),
            ColumnContract("payload", "string", True, "Source payload."),
        ),
        managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
        key_columns=("id",),
    )


def test_bronze_writer_accepts_matching_runtime_types_and_adds_managed_column(spark):
    schema = StructType(
        [
            StructField("id", LongType(), False),
            StructField("amount", DecimalType(18, 2), False),
            StructField("dt_base", DateType(), False),
            StructField("payload", StringType(), True),
        ]
    )
    dataframe = spark.createDataFrame(
        [(1, Decimal("12.34"), date(2026, 9, 17), "source")],
        schema=schema,
    )
    writer = BronzeWriter(spark, "dev.bronze.runtime_types", _contract())

    prepared = writer._prepare_checked_dataframe(dataframe)

    assert isinstance(prepared.schema["id"].dataType, LongType)
    assert prepared.schema["amount"].dataType == DecimalType(18, 2)
    assert isinstance(prepared.schema["dt_base"].dataType, DateType)
    assert isinstance(prepared.schema["payload"].dataType, StringType)
    assert isinstance(prepared.schema["ingestion_timestamp"].dataType, TimestampType)


def test_bronze_writer_rejects_runtime_type_mismatches_before_managed_columns(spark):
    schema = StructType(
        [
            StructField("id", StringType(), False),
            StructField("amount", DecimalType(18, 3), False),
            StructField("dt_base", StringType(), False),
            StructField("payload", StringType(), True),
        ]
    )
    dataframe = spark.createDataFrame(
        [("1", Decimal("12.340"), "2026-09-17", "source")],
        schema=schema,
    )
    writer = BronzeWriter(spark, "dev.bronze.runtime_types", _contract())

    with pytest.raises(ValueError) as exc_info:
        writer._prepare_checked_dataframe(dataframe)

    message = str(exc_info.value)
    assert "DataFrame column types are incompatible with DatasetContract" in message
    assert "id:string->bigint" in message
    assert "amount:decimal(18,3)->decimal(18,2)" in message
    assert "dt_base:string->date" in message
    assert "ingestion_timestamp" not in message
