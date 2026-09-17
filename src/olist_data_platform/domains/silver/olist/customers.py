from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.contract import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.quality import (
    DataQualityContract,
    DataQualityRunner,
    NotNullRule,
    QualityCategory,
    QualityReport,
    QualitySeverity,
    UniqueRule,
)

_CUSTOMER_SOURCE_COLUMNS = (
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
    "source_file",
    "ingestion_timestamp",
)

OLIST_CUSTOMERS_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract(
            "customer_id",
            "string",
            False,
            "Transactional customer identifier and Silver grain.",
        ),
        ColumnContract(
            "customer_unique_id",
            "string",
            False,
            "Longitudinal customer identity from the Olist source.",
        ),
        ColumnContract(
            "customer_zip_code_prefix",
            "string",
            True,
            "Transaction-time customer ZIP prefix; leading zeroes are preserved.",
        ),
        ColumnContract(
            "customer_city",
            "string",
            True,
            "Transaction-time customer city from the source.",
        ),
        ColumnContract(
            "customer_state",
            "string",
            True,
            "Transaction-time customer state code from the source.",
        ),
        ColumnContract(
            "source_file",
            "string",
            True,
            "Source CSV lineage inherited from Bronze.",
        ),
        ColumnContract(
            "bronze_ingestion_timestamp",
            "timestamp",
            True,
            "Bronze ingestion timestamp retained as Silver provenance.",
        ),
        ColumnContract(
            "silver_processed_timestamp",
            "timestamp",
            False,
            "Timestamp when the row was produced by the Silver transformation.",
        ),
    ),
    key_columns=("customer_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description=(
            "Typed and validated Olist customer records at one row per customer_id."
        ),
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_CUSTOMERS_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_customers",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-CUSTOMERS-DQ01",
            version=1,
            description="customer_id must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("customer_id",),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-CUSTOMERS-DQ02",
            version=1,
            description="customer_id must remain unique at the Silver grain.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("customer_id",),
        ),
        NotNullRule(
            rule_id="OLIST-SILVER-CUSTOMERS-DQ03",
            version=1,
            description="customer_unique_id must be present for longitudinal identity.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("customer_unique_id",),
        ),
    ),
)


def transform_customers(bronze: DataFrame) -> DataFrame:
    """Build the explicit Silver customer projection from a Bronze snapshot."""
    missing = sorted(set(_CUSTOMER_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Customers Bronze input is missing required columns: "
            f"{missing}"
        )

    return bronze.select(
        F.col("customer_id").cast("string").alias("customer_id"),
        F.col("customer_unique_id").cast("string").alias("customer_unique_id"),
        F.col("customer_zip_code_prefix")
        .cast("string")
        .alias("customer_zip_code_prefix"),
        F.col("customer_city").cast("string").alias("customer_city"),
        F.col("customer_state").cast("string").alias("customer_state"),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
    )


def process_customers_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    """Validate and atomically replace the Silver Customers snapshot."""
    transformed = transform_customers(bronze)
    checked = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_CUSTOMERS_SILVER_QUALITY_CONTRACT,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
    QualityResultWriter(spark, quality_results_table).write(checked.report)
    checked.report.raise_for_blocking_failures()

    if checked.report.row_count == 0:
        raise ValueError(
            "Silver Customers FULL_REPLACE snapshot cannot be empty; "
            "the existing target was preserved."
        )

    lifecycle = DeltaTableLifecycle(
        spark,
        target_table,
        OLIST_CUSTOMERS_SILVER_CONTRACT,
    )
    lifecycle.ensure()
    (
        checked.dataframe.select(*OLIST_CUSTOMERS_SILVER_CONTRACT.required_columns)
        .write.format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
    )
    return checked.report
