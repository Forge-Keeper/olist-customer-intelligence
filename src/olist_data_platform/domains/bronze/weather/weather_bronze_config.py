from olist_data_platform.platform.delta.bronze.config import (
    BronzeDatasetConfig,
    WriteStrategy,
)

WEATHER_BRONZE_CONFIG = BronzeDatasetConfig(
    primary_key_columns=(
        "dt_base",
        "requested_latitude",
        "requested_longitude",
    ),
    required_columns=(
        "dt_base",
        "payload",
        "request_id",
        "requested_latitude",
        "requested_longitude",
    ),
    clustering_columns=("dt_base",),
    partition_columns=(),
    write_strategy=WriteStrategy.MERGE,
)
