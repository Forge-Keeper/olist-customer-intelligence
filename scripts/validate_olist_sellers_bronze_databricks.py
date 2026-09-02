from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType

REQUIRED_BUSINESS_COLUMNS = (
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state",
)
REQUIRED_SOURCE_COLUMNS = (*REQUIRED_BUSINESS_COLUMNS, "source_file")


def validate_table(spark: SparkSession, target_table: str) -> None:
    """Validate the persisted Sellers Bronze shape without hardcoded row counts."""
    dataframe = spark.table(target_table)
    row_count = dataframe.count()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    if row_count == 0:
        raise AssertionError("Olist sellers Bronze table cannot be empty.")

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

    for column in REQUIRED_BUSINESS_COLUMNS:
        null_rows = dataframe.where(F.col(column).isNull()).limit(1).count()
        if null_rows:
            raise AssertionError(f"{column} contains NULL values.")

    duplicate_primary_keys = (
        dataframe.groupBy("seller_id")
        .count()
        .where(F.col("count") > 1)
        .limit(1)
        .count()
    )
    if duplicate_primary_keys:
        raise AssertionError("seller_id contains duplicate values.")

    invalid_zip_prefixes = (
        dataframe.where(~F.col("seller_zip_code_prefix").rlike(r"^[0-9]{5}$"))
        .limit(1)
        .count()
    )
    if invalid_zip_prefixes:
        raise AssertionError(
            "seller_zip_code_prefix contains values outside the five-digit shape."
        )

    leading_zero_zip_codes = (
        dataframe.where(F.col("seller_zip_code_prefix").startswith("0"))
        .limit(1)
        .count()
    )
    if not leading_zero_zip_codes:
        raise AssertionError(
            "Expected at least one ZIP prefix with a leading zero "
            "to prove STRING preservation."
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
