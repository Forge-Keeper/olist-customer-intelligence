from pyspark.sql.types import DateType, StringType, TimestampType

from olist_data_platform.domains.bronze.ibge.municipality_gdp_bronze_config import (
    IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_should_define_gdp_bronze_contract():
    contract = IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG

    assert contract.key_columns == (
        "municipality_code",
        "reference_year",
        "variable_code",
    )
    assert contract.write_strategy is WriteStrategy.MERGE
    assert contract.layout.clustering_columns == ("dt_base",)
    assert contract.layout.partition_columns == ()
    assert contract.schema_evolution.enabled is False
    assert contract.metadata.tags == {
        "layer": "bronze",
        "domain": "ibge",
        "source_system": "ibge_sidra",
    }


def test_should_expose_authoritative_gdp_persisted_schema():
    contract = IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG
    schema = contract.to_struct_type()

    assert isinstance(schema["municipality_code"].dataType, StringType)
    assert isinstance(schema["reference_year"].dataType, StringType)
    assert isinstance(schema["variable_code"].dataType, StringType)
    assert isinstance(schema["dt_base"].dataType, DateType)
    assert schema["payload"].dataType.simpleString() == "variant"
    assert isinstance(schema["request_id"].dataType, StringType)
    assert isinstance(schema["ingestion_timestamp"].dataType, TimestampType)

    assert schema["municipality_code"].nullable is False
    assert schema["payload"].nullable is False
    assert schema["ingestion_timestamp"].nullable is False
