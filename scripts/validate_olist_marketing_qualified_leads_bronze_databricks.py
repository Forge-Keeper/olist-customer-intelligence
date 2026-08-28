from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType

REQUIRED_SOURCE_COLUMNS = (
    "mql_id",
    "first_contact_date",
    "landing_page_id",
    "origin",
    "source_file",
)


def validate_table(spark: SparkSession, target_table: str) -> None:
    dataframe = spark.table(target_table)
    row_count = dataframe.count()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    if row_count != 8000:
        raise AssertionError(f"Expected 8000 rows, got {row_count}.")

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

    if dataframe.where(F.col("mql_id").isNull()).limit(1).count():
        raise AssertionError("mql_id contains NULL values.")

    duplicated = (
        dataframe.groupBy("mql_id")
        .count()
        .where(F.col("count") > 1)
        .limit(1)
        .count()
    )
    if duplicated:
        raise AssertionError("mql_id contains duplicate values.")

    required_nulls = dataframe.where(
        F.col("first_contact_date").isNull()
        | F.col("landing_page_id").isNull()
    ).limit(1).count()
    if required_nulls:
        raise AssertionError(
            "first_contact_date or landing_page_id contains NULL values."
        )

    date_parse_failures = dataframe.where(
        F.to_date("first_contact_date", "yyyy-MM-dd").isNull()
    ).limit(1).count()
    if date_parse_failures:
        raise AssertionError("first_contact_date contains unparseable values.")

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
