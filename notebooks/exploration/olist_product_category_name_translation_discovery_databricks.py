# Databricks notebook source
# MAGIC %md
# MAGIC # Olist Product Category Name Translation — Bronze Discovery
# MAGIC
# MAGIC Read-only profiling for the physical Product Category Name Translation CSV.
# MAGIC This notebook does not create tables, write Control Plane evidence, cache data,
# MAGIC or mutate source data.

# COMMAND ----------

dbutils.widgets.text(
    "source_path",
    "",
    "Product Category Translation CSV source path",
)
dbutils.widgets.text(
    "products_source_path",
    "",
    "Olist Products CSV source path (optional)",
)

# COMMAND ----------

SOURCE_PATH = dbutils.widgets.get("source_path").strip()
PRODUCTS_SOURCE_PATH = dbutils.widgets.get("products_source_path").strip()

if not SOURCE_PATH:
    raise ValueError("Set source_path before running Discovery.")

# COMMAND ----------

import json
from pathlib import PurePosixPath

from pyspark.sql import functions as F


def _file_metadata(path: str) -> dict[str, object]:
    parent = str(PurePosixPath(path).parent)
    name = PurePosixPath(path).name
    matches = [x for x in dbutils.fs.ls(parent) if x.name.rstrip("/") == name]
    if not matches:
        raise FileNotFoundError(path)
    info = matches[0]
    return {
        "path": info.path,
        "name": info.name,
        "size_bytes": int(info.size),
        "modification_time_ms": int(info.modificationTime),
    }


def _read_csv(path: str):
    return (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .csv(path)
    )


file_metadata = _file_metadata(SOURCE_PATH)
df = _read_csv(SOURCE_PATH)
row_count = df.count()

print("source_path =", SOURCE_PATH)
print("row_count =", row_count)
print("columns =", df.columns)
df.printSchema()
display(df.limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Source inventory and schema
# MAGIC
# MAGIC Discovery intentionally does not assert an expected schema. The physical header,
# MAGIC source-level Spark types and file metadata are captured as evidence first.

# COMMAND ----------

schema_evidence = {
    field.name: field.dataType.simpleString() for field in df.schema.fields
}

source_evidence = {
    **file_metadata,
    "row_count": row_count,
    "column_count": len(df.columns),
    "columns": df.columns,
    "schema": schema_evidence,
}

print(json.dumps(source_evidence, indent=2, sort_keys=True, ensure_ascii=False))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Completeness, blanks, trim differences and cardinality

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
        F.countDistinct(F.lower(F.trim(value))).alias("distinct_trim_lower"),
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
        "distinct_trim_lower": int(row["distinct_trim_lower"] or 0),
    }

display(
    spark.createDataFrame(
        [{"column": column, **stats} for column, stats in profile.items()]
    ).orderBy("column")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exact duplicate rows

# COMMAND ----------

full_duplicates = df.groupBy(*df.columns).count().where(F.col("count") > 1)
full_duplicate_groups = full_duplicates.count()
full_duplicate_excess = (
    full_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"]
    or 0
)

display(full_duplicates.orderBy(F.desc("count")).limit(100))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Candidate grain evidence
# MAGIC
# MAGIC If `product_category_name` is physically present, profile it as the candidate
# MAGIC source key because it is the relationship column used by the Products snapshot.
# MAGIC This is evidence only; the notebook does not declare the grain as a requirement.

# COMMAND ----------

candidate_key_evidence = {}

if "product_category_name" in df.columns:
    key = F.col("product_category_name")
    key_stats = df.agg(
        F.countDistinct(key).alias("distinct_count"),
        F.sum(F.when(key.isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(
            F.when(key.isNotNull() & (F.trim(key) == ""), 1).otherwise(0)
        ).alias("blank_count"),
    ).first()

    key_duplicates = (
        df.groupBy("product_category_name")
        .count()
        .where(F.col("count") > 1)
    )
    key_duplicate_groups = key_duplicates.count()
    key_duplicate_excess = (
        key_duplicates.agg(F.sum(F.col("count") - 1).alias("n")).first()["n"]
        or 0
    )

    candidate_key_evidence = {
        "column": "product_category_name",
        "distinct_count": int(key_stats["distinct_count"] or 0),
        "null_count": int(key_stats["null_count"] or 0),
        "blank_count": int(key_stats["blank_count"] or 0),
        "duplicate_group_count": int(key_duplicate_groups),
        "duplicate_row_excess": int(key_duplicate_excess),
    }
    display(key_duplicates.orderBy(F.desc("count"), "product_category_name"))
else:
    print("product_category_name column not present; candidate grain not inferred.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Encoding and lexical shape
# MAGIC
# MAGIC Basic markers identify suspicious mojibake/replacement characters without
# MAGIC normalizing or altering source values.

# COMMAND ----------

encoding_rows = []
for column in df.columns:
    value = F.col(column)
    stats = df.agg(
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
    encoding_rows.append(
        {
            "column": column,
            "encoding_suspect_rows": int(stats["encoding_suspect_rows"] or 0),
        }
    )

display(spark.createDataFrame(encoding_rows).orderBy("column"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Value distributions

# COMMAND ----------

for column in df.columns:
    print(f"Distribution: {column}")
    display(
        df.groupBy(column)
        .count()
        .orderBy(F.desc("count"), F.col(column).asc_nulls_last())
        .limit(200)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Relationship to Olist Products
# MAGIC
# MAGIC If `products_source_path` is provided, compare raw category sets in both
# MAGIC directions. No normalization or blocking foreign-key rule is introduced here.

# COMMAND ----------

relationship_evidence = {
    "products_source_path_supplied": bool(PRODUCTS_SOURCE_PATH),
}

if PRODUCTS_SOURCE_PATH:
    products_metadata = _file_metadata(PRODUCTS_SOURCE_PATH)
    products = _read_csv(PRODUCTS_SOURCE_PATH)

    relationship_evidence["products_source"] = {
        **products_metadata,
        "row_count": int(products.count()),
        "columns": products.columns,
    }

    if (
        "product_category_name" in df.columns
        and "product_category_name" in products.columns
    ):
        translation_categories = (
            df.select("product_category_name")
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
            "reason": "product_category_name missing from one or both physical schemas",
        }
else:
    relationship_evidence["category_relationship"] = {
        "evaluated": False,
        "reason": "products_source_path not supplied",
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deterministic content signature

# COMMAND ----------

hash_columns = [F.coalesce(F.col(c), F.lit("<NULL>")) for c in df.columns]
row_hash = F.xxhash64(*hash_columns)
signature = df.agg(
    F.count("*").alias("row_count"),
    F.countDistinct(row_hash).alias("distinct_row_hashes"),
    F.sum(row_hash.cast("decimal(38,0)")).alias("row_hash_sum"),
).first()

# COMMAND ----------

summary = {
    "source": source_evidence,
    "column_profile": profile,
    "candidate_key": candidate_key_evidence,
    "full_row_duplicates": {
        "duplicate_group_count": int(full_duplicate_groups),
        "duplicate_row_excess": int(full_duplicate_excess),
    },
    "encoding_profile": encoding_rows,
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
