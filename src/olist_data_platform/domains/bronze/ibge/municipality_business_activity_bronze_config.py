from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableLayout,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

IBGE_MUNICIPALITY_BUSINESS_ACTIVITY_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="municipality_code",
            data_type="string",
            nullable=False,
            description="Official IBGE municipality code.",
        ),
        ColumnContract(
            name="reference_year",
            data_type="string",
            nullable=False,
            description="Reference year returned by IBGE SIDRA.",
        ),
        ColumnContract(
            name="variable_code",
            data_type="string",
            nullable=False,
            description="IBGE SIDRA variable code for the CEMPRE measure.",
        ),
        ColumnContract(
            name="dt_base",
            data_type="date",
            nullable=False,
            description="Logical reference date used by the Bronze dataset.",
        ),
        ColumnContract(
            name="payload",
            data_type="variant",
            nullable=False,
            description="Source SIDRA CEMPRE payload preserved as VARIANT.",
        ),
        ColumnContract(
            name="request_id",
            data_type="string",
            nullable=False,
            description="Request identifier associated with the source ingestion call.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("municipality_code", "reference_year", "variable_code"),
    write_strategy=WriteStrategy.MERGE,
    layout=TableLayout(clustering_columns=("dt_base",)),
    metadata=TableMetadata(
        description="Bronze municipal CEMPRE observations retrieved from IBGE SIDRA.",
        tags={
            "layer": "bronze",
            "domain": "ibge",
            "source_system": "ibge_sidra",
            "dataset": "cempre",
        },
    ),
)
