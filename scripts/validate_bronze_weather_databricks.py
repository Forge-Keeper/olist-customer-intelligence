from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, VariantType

EXPECTED_CLUSTERING_COLUMNS = ["dt_base"]
EXPECTED_PARTITION_COLUMNS: list[str] = []
PRIMARY_KEY_COLUMNS = [
    "dt_base",
    "requested_latitude",
    "requested_longitude",
]


def validate_table(spark: SparkSession, target_table: str) -> None:
    if not spark.catalog.tableExists(target_table):
        raise ValueError(f"Table does not exist: {target_table}")

    dataframe = spark.table(target_table)
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    if not isinstance(schema.get("dt_base"), DateType):
        raise AssertionError("dt_base must be DATE.")

    if not isinstance(schema.get("payload"), VariantType):
        raise AssertionError("payload must be VARIANT.")

    detail = spark.sql(f"DESCRIBE DETAIL {target_table}").first()
    if detail is None:
        raise AssertionError("DESCRIBE DETAIL returned no metadata.")

    if detail["format"] != "delta":
        raise AssertionError(f"Expected Delta table, got {detail['format']!r}.")

    partition_columns = list(detail["partitionColumns"] or [])
    if partition_columns != EXPECTED_PARTITION_COLUMNS:
        raise AssertionError(
            "Unexpected partition columns: "
            f"expected={EXPECTED_PARTITION_COLUMNS}, actual={partition_columns}"
        )

    clustering_columns = list(detail["clusteringColumns"] or [])
    if clustering_columns != EXPECTED_CLUSTERING_COLUMNS:
        raise AssertionError(
            "Unexpected clustering columns: "
            f"expected={EXPECTED_CLUSTERING_COLUMNS}, actual={clustering_columns}"
        )

    null_condition = None
    for column_name in PRIMARY_KEY_COLUMNS:
        condition = F.col(column_name).isNull()
        null_condition = condition if null_condition is None else null_condition | condition

    if null_condition is not None and dataframe.where(null_condition).limit(1).count():
        raise AssertionError("Bronze table contains NULL primary-key values.")

    duplicate_count = (
        dataframe.groupBy(*PRIMARY_KEY_COLUMNS)
        .count()
        .where(F.col("count") > 1)
        .limit(1)
        .count()
    )
    if duplicate_count:
        raise AssertionError("Bronze table contains duplicate primary keys.")

    print(f"Validation passed for {target_table}")
    print(f"rows={dataframe.count()}")
    print(f"partition_columns={partition_columns}")
    print(f"clustering_columns={clustering_columns}")
    print(f"table_features={list(detail['tableFeatures'] or [])}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the Weather Bronze table on Databricks."
    )
    parser.add_argument(
        "--target-table",
        required=True,
        help="Fully qualified Bronze table name, for example catalog.bronze.weather_daily.",
    )
    args = parser.parse_args()

    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    validate_table(spark=spark, target_table=args.target_table)


if __name__ == "__main__":
    main()
