from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_PRODUCT_CATEGORY_NAME_TRANSLATION_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="product_category_name",
            data_type="string",
            nullable=False,
            description="Product category name preserved from the source CSV.",
        ),
        ColumnContract(
            name="product_category_name_english",
            data_type="string",
            nullable=False,
            description="English category name preserved from the source CSV.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("product_category_name",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description=(
            "Olist product category name translation CSV snapshot landed in Bronze "
            "as source strings."
        ),
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
