# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Order Reviews — Candidate Key Discovery
# MAGIC
# MAGIC Read-only follow-up profiling. This notebook exists because neither
# MAGIC `review_id` nor `order_id` is unique in the physical source. It tests
# MAGIC complete two-column combinations and reports duplicate multiplicity for
# MAGIC the identifier columns. No tables are written and no Bronze rule is
# MAGIC persisted.

# COMMAND ----------

dbutils.widgets.text("source_path", "", "Order Reviews CSV source path")
SOURCE_PATH = dbutils.widgets.get("source_path").strip()
if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")

# COMMAND ----------

import itertools
import json
from pyspark.sql import functions as F

source = (
    spark.read.option("header", True)
    .option("inferSchema", False)
    .option("multiLine", True)
    .option("escape", '"')
    .csv(SOURCE_PATH)
)
row_count = source.count()

# COMMAND ----------

column_profile = {}
for column in source.columns:
    value = F.col(column)
    row = source.agg(
        F.sum(F.when(value.isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(
            F.when(value.isNotNull() & (F.trim(value) == ""), 1).otherwise(0)
        ).alias("blank_count"),
        F.countDistinct(value).alias("distinct_non_null"),
    ).first()
    column_profile[column] = {
        "null_count": int(row["null_count"] or 0),
        "blank_count": int(row["blank_count"] or 0),
        "distinct_non_null": int(row["distinct_non_null"] or 0),
    }

complete_columns = [
    column
    for column, stats in column_profile.items()
    if stats["null_count"] == 0 and stats["blank_count"] == 0
]

pair_key_profile = {}
pair_key_candidates = []
for left, right in itertools.combinations(complete_columns, 2):
    duplicate_groups = (
        source.groupBy(left, right)
        .count()
        .where(F.col("count") > 1)
        .count()
    )
    distinct_count = source.select(left, right).distinct().count()
    pair_key_profile[f"{left}+{right}"] = {
        "distinct_count": int(distinct_count),
        "duplicate_groups": int(duplicate_groups),
    }
    if distinct_count == row_count and duplicate_groups == 0:
        pair_key_candidates.append([left, right])

# COMMAND ----------

identifier_duplicate_profile = {}
for column in [c for c in ("review_id", "order_id") if c in source.columns]:
    duplicates = source.groupBy(column).count().where(F.col("count") > 1)
    stats = duplicates.agg(
        F.count("*").alias("duplicate_groups"),
        F.sum(F.col("count") - 1).alias("duplicate_row_excess"),
        F.max("count").alias("max_multiplicity"),
    ).first()
    identifier_duplicate_profile[column] = {
        "duplicate_groups": int(stats["duplicate_groups"] or 0),
        "duplicate_row_excess": int(stats["duplicate_row_excess"] or 0),
        "max_multiplicity": int(stats["max_multiplicity"] or 1),
    }
    display(duplicates.orderBy(F.desc("count"), F.col(column)).limit(50))

# COMMAND ----------

summary = {
    "row_count": int(row_count),
    "complete_columns": complete_columns,
    "pair_key_candidates": pair_key_candidates,
    "pair_key_profile": pair_key_profile,
    "identifier_duplicate_profile": identifier_duplicate_profile,
}
print(json.dumps(summary, indent=2, sort_keys=True))
