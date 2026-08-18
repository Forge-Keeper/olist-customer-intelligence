from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType

REQUIRED_SOURCE_COLUMNS = (
    "mql_id",
    "seller_id",
    "sdr_id",
    "sr_id",
    "won_date",
    "business_segment",
    "lead_type",
    "lead_behaviour_profile",
    "has_company",
    "has_gtin",
    "average_stock",
    "business_type",
    "declared_product_catalog_size",
    "declared_monthly_revenue",
    "source_file",
)


def validate_table(spark: SparkSession, target_table: str) -> None:
    dataframe = spark.table(target_table)
    row_count = dataframe.count()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    if row_count != 842:
        raise AssertionError(f"Expected 842 rows, got {row_count}.")

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

    if (
        dataframe.groupBy("mql_id")
        .count()
        .where(F.col("count") > 1)
        .limit(1)
        .count()
    ):
        raise AssertionError("mql_id contains duplicate values.")

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
