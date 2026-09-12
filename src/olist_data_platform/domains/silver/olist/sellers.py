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

_SOURCE_COLUMNS = (
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state",
    "source_file",
    "ingestion_timestamp",
)

OLIST_SELLERS_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract("seller_id", "string", False, "Seller identifier."),
        ColumnContract(
            "seller_zip_code_prefix",
            "string",
            True,
            "Seller ZIP code prefix with leading zeroes preserved.",
        ),
        ColumnContract("seller_city", "string", True, "Seller city."),
        ColumnContract("seller_state", "string", True, "Seller state code."),
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
            "Bronze ingestion timestamp retained as provenance.",
        ),
        ColumnContract(
            "silver_processed_timestamp",
            "timestamp",
            False,
            "Timestamp when the Silver row was produced.",
        ),
    ),
    key_columns=("seller_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Conformed Olist sellers at seller_id grain.",
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_SELLERS_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_sellers",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-SELLERS-DQ01",
            version=1,
            description="seller_id must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("seller_id",),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-SELLERS-DQ02",
            version=1,
            description="seller_id must be unique.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("seller_id",),
        ),
    ),
)


def transform_sellers(bronze: DataFrame) -> DataFrame:
    missing = sorted(set(_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Sellers Bronze input is missing required columns: "
            f"{missing}"
        )
    return bronze.select(
        F.col("seller_id").cast("string").alias("seller_id"),
        F.col("seller_zip_code_prefix")
        .cast("string")
        .alias("seller_zip_code_prefix"),
        F.col("seller_city").cast("string").alias("seller_city"),
        F.col("seller_state").cast("string").alias("seller_state"),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
    )


def process_sellers_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    checked = DataQualityRunner().evaluate(
        dataframe=transform_sellers(bronze),
        contract=OLIST_SELLERS_SILVER_QUALITY_CONTRACT,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
    QualityResultWriter(spark, quality_results_table).write(checked.report)
    checked.report.raise_for_blocking_failures()
    if checked.report.row_count == 0:
        raise ValueError(
            "Silver Sellers FULL_REPLACE snapshot cannot be empty; "
            "the existing target was preserved."
        )
    DeltaTableLifecycle(
        spark,
        target_table,
        OLIST_SELLERS_SILVER_CONTRACT,
    ).ensure()
    (
        checked.dataframe.select(*OLIST_SELLERS_SILVER_CONTRACT.required_columns)
        .write.format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
    )
    return checked.report
