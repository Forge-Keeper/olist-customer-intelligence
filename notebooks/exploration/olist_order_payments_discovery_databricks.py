# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Order Payments — Bronze Discovery
# MAGIC
# MAGIC Read-only profiling for `olist_order_payments_dataset.csv`.
# MAGIC
# MAGIC This notebook does not create tables, persist Control Plane evidence, or
# MAGIC mutate source data. Its purpose is to establish the physical source
# MAGIC contract and candidate-key evidence before the Bronze contract is
# MAGIC implemented.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "",
    "Order Payments CSV source path",
)

# COMMAND ----------

SOURCE_PATH = dbutils.widgets.get("source_path").strip()
if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")

# COMMAND ----------

import json
from pathlib import PurePosixPath

from pyspark.sql import functions as F

EXPECTED_COLUMNS = [
    "order_id",
    "payment_sequential",
    "payment_type",
    "payment_installments",
    "payment_value",
]

CANDIDATE_KEY = ["order_id", "payment_sequential"]
NUMERIC_COLUMNS = [
    "payment_sequential",
    "payment_installments",
    "payment_value",
]

# COMMAND ----------

source = (
    spark.read.option("header", True)
    .option("inferSchema", False)
    .csv(SOURCE_PATH)
)

row_count = source.count()
actual_columns = source.columns
missing_columns = sorted(set(EXPECTED_COLUMNS) - set(actual_columns))
unexpected_columns = sorted(set(actual_columns) - set(EXPECTED_COLUMNS))

print("source_path =", SOURCE_PATH)
print("row_count =", row_count)
print("columns =", actual_columns)
print("missing_expected_columns =", missing_columns)
print("unexpected_columns =", unexpected_columns)
source.printSchema()
display(source.limit(20))

if missing_columns:
    raise ValueError(
        "Order Payments source is missing expected columns: "
        + ", ".join(missing_columns)
    )

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
for column in EXPECTED_COLUMNS:
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
    )
)

# COMMAND ----------

candidate_key_stats = source.agg(
    F.countDistinct(*CANDIDATE_KEY).alias("distinct_candidate_key"),
    F.sum(
        F.when(
            F.col("order_id").isNull()
            | F.col("payment_sequential").isNull(),
            1,
        ).otherwise(0)
    ).alias("null_candidate_key_rows"),
    F.sum(
        F.when(
            (F.trim(F.col("order_id")) == "")
            | (F.trim(F.col("payment_sequential")) == ""),
            1,
        ).otherwise(0)
    ).alias("blank_candidate_key_rows"),
).first()

candidate_key_duplicates = (
    source.groupBy(*CANDIDATE_KEY)
    .count()
    .where(F.col("count") > 1)
)
candidate_key_duplicate_groups = candidate_key_duplicates.count()
candidate_key_duplicate_excess = (
    candidate_key_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"]
    or 0
)

display(
    candidate_key_duplicates.orderBy(
        F.desc("count"),
        F.col("order_id").asc_nulls_last(),
        F.col("payment_sequential").asc_nulls_last(),
    ).limit(50)
)

# COMMAND ----------

full_duplicates = (
    source.groupBy(*EXPECTED_COLUMNS)
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

numeric_profile = {}
for column in NUMERIC_COLUMNS:
    raw = F.col(column)
    number = raw.cast("decimal(38,18)")
    stats = source.agg(
        F.sum(
            F.when(
                raw.isNotNull() & (F.trim(raw) != "") & number.isNull(),
                1,
            ).otherwise(0)
        ).alias("non_parseable_rows"),
        F.sum(F.when(number < 0, 1).otherwise(0)).alias("negative_rows"),
        F.sum(F.when(number == 0, 1).otherwise(0)).alias("zero_rows"),
        F.min(number).alias("min"),
        F.max(number).alias("max"),
    ).first()

    numeric_profile[column] = {
        "non_parseable_rows": int(stats["non_parseable_rows"] or 0),
        "negative_rows": int(stats["negative_rows"] or 0),
        "zero_rows": int(stats["zero_rows"] or 0),
        "min": str(stats["min"]) if stats["min"] is not None else None,
        "max": str(stats["max"]) if stats["max"] is not None else None,
    }

display(
    spark.createDataFrame(
        [{"column": column, **stats} for column, stats in numeric_profile.items()]
    )
)

# COMMAND ----------

integer_shape = {}
for column in ("payment_sequential", "payment_installments"):
    raw = F.col(column)
    integer = F.expr(f"try_cast({column} AS BIGINT)")
    decimal = F.expr(f"try_cast({column} AS DECIMAL(38,18))")
    stats = source.agg(
        F.sum(
            F.when(
                raw.isNotNull()
                & (F.trim(raw) != "")
                & integer.isNull(),
                1,
            ).otherwise(0)
        ).alias("non_integer_rows"),
        F.sum(
            F.when(
                integer.isNotNull() & decimal.isNotNull() & (decimal != integer),
                1,
            ).otherwise(0)
        ).alias("fractional_rows"),
        F.min(integer).alias("min"),
        F.max(integer).alias("max"),
    ).first()

    integer_shape[column] = {
        "non_integer_rows": int(stats["non_integer_rows"] or 0),
        "fractional_rows": int(stats["fractional_rows"] or 0),
        "min": int(stats["min"]) if stats["min"] is not None else None,
        "max": int(stats["max"]) if stats["max"] is not None else None,
    }

payment_type_profile = (
    source.groupBy("payment_type")
    .count()
    .orderBy(F.desc("count"), F.col("payment_type").asc_nulls_last())
)
display(payment_type_profile)

# COMMAND ----------

per_order = (
    source.groupBy("order_id")
    .agg(
        F.count("*").alias("row_count"),
        F.countDistinct("payment_sequential").alias("distinct_payment_sequences"),
        F.min(F.expr("try_cast(payment_sequential AS BIGINT)")).alias(
            "min_payment_sequence"
        ),
        F.max(F.expr("try_cast(payment_sequential AS BIGINT)")).alias(
            "max_payment_sequence"
        ),
    )
)

display(per_order.orderBy(F.desc("row_count"), F.col("order_id")).limit(50))

# COMMAND ----------

siblings = {x.name.rstrip("/"): x.path for x in dbutils.fs.ls(parent)}
orders_path = siblings.get("olist_orders_dataset.csv")

relationship_evidence = {
    "olist_orders_dataset.csv": {
        "checked": False,
        "path": orders_path,
        "missing_distinct_keys": None,
    }
}

if orders_path:
    orders = (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .csv(orders_path)
        .select(F.col("order_id").alias("foreign_key"))
        .where(F.col("foreign_key").isNotNull())
        .distinct()
    )
    local = (
        source.select(F.col("order_id").alias("local_key"))
        .where(F.col("local_key").isNotNull())
        .distinct()
    )
    missing = (
        local.join(
            orders,
            local.local_key == orders.foreign_key,
            "left_anti",
        ).count()
    )
    relationship_evidence["olist_orders_dataset.csv"] = {
        "checked": True,
        "path": orders_path,
        "missing_distinct_keys": int(missing),
    }

# COMMAND ----------

summary = {
    "source": file_metadata,
    "row_count": int(row_count),
    "actual_columns": actual_columns,
    "missing_expected_columns": missing_columns,
    "unexpected_columns": unexpected_columns,
    "column_profile": column_profile,
    "candidate_key": {
        "columns": CANDIDATE_KEY,
        "distinct_count": int(candidate_key_stats["distinct_candidate_key"] or 0),
        "null_rows": int(candidate_key_stats["null_candidate_key_rows"] or 0),
        "blank_rows": int(candidate_key_stats["blank_candidate_key_rows"] or 0),
        "duplicate_groups": int(candidate_key_duplicate_groups),
        "duplicate_row_excess": int(candidate_key_duplicate_excess),
    },
    "full_duplicates": {
        "duplicate_groups": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "numeric_profile": numeric_profile,
    "integer_shape": integer_shape,
    "payment_type_counts": {
        str(row["payment_type"]): int(row["count"])
        for row in payment_type_profile.collect()
    },
    "relationships": relationship_evidence,
}

print(json.dumps(summary, indent=2, sort_keys=True, default=str))

# MAGIC %md
# MAGIC ## Decision gate
# MAGIC
# MAGIC Do not implement the persisted Bronze key/nullability rules from dataset
# MAGIC documentation alone. Use the emitted source profile to confirm:
# MAGIC
# MAGIC 1. physical columns and source cardinality;
# MAGIC 2. completeness and uniqueness of `(order_id, payment_sequential)`;
# MAGIC 3. parseability and integer/domain shape of payment sequence/installments;
# MAGIC 4. parseability and sign/zero behavior of `payment_value`;
# MAGIC 5. observed `payment_type` values without prematurely enforcing a domain;
# MAGIC 6. whether exact duplicates or anomalies must remain source-faithful;
# MAGIC 7. relationship evidence to Orders as observation only — cross-dataset
# MAGIC    coverage is a Silver concern unless separately approved.
