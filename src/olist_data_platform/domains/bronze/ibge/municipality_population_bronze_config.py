from olist_data_platform.platform.delta.bronze import (
    BronzeDatasetConfig,
    WriteStrategy,
)

IBGE_MUNICIPALITY_POPULATION_BRONZE_CONFIG = BronzeDatasetConfig(
    primary_key_columns=(
        "municipality_code",
        "reference_year",
        "variable_code",
    ),
    required_columns=(
        "municipality_code",
        "municipality_name",
        "variable_code",
        "variable_name",
        "reference_year",
        "unit_code",
        "unit_name",
        "territorial_level_code",
        "territorial_level_name",
        "value",
        "dt_base",
        "request_id",
    ),
    clustering_columns=("dt_base",),
    partition_columns=(),
    write_strategy=WriteStrategy.MERGE,
)
