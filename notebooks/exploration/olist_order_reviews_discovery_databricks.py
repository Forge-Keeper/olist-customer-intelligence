# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Order Reviews — Bronze Discovery
# MAGIC
# MAGIC Read-only profiling for the physical Order Reviews CSV source.
# MAGIC
# MAGIC This notebook deliberately does not encode a persisted Bronze schema,
# MAGIC candidate key, business domain, or cross-dataset constraint before the
# MAGIC physical source has been inspected. It does not create tables, persist
# MAGIC Control Plane evidence, or mutate source data.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "",
    "Order Reviews CSV source path",
)

# COMMAND ----------

SOURCE_PATH = dbutils.widgets.get("source_path").strip()
if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")

# COMMAND ----------

import json
from pathlib import PurePosixPath

from pyspark.sql import functions as F

source = (
    spark.read.option("header", True)
    .option("inferSchema", False)
    .option("multiLine", True)
    .option("escape", '"')
    .csv(SOURCE_PATH)
)

row_count = source.count()
actual_columns = source.columns

print("source_path =", SOURCE_PATH)
print("row_count =", row_count)
print("columns =", actual_columns)
source.printSchema()
display(source.limit(20))

# COMMAND ----------

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

print(json.dumps(file_metadata, indent=2, sort_keys=True))

# COMMAND ----------

column_profile = {}
for column in actual_columns:
    value = F.col(column)
    row = source.agg(
        F.sum(F.when(value.isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(
            F.when(
                value.isNotNull() & (F.trim(value) == ""),
                1,
            ).otherwise(0)
        ).alias("blank_count"),
        F.sum(
            F.when(
                value.isNotNull() & (value != F.trim(value)),
                1,
            ).otherwise(0)
        ).alias("trim_difference_rows"),
        F.countDistinct(value).alias("distinct_non_null"),
    ).first()

    column_profile[column] = {
        "null_count": int(row["null_count"] or 0),
        "blank_count": int(row["blank_count"] or 0),
        "trim_difference_rows": int(row["trim_difference_rows"] or 0),
        "distinct_non_null": int(row["distinct_non_null"] or 0),
    }

display(
    spark.createDataFrame(
        [{"column": column, **stats} for column, stats in column_profile.items()]
    ).orderBy("column")
)

# COMMAND ----------

full_duplicates = (
    source.groupBy(*actual_columns)
    .count()
    .where(F.col("count") > 1)
)
full_duplicate_groups = full_duplicates.count()
full_duplicate_excess = (
    full_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"]
    or 0
)

display(full_duplicates.orderBy(F.desc("count")).limit(50))

# COMMAND ----------

# Candidate-key evidence is observational only. Every single column is tested for
# completeness and uniqueness so the persisted key can be proposed from source
# evidence instead of dataset lore.
single_column_key_candidates = []
for column, stats in column_profile.items():
    if (
        row_count > 0
        and stats["null_count"] == 0
        and stats["blank_count"] == 0
        and stats["distinct_non_null"] == row_count
    ):
        single_column_key_candidates.append(column)

print("single_column_key_candidates =", single_column_key_candidates)

# COMMAND ----------

# Low-cardinality distributions help distinguish observed values from enforceable
# domains. No enum is made blocking by this notebook.
low_cardinality_columns = [
    column
    for column, stats in column_profile.items()
    if stats["distinct_non_null"] <= 50
]

distributions = {}
for column in low_cardinality_columns:
    counts = (
        source.groupBy(column)
        .count()
        .orderBy(F.desc("count"), F.col(column).asc_nulls_last())
    )
    distributions[column] = {
        str(row[column]): int(row["count"])
        for row in counts.limit(100).collect()
    }
    display(counts.limit(100))

# COMMAND ----------

# Parseability probes remain evidence only. Timestamp parsing is attempted for
# columns whose physical names suggest temporal semantics; decimal/integer
# parsing is attempted for every column so unexpected numeric shapes are visible.
temporal_name_tokens = ("date", "time", "timestamp", "created", "answered", "review")
temporal_columns = [
    column
    for column in actual_columns
    if any(token in column.lower() for token in temporal_name_tokens)
]

parseability = {}
for column in actual_columns:
    raw = F.col(column)
    decimal_value = F.expr(f"try_cast(`{column}` AS DECIMAL(38,18))")
    integer_value = F.expr(f"try_cast(`{column}` AS BIGINT)")

    expressions = [
        F.sum(
            F.when(
                raw.isNotNull() & (F.trim(raw) != "") & decimal_value.isNull(),
                1,
            ).otherwise(0)
        ).alias("non_decimal_rows"),
        F.sum(
            F.when(
                raw.isNotNull() & (F.trim(raw) != "") & integer_value.isNull(),
                1,
            ).otherwise(0)
        ).alias("non_integer_rows"),
    ]

    if column in temporal_columns:
        timestamp_value = F.expr(f"try_cast(`{column}` AS TIMESTAMP)")
        expressions.append(
            F.sum(
                F.when(
                    raw.isNotNull()
                    & (F.trim(raw) != "")
                    & timestamp_value.isNull(),
                    1,
                ).otherwise(0)
            ).alias("non_timestamp_rows")
        )

    stats = source.agg(*expressions).first().asDict()
    parseability[column] = {
        key: int(value or 0)
        for key, value in stats.items()
    }

# COMMAND ----------

# Cross-dataset evidence is observational. If the sibling Orders snapshot exists
# and both datasets expose order_id, report coverage but do not enforce an FK.
siblings = {x.name.rstrip("/"): x.path for x in dbutils.fs.ls(parent)}
orders_path = siblings.get("olist_orders_dataset.csv")
relationship_evidence = {
    "olist_orders_dataset.csv": {
        "checked": False,
        "path": orders_path,
        "missing_distinct_order_ids": None,
    }
}

if orders_path and "order_id" in actual_columns:
    orders = (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .csv(orders_path)
    )
    if "order_id" in orders.columns:
        sibling_keys = (
            orders.select(F.col("order_id").alias("foreign_key"))
            .where(F.col("foreign_key").isNotNull())
            .distinct()
        )
        local_keys = (
            source.select(F.col("order_id").alias("local_key"))
            .where(F.col("local_key").isNotNull())
            .distinct()
        )
        missing = (
            local_keys.join(
                sibling_keys,
                local_keys.local_key == sibling_keys.foreign_key,
                "left_anti",
            ).count()
        )
        relationship_evidence["olist_orders_dataset.csv"] = {
            "checked": True,
            "path": orders_path,
            "missing_distinct_order_ids": int(missing),
        }

# COMMAND ----------

summary = {
    "source": file_metadata,
    "row_count": int(row_count),
    "actual_columns": actual_columns,
    "column_profile": column_profile,
    "single_column_key_candidates": single_column_key_candidates,
    "full_duplicates": {
        "duplicate_groups": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "low_cardinality_distributions": distributions,
    "parseability": parseability,
    "relationships": relationship_evidence,
}

print(json.dumps(summary, indent=2, sort_keys=True, default=str))

# MAGIC %md
# MAGIC ## Decision gate
# MAGIC
# MAGIC Do not implement persisted Bronze constraints from public Olist schema
# MAGIC knowledge alone. Use the emitted profile to decide:
# MAGIC
# MAGIC 1. exact physical schema and source cardinality;
# MAGIC 2. null/blank/trim behavior for every field;
# MAGIC 3. exact-duplicate behavior;
# MAGIC 4. candidate natural key(s) supported by completeness + uniqueness;
# MAGIC 5. observed distributions without prematurely turning them into enums;
# MAGIC 6. timestamp/numeric parseability only where source evidence supports it;
# MAGIC 7. relationship evidence to sibling datasets as observation only unless a
# MAGIC    separate Bronze requirement explicitly approves cross-dataset blocking.
