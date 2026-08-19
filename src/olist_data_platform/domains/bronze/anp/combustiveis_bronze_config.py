from olist_data_platform.platform.delta.bronze.config import (
    BronzeDatasetConfig,
    WriteStrategy,
)

ANP_COMBUSTIVEIS_BRONZE_CONFIG = BronzeDatasetConfig(
    primary_key_columns=("id",),
    required_columns=(
        "id",
        "cnpj_revenda",
        "produto",
        "data_coleta",
        "valor_venda",
        "source_file",
        "dt_base",
        "source_system",
    ),
    clustering_columns=("dt_base",),
    write_strategy=WriteStrategy.REPLACE_WHERE,
)
