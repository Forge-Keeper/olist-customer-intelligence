from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_CLOSED_DEALS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="mql_id",
            data_type="string",
            nullable=False,
            description=(
                "Marketing qualified lead identifier from the Olist source snapshot."
            ),
        ),
        ColumnContract(
            name="seller_id",
            data_type="string",
            nullable=True,
            description="Seller identifier preserved from the source CSV.",
        ),
        ColumnContract(
            name="sdr_id",
            data_type="string",
            nullable=True,
            description=(
                "Sales development representative identifier preserved from the "
                "source CSV."
            ),
        ),
        ColumnContract(
            name="sr_id",
            data_type="string",
            nullable=True,
            description="Sales representative identifier preserved from the source CSV.",
        ),
        ColumnContract(
            name="won_date",
            data_type="string",
            nullable=True,
            description="Closed-deal won date preserved as the source CSV string.",
        ),
        ColumnContract(
            name="business_segment",
            data_type="string",
            nullable=True,
            description="Business segment preserved from the source CSV.",
        ),
        ColumnContract(
            name="lead_type",
            data_type="string",
            nullable=True,
            description="Lead type preserved from the source CSV.",
        ),
        ColumnContract(
            name="lead_behaviour_profile",
            data_type="string",
            nullable=True,
            description="Lead behaviour profile preserved from the source CSV.",
        ),
        ColumnContract(
            name="has_company",
            data_type="string",
            nullable=True,
            description=(
                "Source value indicating whether the lead has a company, preserved "
                "as a string."
            ),
        ),
        ColumnContract(
            name="has_gtin",
            data_type="string",
            nullable=True,
            description=(
                "Source value indicating whether the lead has GTIN information, "
                "preserved as a string."
            ),
        ),
        ColumnContract(
            name="average_stock",
            data_type="string",
            nullable=True,
            description="Average stock value preserved as the source CSV string.",
        ),
        ColumnContract(
            name="business_type",
            data_type="string",
            nullable=True,
            description="Business type preserved from the source CSV.",
        ),
        ColumnContract(
            name="declared_product_catalog_size",
            data_type="string",
            nullable=True,
            description=(
                "Declared product catalog size preserved as the source CSV string."
            ),
        ),
        ColumnContract(
            name="declared_monthly_revenue",
            data_type="string",
            nullable=True,
            description=(
                "Declared monthly revenue preserved as the source CSV string."
            ),
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("mql_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description=(
            "Olist closed-deals CSV snapshot landed in Bronze as source strings."
        ),
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
