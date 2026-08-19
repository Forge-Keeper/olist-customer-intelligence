# Databricks notebook source
# MAGIC %md
# MAGIC # IBGE Bronze validation
# MAGIC
# MAGIC Validation notebook for the IBGE API ingestion feature.
# MAGIC It executes the two approved Bronze datasets and verifies:
# MAGIC - 2016-2018 analytical coverage
# MAGIC - expected territorial cardinality
# MAGIC - natural-key uniqueness
# MAGIC - referential integrity between population and municipalities
# MAGIC - Delta clustering metadata
# MAGIC - idempotent MERGE behavior on re-execution

# COMMAND ----------
from pyspark.sql import functions as F

from olist_data_platform.domains.bronze.ibge.bronze_municipalities_writer import (
    BronzeMunicipalitiesWriter,
)
from olist_data_platform.domains.bronze.ibge.bronze_municipality_population_writer import (
    BronzeMunicipalityPopulationWriter,
)
from olist_data_platform.domains.ingestion.ibge.localities_client import LocalitiesClient
from olist_data_platform.domains.ingestion.ibge.municipalities_ingestion_service import (
    MunicipalitiesIngestionService,
)
from olist_data_platform.domains.ingestion.ibge.municipality_population_ingestion_service import (
    MunicipalityPopulationIngestionService,
)
from olist_data_platform.domains.ingestion.ibge.sidra_client import SidraClient

MUNICIPALITIES_TABLE = "prd.bronze.ibge_municipalities"
POPULATION_TABLE = "prd.bronze.ibge_municipality_population"
EXPECTED_YEARS = (2016, 2017, 2018)
EXPECTED_MUNICIPALITIES_PER_YEAR = 5570

# COMMAND ----------
municipalities_service = MunicipalitiesIngestionService(
    client=LocalitiesClient(),
    bronze_writer=BronzeMunicipalitiesWriter(
        spark=spark,
        target_table=MUNICIPALITIES_TABLE,
    ),
)

population_service = MunicipalityPopulationIngestionService(
    client=SidraClient(),
    bronze_writer=BronzeMunicipalityPopulationWriter(
        spark=spark,
        target_table=POPULATION_TABLE,
    ),
)

municipalities_request_id = municipalities_service.ingest()
population_request_id = population_service.ingest(
    periods=tuple(str(year) for year in EXPECTED_YEARS)
)

print("municipalities_request_id=", municipalities_request_id)
print("population_request_id=", population_request_id)

# COMMAND ----------
municipalities = spark.table(MUNICIPALITIES_TABLE)
population = spark.table(POPULATION_TABLE)

print("municipalities_count=", municipalities.count())
print("population_count=", population.count())

# COMMAND ----------
municipalities_by_year = (
    municipalities
    .groupBy(F.year("dt_base").alias("year"))
    .agg(
        F.count("*").alias("rows"),
        F.countDistinct("municipality_code").alias("municipalities"),
    )
    .orderBy("year")
)
display(municipalities_by_year)

municipality_year_stats = {
    row["year"]: (row["rows"], row["municipalities"])
    for row in municipalities_by_year.collect()
}

assert tuple(sorted(municipality_year_stats)) == EXPECTED_YEARS
for year in EXPECTED_YEARS:
    rows, unique_municipalities = municipality_year_stats[year]
    assert rows == EXPECTED_MUNICIPALITIES_PER_YEAR
    assert unique_municipalities == EXPECTED_MUNICIPALITIES_PER_YEAR

# COMMAND ----------
municipality_duplicates = (
    municipalities
    .groupBy("municipality_code", "dt_base")
    .count()
    .filter(F.col("count") > 1)
)
assert municipality_duplicates.count() == 0

population_duplicates = (
    population
    .groupBy("municipality_code", "reference_year", "variable_code")
    .count()
    .filter(F.col("count") > 1)
)
assert population_duplicates.count() == 0

# COMMAND ----------
population_years = tuple(
    row["reference_year"]
    for row in population
    .select("reference_year")
    .distinct()
    .orderBy("reference_year")
    .collect()
)
assert population_years == EXPECTED_YEARS

invalid_population_dt_base = population.filter(
    F.col("dt_base")
    != F.make_date(F.col("reference_year"), F.lit(1), F.lit(1))
)
assert invalid_population_dt_base.count() == 0

# COMMAND ----------
missing_municipality_reference = (
    population.alias("p")
    .join(
        municipalities.alias("m"),
        on=(
            (F.col("p.municipality_code") == F.col("m.municipality_code"))
            & (F.col("p.dt_base") == F.col("m.dt_base"))
        ),
        how="left_anti",
    )
)

missing_count = missing_municipality_reference.count()
if missing_count:
    display(missing_municipality_reference)
assert missing_count == 0

# COMMAND ----------
municipalities_detail = spark.sql(f"DESCRIBE DETAIL {MUNICIPALITIES_TABLE}").first()
population_detail = spark.sql(f"DESCRIBE DETAIL {POPULATION_TABLE}").first()

print("municipalities_clustering=", municipalities_detail["clusteringColumns"])
print("population_clustering=", population_detail["clusteringColumns"])

assert set(municipalities_detail["clusteringColumns"]) == {"dt_base", "state_code"}
assert set(population_detail["clusteringColumns"]) == {"dt_base"}

# COMMAND ----------
municipalities_before = municipalities.count()
population_before = population.count()

municipalities_service.ingest()
population_service.ingest(periods=tuple(str(year) for year in EXPECTED_YEARS))

municipalities_after = spark.table(MUNICIPALITIES_TABLE).count()
population_after = spark.table(POPULATION_TABLE).count()

assert municipalities_after == municipalities_before
assert population_after == population_before

print(
    "Validation passed | "
    f"municipalities_rows={municipalities_after} | "
    f"population_rows={population_after}"
)
