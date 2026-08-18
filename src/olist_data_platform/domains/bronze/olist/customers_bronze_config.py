from olist_data_platform.platform.delta.bronze import (
    BronzeDatasetConfig,
    WriteStrategy,
)

OLIST_CUSTOMERS_BRONZE_CONFIG = BronzeDatasetConfig(
    primary_key_columns=("customer_id",),
    required_columns=(
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
        "source_file",
    ),
    clustering_columns=(),
    partition_columns=(),
    write_strategy=WriteStrategy.FULL_REPLACE,
)
