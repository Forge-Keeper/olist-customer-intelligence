from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze.config import WriteStrategy


OLIST_CUSTOMERS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="customer_id",
            data_type="string",
            nullable=False,
            description="Customer identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="customer_unique_id",
            data_type="string",
            nullable=True,
            description="Stable customer identifier provided by the Olist source snapshot.",
        ),
        ColumnContract(
            name="customer_zip_code_prefix",
            data_type="string",
            nullable=True,
            description="Customer ZIP code prefix preserved from the source CSV.",
        ),
        ColumnContract(
            name="customer_city",
            data_type="string",
            nullable=True,
            description="Customer city preserved from the source CSV.",
        ),
        ColumnContract(
            name="customer_state",
            data_type="string",
            nullable=True,
            description="Customer state preserved from the source CSV.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("customer_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Olist customers CSV snapshot landed in Bronze as source strings.",
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
