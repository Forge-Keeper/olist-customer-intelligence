# Databricks notebook source
# MAGIC %md
# MAGIC # IBGE Bronze validation
# MAGIC
# MAGIC Validation notebook for the IBGE API ingestion feature.
# MAGIC It executes the approved Bronze datasets and verifies:
# MAGIC - current Localidades snapshot landing
# MAGIC - 2016-2018 population coverage
# MAGIC - natural-key uniqueness
# MAGIC - source payload preservation in VARIANT
# MAGIC - municipality-code compatibility between sources
# MAGIC - Delta clustering metadata
# MAGIC - idempotent MERGE behavior on same-scope re-execution

# COMMAND ----------
import sys
from pathlib import Path


def _bootstrap_src_path() -> Path:
    candidates = (Path.cwd(), *Path.cwd().parents)
    for candidate in candidates:
        src_path = candidate / "src"
        package_path = src_path / "olist_data_platform"
        if package_path.is_dir():
            src_value = str(src_path)
            if src_value not in sys.path:
                sys.path.insert(0, src_value)
            return src_path
    raise RuntimeError(
        "Could not locate src/olist_data_platform from the Databricks Repo."
    )


SRC_PATH = _bootstrap_src_path()
print("Using project src path:", SRC_PATH)

# COMMAND ----------
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from olist_data_platform.domains.bronze.ibge import (
    bronze_municipalities_writer as municipalities_writer,
)
from olist_data_platform.domains.bronze.ibge import (
    bronze_municipality_population_writer as population_writer,
)
from olist_data_platform.domains.ingestion.ibge import localities_client
from olist_data_platform.domains.ingestion.ibge import (
    municipalities_ingestion_service,
)
from olist_data_platform.domains.ingestion.ibge import (
    municipality_population_ingestion_service,
)
from olist_data_platform.domains.ingestion.ibge import sidra_client

spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

MUNICIPALITIES_TABLE = "prd.bronze.ibge_municipalities"
POPULATION_TABLE = "prd.bronze.ibge_municipality_population"
EXPECTED_YEARS = (2016, 2017, 2018)
EXPECTED_POPULATION_MUNICIPALITIES_PER_YEAR = 5570

# Contract migration is intentionally explicit. Set this to True only for the
# one-time development reset after changing the IBGE Bronze schema.
RESET_BRONZE_TABLES = False

if RESET_BRONZE_TABLES:
    spark.sql(f"DROP TABLE IF EXISTS {MUNICIPALITIES_TABLE}")
    spark.sql(f"DROP TABLE IF EXISTS {POPULATION_TABLE}")
    print("IBGE Bronze development tables reset for contract migration.")

# COMMAND ----------
municipalities_service = (
    municipalities_ingestion_service.MunicipalitiesIngestionService(
        client=localities_client.LocalitiesClient(),
        bronze_writer=municipalities_writer.BronzeMunicipalitiesWriter(
            spark=spark,
            target_table=MUNICIPALITIES_TABLE,
        ),
    )
)

population_service = (
    municipality_population_ingestion_service.MunicipalityPopulationIngestionService(
        client=sidra_client.SidraClient(),
        bronze_writer=population_writer.BronzeMunicipalityPopulationWriter(
            spark=spark,
            target_table=POPULATION_TABLE,
        ),
    )
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
latest_municipality_snapshot = municipalities.agg(F.max("dt_base")).first()[0]
assert latest_municipality_snapshot is not None

municipalities_snapshot = municipalities.filter(
    F.col("dt_base") == F.lit(latest_municipality_snapshot)
)
municipalities_snapshot_count = municipalities_snapshot.count()
municipalities_snapshot_unique = municipalities_snapshot.select(
    "municipality_code"
).distinct().count()

assert municipalities_snapshot_count > 0
assert municipalities_snapshot_unique == municipalities_snapshot_count

print(
    "latest_municipality_snapshot=",
    latest_municipality_snapshot,
    "rows=",
    municipalities_snapshot_count,
)

# COMMAND ----------
municipality_duplicates = (
    municipalities.groupBy("municipality_code", "dt_base")
    .count()
    .filter(F.col("count") > 1)
)
assert municipality_duplicates.count() == 0

population_duplicates = (
    population.groupBy(
        "municipality_code",
        "reference_year",
        "variable_code",
    )
    .count()
    .filter(F.col("count") > 1)
)
assert population_duplicates.count() == 0

# COMMAND ----------
population_year_stats = (
    population.groupBy("reference_year")
    .agg(
        F.count("*").alias("rows"),
        F.countDistinct("municipality_code").alias("municipalities"),
    )
    .orderBy("reference_year")
)
population_year_stats.show(truncate=False)

population_stats = {
    int(row["reference_year"]): (row["rows"], row["municipalities"])
    for row in population_year_stats.collect()
}

assert tuple(sorted(population_stats)) == EXPECTED_YEARS
for year in EXPECTED_YEARS:
    rows, unique_municipalities = population_stats[year]
    assert rows == EXPECTED_POPULATION_MUNICIPALITIES_PER_YEAR
    assert unique_municipalities == EXPECTED_POPULATION_MUNICIPALITIES_PER_YEAR

invalid_population_dt_base = population.filter(
    F.col("dt_base")
    != F.make_date(F.col("reference_year").cast("int"), F.lit(1), F.lit(1))
)
assert invalid_population_dt_base.count() == 0

# COMMAND ----------
# Bronze preserves source values in the VARIANT payload. Business typing and
# semantic normalization belong downstream.
population_payload_check = population.selectExpr(
    "variant_get(payload, '$.Valor', 'string') AS source_value",
    "variant_get(payload, '$.Ano', 'string') AS source_year",
).limit(1).first()
assert population_payload_check is not None
assert population_payload_check["source_value"] is not None
assert population_payload_check["source_year"] is not None

municipality_payload_check = municipalities_snapshot.selectExpr(
    "variant_get(payload, '$.nome', 'string') AS source_name"
).limit(1).first()
assert municipality_payload_check is not None
assert municipality_payload_check["source_name"] is not None

# COMMAND ----------
# This is intentionally not a historical join by dt_base. Localidades is a
# current source snapshot; historical reconstruction belongs in Silver.
missing_current_municipality_code = (
    population.select("municipality_code")
    .distinct()
    .join(
        municipalities_snapshot.select("municipality_code").distinct(),
        on="municipality_code",
        how="left_anti",
    )
)
missing_count = missing_current_municipality_code.count()
if missing_count:
    missing_current_municipality_code.show(truncate=False)
assert missing_count == 0

# COMMAND ----------
municipalities_detail = spark.sql(
    f"DESCRIBE DETAIL {MUNICIPALITIES_TABLE}"
).first()
population_detail = spark.sql(
    f"DESCRIBE DETAIL {POPULATION_TABLE}"
).first()

assert municipalities_detail is not None
assert population_detail is not None

municipalities_clustering = municipalities_detail["clusteringColumns"]
population_clustering = population_detail["clusteringColumns"]

print("municipalities_clustering=", municipalities_clustering)
print("population_clustering=", population_clustering)

assert set(municipalities_clustering) == {"dt_base"}
assert set(population_clustering) == {"dt_base"}

# COMMAND ----------
# Re-execution in the same run uses the same calendar date for Localidades and
# the same logical SIDRA keys, so MERGE must not increase row counts.
municipalities_before = municipalities.count()
population_before = population.count()

municipalities_service.ingest()
population_service.ingest(
    periods=tuple(str(year) for year in EXPECTED_YEARS)
)

municipalities_after = spark.table(MUNICIPALITIES_TABLE).count()
population_after = spark.table(POPULATION_TABLE).count()

assert municipalities_after == municipalities_before
assert population_after == population_before

print(
    "Validation passed | "
    f"municipalities_rows={municipalities_after} | "
    f"population_rows={population_after}"
)
