from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_ORDER_PAYMENTS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="order_id",
            data_type="string",
            nullable=False,
            description="Order identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="payment_sequential",
            data_type="string",
            nullable=False,
            description=(
                "Payment sequence identifier within the order, preserved as source "
                "text."
            ),
        ),
        ColumnContract(
            name="payment_type",
            data_type="string",
            nullable=False,
            description="Payment method label preserved exactly as source text.",
        ),
        ColumnContract(
            name="payment_installments",
            data_type="string",
            nullable=False,
            description="Installment count preserved exactly as source text.",
        ),
        ColumnContract(
            name="payment_value",
            data_type="string",
            nullable=False,
            description="Payment value preserved exactly as source text.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("order_id", "payment_sequential"),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description=(
            "Olist order payments CSV snapshot landed in Bronze as source strings."
        ),
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
