from olist_data_platform.domains.bronze.olist.products_bronze_config import (
    OLIST_PRODUCTS_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_should_define_olist_products_bronze_contract():
    config = OLIST_PRODUCTS_BRONZE_CONFIG

    assert config.primary_key_columns == ("product_id",)
    assert config.required_columns == (
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
        "source_file",
        "ingestion_timestamp",
    )
    assert config.clustering_columns == ()
    assert config.partition_columns == ()
    assert config.write_strategy is WriteStrategy.FULL_REPLACE
