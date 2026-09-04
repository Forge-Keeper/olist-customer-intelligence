from olist_data_platform.domains.bronze.olist import (
    product_category_name_translation_bronze_config as bronze_config,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_should_define_category_translation_bronze_contract():
    config = bronze_config.OLIST_PRODUCT_CATEGORY_NAME_TRANSLATION_BRONZE_CONFIG

    assert config.primary_key_columns == ("product_category_name",)
    assert config.required_columns == (
        "product_category_name",
        "product_category_name_english",
        "source_file",
        "ingestion_timestamp",
    )
    assert config.clustering_columns == ()
    assert config.partition_columns == ()
    assert config.write_strategy is WriteStrategy.FULL_REPLACE
