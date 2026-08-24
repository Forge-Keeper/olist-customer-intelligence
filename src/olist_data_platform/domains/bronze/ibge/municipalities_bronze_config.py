from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableLayout,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

IBGE_MUNICIPALITIES_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="municipality_code",
            data_type="string",
            nullable=False,
            description="Official IBGE municipality code.",
        ),
        ColumnContract(
            name="dt_base",
            data_type="date",
            nullable=False,
            description="Logical reference date for the municipality snapshot.",
        ),
        ColumnContract(
            name="payload",
            data_type="variant",
            nullable=False,
            description="Source municipality payload preserved as VARIANT.",
        ),
        ColumnContract(
            name="request_id",
            data_type="string",
            nullable=False,
            description="Request identifier associated with the source ingestion call.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("municipality_code", "dt_base"),
    write_strategy=WriteStrategy.MERGE,
    layout=TableLayout(clustering_columns=("dt_base",)),
    metadata=TableMetadata(
        description="Bronze snapshot of IBGE municipality locality records.",
        tags={
            "layer": "bronze",
            "domain": "ibge",
            "source_system": "ibge_localidades",
        },
    ),
)
