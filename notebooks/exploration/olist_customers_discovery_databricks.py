# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Customers — Bronze Discovery
# MAGIC Read-only discovery for `olist_customers_dataset.csv`.
# MAGIC No DDL, Bronze writes, or Control Plane writes.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_customers_dataset.csv",
    "Customers CSV source path",
)
SOURCE_PATH = dbutils.widgets.get("source_path").strip()
if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")

# COMMAND ----------

import json
from pathlib import PurePosixPath

from pyspark.sql import functions as F

EXPECTED_COLUMNS = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
]

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)
    .csv(SOURCE_PATH)
    .cache()
)
row_count = df.count()

print("source_path =", SOURCE_PATH)
print("row_count =", row_count)
print("columns =", df.columns)
df.printSchema()
display(df.limit(20))

# COMMAND ----------

# Physical file metadata.
parent = str(PurePosixPath(SOURCE_PATH).parent)
name = PurePosixPath(SOURCE_PATH).name
matches = [x for x in dbutils.fs.ls(parent) if x.name.rstrip("/") == name]
if not matches:
    raise FileNotFoundError(SOURCE_PATH)
info = matches[0]

file_metadata = {
    "path": info.path,
    "name": info.name,
    "size_bytes": int(info.size),
    "modification_time_ms": int(info.modificationTime),
}

# COMMAND ----------

# NULL / blank / distinct profile.
profile_rows = []
for column in df.columns:
    c = F.col(column)
    row = df.agg(
        F.sum(F.when(c.isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(F.when(c.isNotNull() & (F.trim(c) == ""), 1).otherwise(0)).alias(
            "blank_or_whitespace_count"
        ),
        F.countDistinct(c).alias("distinct_non_null"),
        F.sum(F.when(c.isNotNull() & (c != F.trim(c)), 1).otherwise(0)).alias(
            "trim_difference_rows"
        ),
    ).first()
    profile_rows.append(
        {
            "column": column,
            "null_count": int(row["null_count"] or 0),
            "null_rate_pct": (
                float(row["null_count"] or 0) / row_count * 100.0
                if row_count
                else 0.0
            ),
            "blank_or_whitespace_count": int(
                row["blank_or_whitespace_count"] or 0
            ),
            "distinct_non_null": int(row["distinct_non_null"] or 0),
            "trim_difference_rows": int(row["trim_difference_rows"] or 0),
        }
    )

profile_df = spark.createDataFrame(profile_rows)
display(profile_df.orderBy(F.desc("null_rate_pct"), "column"))

# COMMAND ----------

# Grain / candidate key: customer_id.
customer_id_stats = df.agg(
    F.countDistinct("customer_id").alias("distinct_count"),
    F.sum(F.when(F.col("customer_id").isNull(), 1).otherwise(0)).alias(
        "null_count"
    ),
).first()

customer_id_duplicates = (
    df.groupBy("customer_id")
    .count()
    .where(F.col("count") > 1)
    .orderBy(F.desc("count"), F.col("customer_id").asc_nulls_last())
    .cache()
)
customer_id_duplicate_groups = customer_id_duplicates.count()
customer_id_duplicate_excess = (
    customer_id_duplicates
    .agg(F.sum(F.col("count") - 1).alias("n"))
    .first()["n"]
    or 0
)
display(customer_id_duplicates.limit(50))

# COMMAND ----------

# customer_unique_id behavior / repeat-customer evidence for Silver.
unique_id_stats = df.agg(
    F.countDistinct("customer_unique_id").alias("distinct_count"),
    F.sum(F.when(F.col("customer_unique_id").isNull(), 1).otherwise(0)).alias(
        "null_count"
    ),
).first()

customers_per_unique = (
    df.where(F.col("customer_unique_id").isNotNull())
    .groupBy("customer_unique_id")
    .agg(F.countDistinct("customer_id").alias("customer_ids"))
    .cache()
)
repeat_unique_ids = customers_per_unique.where(F.col("customer_ids") > 1).cache()
repeat_unique_id_count = repeat_unique_ids.count()
max_customer_ids_per_unique = (
    customers_per_unique.agg(F.max("customer_ids").alias("n")).first()["n"] or 0
)

display(
    customers_per_unique
    .groupBy("customer_ids")
    .count()
    .orderBy("customer_ids")
)
display(repeat_unique_ids.orderBy(F.desc("customer_ids")).limit(100))

# COMMAND ----------

# Exact duplicate rows.
full_duplicates = (
    df.groupBy(*df.columns)
    .count()
    .where(F.col("count") > 1)
    .cache()
)
full_duplicate_groups = full_duplicates.count()
full_duplicate_excess = (
    full_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"] or 0
)
display(full_duplicates.orderBy(F.desc("count")).limit(50))

# COMMAND ----------

# ZIP preservation / shape. Observation only; not a DQ proposal.
zip_col = F.col("customer_zip_code_prefix")
zip_stats = df.agg(
    F.sum(F.when(zip_col.startswith("0"), 1).otherwise(0)).alias(
        "leading_zero_rows"
    ),
    F.sum(
        F.when(zip_col.isNotNull() & (~zip_col.rlike(r"^[0-9]+$")), 1).otherwise(0)
    ).alias("non_digit_rows"),
    F.sum(
        F.when(zip_col.isNotNull() & (F.length(zip_col) != 5), 1).otherwise(0)
    ).alias("non_5_char_rows"),
).first()

display(
    df.where(zip_col.startswith("0"))
    .select("customer_zip_code_prefix", "customer_city", "customer_state")
    .limit(50)
)

# COMMAND ----------

# City/state whitespace, case and basic encoding symptoms.
text_shape = {}
for column in ("customer_city", "customer_state"):
    c = F.col(column)
    row = df.agg(
        F.countDistinct(c).alias("distinct_raw"),
        F.countDistinct(F.lower(F.trim(c))).alias("distinct_trim_lower"),
        F.sum(F.when(c.isNotNull() & (c != F.trim(c)), 1).otherwise(0)).alias(
            "trim_difference_rows"
        ),
        F.sum(
            F.when(
                c.isNotNull()
                & (c.contains("\uFFFD") | c.contains("Ã") | c.contains("Â")),
                1,
            ).otherwise(0)
        ).alias("encoding_suspect_rows"),
    ).first()
    text_shape[column] = {k: int(v or 0) for k, v in row.asDict().items()}

display(
    df.groupBy("customer_state")
    .count()
    .orderBy(F.desc("count"), F.col("customer_state").asc_nulls_last())
)
display(
    df.groupBy("customer_state", "customer_city")
    .count()
    .orderBy(F.desc("count"))
    .limit(100)
)

# COMMAND ----------

# Deterministic content signature for later snapshot/re-run comparison.
hash_columns = [
    F.coalesce(F.col(c), F.lit("<NULL>")) for c in EXPECTED_COLUMNS
]
row_hash = F.xxhash64(*hash_columns)
sig = df.agg(
    F.count("*").alias("row_count"),
    F.countDistinct(row_hash).alias("distinct_row_hashes"),
    F.sum(row_hash.cast("decimal(38,0)")).alias("row_hash_sum"),
).first()

# COMMAND ----------

summary = {
    "source": {
        **file_metadata,
        "row_count": row_count,
        "actual_columns": df.columns,
        "missing_expected_columns": sorted(set(EXPECTED_COLUMNS) - set(df.columns)),
        "unexpected_columns": sorted(set(df.columns) - set(EXPECTED_COLUMNS)),
        "schema": {
            f.name: f.dataType.simpleString() for f in df.schema.fields
        },
    },
    "column_profile": {
        row["column"]: {
            "null_count": int(row["null_count"]),
            "null_rate_pct": float(row["null_rate_pct"]),
            "blank_or_whitespace_count": int(row["blank_or_whitespace_count"]),
            "distinct_non_null": int(row["distinct_non_null"]),
            "trim_difference_rows": int(row["trim_difference_rows"]),
        }
        for row in profile_df.collect()
    },
    "customer_id": {
        "null_count": int(customer_id_stats["null_count"] or 0),
        "distinct_count": int(customer_id_stats["distinct_count"] or 0),
        "duplicate_group_count": int(customer_id_duplicate_groups),
        "duplicate_row_excess": int(customer_id_duplicate_excess),
    },
    "customer_unique_id": {
        "null_count": int(unique_id_stats["null_count"] or 0),
        "distinct_count": int(unique_id_stats["distinct_count"] or 0),
        "unique_ids_with_multiple_customer_ids": int(repeat_unique_id_count),
        "max_customer_ids_per_unique_id": int(max_customer_ids_per_unique),
    },
    "full_row_duplicates": {
        "duplicate_group_count": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "zip_prefix": {k: int(v or 0) for k, v in zip_stats.asDict().items()},
    "city_state_text_shape": text_shape,
    "content_signature": {
        "row_count": int(sig["row_count"]),
        "distinct_row_hashes": int(sig["distinct_row_hashes"]),
        "row_hash_sum": str(sig["row_hash_sum"]),
    },
    "snapshot_frequency_evidence": (
        "Not provable from one static CSV. Requires process evidence or comparison "
        "with a later snapshot."
    ),
    "silver_discovery_boundary": (
        "customer_unique_id repeat-customer identity is evidence for Silver; "
        "do not normalize/deduplicate it in Bronze."
    ),
}

print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
