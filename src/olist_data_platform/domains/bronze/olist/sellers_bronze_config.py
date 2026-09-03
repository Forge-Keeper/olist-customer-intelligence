from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_SELLERS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="seller_id",
            data_type="string",
            nullable=False,
            description="Seller identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="seller_zip_code_prefix",
            data_type="string",
            nullable=True,
            description="Seller ZIP code prefix preserved from the source CSV.",
        ),
        ColumnContract(
            name="seller_city",
            data_type="string",
            nullable=True,
            description="Seller city preserved from the source CSV.",
        ),
        ColumnContract(
            name="seller_state",
            data_type="string",
            nullable=True,
            description="Seller state preserved from the source CSV.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("seller_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Olist sellers CSV snapshot landed in Bronze as source strings.",
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
