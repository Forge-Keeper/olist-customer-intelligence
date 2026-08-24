# Databricks notebook source
# MAGIC %md
# MAGIC # IBGE municipal GDP Bronze validation
# MAGIC
# MAGIC Executes the approved 2016-2018 municipal GDP/VAB ingestion and validates:
# MAGIC - selected production variables only
# MAGIC - natural-key uniqueness
# MAGIC - annual dt_base semantics
# MAGIC - source payload preservation in VARIANT, including special markers
# MAGIC - municipality-code compatibility with Localidades
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
    bronze_municipality_gdp_writer as gdp_writer,
)
from olist_data_platform.domains.ingestion.ibge.datasets import MUNICIPALITY_GDP
from olist_data_platform.domains.ingestion.ibge import (
    municipality_gdp_ingestion_service,
)
from olist_data_platform.domains.ingestion.ibge.sidra_client import SidraClient

spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

GDP_TABLE = "prd.bronze.ibge_municipality_gdp"
MUNICIPALITIES_TABLE = "prd.bronze.ibge_municipalities"
EXPECTED_YEARS = (2016, 2017, 2018)
EXPECTED_VARIABLES = tuple(MUNICIPALITY_GDP.variables)

RESET_GDP_TABLE = False

if RESET_GDP_TABLE:
    spark.sql(f"DROP TABLE IF EXISTS {GDP_TABLE}")
    print("IBGE municipal GDP Bronze table reset for contract migration.")

# COMMAND ----------
gdp_service = municipality_gdp_ingestion_service.MunicipalityGdpIngestionService(
    client=SidraClient(),
    bronze_writer=gdp_writer.BronzeMunicipalityGdpWriter(
        spark=spark,
        target_table=GDP_TABLE,
    ),
)

gdp_request_id = gdp_service.ingest(
    periods=tuple(str(year) for year in EXPECTED_YEARS)
)
print("gdp_request_id=", gdp_request_id)

# COMMAND ----------
gdp = spark.table(GDP_TABLE)
print("gdp_count=", gdp.count())

gdp_stats = (
    gdp.groupBy("reference_year", "variable_code")
    .agg(
        F.count("*").alias("rows"),
        F.countDistinct("municipality_code").alias("municipalities"),
    )
    .orderBy("reference_year", "variable_code")
)
gdp_stats.show(100, truncate=False)

observed_years = {
    int(row["reference_year"])
    for row in gdp.select("reference_year").distinct().collect()
}
observed_variables = {
    row["variable_code"]
    for row in gdp.select("variable_code").distinct().collect()
}

assert observed_years == set(EXPECTED_YEARS)
assert observed_variables == set(EXPECTED_VARIABLES)

# COMMAND ----------
duplicates = (
    gdp.groupBy("municipality_code", "reference_year", "variable_code")
    .count()
    .filter(F.col("count") > 1)
)
assert duplicates.count() == 0

invalid_dt_base = gdp.filter(
    F.col("dt_base")
    != F.make_date(F.col("reference_year").cast("int"), F.lit(1), F.lit(1))
)
assert invalid_dt_base.count() == 0

# COMMAND ----------
# Bronze preserves SIDRA source representation. Monetary typing and handling of
# special markers such as '...' belong downstream.
payload_values = gdp.selectExpr(
    "variable_code",
    "variant_get(payload, '$.Valor', 'string') AS source_value",
    "variant_get(payload, '$.Ano', 'string') AS source_year",
).filter(F.col("source_value").isNotNull())

assert payload_values.limit(1).count() == 1
assert payload_values.filter(F.col("source_year").isNull()).count() == 0

special_values = payload_values.filter(F.col("source_value") == F.lit("...")).count()
print("special_value_rows=", special_values)

# COMMAND ----------
# Compare with the current municipality source by code only. Historical
# reconstruction is intentionally not fabricated in Bronze.
municipalities = spark.table(MUNICIPALITIES_TABLE)
latest_snapshot = municipalities.agg(F.max("dt_base")).first()[0]
assert latest_snapshot is not None
current_municipality_codes = (
    municipalities.filter(F.col("dt_base") == F.lit(latest_snapshot))
    .select("municipality_code")
    .distinct()
)

missing_current_codes = (
    gdp.select("municipality_code")
    .distinct()
    .join(current_municipality_codes, on="municipality_code", how="left_anti")
)
missing_count = missing_current_codes.count()
if missing_count:
    missing_current_codes.show(truncate=False)
assert missing_count == 0

# COMMAND ----------
detail = spark.sql(f"DESCRIBE DETAIL {GDP_TABLE}").first()
assert detail is not None
print("gdp_clustering=", detail["clusteringColumns"])
assert set(detail["clusteringColumns"]) == {"dt_base"}

# COMMAND ----------
# Same logical scope must MERGE without increasing row count.
rows_before = gdp.count()
gdp_service.ingest(periods=tuple(str(year) for year in EXPECTED_YEARS))
rows_after = spark.table(GDP_TABLE).count()
assert rows_after == rows_before

print(
    "GDP validation passed | "
    f"rows={rows_after} | years={EXPECTED_YEARS} | variables={EXPECTED_VARIABLES}"
)
