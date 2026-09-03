from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType

REQUIRED_BUSINESS_COLUMNS = (
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
)
NUMERIC_SOURCE_COLUMNS = REQUIRED_BUSINESS_COLUMNS[2:]
REQUIRED_SOURCE_COLUMNS = (*REQUIRED_BUSINESS_COLUMNS, "source_file")


def validate_table(spark: SparkSession, target_table: str) -> None:
    """Validate the persisted Products Bronze shape without row-count constants."""
    dataframe = spark.table(target_table)
    row_count = dataframe.count()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    if row_count == 0:
        raise AssertionError("Olist Products Bronze table cannot be empty.")

    missing_columns = set(REQUIRED_SOURCE_COLUMNS) - set(dataframe.columns)
    if missing_columns:
        raise AssertionError(
            f"Missing required Bronze columns: {sorted(missing_columns)}"
        )

    for column in REQUIRED_SOURCE_COLUMNS:
        if not isinstance(schema[column], StringType):
            raise AssertionError(
                f"Expected {column} to be STRING, got {schema[column].simpleString()}."
            )

    if not isinstance(schema.get("ingestion_timestamp"), TimestampType):
        raise AssertionError("ingestion_timestamp must be TIMESTAMP.")

    if dataframe.where(F.col("product_id").isNull()).limit(1).count():
        raise AssertionError("product_id contains NULL values.")

    duplicate_primary_keys = (
        dataframe.groupBy("product_id")
        .count()
        .where(F.col("count") > 1)
        .limit(1)
        .count()
    )
    if duplicate_primary_keys:
        raise AssertionError("product_id contains duplicate values.")

    invalid_numeric_expression = " OR ".join(
        f"({column} IS NOT NULL AND NOT ({column} RLIKE '^[0-9]+$'))"
        for column in NUMERIC_SOURCE_COLUMNS
    )
    if dataframe.where(F.expr(invalid_numeric_expression)).limit(1).count():
        raise AssertionError(
            "Products numeric source attributes contain malformed values."
        )

    detail = spark.sql(f"DESCRIBE DETAIL {target_table}").first()
    if detail is None:
        raise AssertionError("DESCRIBE DETAIL returned no result.")

    partition_columns = list(detail["partitionColumns"] or [])
    clustering_columns = list(detail["clusteringColumns"] or [])

    if partition_columns:
        raise AssertionError(
            f"Expected no partition columns, got {partition_columns}."
        )
    if clustering_columns:
        raise AssertionError(
            f"Expected no clustering columns, got {clustering_columns}."
        )

    print(
        "Validation passed for "
        f"{target_table} rows={row_count} "
        f"partition_columns={partition_columns} "
        f"clustering_columns={clustering_columns}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-table", required=True)
    args = parser.parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    validate_table(spark, args.target_table)


if __name__ == "__main__":
    main()
