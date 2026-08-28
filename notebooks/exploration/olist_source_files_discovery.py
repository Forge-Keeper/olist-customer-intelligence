# Databricks notebook source
# MAGIC %md
# MAGIC # Olist source files discovery
# MAGIC
# MAGIC Inventory and lightweight profiling notebook for the complete Olist source boundary.
# MAGIC
# MAGIC Scope:
# MAGIC - E-commerce dataset: all CSV files in the configured e-commerce source directory;
# MAGIC - Marketing Funnel dataset: all CSV files in the configured funnel source directory;
# MAGIC - capture file inventory, CSV columns, row counts and lightweight structural evidence;
# MAGIC - do not create Bronze tables or mutate source data.
# MAGIC
# MAGIC Environment-specific Volume paths are supplied explicitly through widgets.

# COMMAND ----------
dbutils.widgets.text("e_commerce_source_dir", "", "E-commerce source directory")
dbutils.widgets.text("funnel_source_dir", "", "Marketing Funnel source directory")

E_COMMERCE_SOURCE_DIR = dbutils.widgets.get("e_commerce_source_dir").strip().rstrip("/")
FUNNEL_SOURCE_DIR = dbutils.widgets.get("funnel_source_dir").strip().rstrip("/")

if not E_COMMERCE_SOURCE_DIR:
    raise ValueError("Set the e_commerce_source_dir widget before running discovery.")
if not FUNNEL_SOURCE_DIR:
    raise ValueError("Set the funnel_source_dir widget before running discovery.")

print("E-commerce source:", E_COMMERCE_SOURCE_DIR)
print("Marketing Funnel source:", FUNNEL_SOURCE_DIR)

# COMMAND ----------
from pathlib import PurePosixPath

from pyspark.sql import functions as F


def list_csv_files(source_dir: str) -> list[dict[str, object]]:
    files = []
    for item in dbutils.fs.ls(source_dir):
        if item.path.lower().endswith(".csv"):
            files.append(
                {
                    "name": item.name,
                    "path": item.path,
                    "size_bytes": item.size,
                }
            )
    return sorted(files, key=lambda item: str(item["name"]))


e_commerce_files = list_csv_files(E_COMMERCE_SOURCE_DIR)
funnel_files = list_csv_files(FUNNEL_SOURCE_DIR)

print(f"E-commerce CSV files: {len(e_commerce_files)}")
print(f"Marketing Funnel CSV files: {len(funnel_files)}")

# COMMAND ----------
file_inventory_rows = [
    {"dataset_group": "e_commerce", **item} for item in e_commerce_files
] + [{"dataset_group": "funnel", **item} for item in funnel_files]

file_inventory_df = spark.createDataFrame(file_inventory_rows)
display(file_inventory_df.orderBy("dataset_group", "name"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Structural profiling
# MAGIC
# MAGIC Each CSV is read with `inferSchema=false` so discovery sees source values as strings,
# MAGIC matching the current source-faithful Olist Bronze approach.

# COMMAND ----------
def profile_csv(dataset_group: str, file_info: dict[str, object]) -> dict[str, object]:
    path = str(file_info["path"])
    dataframe = spark.read.option("header", True).option("inferSchema", False).csv(path)
    return {
        "dataset_group": dataset_group,
        "file_name": str(file_info["name"]),
        "file_path": path,
        "size_bytes": int(file_info["size_bytes"]),
        "row_count": dataframe.count(),
        "column_count": len(dataframe.columns),
        "columns": dataframe.columns,
    }


profiles = [
    profile_csv("e_commerce", item) for item in e_commerce_files
] + [profile_csv("funnel", item) for item in funnel_files]

profile_df = spark.createDataFrame(profiles)
display(profile_df.orderBy("dataset_group", "file_name"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Coverage checkpoint
# MAGIC
# MAGIC Expected project boundary after the inventory decision:
# MAGIC - every CSV found in the configured E-commerce directory is required;
# MAGIC - every CSV found in the configured Marketing Funnel directory is required;
# MAGIC - no Olist source is intentionally excluded from the Bronze completion milestone.
# MAGIC
# MAGIC Use the output above as evidence for the exact physical file inventory before
# MAGIC implementing any additional Bronze dataset.

# COMMAND ----------
summary_df = (
    profile_df.groupBy("dataset_group")
    .agg(
        F.count("*").alias("csv_files"),
        F.sum("row_count").alias("rows_across_files"),
        F.sum("size_bytes").alias("bytes_across_files"),
    )
    .orderBy("dataset_group")
)
display(summary_df)
