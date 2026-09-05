from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableLayout,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

ANP_COMBUSTIVEIS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            "id",
            "long",
            False,
            "PostgreSQL-generated technical identity.",
        ),
        ColumnContract(
            "regiao_sigla",
            "string",
            True,
            "ANP region abbreviation.",
        ),
        ColumnContract(
            "estado_sigla",
            "string",
            True,
            "ANP state abbreviation.",
        ),
        ColumnContract(
            "municipio",
            "string",
            True,
            "Municipality preserved from ANP.",
        ),
        ColumnContract(
            "revenda",
            "string",
            True,
            "Fuel retailer name preserved from ANP.",
        ),
        ColumnContract(
            "cnpj_revenda",
            "string",
            True,
            "Retailer CNPJ preserved from ANP.",
        ),
        ColumnContract(
            "nome_rua",
            "string",
            True,
            "Street name preserved from ANP.",
        ),
        ColumnContract(
            "numero_rua",
            "string",
            True,
            "Street number preserved from ANP.",
        ),
        ColumnContract(
            "complemento",
            "string",
            True,
            "Address complement preserved from ANP.",
        ),
        ColumnContract(
            "bairro",
            "string",
            True,
            "Neighborhood preserved from ANP.",
        ),
        ColumnContract(
            "cep",
            "string",
            True,
            "Postal code preserved from ANP.",
        ),
        ColumnContract(
            "produto",
            "string",
            True,
            "Fuel product preserved from ANP.",
        ),
        ColumnContract(
            "data_coleta",
            "date",
            False,
            "ANP collection date.",
        ),
        ColumnContract(
            "valor_venda",
            "decimal(38,18)",
            False,
            "ANP sale price from PostgreSQL NUMERIC.",
        ),
        ColumnContract(
            "valor_compra",
            "decimal(38,18)",
            True,
            "ANP purchase price from PostgreSQL NUMERIC.",
        ),
        ColumnContract(
            "unidade_medida",
            "string",
            True,
            "ANP measurement unit.",
        ),
        ColumnContract(
            "bandeira",
            "string",
            True,
            "ANP retailer brand.",
        ),
        ColumnContract(
            "source_file",
            "string",
            False,
            "Original ANP CSV file loaded into PostgreSQL.",
        ),
        ColumnContract(
            "dt_base",
            "date",
            False,
            "Bronze reprocessing scope derived from data_coleta.",
        ),
        ColumnContract(
            "source_system",
            "string",
            False,
            "Operational source identifier.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("id",),
    layout=TableLayout(clustering_columns=("dt_base",)),
    write_strategy=WriteStrategy.REPLACE_WHERE,
    metadata=TableMetadata(
        description="ANP fuel prices read from PostgreSQL and landed in Bronze.",
        tags={
            "layer": "bronze",
            "domain": "anp",
            "source_system": "azure_postgresql",
        },
    ),
)
