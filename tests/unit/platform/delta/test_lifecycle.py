from unittest.mock import Mock

import pytest
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from olist_data_platform.platform.delta import (
    ColumnContract,
    DatasetContract,
    SchemaEvolutionPolicy,
    TableMetadata,
)
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle


def _column(
    name: str,
    data_type: str = "string",
    *,
    nullable: bool = False,
    tags: dict[str, str] | None = None,
) -> ColumnContract:
    return ColumnContract(
        name=name,
        data_type=data_type,
        nullable=nullable,
        description=f"Description for {name}.",
        tags=tags or {},
    )


def _contract(*, evolution: bool = False) -> DatasetContract:
    return DatasetContract(
        columns=(
            _column("id"),
            _column(
                "new_value",
                nullable=True,
                tags={"classification": "public"},
            ),
        ),
        key_columns=("id",),
        metadata=TableMetadata(
            description="Example managed table.",
            tags={"layer": "bronze"},
        ),
        schema_evolution=SchemaEvolutionPolicy(enabled=evolution),
    )


def test_should_classify_schema_drift():
    lifecycle = DeltaTableLifecycle(Mock(), "dev.bronze.example", _contract())
    actual = StructType(
        [
            StructField("id", IntegerType(), False),
            StructField("unexpected", StringType(), True),
        ]
    )

    diff = lifecycle.diff_schema(actual)

    assert diff.missing_columns == ("new_value",)
    assert diff.unexpected_columns == ("unexpected",)
    assert len(diff.type_mismatches) == 1
    assert diff.type_mismatches[0].column == "id"
    assert diff.is_compatible is False


def test_should_fail_fast_when_evolution_is_disabled():
    spark = Mock()
    spark.catalog.tableExists.return_value = True
    spark.table.return_value.schema = StructType(
        [StructField("id", StringType(), False)]
    )
    lifecycle = DeltaTableLifecycle(spark, "dev.bronze.example", _contract())

    with pytest.raises(ValueError, match="missing_columns=\['new_value'\]"):
        lifecycle.ensure()

    assert not any("ADD COLUMNS" in str(call) for call in spark.sql.call_args_list)


def test_should_add_missing_nullable_column_when_evolution_is_enabled():
    spark = Mock()
    spark.catalog.tableExists.return_value = True
    spark.table.return_value.schema = StructType(
        [StructField("id", StringType(), False)]
    )
    lifecycle = DeltaTableLifecycle(
        spark,
        "dev.bronze.example",
        _contract(evolution=True),
    )

    evolved_schema = StructType(
        [
            StructField("id", StringType(), False),
            StructField("new_value", StringType(), True),
        ]
    )
    lifecycle.inspect_schema = Mock(
        side_effect=[
            lifecycle.diff_schema(spark.table.return_value.schema),
            lifecycle.diff_schema(evolved_schema),
        ]
    )

    lifecycle.ensure()

    sql_calls = [call.args[0] for call in spark.sql.call_args_list]
    assert any("ADD COLUMNS (`new_value` string" in sql for sql in sql_calls)
    assert any("COMMENT ON TABLE dev.bronze.example" in sql for sql in sql_calls)
    assert any("SET TAGS ('layer' = 'bronze')" in sql for sql in sql_calls)
    assert any("SET TAGS ('classification' = 'public')" in sql for sql in sql_calls)


def test_should_create_empty_cluster_or_partition_independent_table():
    spark = Mock()
    spark.catalog.tableExists.return_value = False
    dataframe = Mock()
    writer = Mock()
    spark.createDataFrame.return_value = dataframe
    dataframe.write.format.return_value.mode.return_value = writer

    lifecycle = DeltaTableLifecycle(spark, "dev.bronze.example", _contract())
    lifecycle.ensure()

    spark.createDataFrame.assert_called_once()
    writer.saveAsTable.assert_called_once_with("dev.bronze.example")


def test_should_reconcile_table_and_column_metadata():
    spark = Mock()
    lifecycle = DeltaTableLifecycle(spark, "dev.bronze.example", _contract())

    lifecycle.reconcile_metadata()

    sql_calls = [call.args[0] for call in spark.sql.call_args_list]
    assert any("COMMENT ON TABLE" in sql for sql in sql_calls)
    assert any("ALTER COLUMN `id` COMMENT" in sql for sql in sql_calls)
    assert any("SET TAGS ('layer' = 'bronze')" in sql for sql in sql_calls)
    assert any("ALTER COLUMN `new_value` SET TAGS" in sql for sql in sql_calls)
