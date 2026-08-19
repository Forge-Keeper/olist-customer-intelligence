from olist_data_platform.domains.ingestion.ibge.sidra_dataset import SidraDataset

MUNICIPALITY_POPULATION = SidraDataset(
    name="municipality_population",
    table_id=6579,
    territorial_level=6,
    variables=("9324",),
    description="IBGE estimated resident population by municipality and year.",
)

MUNICIPALITY_GDP = SidraDataset(
    name="municipality_gdp",
    table_id=5938,
    territorial_level=6,
    variables=("all",),
    description=(
        "IBGE municipal GDP dataset. Variables remain intentionally broad "
        "until the GDP Bronze feature selects its production contract."
    ),
)
