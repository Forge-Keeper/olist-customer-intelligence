from __future__ import annotations

import argparse
from dataclasses import replace

from pyspark.sql import SparkSession

from olist_data_platform.domains.bronze.ibge.municipality_gdp_bronze_config import (
    IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta import (
    ColumnContract,
    DatasetContract,
    DeltaTableLifecycle,
    SchemaEvolutionPolicy,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the Databricks dev contract smoke job."""
    parser = argparse.ArgumentParser(
        description="Validate Delta contract lifecycle behavior in a Databricks dev workspace."
    )
    parser.add_argument("--gdp-table", required=True)
    parser.add_argument("--scratch-table", required=True)
    return parser


def _evolution_contract(base: DatasetContract) -> DatasetContract:
    """Return a disposable contract with one nullable additive column enabled."""
    additive_column = ColumnContract(
        name="smoke_nullable_note",
        data_type="string",
        nullable=True,
        description="Disposable nullable column used by the lifecycle smoke test.",
    )
    return replace(
        base,
        columns=(*base.columns, additive_column),
        schema_evolution=SchemaEvolutionPolicy(enabled=True),
    )


def run(args: argparse.Namespace, spark: SparkSession) -> None:
    """Run idempotency, drift and additive-evolution checks against dev tables.

    The GDP table is only ensured/validated. Destructive drift and evolution
    checks are isolated to the explicitly supplied scratch table.
    """
    gdp_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=args.gdp_table,
        contract=IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
    )
    gdp_lifecycle.ensure()
    gdp_lifecycle.ensure()

    scratch_contract = replace(
        IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
        metadata=replace(
            IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG.metadata,
            description="Disposable dev table for Delta contract lifecycle smoke validation.",
        ),
    )
    scratch_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=args.scratch_table,
        contract=scratch_contract,
    )
    scratch_lifecycle.ensure()
    scratch_lifecycle.ensure()

    spark.sql(
        f"ALTER TABLE {args.scratch_table} ADD COLUMNS (`unsupported_drift` STRING)"
    )
    try:
        scratch_lifecycle.ensure()
    except ValueError:
        pass
    else:
        raise AssertionError("Expected unsupported schema drift to fail fast.")

    spark.sql(f"ALTER TABLE {args.scratch_table} DROP COLUMN `unsupported_drift`")

    evolution_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=args.scratch_table,
        contract=_evolution_contract(scratch_contract),
    )
    evolution_lifecycle.ensure()

    evolved_columns = {field.name for field in spark.table(args.scratch_table).schema.fields}
    if "smoke_nullable_note" not in evolved_columns:
        raise AssertionError("Expected opt-in nullable additive evolution to materialize.")

    print(
        "platform_contract_smoke_completed "
        f"gdp_table={args.gdp_table} scratch_table={args.scratch_table}"
    )


def main() -> None:
    """Execute the Databricks dev contract smoke job."""
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    run(args=args, spark=spark)


if __name__ == "__main__":
    main()
