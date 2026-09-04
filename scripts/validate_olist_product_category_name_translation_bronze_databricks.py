from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType

REQUIRED_BUSINESS_COLUMNS = (
    "product_category_name",
    "product_category_name_english",
)
REQUIRED_SOURCE_COLUMNS = (*REQUIRED_BUSINESS_COLUMNS, "source_file")


def validate_table(spark: SparkSession, target_table: str) -> None:
    """Validate the persisted category translation Bronze shape."""
    dataframe = spark.table(target_table)
    row_count = dataframe.count()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    if row_count == 0:
        raise AssertionError("Olist category translation Bronze table cannot be empty.")

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
        invalid = dataframe.where(
            F.col(column).isNull() | (F.trim(F.col(column)) == "")
        ).limit(1).count()
        if invalid:
            raise AssertionError(f"{column} contains NULL or blank values.")

    duplicate_keys = (
        dataframe.groupBy("product_category_name")
        .count()
        .where(F.col("count") > 1)
        .limit(1)
        .count()
    )
    if duplicate_keys:
        raise AssertionError("product_category_name contains duplicate values.")

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
