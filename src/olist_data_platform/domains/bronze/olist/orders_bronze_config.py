from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_ORDERS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="order_id",
            data_type="string",
            nullable=False,
            description="Order identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="customer_id",
            data_type="string",
            nullable=False,
            description="Customer identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="order_status",
            data_type="string",
            nullable=False,
            description="Order status preserved exactly from the source CSV.",
        ),
        ColumnContract(
            name="order_purchase_timestamp",
            data_type="string",
            nullable=False,
            description="Purchase timestamp preserved as source text.",
        ),
        ColumnContract(
            name="order_approved_at",
            data_type="string",
            nullable=True,
            description="Approval timestamp preserved as source text.",
        ),
        ColumnContract(
            name="order_delivered_carrier_date",
            data_type="string",
            nullable=True,
            description="Carrier delivery timestamp preserved as source text.",
        ),
        ColumnContract(
            name="order_delivered_customer_date",
            data_type="string",
            nullable=True,
            description="Customer delivery timestamp preserved as source text.",
        ),
        ColumnContract(
            name="order_estimated_delivery_date",
            data_type="string",
            nullable=False,
            description="Estimated delivery timestamp preserved as source text.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("order_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Olist orders CSV snapshot landed in Bronze as source strings.",
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
