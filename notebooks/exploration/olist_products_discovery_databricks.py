# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Products — Bronze Discovery
# MAGIC
# MAGIC Read-only profiling for `olist_products_dataset.csv`. This notebook does
# MAGIC not create tables, write Control Plane evidence, or mutate source data.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "",
    "Products CSV source path",
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
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]
NUMERIC_COLUMNS = EXPECTED_COLUMNS[2:]

df = (
    spark.read.option("header", True)
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

profile = {}
for column in df.columns:
    value = F.col(column)
    row = df.agg(
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
    profile[column] = {
        "null_count": int(row["null_count"] or 0),
        "null_rate_pct": (
            float(row["null_count"] or 0) / row_count * 100.0
            if row_count
            else 0.0
        ),
        "blank_count": int(row["blank_count"] or 0),
        "trim_difference_rows": int(row["trim_difference_rows"] or 0),
        "distinct_non_null": int(row["distinct_non_null"] or 0),
    }

display(spark.createDataFrame([{"column": k, **v} for k, v in profile.items()]))

# COMMAND ----------

key_stats = df.agg(
    F.countDistinct("product_id").alias("distinct_count"),
    F.sum(F.when(F.col("product_id").isNull(), 1).otherwise(0)).alias(
        "null_count"
    ),
    F.sum(
        F.when(
            F.col("product_id").isNotNull()
            & (F.trim("product_id") == ""),
            1,
        ).otherwise(0)
    ).alias("blank_count"),
).first()

key_duplicates = df.groupBy("product_id").count().where(F.col("count") > 1)
key_duplicate_groups = key_duplicates.count()
key_duplicate_excess = (
    key_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"]
    or 0
)
display(key_duplicates.orderBy(F.desc("count")).limit(50))

full_duplicates = df.groupBy(*df.columns).count().where(F.col("count") > 1)
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
    number = raw.cast("double")
    stats = df.agg(
        F.sum(
            F.when(
                raw.isNotNull() & (F.trim(raw) != "") & number.isNull(),
                1,
            ).otherwise(0)
        ).alias("non_parseable_rows"),
        F.sum(F.when(number < 0, 1).otherwise(0)).alias("negative_rows"),
        F.sum(F.when(number == 0, 1).otherwise(0)).alias("zero_rows"),
        F.sum(
            F.when(
                number.isNotNull() & (number != F.floor(number)),
                1,
            ).otherwise(0)
        ).alias("fractional_rows"),
        F.min(number).alias("min"),
        F.max(number).alias("max"),
        F.avg(number).alias("mean"),
    ).first()
    values = df.select(number.alias("value")).where(number.isNotNull())
    quantiles = values.approxQuantile(
        "value",
        [0.25, 0.5, 0.75, 0.95, 0.99],
        0.0,
    )
    numeric_profile[column] = {
        "non_parseable_rows": int(stats["non_parseable_rows"] or 0),
        "negative_rows": int(stats["negative_rows"] or 0),
        "zero_rows": int(stats["zero_rows"] or 0),
        "fractional_rows": int(stats["fractional_rows"] or 0),
        "min": float(stats["min"]) if stats["min"] is not None else None,
        "max": float(stats["max"]) if stats["max"] is not None else None,
        "mean": float(stats["mean"]) if stats["mean"] is not None else None,
        "p25": quantiles[0],
        "p50": quantiles[1],
        "p75": quantiles[2],
        "p95": quantiles[3],
        "p99": quantiles[4],
    }

display(
    spark.createDataFrame(
        [{"column": k, **v} for k, v in numeric_profile.items()]
    )
)

# COMMAND ----------

category = F.col("product_category_name")
category_stats = df.agg(
    F.countDistinct(category).alias("distinct_raw"),
    F.countDistinct(F.lower(F.trim(category))).alias("distinct_trim_lower"),
    F.sum(
        F.when(
            category.isNotNull() & (category != F.trim(category)),
            1,
        ).otherwise(0)
    ).alias("trim_difference_rows"),
    F.sum(
        F.when(
            category.isNotNull()
            & (
                category.contains("\uFFFD")
                | category.contains("Ã")
                | category.contains("Â")
            ),
            1,
        ).otherwise(0)
    ).alias("encoding_suspect_rows"),
).first()

display(
    df.groupBy("product_category_name")
    .count()
    .orderBy(F.desc("count"), F.col("product_category_name").asc_nulls_last())
)

# COMMAND ----------

descriptive_columns = [
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
]
physical_columns = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

null_pattern = (
    df.select(
        *[
            F.col(column).isNull().cast("int").alias(column)
            for column in descriptive_columns + physical_columns
        ]
    )
    .groupBy(*(descriptive_columns + physical_columns))
    .count()
    .orderBy(F.desc("count"))
)
display(null_pattern)

display(
    df.where(F.col("product_weight_g").cast("double") == 0)
    .select("product_id", *descriptive_columns, *physical_columns)
    .orderBy("product_id")
)

display(
    df.where(F.expr(" OR ".join(f"{c} IS NULL" for c in physical_columns)))
    .select("product_id", *descriptive_columns, *physical_columns)
    .orderBy("product_id")
)

# COMMAND ----------

siblings = {x.name.rstrip("/"): x.path for x in dbutils.fs.ls(parent)}
relationship_evidence = {}

order_items_path = siblings.get("olist_order_items_dataset.csv")
if order_items_path:
    order_items = (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .csv(order_items_path)
    )
    if "product_id" in order_items.columns:
        product_ids = (
            df.select("product_id")
            .where(F.col("product_id").isNotNull())
            .distinct()
        )
        order_item_ids = (
            order_items.select("product_id")
            .where(F.col("product_id").isNotNull())
            .distinct()
        )
        relationship_evidence["order_items"] = {
            "path": order_items_path,
            "row_count": int(order_items.count()),
            "distinct_product_ids": int(order_item_ids.count()),
            "product_ids_missing_from_products": int(
                order_item_ids.join(product_ids, "product_id", "left_anti").count()
            ),
            "products_not_used_by_order_items": int(
                product_ids.join(order_item_ids, "product_id", "left_anti").count()
            ),
        }

translation_path = siblings.get("product_category_name_translation.csv")
if translation_path:
    translation = (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .csv(translation_path)
    )
    product_categories = (
        df.select("product_category_name")
        .where(F.col("product_category_name").isNotNull())
        .distinct()
    )
    translation_categories = (
        translation.select("product_category_name")
        .where(F.col("product_category_name").isNotNull())
        .distinct()
    )
    missing_translations = product_categories.join(
        translation_categories,
        "product_category_name",
        "left_anti",
    )
    relationship_evidence["category_translation"] = {
        "path": translation_path,
        "row_count": int(translation.count()),
        "distinct_categories": int(translation_categories.count()),
        "product_categories_missing_translation": int(missing_translations.count()),
        "missing_translation_values": [
            row["product_category_name"]
            for row in missing_translations.orderBy("product_category_name").collect()
        ],
        "translations_not_used_by_products": int(
            translation_categories.join(
                product_categories,
                "product_category_name",
                "left_anti",
            ).count()
        ),
    }

# COMMAND ----------

hash_columns = [F.coalesce(F.col(c), F.lit("<NULL>")) for c in df.columns]
row_hash = F.xxhash64(*hash_columns)
signature = df.agg(
    F.count("*").alias("row_count"),
    F.countDistinct(row_hash).alias("distinct_row_hashes"),
    F.sum(row_hash.cast("decimal(38,0)")).alias("row_hash_sum"),
).first()

summary = {
    "source": {
        **file_metadata,
        "row_count": row_count,
        "actual_columns": df.columns,
        "missing_expected_columns": sorted(
            set(EXPECTED_COLUMNS) - set(df.columns)
        ),
        "unexpected_columns": sorted(set(df.columns) - set(EXPECTED_COLUMNS)),
        "schema": {
            field.name: field.dataType.simpleString() for field in df.schema.fields
        },
    },
    "column_profile": profile,
    "product_id": {
        "null_count": int(key_stats["null_count"] or 0),
        "blank_count": int(key_stats["blank_count"] or 0),
        "distinct_count": int(key_stats["distinct_count"] or 0),
        "duplicate_group_count": int(key_duplicate_groups),
        "duplicate_row_excess": int(key_duplicate_excess),
    },
    "full_row_duplicates": {
        "duplicate_group_count": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "numeric_profile": numeric_profile,
    "category_shape": {
        key: int(value or 0) for key, value in category_stats.asDict().items()
    },
    "relationships": relationship_evidence,
    "content_signature": {
        "row_count": int(signature["row_count"]),
        "distinct_row_hashes": int(signature["distinct_row_hashes"]),
        "row_hash_sum": str(signature["row_hash_sum"]),
    },
    "snapshot_cadence_evidence": (
        "One physical CSV snapshot observed; no business date or refresh cadence "
        "proven."
    ),
}

print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
