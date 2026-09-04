# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Product Category Name Translation — Bronze Discovery
# MAGIC
# MAGIC Read-only profiling for `product_category_name_translation.csv` and its
# MAGIC observed relationship to Products. This notebook does not create tables,
# MAGIC write Control Plane evidence, cache/persist data, or mutate source data.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/product_category_name_translation.csv",
    "Product Category Translation CSV source path",
)
dbutils.widgets.text(
    "products_source_path",
    "/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_products_dataset.csv",
    "Olist Products CSV source path",
)

# COMMAND ----------

SOURCE_PATH = dbutils.widgets.get("source_path").strip()
PRODUCTS_SOURCE_PATH = dbutils.widgets.get("products_source_path").strip()

if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")
if not PRODUCTS_SOURCE_PATH:
    raise ValueError("Set products_source_path before running Discovery.")

# COMMAND ----------

import json
from pathlib import PurePosixPath

from pyspark.sql import functions as F


def file_metadata(path: str) -> dict[str, object]:
    parent = str(PurePosixPath(path).parent)
    name = PurePosixPath(path).name
    matches = [item for item in dbutils.fs.ls(parent) if item.name.rstrip("/") == name]
    if not matches:
        raise FileNotFoundError(path)
    info = matches[0]
    return {
        "path": info.path,
        "name": info.name,
        "size_bytes": int(info.size),
        "modification_time_ms": int(info.modificationTime),
    }


def read_csv(path: str):
    return spark.read.option("header", True).option("inferSchema", False).csv(path)


translation = read_csv(SOURCE_PATH)
products = read_csv(PRODUCTS_SOURCE_PATH)
translation_row_count = translation.count()

print("source_path =", SOURCE_PATH)
print("row_count =", translation_row_count)
print("columns =", translation.columns)
translation.printSchema()
display(translation.limit(20))

# COMMAND ----------

profile = {}
for column in translation.columns:
    value = F.col(column)
    stats = translation.agg(
        F.sum(F.when(value.isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(
            F.when(value.isNotNull() & (F.trim(value) == ""), 1).otherwise(0)
        ).alias("blank_count"),
        F.sum(
            F.when(value.isNotNull() & (value != F.trim(value)), 1).otherwise(0)
        ).alias("trim_difference_rows"),
        F.countDistinct(value).alias("distinct_non_null"),
        F.countDistinct(F.lower(F.trim(value))).alias("distinct_trim_lower"),
    ).first()
    profile[column] = {
        "null_count": int(stats["null_count"] or 0),
        "null_rate_pct": (
            float(stats["null_count"] or 0) / translation_row_count * 100.0
            if translation_row_count
            else 0.0
        ),
        "blank_count": int(stats["blank_count"] or 0),
        "trim_difference_rows": int(stats["trim_difference_rows"] or 0),
        "distinct_non_null": int(stats["distinct_non_null"] or 0),
        "distinct_trim_lower": int(stats["distinct_trim_lower"] or 0),
    }

display(
    spark.createDataFrame(
        [{"column": column, **stats} for column, stats in profile.items()]
    ).orderBy("column")
)

# COMMAND ----------

full_duplicates = (
    translation.groupBy(*translation.columns).count().where(F.col("count") > 1)
)
full_duplicate_groups = full_duplicates.count()
full_duplicate_excess = (
    full_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"] or 0
)
display(full_duplicates.orderBy(F.desc("count")).limit(100))

# COMMAND ----------

candidate_key_evidence = {}
if "product_category_name" in translation.columns:
    key = F.col("product_category_name")
    key_stats = translation.agg(
        F.countDistinct(key).alias("distinct_count"),
        F.sum(F.when(key.isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(
            F.when(key.isNotNull() & (F.trim(key) == ""), 1).otherwise(0)
        ).alias("blank_count"),
    ).first()
    key_duplicates = (
        translation.groupBy("product_category_name")
        .count()
        .where(F.col("count") > 1)
    )
    duplicate_groups = key_duplicates.count()
    duplicate_excess = (
        key_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"]
        or 0
    )
    candidate_key_evidence = {
        "column": "product_category_name",
        "distinct_count": int(key_stats["distinct_count"] or 0),
        "null_count": int(key_stats["null_count"] or 0),
        "blank_count": int(key_stats["blank_count"] or 0),
        "duplicate_group_count": int(duplicate_groups),
        "duplicate_row_excess": int(duplicate_excess),
    }
    display(key_duplicates.orderBy(F.desc("count"), "product_category_name"))

# COMMAND ----------

encoding_profile = []
for column in translation.columns:
    value = F.col(column)
    stats = translation.agg(
        F.sum(
            F.when(
                value.isNotNull()
                & (
                    value.contains("\uFFFD")
                    | value.contains("Ã")
                    | value.contains("Â")
                ),
                1,
            ).otherwise(0)
        ).alias("encoding_suspect_rows")
    ).first()
    encoding_profile.append(
        {
            "column": column,
            "encoding_suspect_rows": int(stats["encoding_suspect_rows"] or 0),
        }
    )

display(spark.createDataFrame(encoding_profile).orderBy("column"))

# COMMAND ----------

for column in translation.columns:
    display(
        translation.groupBy(column)
        .count()
        .orderBy(F.desc("count"), F.col(column).asc_nulls_last())
        .limit(200)
    )

# COMMAND ----------

relationship_evidence = {
    "products_source_path_supplied": True,
    "products_source": {
        **file_metadata(PRODUCTS_SOURCE_PATH),
        "row_count": int(products.count()),
        "columns": products.columns,
    },
}

if (
    "product_category_name" in translation.columns
    and "product_category_name" in products.columns
):
    translation_categories = (
        translation.select("product_category_name")
        .where(F.col("product_category_name").isNotNull())
        .distinct()
    )
    product_categories = (
        products.select("product_category_name")
        .where(F.col("product_category_name").isNotNull())
        .distinct()
    )
    missing_translation = product_categories.join(
        translation_categories,
        "product_category_name",
        "left_anti",
    )
    unused_translation = translation_categories.join(
        product_categories,
        "product_category_name",
        "left_anti",
    )
    relationship_evidence["category_relationship"] = {
        "translation_distinct_categories": int(translation_categories.count()),
        "products_distinct_non_null_categories": int(product_categories.count()),
        "product_categories_missing_translation_count": int(
            missing_translation.count()
        ),
        "product_categories_missing_translation_values": [
            row["product_category_name"]
            for row in missing_translation.orderBy("product_category_name").collect()
        ],
        "translations_not_used_by_products_count": int(unused_translation.count()),
        "translations_not_used_by_products_values": [
            row["product_category_name"]
            for row in unused_translation.orderBy("product_category_name").collect()
        ],
    }
    display(missing_translation.orderBy("product_category_name"))
    display(unused_translation.orderBy("product_category_name"))
else:
    relationship_evidence["category_relationship"] = {
        "evaluated": False,
        "reason": "product_category_name missing from one or both schemas",
    }

# COMMAND ----------

hash_columns = [
    F.coalesce(F.col(column), F.lit("<NULL>")) for column in translation.columns
]
row_hash = F.xxhash64(*hash_columns)
signature = translation.agg(
    F.count("*").alias("row_count"),
    F.countDistinct(row_hash).alias("distinct_row_hashes"),
    F.sum(row_hash.cast("decimal(38,0)")).alias("row_hash_sum"),
).first()

summary = {
    "source": {
        **file_metadata(SOURCE_PATH),
        "row_count": translation_row_count,
        "column_count": len(translation.columns),
        "columns": translation.columns,
        "schema": {
            field.name: field.dataType.simpleString()
            for field in translation.schema.fields
        },
    },
    "column_profile": profile,
    "candidate_key": candidate_key_evidence,
    "full_row_duplicates": {
        "duplicate_group_count": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "encoding_profile": encoding_profile,
    "relationships": relationship_evidence,
    "content_signature": {
        "row_count": int(signature["row_count"]),
        "distinct_row_hashes": int(signature["distinct_row_hashes"]),
        "row_hash_sum": str(signature["row_hash_sum"]),
    },
    "snapshot_cadence_evidence": (
        "One physical CSV snapshot observed by this run; no business date or refresh "
        "cadence is inferred from the file alone."
    ),
}

print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
