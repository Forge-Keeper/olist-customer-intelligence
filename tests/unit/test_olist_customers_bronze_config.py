from olist_data_platform.domains.bronze.olist.customers_bronze_config import (
    OLIST_CUSTOMERS_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_should_define_olist_customers_bronze_contract():
    config = OLIST_CUSTOMERS_BRONZE_CONFIG

    assert config.primary_key_columns == ("customer_id",)
    assert config.required_columns == (
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
        "source_file",
        "ingestion_timestamp",
    )
    assert config.clustering_columns == ()
    assert config.partition_columns == ()
    assert config.write_strategy is WriteStrategy.FULL_REPLACE
