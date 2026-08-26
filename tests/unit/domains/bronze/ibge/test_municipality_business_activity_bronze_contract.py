from olist_data_platform.domains.bronze.ibge.municipality_business_activity_bronze_config import (
    IBGE_MUNICIPALITY_BUSINESS_ACTIVITY_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_cempre_bronze_contract_uses_expected_keys_and_layout() -> None:
    contract = IBGE_MUNICIPALITY_BUSINESS_ACTIVITY_BRONZE_CONFIG
    schema = contract.to_struct_type()

    assert contract.key_columns == (
        "municipality_code",
        "reference_year",
        "variable_code",
    )
    assert contract.write_strategy is WriteStrategy.MERGE
    assert contract.layout.clustering_columns == ("dt_base",)
    assert contract.layout.partition_columns == ()
    assert contract.metadata.tags["dataset"] == "cempre"
    assert schema["payload"].dataType.simpleString() == "variant"
    assert schema["payload"].nullable is False
