from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_PRODUCTS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="product_id",
            data_type="string",
            nullable=False,
            description="Product identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="product_category_name",
            data_type="string",
            nullable=True,
            description="Product category preserved from the source CSV.",
        ),
        ColumnContract(
            name="product_name_lenght",
            data_type="string",
            nullable=True,
            description="Source product-name length value preserved as text.",
        ),
        ColumnContract(
            name="product_description_lenght",
            data_type="string",
            nullable=True,
            description="Source product-description length preserved as text.",
        ),
        ColumnContract(
            name="product_photos_qty",
            data_type="string",
            nullable=True,
            description="Source product photo count preserved as text.",
        ),
        ColumnContract(
            name="product_weight_g",
            data_type="string",
            nullable=True,
            description="Source product weight in grams preserved as text.",
        ),
        ColumnContract(
            name="product_length_cm",
            data_type="string",
            nullable=True,
            description="Source product length in centimetres preserved as text.",
        ),
        ColumnContract(
            name="product_height_cm",
            data_type="string",
            nullable=True,
            description="Source product height in centimetres preserved as text.",
        ),
        ColumnContract(
            name="product_width_cm",
            data_type="string",
            nullable=True,
            description="Source product width in centimetres preserved as text.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("product_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Olist products CSV snapshot landed in Bronze as source strings.",
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
