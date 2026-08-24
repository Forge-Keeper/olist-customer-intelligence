import pytest
from pyspark.sql.types import StringType, TimestampType

from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.delta.contract import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    SchemaEvolutionPolicy,
    TableLayout,
    TableMetadata,
)


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


def test_should_build_column_contract_and_struct_field():
    column = _column("id", tags={"classification": "identifier"})

    field = column.to_struct_field()

    assert field.name == "id"
    assert isinstance(field.dataType, StringType)
    assert field.nullable is False
    assert field.metadata["comment"] == "Description for id."
    assert column.tags["classification"] == "identifier"


def test_should_reject_invalid_ddl_type():
    with pytest.raises(ValueError, match="Invalid Spark DDL type"):
        _column("id", "definitely_not_a_spark_type")


def test_should_reject_empty_column_description():
    with pytest.raises(ValueError, match="column description cannot be empty"):
        ColumnContract(
            name="id",
            data_type="string",
            nullable=False,
            description="",
        )


def test_should_reject_invalid_tags():
    with pytest.raises(ValueError, match="tag values cannot be empty"):
        _column("id", tags={"classification": ""})


def test_should_build_dataset_contract_with_managed_column():
    contract = DatasetContract(
        columns=(
            _column("id"),
            _column("dt_base", "date"),
            _column("payload", "variant", nullable=True),
        ),
        managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
        key_columns=("id",),
        layout=TableLayout(clustering_columns=("dt_base",)),
        metadata=TableMetadata(
            description="Example Bronze dataset.",
            tags={"layer": "bronze", "domain": "example"},
        ),
    )

    assert contract.primary_key_columns == ("id",)
    assert contract.required_columns == (
        "id",
        "dt_base",
        "payload",
        "ingestion_timestamp",
    )
    assert contract.clustering_columns == ("dt_base",)
    assert contract.partition_columns == ()
    assert contract.write_strategy is WriteStrategy.MERGE
    assert contract.metadata.tags["layer"] == "bronze"

    schema = contract.to_struct_type()
    ingestion_field = schema["ingestion_timestamp"]
    assert isinstance(ingestion_field.dataType, TimestampType)
    assert ingestion_field.nullable is False


def test_should_reject_duplicate_dataset_and_managed_columns():
    with pytest.raises(ValueError, match="cannot contain duplicate column names"):
        DatasetContract(
            columns=(BRONZE_INGESTION_TIMESTAMP,),
            managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
            key_columns=("ingestion_timestamp",),
        )


def test_should_reject_missing_key_column():
    with pytest.raises(ValueError, match="key_columns must be included"):
        DatasetContract(
            columns=(_column("payload"),),
            key_columns=("id",),
        )


def test_should_reject_missing_layout_column():
    with pytest.raises(ValueError, match="layout columns must be included"):
        DatasetContract(
            columns=(_column("id"),),
            key_columns=("id",),
            layout=TableLayout(clustering_columns=("dt_base",)),
        )


def test_should_reject_layout_column_that_is_both_clustered_and_partitioned():
    with pytest.raises(ValueError, match="cannot be both clustered and partitioned"):
        TableLayout(
            clustering_columns=("dt_base",),
            partition_columns=("dt_base",),
        )


def test_schema_evolution_should_be_fail_fast_by_default():
    policy = SchemaEvolutionPolicy()

    assert policy.enabled is False
    assert policy.can_add_nullable_columns is False


def test_schema_evolution_should_allow_nullable_addition_only_when_enabled():
    policy = SchemaEvolutionPolicy(enabled=True)

    assert policy.can_add_nullable_columns is True


def test_should_reject_invalid_write_strategy_type():
    with pytest.raises(TypeError, match="write_strategy must be a WriteStrategy"):
        DatasetContract(
            columns=(_column("id"),),
            key_columns=("id",),
            write_strategy="merge",  # ty: ignore[invalid-argument-type]
        )
