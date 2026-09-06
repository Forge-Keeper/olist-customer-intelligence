from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_GEOLOCATION_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="geolocation_zip_code_prefix",
            data_type="string",
            nullable=False,
            description="ZIP code prefix preserved from the Olist source snapshot.",
        ),
        ColumnContract(
            name="geolocation_lat",
            data_type="string",
            nullable=False,
            description="Latitude preserved as source text.",
        ),
        ColumnContract(
            name="geolocation_lng",
            data_type="string",
            nullable=False,
            description="Longitude preserved as source text.",
        ),
        ColumnContract(
            name="geolocation_city",
            data_type="string",
            nullable=False,
            description="City name preserved exactly from the source CSV.",
        ),
        ColumnContract(
            name="geolocation_state",
            data_type="string",
            nullable=False,
            description="State code preserved exactly from the source CSV.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=(),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description=(
            "Olist geolocation CSV snapshot landed in Bronze without deduplicating "
            "or normalizing repeated source observations."
        ),
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
