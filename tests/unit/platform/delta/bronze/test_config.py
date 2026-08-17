import pytest

from olist_data_platform.platform.delta.bronze import (
    BronzeDatasetConfig,
    WriteStrategy,
)


def test_should_create_valid_bronze_dataset_config():
    config = BronzeDatasetConfig(
        primary_key_columns=("dt_base", "location_id"),
        required_columns=("dt_base", "location_id", "payload"),
        clustering_columns=("dt_base",),
        write_strategy=WriteStrategy.MERGE,
    )

    assert config.primary_key_columns == ("dt_base", "location_id")
    assert config.required_columns == ("dt_base", "location_id", "payload")
    assert config.clustering_columns == ("dt_base",)
    assert config.partition_columns == ()
    assert config.write_strategy is WriteStrategy.MERGE


def test_should_default_to_merge_strategy():
    config = BronzeDatasetConfig(
        primary_key_columns=("id",),
        required_columns=("id", "payload"),
    )

    assert config.write_strategy is WriteStrategy.MERGE


def test_should_reject_empty_primary_key_columns():
    with pytest.raises(ValueError, match="primary_key_columns cannot be empty"):
        BronzeDatasetConfig(
            primary_key_columns=(),
            required_columns=("payload",),
        )


def test_should_reject_primary_key_not_in_required_columns():
    with pytest.raises(
        ValueError,
        match="primary_key_columns must be included in required_columns",
    ):
        BronzeDatasetConfig(
            primary_key_columns=("id",),
            required_columns=("payload",),
        )


def test_should_reject_duplicate_columns():
    with pytest.raises(ValueError, match="cannot contain duplicate columns"):
        BronzeDatasetConfig(
            primary_key_columns=("id", "id"),
            required_columns=("id", "payload"),
        )


def test_should_reject_empty_column_name():
    with pytest.raises(ValueError, match="cannot contain empty column names"):
        BronzeDatasetConfig(
            primary_key_columns=("id",),
            required_columns=("id", ""),
        )


def test_should_reject_column_that_is_clustered_and_partitioned():
    with pytest.raises(
        ValueError,
        match="cannot be both clustered and partitioned",
    ):
        BronzeDatasetConfig(
            primary_key_columns=("id",),
            required_columns=("id", "dt_base", "payload"),
            clustering_columns=("dt_base",),
            partition_columns=("dt_base",),
        )


def test_should_reject_invalid_write_strategy_type():
    with pytest.raises(TypeError, match="write_strategy must be a WriteStrategy"):
        BronzeDatasetConfig(
            primary_key_columns=("id",),
            required_columns=("id", "payload"),
            write_strategy="merge",  # ty: ignore[invalid-argument-type]
        )
