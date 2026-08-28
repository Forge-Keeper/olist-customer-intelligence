from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_MARKETING_QUALIFIED_LEADS_BRONZE_CONFIG = DatasetContract(
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
            name="first_contact_date",
            data_type="string",
            nullable=False,
            description="First contact date preserved as the source CSV string.",
        ),
        ColumnContract(
            name="landing_page_id",
            data_type="string",
            nullable=False,
            description="Landing page identifier preserved from the source CSV.",
        ),
        ColumnContract(
            name="origin",
            data_type="string",
            nullable=True,
            description="Marketing lead origin preserved from the source CSV.",
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
            "Olist marketing-qualified-leads CSV snapshot landed in Bronze as "
            "source strings."
        ),
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
