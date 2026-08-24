from unittest.mock import Mock, patch

import pytest

from olist_data_platform.platform.delta import (
    ColumnContract,
    DatasetContract,
    TableLayout,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter


def _column(name: str) -> ColumnContract:
    return ColumnContract(
        name=name,
        data_type="string",
        nullable=False,
        description=f"Test column {name}.",
    )


@pytest.fixture
def config() -> DatasetContract:
    return DatasetContract(
        columns=(
            _column("id"),
            _column("payload"),
        ),
        key_columns=("id",),
        layout=TableLayout(clustering_columns=("id",)),
        write_strategy=WriteStrategy.MERGE,
    )


def test_should_reject_empty_target_table(config):
    with pytest.raises(ValueError, match="target_table"):
        BronzeWriter(Mock(), " ", config)


@patch.object(BronzeWriter, "_prepare_dataframe")
def test_should_create_clustered_table(mock_prepare, config):
    spark = Mock()
    dataframe = Mock()
    prepared = Mock()
    writer_chain = Mock()

    mock_prepare.return_value = prepared
    prepared.write.format.return_value.mode.return_value = writer_chain
    writer_chain.clusterBy.return_value = writer_chain
    spark.catalog.tableExists.return_value = False

    writer = BronzeWriter(spark, "bronze.example", config)
    writer.write(dataframe)

    writer_chain.clusterBy.assert_called_once_with("id")
    writer_chain.saveAsTable.assert_called_once_with("bronze.example")


@patch.object(BronzeWriter, "_prepare_dataframe")
def test_should_replace_explicit_scope(mock_prepare, config):
    spark = Mock()
    dataframe = Mock()
    prepared = Mock()
    mock_prepare.return_value = prepared
    spark.catalog.tableExists.return_value = True

    writer = BronzeWriter(spark, "bronze.example", config)
    writer.replace_where(dataframe, "id = 1")

    chain = prepared.write.format.return_value.mode.return_value
    chain.option.assert_called_once_with("replaceWhere", "id = 1")
    chain.option.return_value.saveAsTable.assert_called_once_with("bronze.example")


def test_should_reject_empty_reprocess_predicate(config):
    writer = BronzeWriter(Mock(), "bronze.example", config)

    with pytest.raises(ValueError, match="predicate"):
        writer.replace_where(Mock(), " ")


@patch.object(BronzeWriter, "_prepare_dataframe")
def test_should_merge_existing_table(mock_prepare, config):
    spark = Mock()
    dataframe = Mock()
    prepared = Mock()
    mock_prepare.return_value = prepared
    spark.catalog.tableExists.return_value = True

    writer = BronzeWriter(spark, "bronze.example", config)
    writer.write(dataframe)

    spark.sql.assert_called_once()
    sql = spark.sql.call_args.args[0]
    assert "MERGE INTO bronze.example" in sql
    assert "target.`id` = source.`id`" in sql
    assert "WHEN MATCHED THEN UPDATE SET *" in sql
    assert "WHEN NOT MATCHED THEN INSERT *" in sql


@patch.object(BronzeWriter, "_prepare_dataframe")
def test_should_full_replace_existing_table(mock_prepare):
    spark = Mock()
    dataframe = Mock()
    prepared = Mock()
    mock_prepare.return_value = prepared
    prepared.limit.return_value.count.return_value = 1
    spark.catalog.tableExists.return_value = True
    full_replace_config = DatasetContract(
        columns=(_column("id"),),
        key_columns=("id",),
        write_strategy=WriteStrategy.FULL_REPLACE,
    )

    writer = BronzeWriter(spark, "bronze.example", full_replace_config)
    writer.write(dataframe)

    chain = prepared.write.format.return_value.mode.return_value
    chain.option.assert_called_once_with("overwriteSchema", "true")
    chain.option.return_value.saveAsTable.assert_called_once_with("bronze.example")


@patch.object(BronzeWriter, "_prepare_dataframe")
def test_should_reject_empty_full_replace_snapshot(mock_prepare):
    spark = Mock()
    dataframe = Mock()
    prepared = Mock()
    mock_prepare.return_value = prepared
    prepared.limit.return_value.count.return_value = 0
    full_replace_config = DatasetContract(
        columns=(_column("id"),),
        key_columns=("id",),
        write_strategy=WriteStrategy.FULL_REPLACE,
    )

    writer = BronzeWriter(spark, "bronze.example", full_replace_config)

    with pytest.raises(ValueError, match="FULL_REPLACE snapshot cannot be empty"):
        writer.write(dataframe)

    spark.catalog.tableExists.assert_not_called()
