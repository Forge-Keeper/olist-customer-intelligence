# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Sellers — Bronze Discovery
# MAGIC
# MAGIC Read-only discovery for `olist_sellers_dataset.csv`.
# MAGIC
# MAGIC Goals:
# MAGIC - observe the physical source schema and row count;
# MAGIC - profile nulls, blanks, distinctness and whitespace behavior;
# MAGIC - test `seller_id` only as a candidate grain/key based on source evidence;
# MAGIC - inspect ZIP, city and state source-value shape without normalizing them;
# MAGIC - identify exact duplicate rows and compute a deterministic snapshot signature;
# MAGIC - collect optional relationship evidence to sibling Olist files when present;
# MAGIC - do not create Bronze tables, write Control Plane records, or propose DQ rules here.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "",
    "Sellers CSV source path",
)

# COMMAND ----------

SOURCE_PATH = dbutils.widgets.get("source_path").strip()
if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")

# COMMAND ----------

import json
from pathlib import PurePosixPath

from pyspark.sql import functions as F


df = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)
    .csv(SOURCE_PATH)
)
row_count = df.count()

print("source_path =", SOURCE_PATH)
print("row_count =", row_count)
print("columns =", df.columns)
df.printSchema()
display(df.limit(20))

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

# COMMAND ----------

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

seller_id_evidence = None
seller_id_duplicates = None
if "seller_id" in df.columns:
    seller_id_stats = df.agg(
        F.countDistinct("seller_id").alias("distinct_count"),
        F.sum(F.when(F.col("seller_id").isNull(), 1).otherwise(0)).alias(
            "null_count"
        ),
        F.sum(
            F.when(
                F.col("seller_id").isNotNull()
                & (F.trim(F.col("seller_id")) == ""),
                1,
            ).otherwise(0)
        ).alias("blank_count"),
    ).first()

    seller_id_duplicates = (
        df.groupBy("seller_id")
        .count()
        .where(F.col("count") > 1)
        .orderBy(F.desc("count"), F.col("seller_id").asc_nulls_last())
    )
    duplicate_group_count = seller_id_duplicates.count()
    duplicate_row_excess = (
        seller_id_duplicates
        .agg(F.sum(F.col("count") - 1).alias("n"))
        .first()["n"]
        or 0
    )

    seller_id_evidence = {
        "null_count": int(seller_id_stats["null_count"] or 0),
        "blank_count": int(seller_id_stats["blank_count"] or 0),
        "distinct_count": int(seller_id_stats["distinct_count"] or 0),
        "duplicate_group_count": int(duplicate_group_count),
        "duplicate_row_excess": int(duplicate_row_excess),
    }
    display(seller_id_duplicates.limit(50))
else:
    print("seller_id column not present; candidate-key analysis skipped.")

# COMMAND ----------

full_duplicates = (
    df.groupBy(*df.columns)
    .count()
    .where(F.col("count") > 1)
)
full_duplicate_groups = full_duplicates.count()
full_duplicate_excess = (
    full_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"] or 0
)
display(full_duplicates.orderBy(F.desc("count")).limit(50))

# COMMAND ----------

zip_evidence = None
if "seller_zip_code_prefix" in df.columns:
    zip_col = F.col("seller_zip_code_prefix")
    zip_stats = df.agg(
        F.countDistinct(zip_col).alias("distinct_count"),
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
    zip_evidence = {k: int(v or 0) for k, v in zip_stats.asDict().items()}

    display(
        df.where(zip_col.startswith("0"))
        .select(
            *[
                c
                for c in (
                    "seller_zip_code_prefix",
                    "seller_city",
                    "seller_state",
                )
                if c in df.columns
            ]
        )
        .limit(50)
    )
else:
    print("seller_zip_code_prefix column not present; ZIP-shape analysis skipped.")

# COMMAND ----------

text_shape = {}
for column in ("seller_city", "seller_state"):
    if column not in df.columns:
        continue
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

if "seller_state" in df.columns:
    display(
        df.groupBy("seller_state")
        .count()
        .orderBy(F.desc("count"), F.col("seller_state").asc_nulls_last())
    )

if {"seller_state", "seller_city"}.issubset(df.columns):
    display(
        df.groupBy("seller_state", "seller_city")
        .count()
        .orderBy(F.desc("count"))
        .limit(100)
    )

# COMMAND ----------

relationship_evidence = {
    "order_items_checked": False,
    "order_items_path": None,
    "order_items_rows": None,
    "distinct_order_item_seller_ids": None,
    "order_item_seller_ids_missing_from_sellers": None,
    "seller_ids_not_used_by_order_items": None,
}

order_items_name = "olist_order_items_dataset.csv"
order_items_candidates = [
    x for x in dbutils.fs.ls(parent) if x.name.rstrip("/") == order_items_name
]

if order_items_candidates and "seller_id" in df.columns:
    order_items_path = order_items_candidates[0].path
    order_items_df = (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .csv(order_items_path)
    )

    if "seller_id" in order_items_df.columns:
        seller_ids_df = df.select("seller_id").where(F.col("seller_id").isNotNull()).distinct()
        order_item_seller_ids_df = (
            order_items_df
            .select("seller_id")
            .where(F.col("seller_id").isNotNull())
            .distinct()
        )

        missing_from_sellers = order_item_seller_ids_df.join(
            seller_ids_df,
            on="seller_id",
            how="left_anti",
        )
        unused_by_order_items = seller_ids_df.join(
            order_item_seller_ids_df,
            on="seller_id",
            how="left_anti",
        )

        relationship_evidence = {
            "order_items_checked": True,
            "order_items_path": order_items_path,
            "order_items_rows": int(order_items_df.count()),
            "distinct_order_item_seller_ids": int(order_item_seller_ids_df.count()),
            "order_item_seller_ids_missing_from_sellers": int(missing_from_sellers.count()),
            "seller_ids_not_used_by_order_items": int(unused_by_order_items.count()),
        }

        display(missing_from_sellers.limit(50))
        display(unused_by_order_items.limit(50))
    else:
        print("Sibling order_items file exists but has no seller_id column.")
else:
    print("Sibling order_items relationship evidence skipped: source file or seller_id unavailable.")

# COMMAND ----------

hash_columns = [F.coalesce(F.col(c), F.lit("<NULL>")) for c in df.columns]
if hash_columns:
    row_hash = F.xxhash64(*hash_columns)
    sig = df.agg(
        F.count("*").alias("row_count"),
        F.countDistinct(row_hash).alias("distinct_row_hashes"),
        F.sum(row_hash.cast("decimal(38,0)")).alias("row_hash_sum"),
    ).first()
    content_signature = {
        "row_count": int(sig["row_count"]),
        "distinct_row_hashes": int(sig["distinct_row_hashes"]),
        "row_hash_sum": str(sig["row_hash_sum"]),
    }
else:
    content_signature = {
        "row_count": row_count,
        "distinct_row_hashes": 0,
        "row_hash_sum": None,
    }

# COMMAND ----------

summary = {
    "source": {
        **file_metadata,
        "row_count": row_count,
        "actual_columns": df.columns,
        "column_count": len(df.columns),
        "schema": {f.name: f.dataType.simpleString() for f in df.schema.fields},
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
    "seller_id_candidate_key": seller_id_evidence,
    "full_row_duplicates": {
        "duplicate_group_count": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "zip_prefix": zip_evidence,
    "city_state_text_shape": text_shape,
    "order_items_relationship_evidence": relationship_evidence,
    "content_signature": content_signature,
    "snapshot_frequency_evidence": (
        "Not provable from one static CSV. Requires process evidence or comparison "
        "with a later snapshot."
    ),
    "discovery_boundary": (
        "This notebook records source evidence only. Grain, key, write strategy, "
        "Data Quality contract and physical layout remain decisions for later gates."
    ),
}

print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
