from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableLayout,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

WEATHER_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="dt_base",
            data_type="date",
            nullable=False,
            description="Logical reference date for the daily weather observation.",
        ),
        ColumnContract(
            name="payload",
            data_type="variant",
            nullable=False,
            description=(
                "Open-Meteo daily response payload preserved as semi-structured data."
            ),
        ),
        ColumnContract(
            name="request_id",
            data_type="string",
            nullable=False,
            description="Identifier used to trace the source API request.",
        ),
        ColumnContract(
            name="requested_latitude",
            data_type="double",
            nullable=False,
            description="Latitude requested from the Open-Meteo API.",
        ),
        ColumnContract(
            name="requested_longitude",
            data_type="double",
            nullable=False,
            description="Longitude requested from the Open-Meteo API.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=(
        "dt_base",
        "requested_latitude",
        "requested_longitude",
    ),
    layout=TableLayout(clustering_columns=("dt_base",)),
    write_strategy=WriteStrategy.MERGE,
    metadata=TableMetadata(
        description="Daily Open-Meteo API responses landed in Bronze.",
        tags={
            "layer": "bronze",
            "domain": "weather",
            "source_system": "open_meteo",
        },
    ),
)
