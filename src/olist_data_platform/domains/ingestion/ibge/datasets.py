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

MUNICIPALITY_BUSINESS_ACTIVITY = SidraDataset(
    name="municipality_business_activity",
    table_id=1685,
    territorial_level=6,
    variables=("367", "706", "707", "708", "5944", "662", "1606", "10143"),
    description=(
        "IBGE CEMPRE municipal business activity indicators selected for the "
        "2016-2018 Olist enrichment scope."
    ),
    default_periods=("2016", "2017", "2018"),
)
