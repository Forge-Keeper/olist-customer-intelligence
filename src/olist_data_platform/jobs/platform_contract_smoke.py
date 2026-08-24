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
        description=(
            "Validate Delta contract lifecycle behavior in a Databricks dev workspace."
        )
    )
    parser.add_argument("--gdp-table", required=True)
    parser.add_argument("--scratch-prefix", required=True)
    return parser


def _scratch_contract() -> DatasetContract:
    """Return the disposable base contract used by lifecycle smoke fixtures."""
    return replace(
        IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
        metadata=replace(
            IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG.metadata,
            description=(
                "Disposable dev table for Delta contract lifecycle smoke validation."
            ),
        ),
    )


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
    """Run lifecycle idempotency, drift and additive-evolution checks in dev.

    The GDP table is only ensured/validated. Drift and evolution are isolated to
    separate disposable tables derived from the supplied scratch prefix.
    """
    gdp_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=args.gdp_table,
        contract=IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
    )
    gdp_lifecycle.ensure()
    gdp_lifecycle.ensure()

    scratch_contract = _scratch_contract()
    drift_table = f"{args.scratch_prefix}_drift"
    evolution_table = f"{args.scratch_prefix}_evolution"

    drift_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=drift_table,
        contract=scratch_contract,
    )
    drift_lifecycle.ensure()
    drift_lifecycle.ensure()
    spark.sql(f"ALTER TABLE {drift_table} ADD COLUMNS (`unsupported_drift` STRING)")
    try:
        drift_lifecycle.ensure()
    except ValueError:
        pass
    else:
        raise AssertionError("Expected unsupported schema drift to fail fast.")

    evolution_base_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=evolution_table,
        contract=scratch_contract,
    )
    evolution_base_lifecycle.ensure()
    evolution_lifecycle = DeltaTableLifecycle(
        spark=spark,
        target_table=evolution_table,
        contract=_evolution_contract(scratch_contract),
    )
    evolution_lifecycle.ensure()

    evolved_columns = {
        field.name for field in spark.table(evolution_table).schema.fields
    }
    if "smoke_nullable_note" not in evolved_columns:
        raise AssertionError(
            "Expected opt-in nullable additive evolution to materialize."
        )

    print(
        "platform_contract_smoke_completed "
        f"gdp_table={args.gdp_table} drift_table={drift_table} "
        f"evolution_table={evolution_table}"
    )


def main() -> None:
    """Execute the Databricks dev contract smoke job."""
    args = build_parser().parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    run(args=args, spark=spark)


if __name__ == "__main__":
    main()
