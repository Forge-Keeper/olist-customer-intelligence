from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_ORDER_ITEMS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="order_id",
            data_type="string",
            nullable=False,
            description="Order identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="order_item_id",
            data_type="string",
            nullable=False,
            description="Item sequence identifier within the order, preserved as source text.",
        ),
        ColumnContract(
            name="product_id",
            data_type="string",
            nullable=False,
            description="Product identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="seller_id",
            data_type="string",
            nullable=False,
            description="Seller identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="shipping_limit_date",
            data_type="string",
            nullable=False,
            description="Shipping limit timestamp preserved as source text.",
        ),
        ColumnContract(
            name="price",
            data_type="string",
            nullable=False,
            description="Item price preserved exactly as source text.",
        ),
        ColumnContract(
            name="freight_value",
            data_type="string",
            nullable=False,
            description="Freight value preserved exactly as source text.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("order_id", "order_item_id"),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Olist order items CSV snapshot landed in Bronze as source strings.",
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
