from olist_data_platform.platform.delta.bronze import (
    BronzeDatasetConfig,
    WriteStrategy,
)

OLIST_CLOSED_DEALS_BRONZE_CONFIG = BronzeDatasetConfig(
    primary_key_columns=("mql_id",),
    required_columns=(
        "mql_id",
        "seller_id",
        "sdr_id",
        "sr_id",
        "won_date",
        "business_segment",
        "lead_type",
        "lead_behaviour_profile",
        "has_company",
        "has_gtin",
        "average_stock",
        "business_type",
        "declared_product_catalog_size",
        "declared_monthly_revenue",
        "source_file",
    ),
    clustering_columns=(),
    partition_columns=(),
    write_strategy=WriteStrategy.FULL_REPLACE,
)
