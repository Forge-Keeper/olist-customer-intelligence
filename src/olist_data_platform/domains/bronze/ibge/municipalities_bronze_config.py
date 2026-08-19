from olist_data_platform.platform.delta.bronze import (
    BronzeDatasetConfig,
    WriteStrategy,
)

IBGE_MUNICIPALITIES_BRONZE_CONFIG = BronzeDatasetConfig(
    primary_key_columns=("municipality_code", "dt_base"),
    required_columns=(
        "municipality_code",
        "municipality_name",
        "state_code",
        "state_name",
        "region_code",
        "region_name",
        "dt_base",
        "request_id",
    ),
    clustering_columns=("dt_base", "state_code"),
    partition_columns=(),
    write_strategy=WriteStrategy.MERGE,
)
