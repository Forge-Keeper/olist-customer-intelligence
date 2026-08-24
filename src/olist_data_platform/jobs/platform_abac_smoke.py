from __future__ import annotations

import argparse

from pyspark.sql import Row, SparkSession

from olist_data_platform.platform.governance import (
    GovernancePolicyDefinition,
    GovernancePolicyLifecycle,
    GovernancePolicyScope,
    GovernancePolicyType,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the Databricks dev ABAC smoke job."""
    parser = argparse.ArgumentParser(
        description="Validate Unity Catalog ABAC row filters and column masks in dev."
    )
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", default="governance_validation")
    parser.add_argument("--tag-key", required=True)
    parser.add_argument("--cleanup", action="store_true")
    return parser


def _qualified(catalog: str, schema: str, name: str) -> str:
    return f"{catalog}.{schema}.{name}"


def _policy_definitions(
    *, catalog: str, schema: str, tag_key: str
) -> tuple[GovernancePolicyDefinition, GovernancePolicyDefinition]:
    scope_name = f"{catalog}.{schema}"
    row_filter = GovernancePolicyDefinition(
        name="olist_abac_demo_row_filter",
        policy_type=GovernancePolicyType.ROW_FILTER,
        scope=GovernancePolicyScope.SCHEMA,
        scope_name=scope_name,
        function_name=_qualified(catalog, schema, "olist_abac_allow_region"),
        principals=("account users",),
        match_condition=f"has_tag_value('{tag_key}', 'region')",
        match_alias="region_col",
        using_columns=("region_col",),
        description="Disposable dev ABAC row-filter validation policy.",
    )
    column_mask = GovernancePolicyDefinition(
        name="olist_abac_demo_column_mask",
        policy_type=GovernancePolicyType.COLUMN_MASK,
        scope=GovernancePolicyScope.SCHEMA,
        scope_name=scope_name,
        function_name=_qualified(catalog, schema, "olist_abac_mask_secret"),
        principals=("account users",),
        match_condition=f"has_tag_value('{tag_key}', 'secret')",
        match_alias="secret_col",
        description="Disposable dev ABAC column-mask validation policy.",
    )
    return row_filter, column_mask


def _row_value(row, *keys: str):
    for key in keys:
        try:
            value = row[key]
        except (KeyError, TypeError, ValueError):
            continue
        if value is not None:
            return value
    return None


def _existing_policy_names(spark: SparkSession, scope_name: str) -> set[str]:
    """Return policy names currently attached directly to the schema."""
    rows = spark.sql(f"SHOW POLICIES ON SCHEMA {scope_name}").collect()
    names: set[str] = set()
    for row in rows:
        name = _row_value(row, "Policy Name", "policy_name")
        if isinstance(name, str):
            names.add(name)
    return names


def _cleanup(spark: SparkSession, *, catalog: str, schema: str) -> None:
    """Remove disposable ABAC fixtures using supported Databricks SQL syntax."""
    scope_name = f"{catalog}.{schema}"
    existing_policies = _existing_policy_names(spark, scope_name)
    for policy_name in (
        "olist_abac_demo_row_filter",
        "olist_abac_demo_column_mask",
    ):
        if policy_name in existing_policies:
            spark.sql(f"DROP POLICY {policy_name} ON SCHEMA {scope_name}")

    table_name = _qualified(catalog, schema, "abac_people_demo")
    allow_region_fn = _qualified(catalog, schema, "olist_abac_allow_region")
    mask_secret_fn = _qualified(catalog, schema, "olist_abac_mask_secret")
    spark.sql(f"DROP TABLE IF EXISTS {table_name}")
    spark.sql(f"DROP FUNCTION IF EXISTS {allow_region_fn}")
    spark.sql(f"DROP FUNCTION IF EXISTS {mask_secret_fn}")


def run(args: argparse.Namespace, spark: SparkSession) -> None:
    """Create synthetic fixtures and prove row filtering plus column masking."""
    catalog = args.catalog
    schema = args.schema
    tag_key = args.tag_key
    scope_name = f"{catalog}.{schema}"
    table_name = _qualified(catalog, schema, "abac_people_demo")
    allow_region_fn = _qualified(catalog, schema, "olist_abac_allow_region")
    mask_secret_fn = _qualified(catalog, schema, "olist_abac_mask_secret")

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {scope_name}")
    _cleanup(spark, catalog=catalog, schema=schema)

    spark.sql(
        f"""
        CREATE TABLE {table_name} (
          id INT,
          region STRING,
          synthetic_secret STRING
        ) USING DELTA
        """
    )
    spark.createDataFrame(
        [
            (1, "public", "secret-alpha"),
            (2, "restricted", "secret-beta"),
            (3, "public", "secret-gamma"),
        ],
        "id INT, region STRING, synthetic_secret STRING",
    ).write.mode("append").saveAsTable(table_name)

    spark.sql(
        f"ALTER TABLE {table_name} ALTER COLUMN region "
        f"SET TAGS ('{tag_key}' = 'region')"
    )
    spark.sql(
        f"ALTER TABLE {table_name} ALTER COLUMN synthetic_secret "
        f"SET TAGS ('{tag_key}' = 'secret')"
    )

    spark.sql(
        f"""
        CREATE OR REPLACE FUNCTION {allow_region_fn}
        (region STRING)
        RETURNS BOOLEAN
        RETURN region <> 'restricted'
        """
    )
    spark.sql(
        f"""
        CREATE OR REPLACE FUNCTION {mask_secret_fn}
        (secret STRING)
        RETURNS STRING
        RETURN '***MASKED***'
        """
    )

    row_filter, column_mask = _policy_definitions(
        catalog=catalog,
        schema=schema,
        tag_key=tag_key,
    )
    GovernancePolicyLifecycle(spark, row_filter).ensure()
    GovernancePolicyLifecycle(spark, column_mask).ensure()

    observed = spark.sql(
        f"SELECT id, region, synthetic_secret FROM {table_name} ORDER BY id"
    ).collect()
    expected = [
        Row(id=1, region="public", synthetic_secret="***MASKED***"),
        Row(id=3, region="public", synthetic_secret="***MASKED***"),
    ]
    if observed != expected:
        raise AssertionError(
            "ABAC behavior did not match expected filtered/masked result: "
            f"observed={observed!r}"
        )

    print(
        "platform_abac_smoke_completed "
        f"scope={scope_name} table={table_name} "
        f"row_count={len(observed)} masked=true"
    )

    if args.cleanup:
        _cleanup(spark, catalog=catalog, schema=schema)
        print("platform_abac_smoke_cleanup_completed")


def main() -> None:
    """Execute the Databricks dev ABAC smoke job."""
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    run(args=args, spark=spark)


if __name__ == "__main__":
    main()
