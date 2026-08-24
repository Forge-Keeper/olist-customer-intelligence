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
    variables=("37", "498", "513", "517", "525", "6575"),
    description=(
        "IBGE municipal GDP and gross value added indicators selected for the "
        "2016-2018 Olist enrichment scope."
    ),
)
