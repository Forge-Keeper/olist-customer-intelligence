# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Marketing Qualified Leads discovery
# MAGIC
# MAGIC Discovery notebook for `olist_marketing_qualified_leads_dataset.csv` before Bronze design.
# MAGIC
# MAGIC Goals:
# MAGIC - inspect source schema and representative rows;
# MAGIC - validate grain and candidate logical key;
# MAGIC - measure nulls and duplicates;
# MAGIC - inspect categorical domains and timestamp parseability;
# MAGIC - validate the relationship with Closed Deals through `mql_id`;
# MAGIC - collect evidence for Bronze contract, Data Quality and write strategy;
# MAGIC - do not create or modify Bronze tables.
# MAGIC
# MAGIC Environment-specific Volume paths are supplied explicitly through widgets.

# COMMAND ----------
dbutils.widgets.text("funnel_source_dir", "", "Marketing Funnel source directory")

FUNNEL_SOURCE_DIR = dbutils.widgets.get("funnel_source_dir").strip().rstrip("/")
if not FUNNEL_SOURCE_DIR:
    raise ValueError("Set the funnel_source_dir widget before running discovery.")

MQL_FILE_NAME = "olist_marketing_qualified_leads_dataset.csv"
CLOSED_DEALS_FILE_NAME = "olist_closed_deals_dataset.csv"
MQL_SOURCE_PATH = f"{FUNNEL_SOURCE_DIR}/{MQL_FILE_NAME}"
CLOSED_DEALS_SOURCE_PATH = f"{FUNNEL_SOURCE_DIR}/{CLOSED_DEALS_FILE_NAME}"

print("MQL source:", MQL_SOURCE_PATH)
print("Closed Deals source:", CLOSED_DEALS_SOURCE_PATH)

# COMMAND ----------
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

mql_df = (
    spark.read.option("header", True)
    .option("inferSchema", False)
    .csv(MQL_SOURCE_PATH)
)

print("Rows:", mql_df.count())
print("Columns:", len(mql_df.columns))
print("Column names:", mql_df.columns)
mql_df.printSchema()
display(mql_df.limit(20))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Grain and candidate key
# MAGIC
# MAGIC `mql_id` is the expected relationship key to Closed Deals, but discovery must prove
# MAGIC whether it is non-null and unique before it becomes the Bronze logical key.

# COMMAND ----------
if "mql_id" not in mql_df.columns:
    raise ValueError("Expected source column mql_id was not found.")

mql_key_profile = mql_df.agg(
    F.count("*").alias("row_count"),
    F.count("mql_id").alias("non_null_mql_id"),
    F.countDistinct("mql_id").alias("distinct_mql_id"),
    F.sum(F.when(F.col("mql_id").isNull(), 1).otherwise(0)).alias("null_mql_id"),
)
display(mql_key_profile)

mql_duplicates = (
    mql_df.groupBy("mql_id")
    .count()
    .where(F.col("count") > 1)
    .orderBy(F.desc("count"), "mql_id")
)

print("Duplicate mql_id groups:", mql_duplicates.count())
display(mql_duplicates.limit(50))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Null profile

# COMMAND ----------
def null_profile(dataframe: DataFrame) -> DataFrame:
    expressions = [
        F.sum(F.when(F.col(column).isNull(), 1).otherwise(0)).alias(column)
        for column in dataframe.columns
    ]
    aggregated = dataframe.agg(*expressions).first().asDict()
    total_rows = dataframe.count()
    rows = [
        {
            "column": column,
            "null_count": int(aggregated[column]),
            "null_pct": (
                float(aggregated[column]) / total_rows * 100.0 if total_rows else 0.0
            ),
        }
        for column in dataframe.columns
    ]
    return spark.createDataFrame(rows)


display(null_profile(mql_df).orderBy(F.desc("null_pct"), "column"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Distinct-value profile
# MAGIC
# MAGIC Useful for identifying low-cardinality categorical columns without asserting business
# MAGIC semantics prematurely.

# COMMAND ----------
distinct_profile_rows = []
for column in mql_df.columns:
    distinct_profile_rows.append(
        {
            "column": column,
            "distinct_count": mql_df.select(column).distinct().count(),
        }
    )

distinct_profile_df = spark.createDataFrame(distinct_profile_rows)
display(distinct_profile_df.orderBy("distinct_count", "column"))

# COMMAND ----------
low_cardinality_columns = [
    row["column"]
    for row in distinct_profile_df.where(F.col("distinct_count") <= 50).collect()
]

for column in low_cardinality_columns:
    print(f"Distinct values for {column}")
    display(
        mql_df.groupBy(column)
        .count()
        .orderBy(F.desc("count"), F.col(column).asc_nulls_last())
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Timestamp evidence
# MAGIC
# MAGIC The source is intentionally read as strings. This section only measures whether likely
# MAGIC timestamp/date columns parse consistently; semantic typing remains a downstream decision.

# COMMAND ----------
timestamp_candidates = [
    column
    for column in mql_df.columns
    if any(token in column.lower() for token in ("date", "time", "timestamp", "created"))
]

parse_profile_rows = []
for column in timestamp_candidates:
    parsed = F.to_timestamp(F.col(column))
    row = mql_df.agg(
        F.sum(F.when(F.col(column).isNotNull(), 1).otherwise(0)).alias("source_non_null"),
        F.sum(
            F.when(F.col(column).isNotNull() & parsed.isNull(), 1).otherwise(0)
        ).alias("parse_failures"),
        F.min(parsed).alias("min_parsed"),
        F.max(parsed).alias("max_parsed"),
    ).first()
    parse_profile_rows.append(
        {
            "column": column,
            "source_non_null": int(row["source_non_null"]),
            "parse_failures": int(row["parse_failures"]),
            "min_parsed": row["min_parsed"],
            "max_parsed": row["max_parsed"],
        }
    )

if parse_profile_rows:
    display(spark.createDataFrame(parse_profile_rows).orderBy("column"))
else:
    print("No timestamp-like source columns detected by name.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Relationship with Closed Deals
# MAGIC
# MAGIC Closed Deals already uses `mql_id` as its logical key. This section measures the funnel
# MAGIC relationship directly from the two source CSVs.

# COMMAND ----------
closed_deals_df = (
    spark.read.option("header", True)
    .option("inferSchema", False)
    .csv(CLOSED_DEALS_SOURCE_PATH)
)

if "mql_id" not in closed_deals_df.columns:
    raise ValueError("Closed Deals source does not contain expected column mql_id.")

mql_keys = mql_df.select("mql_id").where(F.col("mql_id").isNotNull()).distinct()
closed_keys = (
    closed_deals_df.select("mql_id").where(F.col("mql_id").isNotNull()).distinct()
)

relationship_summary = spark.createDataFrame(
    [
        {
            "metric": "mql_distinct_keys",
            "value": mql_keys.count(),
        },
        {
            "metric": "closed_deals_distinct_keys",
            "value": closed_keys.count(),
        },
        {
            "metric": "closed_deals_keys_found_in_mql",
            "value": closed_keys.join(mql_keys, "mql_id", "inner").count(),
        },
        {
            "metric": "closed_deals_keys_missing_from_mql",
            "value": closed_keys.join(mql_keys, "mql_id", "left_anti").count(),
        },
        {
            "metric": "mql_without_closed_deal",
            "value": mql_keys.join(closed_keys, "mql_id", "left_anti").count(),
        },
    ]
)
display(relationship_summary)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Discovery checklist for the next gate
# MAGIC
# MAGIC Record the observed evidence before approving requirements/design:
# MAGIC
# MAGIC - exact source columns and row count;
# MAGIC - whether `mql_id` is non-null and unique;
# MAGIC - nullability by column;
# MAGIC - duplicate behavior;
# MAGIC - low-cardinality source domains;
# MAGIC - timestamp parseability/range, if applicable;
# MAGIC - Closed Deals referential coverage through `mql_id`;
# MAGIC - whether the file behaves as an authoritative full snapshot;
# MAGIC - proposed Bronze write strategy and reprocessing semantics;
# MAGIC - minimum technical Data Quality rules justified by the evidence;
# MAGIC - any downstream Silver/Gold implications discovered from the source.
# MAGIC
# MAGIC Do not convert these observations into implementation decisions until the Discovery gate
# MAGIC has been reviewed.
